import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

import inspection_copilot.live_validation as live_validation_module
from inspection_copilot.demo import load_demo_request, run_demo
from inspection_copilot.domain import InspectionRequest, ProviderOutcome, ProviderStatus
from inspection_copilot.live_evidence import (
    LIVE_EVIDENCE_RELATIVE_PATH as CONTRACT_LIVE_EVIDENCE_RELATIVE_PATH,
)
from inspection_copilot.live_evidence import (
    MAX_LIVE_EVIDENCE_BYTES,
    LiveEvidenceRecord,
    build_live_evidence,
)
from inspection_copilot.live_smoke import DEFAULT_LIVE_EVIDENCE_RELATIVE_PATH
from inspection_copilot.live_validation import (
    LIVE_EVIDENCE_RELATIVE_PATH,
    LiveValidationState,
    load_live_validation,
)
from inspection_copilot.service import Inspector, run_inspection

REPO_ROOT = Path(__file__).resolve().parents[1]


class FailureInspector(Inspector):
    model = "gpt-5.6"

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        return ProviderOutcome(
            status=ProviderStatus.TIMEOUT,
            assessment=None,
            requested_model=self.model,
            effective_model=None,
            prompt_version="inspection-v1",
        )


def _temporary_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "evidence").mkdir(parents=True)
    return repo_root


def _success_record() -> LiveEvidenceRecord:
    return build_live_evidence(
        run_demo(REPO_ROOT),
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=datetime(2026, 7, 16, 8, 30, tzinfo=UTC),
    )


def _failure_record() -> LiveEvidenceRecord:
    result = run_inspection(
        load_demo_request(REPO_ROOT),
        provider=FailureInspector(),
    )
    return build_live_evidence(
        result,
        provider_status=ProviderStatus.TIMEOUT,
        recorded_at=datetime(2026, 7, 16, 8, 31, tzinfo=UTC),
    )


def _write_record(repo_root: Path, record: LiveEvidenceRecord) -> Path:
    evidence_path = repo_root / LIVE_EVIDENCE_RELATIVE_PATH
    evidence_path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return evidence_path


def test_writer_and_reader_share_one_canonical_relative_path() -> None:
    assert LIVE_EVIDENCE_RELATIVE_PATH is CONTRACT_LIVE_EVIDENCE_RELATIVE_PATH
    assert DEFAULT_LIVE_EVIDENCE_RELATIVE_PATH is CONTRACT_LIVE_EVIDENCE_RELATIVE_PATH


def test_missing_canonical_evidence_is_not_run_and_decoy_is_ignored(tmp_path: Path) -> None:
    repo_root = _temporary_repo(tmp_path)
    (repo_root / "live_validation_evidence.json").write_text(
        _success_record().model_dump_json(),
        encoding="utf-8",
    )

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.NOT_RUN
    assert snapshot.record is None


@pytest.mark.parametrize("record_factory", [_success_record, _failure_record])
def test_strict_valid_record_is_verified_read_only(
    tmp_path: Path,
    record_factory: Callable[[], LiveEvidenceRecord],
) -> None:
    repo_root = _temporary_repo(tmp_path)
    record = record_factory()
    evidence_path = _write_record(repo_root, record)
    original_bytes = evidence_path.read_bytes()

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.VERIFIED
    assert snapshot.record == record
    assert evidence_path.read_bytes() == original_bytes


def test_tampered_record_is_untrusted_without_exposing_partial_data(tmp_path: Path) -> None:
    repo_root = _temporary_repo(tmp_path)
    payload = _success_record().model_dump()
    payload["record_id"] = "f" * 64
    evidence_path = repo_root / LIVE_EVIDENCE_RELATIVE_PATH
    evidence_path.write_text(LiveEvidenceRecord.model_construct(**payload).model_dump_json())
    original_bytes = evidence_path.read_bytes()

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert snapshot.record is None
    assert evidence_path.read_bytes() == original_bytes


def test_oversized_record_is_untrusted(tmp_path: Path) -> None:
    repo_root = _temporary_repo(tmp_path)
    evidence_path = repo_root / LIVE_EVIDENCE_RELATIVE_PATH
    evidence_path.write_bytes(b"{" + b" " * MAX_LIVE_EVIDENCE_BYTES)

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert snapshot.record is None


