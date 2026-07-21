import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from openai import OpenAIError
from pydantic import ValidationError

from inspection_copilot.demo import run_demo
from inspection_copilot.domain import (
    Decision,
    InspectionRequest,
    ProviderOutcome,
    ProviderStatus,
)
from inspection_copilot.live_evidence import LiveEvidenceWriteStatus, load_live_evidence
from inspection_copilot.live_smoke import (
    LiveSmokeReceipt,
    live_smoke_marker_path,
    main,
    run_live_smoke,
)
from inspection_copilot.service import provider_review_reason

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDED_AT = datetime(2026, 7, 16, 9, 30, tzinfo=UTC)


class OutcomeInspector:
    model = "gpt-5.6"

    def __init__(self, outcome: ProviderOutcome) -> None:
        self.outcome = outcome
        self.calls = 0

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        self.calls += 1
        return self.outcome


class ExplodingInspector:
    model = "gpt-5.6"

    def __init__(self) -> None:
        self.calls = 0

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        self.calls += 1
        raise RuntimeError("private transport detail")


def _success_outcome() -> ProviderOutcome:
    return ProviderOutcome(
        status=ProviderStatus.SUCCESS,
        assessment=run_demo(REPO_ROOT).assessment,
        requested_model="gpt-5.6",
        effective_model="gpt-5.6-sol",
        prompt_version="inspection-v1",
    )


def _failure_outcome(status: ProviderStatus) -> ProviderOutcome:
    return ProviderOutcome(
        status=status,
        assessment=None,
        requested_model="gpt-5.6",
        effective_model=None,
        prompt_version="inspection-v1",
    )


