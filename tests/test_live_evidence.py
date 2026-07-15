from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from inspection_copilot.demo import load_demo_request, run_demo
from inspection_copilot.domain import (
    InspectionRequest,
    ProviderOutcome,
    ProviderStatus,
    ReviewReason,
)
from inspection_copilot.live_evidence import (
    MAX_LIVE_EVIDENCE_BYTES,
    LiveEvidenceRecord,
    LiveEvidenceWriteStatus,
    build_live_evidence,
    load_live_evidence,
    write_live_evidence,
)
from inspection_copilot.service import Inspector, run_inspection

REPO_ROOT = Path(__file__).resolve().parents[1]


class TimeoutInspector(Inspector):
    model = "gpt-5.6"

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        return ProviderOutcome(
            status=ProviderStatus.TIMEOUT,
            assessment=None,
            requested_model=self.model,
            effective_model=None,
            prompt_version="inspection-v1",
        )


def test_success_record_contains_only_sanitized_contract_fields() -> None:
    result = run_demo(REPO_ROOT)
    recorded_at = datetime(2026, 7, 15, 12, 30, tzinfo=UTC)

    record = build_live_evidence(
        result,
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=recorded_at,
    )
    payload = record.model_dump(mode="json")
    serialized = record.model_dump_json()

    assert set(payload) == {
        "schema_version",
        "record_id",
        "recorded_at",
        "case_sha256",
        "provider_status",
        "final_decision",
        "evidence_complete",
        "review_reasons",
        "requested_model",
        "effective_model",
        "result_schema_version",
        "prompt_version",
        "policy_version",
        "sop_sha256",
        "image_sha256",
    }
    assert payload["schema_version"] == "1.0"
    assert record.case_sha256 == sha256(result.case_id.encode()).hexdigest()
    assert record.requested_model == result.provenance.requested_model
    assert record.effective_model == result.provenance.effective_model
    assert record.result_schema_version == result.provenance.schema_version
    assert result.case_id not in serialized
    assert result.assessment.summary not in serialized
    assert result.assessment.evidence[0].observation not in serialized
    assert "assessment" not in payload
    assert "summary" not in payload


def test_timestamp_is_normalized_to_utc_whole_seconds() -> None:
    local_time = datetime(
        2026,
        7,
        15,
        15,
        30,
        12,
        987654,
        tzinfo=timezone(timedelta(hours=3)),
    )

    record = build_live_evidence(
        run_demo(REPO_ROOT),
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=local_time,
    )

    assert record.recorded_at == datetime(2026, 7, 15, 12, 30, 12, tzinfo=UTC)
    assert record.model_dump(mode="json")["recorded_at"] == "2026-07-15T12:30:12Z"


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_live_evidence(
            run_demo(REPO_ROOT),
            provider_status=ProviderStatus.SUCCESS,
            recorded_at=datetime(2026, 7, 15, 12, 30),
        )


def test_record_id_tampering_is_rejected() -> None:
    record = build_live_evidence(
        run_demo(REPO_ROOT),
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=datetime(2026, 7, 15, 12, 30, tzinfo=UTC),
    )
    payload = record.model_dump()
    payload["record_id"] = "f" * 64

    with pytest.raises(ValidationError, match="record_id"):
        LiveEvidenceRecord.model_validate(payload)


def test_provider_failure_requires_matching_fail_closed_reason() -> None:
    result = run_inspection(
        load_demo_request(REPO_ROOT),
        provider=TimeoutInspector(),
    )

    record = build_live_evidence(
        result,
        provider_status=ProviderStatus.TIMEOUT,
        recorded_at=datetime(2026, 7, 15, 12, 30, tzinfo=UTC),
    )

    assert record.provider_status is ProviderStatus.TIMEOUT
    assert ReviewReason.PROVIDER_TIMEOUT in record.review_reasons
    assert record.effective_model is None

    with pytest.raises(ValidationError, match="provider status"):
        build_live_evidence(
            result,
            provider_status=ProviderStatus.SUCCESS,
            recorded_at=datetime(2026, 7, 15, 12, 30, tzinfo=UTC),
        )


def _record(*, minute: int = 30) -> LiveEvidenceRecord:
    return build_live_evidence(
        run_demo(REPO_ROOT),
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=datetime(2026, 7, 15, 12, minute, tzinfo=UTC),
    )


def test_exact_replay_is_a_byte_identical_no_op(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    record = _record()

    first = write_live_evidence(evidence_path, record)
    original_bytes = evidence_path.read_bytes()
    second = write_live_evidence(evidence_path, record)

    assert first.status is LiveEvidenceWriteStatus.WRITTEN
    assert second.status is LiveEvidenceWriteStatus.DUPLICATE
    assert second.record_id == first.record_id
    assert evidence_path.read_bytes() == original_bytes
    assert load_live_evidence(evidence_path) == record


def test_different_existing_evidence_is_a_non_destructive_conflict(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    write_live_evidence(evidence_path, _record(minute=30))
    original_bytes = evidence_path.read_bytes()

    with pytest.raises(FileExistsError, match="different live evidence"):
        write_live_evidence(evidence_path, _record(minute=31))

    assert evidence_path.read_bytes() == original_bytes


def test_oversized_evidence_is_rejected_before_json_parsing(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    evidence_path.write_bytes(b"{" + b" " * MAX_LIVE_EVIDENCE_BYTES)

    with pytest.raises(ValueError, match="size limit"):
        load_live_evidence(evidence_path)


def test_writer_requires_existing_parent_directory(tmp_path: Path) -> None:
    evidence_path = tmp_path / "missing" / "live_validation_evidence.json"

    with pytest.raises(FileNotFoundError, match="parent directory"):
        write_live_evidence(evidence_path, _record())

    assert not evidence_path.exists()


def test_failed_atomic_publish_cleans_up_without_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"

    def fail_link(source: Path, destination: Path) -> None:
        raise OSError(f"cannot publish {source.name} to {destination.name}")

    monkeypatch.setattr("inspection_copilot.live_evidence.os.link", fail_link)

    with pytest.raises(OSError, match="cannot publish"):
        write_live_evidence(evidence_path, _record())

    assert not evidence_path.exists()
    assert list(tmp_path.iterdir()) == []