def test_symlink_and_non_regular_evidence_are_untrusted(tmp_path: Path) -> None:
    symlink_repo = _temporary_repo(tmp_path / "symlink")
    target = tmp_path / "outside.json"
    target.write_text(_success_record().model_dump_json(), encoding="utf-8")
    (symlink_repo / LIVE_EVIDENCE_RELATIVE_PATH).symlink_to(target)

    directory_repo = _temporary_repo(tmp_path / "directory")
    (directory_repo / LIVE_EVIDENCE_RELATIVE_PATH).mkdir()

    broken_repo = _temporary_repo(tmp_path / "broken")
    (broken_repo / LIVE_EVIDENCE_RELATIVE_PATH).symlink_to(tmp_path / "missing.json")

    linked_directory_repo = tmp_path / "linked-directory" / "repo"
    linked_directory_repo.mkdir(parents=True)
    external_evidence = tmp_path / "external-evidence"
    external_evidence.mkdir()
    (linked_directory_repo / "evidence").symlink_to(external_evidence, target_is_directory=True)

    assert load_live_validation(symlink_repo).state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert (
        load_live_validation(directory_repo).state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    )
    assert load_live_validation(broken_repo).state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert (
        load_live_validation(linked_directory_repo).state
        is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    )


def test_unreadable_evidence_is_untrusted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = _temporary_repo(tmp_path)
    _write_record(repo_root, _success_record())
    real_open = os.open

    def deny_open(path: str | Path, flags: int, *, dir_fd: int | None = None) -> int:
        if Path(path).name == LIVE_EVIDENCE_RELATIVE_PATH.name:
            raise PermissionError("refusing evidence read")
        if dir_fd is None:
            return real_open(path, flags)
        return real_open(path, flags, dir_fd=dir_fd)

    monkeypatch.setattr("inspection_copilot.live_validation.os.open", deny_open)

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert snapshot.record is None


@pytest.mark.parametrize("mutation", ["replace", "modify_in_place"])
def test_evidence_changed_during_read_is_untrusted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repo_root = _temporary_repo(tmp_path)
    evidence_path = _write_record(repo_root, _success_record())
    replacement_bytes = (_failure_record().model_dump_json(indent=2) + "\n").encode()
    real_read = live_validation_module._read_fixed_evidence

    def mutate_after_read(
        evidence_name: str,
        *,
        directory_fd: int,
        expected_stat: os.stat_result,
    ) -> bytes:
        serialized = real_read(
            evidence_name,
            directory_fd=directory_fd,
            expected_stat=expected_stat,
        )
        if mutation == "replace":
            replacement_path = tmp_path / "replacement.json"
            replacement_path.write_bytes(replacement_bytes)
            os.replace(replacement_path, evidence_path)
        else:
            evidence_path.write_bytes(replacement_bytes)
        return serialized

    monkeypatch.setattr(live_validation_module, "_read_fixed_evidence", mutate_after_read)

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert snapshot.record is None


def test_evidence_directory_replaced_during_read_is_untrusted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = _temporary_repo(tmp_path)
    _write_record(repo_root, _success_record())
    evidence_directory = repo_root / LIVE_EVIDENCE_RELATIVE_PATH.parent
    detached_directory = repo_root / "detached-evidence"
    replacement_directory = tmp_path / "replacement-evidence"
    replacement_directory.mkdir()
    real_read = live_validation_module._read_fixed_evidence

    def swap_directory_after_read(
        evidence_name: str,
        *,
        directory_fd: int,
        expected_stat: os.stat_result,
    ) -> bytes:
        serialized = real_read(
            evidence_name,
            directory_fd=directory_fd,
            expected_stat=expected_stat,
        )
        evidence_directory.rename(detached_directory)
        evidence_directory.symlink_to(replacement_directory, target_is_directory=True)
        return serialized

    monkeypatch.setattr(
        live_validation_module,
        "_read_fixed_evidence",
        swap_directory_after_read,
    )

    snapshot = load_live_validation(repo_root)

    assert snapshot.state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE
    assert snapshot.record is None