def test_success_smoke_writes_status_from_one_actual_outcome(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    provider = OutcomeInspector(_success_outcome())
    factory_calls: list[Path] = []

    def factory(*, image_root: Path) -> OutcomeInspector:
        factory_calls.append(image_root)
        assert live_smoke_marker_path(evidence_path).is_file()
        return provider

    receipt = run_live_smoke(
        repo_root=REPO_ROOT,
        evidence_path=evidence_path,
        live_provider_factory=factory,
        clock=lambda: RECORDED_AT,
    )

    record = load_live_evidence(evidence_path)
    assert factory_calls == [(REPO_ROOT / "examples" / "synthetic").resolve()]
    assert provider.calls == 1
    assert receipt.provider_status is ProviderStatus.SUCCESS
    assert receipt.final_decision is Decision.FAIL
    assert receipt.record_id == record.record_id
    assert record.provider_status is provider.outcome.status
    assert record.recorded_at == RECORDED_AT
    assert not live_smoke_marker_path(evidence_path).exists()
    serialized = evidence_path.read_text(encoding="utf-8")
    assert provider.outcome.assessment is not None
    assert provider.outcome.assessment.summary not in serialized


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.TIMEOUT,
        ProviderStatus.RATE_LIMITED,
        ProviderStatus.UNAVAILABLE,
        ProviderStatus.REFUSAL,
        ProviderStatus.INVALID_OUTPUT,
    ],
)
def test_provider_failure_is_persisted_without_application_retry(
    status: ProviderStatus,
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    provider = OutcomeInspector(_failure_outcome(status))

    receipt = run_live_smoke(
        repo_root=REPO_ROOT,
        evidence_path=evidence_path,
        live_provider_factory=lambda *, image_root: provider,
        clock=lambda: RECORDED_AT,
    )

    record = load_live_evidence(evidence_path)
    assert provider.calls == 1
    assert receipt.provider_status is status
    assert record.provider_status is status
    assert record.final_decision is Decision.NEEDS_REVIEW
    assert provider_review_reason(status) in record.review_reasons
    assert not live_smoke_marker_path(evidence_path).exists()


def test_existing_evidence_refuses_before_provider_construction(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    original = b"existing evidence must remain untouched\n"
    evidence_path.write_bytes(original)

    def forbidden_factory(*, image_root: Path) -> OutcomeInspector:
        raise AssertionError(f"provider must not be built for {image_root}")

    with pytest.raises(FileExistsError, match="already exists"):
        run_live_smoke(
            repo_root=REPO_ROOT,
            evidence_path=evidence_path,
            live_provider_factory=forbidden_factory,
            clock=lambda: RECORDED_AT,
        )

    assert evidence_path.read_bytes() == original
    assert not live_smoke_marker_path(evidence_path).exists()


def test_broken_evidence_symlink_refuses_before_provider_construction(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    evidence_path.symlink_to(tmp_path / "missing-target.json")

    def forbidden_factory(*, image_root: Path) -> OutcomeInspector:
        raise AssertionError(f"provider must not be built for {image_root}")

    with pytest.raises(FileExistsError, match="already exists"):
        run_live_smoke(
            repo_root=REPO_ROOT,
            evidence_path=evidence_path,
            live_provider_factory=forbidden_factory,
            clock=lambda: RECORDED_AT,
        )

    assert evidence_path.is_symlink()
    assert not live_smoke_marker_path(evidence_path).exists()


def test_existing_reservation_refuses_before_provider_construction(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    marker_path = live_smoke_marker_path(evidence_path)
    marker_path.write_text("request-may-have-started\n", encoding="ascii")

    def forbidden_factory(*, image_root: Path) -> OutcomeInspector:
        raise AssertionError(f"provider must not be built for {image_root}")

    with pytest.raises(FileExistsError, match="reservation"):
        run_live_smoke(
            repo_root=REPO_ROOT,
            evidence_path=evidence_path,
            live_provider_factory=forbidden_factory,
            clock=lambda: RECORDED_AT,
        )

    assert marker_path.read_text(encoding="ascii") == "request-may-have-started\n"
    assert not evidence_path.exists()


def test_missing_parent_refuses_before_provider_construction(tmp_path: Path) -> None:
    evidence_path = tmp_path / "missing" / "live_validation_evidence.json"

    def forbidden_factory(*, image_root: Path) -> OutcomeInspector:
        raise AssertionError(f"provider must not be built for {image_root}")

    with pytest.raises(FileNotFoundError, match="parent directory"):
        run_live_smoke(
            repo_root=REPO_ROOT,
            evidence_path=evidence_path,
            live_provider_factory=forbidden_factory,
            clock=lambda: RECORDED_AT,
        )

    assert not evidence_path.exists()
    assert not live_smoke_marker_path(evidence_path).exists()


def test_provider_construction_failure_leaves_no_artifact(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"

    def unavailable_factory(*, image_root: Path) -> OutcomeInspector:
        raise OpenAIError(f"private credential detail for {image_root}")

    with pytest.raises(OpenAIError, match="private credential detail"):
        run_live_smoke(
            repo_root=REPO_ROOT,
            evidence_path=evidence_path,
            live_provider_factory=unavailable_factory,
            clock=lambda: RECORDED_AT,
        )

    assert not evidence_path.exists()
    assert not live_smoke_marker_path(evidence_path).exists()


def test_uncertain_post_boundary_failure_retains_reservation(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    provider = ExplodingInspector()

    with pytest.raises(RuntimeError, match="private transport detail"):
        run_live_smoke(
            repo_root=REPO_ROOT,
            evidence_path=evidence_path,
            live_provider_factory=lambda *, image_root: provider,
            clock=lambda: RECORDED_AT,
        )

    assert provider.calls == 1
    assert not evidence_path.exists()
    assert (
        live_smoke_marker_path(evidence_path).read_text(encoding="ascii")
        == "request-may-have-started\n"
    )


def test_live_smoke_cli_requires_confirmation_before_factory(capsys: Any) -> None:
    def forbidden_factory(*, image_root: Path) -> OutcomeInspector:
        raise AssertionError(f"provider must not be built for {image_root}")

    with pytest.raises(SystemExit) as error:
        main(["--repo-root", str(REPO_ROOT)], live_provider_factory=forbidden_factory)

    assert error.value.code == 2
    assert "--confirm-one-live-request" in capsys.readouterr().err


def test_live_smoke_cli_rejects_output_path_override(capsys: Any) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--evidence-path", "somewhere-else.json"])

    assert error.value.code == 2
    assert "unrecognized arguments: --evidence-path" in capsys.readouterr().err


def test_confirmed_cli_emits_only_sanitized_receipt(tmp_path: Path, capsys: Any) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    provider = OutcomeInspector(_success_outcome())

    main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--confirm-one-live-request",
        ],
        live_provider_factory=lambda *, image_root: provider,
        clock=lambda: RECORDED_AT,
        evidence_path=evidence_path,
    )

    output = capsys.readouterr().out
    receipt = LiveSmokeReceipt.model_validate_json(output)
    payload = json.loads(output)
    assert receipt.provider_status is ProviderStatus.SUCCESS
    assert set(payload) == {
        "schema_version",
        "record_id",
        "provider_status",
        "final_decision",
        "write_status",
    }
    assert "summary" not in output
    assert "assessment" not in output


def test_cli_sanitizes_post_boundary_failure_and_retains_reservation(
    tmp_path: Path,
    capsys: Any,
) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    provider = ExplodingInspector()

    with pytest.raises(SystemExit) as error:
        main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--confirm-one-live-request",
            ],
            live_provider_factory=lambda *, image_root: provider,
            clock=lambda: RECORDED_AT,
            evidence_path=evidence_path,
        )

    stderr = capsys.readouterr().err
    assert error.value.code == 2
    assert "inspect the reservation before any retry" in stderr
    assert "private transport detail" not in stderr
    assert live_smoke_marker_path(evidence_path).is_file()
    assert not evidence_path.exists()


def test_receipt_rejects_non_content_addressed_record_id() -> None:
    with pytest.raises(ValidationError, match="record_id"):
        LiveSmokeReceipt(
            record_id="private free text",
            provider_status=ProviderStatus.SUCCESS,
            final_decision=Decision.FAIL,
            write_status=LiveEvidenceWriteStatus.WRITTEN,
        )
