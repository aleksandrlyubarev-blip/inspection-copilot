"""Read-only trust boundary for the fixed live-validation evidence artifact."""

from __future__ import annotations

import os
import stat
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import model_validator

from inspection_copilot.domain import StrictModel
from inspection_copilot.live_evidence import (
    LIVE_EVIDENCE_RELATIVE_PATH,
    MAX_LIVE_EVIDENCE_BYTES,
    LiveEvidenceRecord,
)


class LiveValidationState(StrEnum):
    NOT_RUN = "not_run"
    VERIFIED = "verified"
    UNTRUSTED_OR_UNAVAILABLE = "untrusted_or_unavailable"


class LiveValidationSnapshot(StrictModel):
    state: LiveValidationState
    record: LiveEvidenceRecord | None = None

    @model_validator(mode="after")
    def require_verified_record(self) -> Self:
        if (self.state is LiveValidationState.VERIFIED) != (self.record is not None):
            raise ValueError("only verified live validation can expose a record")
        return self


def load_live_validation(repo_root: Path) -> LiveValidationSnapshot:
    """Load the one fixed artifact without following links or changing repository state."""

    try:
        root = repo_root.resolve(strict=True)
        evidence_directory = root / LIVE_EVIDENCE_RELATIVE_PATH.parent
        directory_stat = evidence_directory.lstat()
    except FileNotFoundError:
        return _snapshot(LiveValidationState.NOT_RUN)
    except OSError:
        return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)

    if not stat.S_ISDIR(directory_stat.st_mode):
        return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)

    directory_fd = -1
    try:
        directory_fd = os.open(evidence_directory, _directory_open_flags())
        opened_directory_stat = os.fstat(directory_fd)
        if not _same_file(directory_stat, opened_directory_stat):
            return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)

        evidence_name = LIVE_EVIDENCE_RELATIVE_PATH.name
        try:
            evidence_stat = os.stat(
                evidence_name,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return _snapshot(LiveValidationState.NOT_RUN)
        if not stat.S_ISREG(evidence_stat.st_mode):
            return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)

        serialized = _read_fixed_evidence(
            evidence_name,
            directory_fd=directory_fd,
            expected_stat=evidence_stat,
        )
        evidence_stat_after_read = os.stat(
            evidence_name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        if not _same_snapshot(evidence_stat, evidence_stat_after_read):
            return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)
        if len(serialized) > MAX_LIVE_EVIDENCE_BYTES:
            return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)
        record = LiveEvidenceRecord.model_validate_json(serialized)
        evidence_stat_after_validation = os.stat(
            evidence_name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        if not _same_snapshot(evidence_stat, evidence_stat_after_validation):
            return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)
        directory_stat_after_validation = evidence_directory.lstat()
        if not stat.S_ISDIR(directory_stat_after_validation.st_mode) or not _same_file(
            directory_stat,
            directory_stat_after_validation,
        ):
            return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)
    except (OSError, ValueError):
        return _snapshot(LiveValidationState.UNTRUSTED_OR_UNAVAILABLE)
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)

    return LiveValidationSnapshot(state=LiveValidationState.VERIFIED, record=record)


def _read_fixed_evidence(
    evidence_name: str,
    *,
    directory_fd: int,
    expected_stat: os.stat_result,
) -> bytes:
    evidence_fd = os.open(
        evidence_name,
        _file_open_flags(),
        dir_fd=directory_fd,
    )
    try:
        opened_stat = os.fstat(evidence_fd)
        if not stat.S_ISREG(opened_stat.st_mode) or not _same_file(expected_stat, opened_stat):
            raise ValueError("live evidence changed during validation")
        with os.fdopen(evidence_fd, "rb") as evidence_file:
            evidence_fd = -1
            serialized = evidence_file.read(MAX_LIVE_EVIDENCE_BYTES + 1)
            completed_stat = os.fstat(evidence_file.fileno())
            if not _same_snapshot(opened_stat, completed_stat):
                raise ValueError("live evidence changed during validation")
            return serialized
    finally:
        if evidence_fd >= 0:
            os.close(evidence_fd)


def _directory_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _file_open_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)


def _same_file(expected: os.stat_result, actual: os.stat_result) -> bool:
    return expected.st_dev == actual.st_dev and expected.st_ino == actual.st_ino


def _same_snapshot(expected: os.stat_result, actual: os.stat_result) -> bool:
    return _same_file(expected, actual) and (
        expected.st_mode,
        expected.st_size,
        expected.st_mtime_ns,
        expected.st_ctime_ns,
        expected.st_nlink,
    ) == (
        actual.st_mode,
        actual.st_size,
        actual.st_mtime_ns,
        actual.st_ctime_ns,
        actual.st_nlink,
    )


def _snapshot(state: LiveValidationState) -> LiveValidationSnapshot:
    return LiveValidationSnapshot(state=state)


__all__ = [
    "LIVE_EVIDENCE_RELATIVE_PATH",
    "LiveValidationSnapshot",
    "LiveValidationState",
    "load_live_validation",
]
