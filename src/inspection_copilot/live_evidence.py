"""Sanitized contract for one separately authorized live validation result."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from inspection_copilot.domain import (
    Decision,
    InspectionResult,
    ProviderStatus,
    ReviewReason,
    StrictModel,
)
from inspection_copilot.service import provider_review_reason

MAX_LIVE_EVIDENCE_BYTES = 64 * 1024
Identifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$",
    ),
]


class LiveEvidenceWriteStatus(StrEnum):
    WRITTEN = "written"
    DUPLICATE = "duplicate"


class LiveEvidenceWriteResult(StrictModel):
    status: LiveEvidenceWriteStatus
    record_id: str = Field(pattern=r"^[0-9a-f]{64}$")


class LiveEvidenceRecord(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    record_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    recorded_at: datetime
    case_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_status: ProviderStatus
    final_decision: Decision
    evidence_complete: bool
    review_reasons: list[ReviewReason]
    requested_model: Identifier
    effective_model: Identifier | None
    result_schema_version: Literal["1.0"]
    prompt_version: Identifier
    policy_version: Identifier
    sop_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("recorded_at")
    @classmethod
    def normalize_recorded_at(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value)

    @model_validator(mode="after")
    def require_consistent_record(self) -> Self:
        if len(self.review_reasons) != len(set(self.review_reasons)):
            raise ValueError("review reasons must be unique")
        if self.final_decision is Decision.NEEDS_REVIEW:
            if self.evidence_complete or not self.review_reasons:
                raise ValueError("needs_review evidence requires review reasons")
        elif not self.evidence_complete or self.review_reasons:
            raise ValueError("automatic evidence requires complete evidence")

        if self.provider_status is ProviderStatus.SUCCESS:
            if self.effective_model is None or any(
                reason in _PROVIDER_FAILURE_REASONS for reason in self.review_reasons
            ):
                raise ValueError("provider status does not match review reasons")
        else:
            expected_reason = provider_review_reason(self.provider_status)
            if (
                self.final_decision is not Decision.NEEDS_REVIEW
                or expected_reason not in self.review_reasons
            ):
                raise ValueError("provider status does not match fail-closed result")

        if self.record_id != _record_id(self):
            raise ValueError("record_id must match the sanitized record content")
        return self


_PROVIDER_FAILURE_REASONS = frozenset(
    provider_review_reason(status)
    for status in ProviderStatus
    if status is not ProviderStatus.SUCCESS
)


def build_live_evidence(
    result: InspectionResult,
    *,
    provider_status: ProviderStatus,
    recorded_at: datetime,
) -> LiveEvidenceRecord:
    normalized_timestamp = _normalize_timestamp(recorded_at)
    case_sha256 = sha256(result.case_id.encode()).hexdigest()
    record_id = _record_id_from_values(
        recorded_at=normalized_timestamp,
        case_sha256=case_sha256,
        provider_status=provider_status,
        final_decision=result.final_decision,
        evidence_complete=result.evidence_complete,
        review_reasons=result.review_reasons,
        requested_model=result.provenance.requested_model,
        effective_model=result.provenance.effective_model,
        result_schema_version=result.provenance.schema_version,
        prompt_version=result.provenance.prompt_version,
        policy_version=result.provenance.policy_version,
        sop_sha256=result.provenance.sop_sha256,
        image_sha256=result.provenance.image_sha256,
    )
    return LiveEvidenceRecord(
        record_id=record_id,
        recorded_at=normalized_timestamp,
        case_sha256=case_sha256,
        provider_status=provider_status,
        final_decision=result.final_decision,
        evidence_complete=result.evidence_complete,
        review_reasons=result.review_reasons,
        requested_model=result.provenance.requested_model,
        effective_model=result.provenance.effective_model,
        result_schema_version=result.provenance.schema_version,
        prompt_version=result.provenance.prompt_version,
        policy_version=result.provenance.policy_version,
        sop_sha256=result.provenance.sop_sha256,
        image_sha256=result.provenance.image_sha256,
    )


def load_live_evidence(path: Path) -> LiveEvidenceRecord:
    with path.open("rb") as evidence_file:
        serialized = evidence_file.read(MAX_LIVE_EVIDENCE_BYTES + 1)
    if len(serialized) > MAX_LIVE_EVIDENCE_BYTES:
        raise ValueError("live evidence exceeds the 64 KiB size limit")
    return LiveEvidenceRecord.model_validate_json(serialized)


def write_live_evidence(
    path: Path,
    record: LiveEvidenceRecord,
) -> LiveEvidenceWriteResult:
    serialized = (record.model_dump_json(indent=2) + "\n").encode()
    if len(serialized) > MAX_LIVE_EVIDENCE_BYTES:
        raise ValueError("live evidence exceeds the 64 KiB size limit")
    if path.exists():
        return _existing_write_result(path, record)
    try:
        _atomic_create(path, serialized)
    except FileExistsError:
        return _existing_write_result(path, record)
    return LiveEvidenceWriteResult(
        status=LiveEvidenceWriteStatus.WRITTEN,
        record_id=record.record_id,
    )


def _existing_write_result(
    path: Path,
    record: LiveEvidenceRecord,
) -> LiveEvidenceWriteResult:
    existing = load_live_evidence(path)
    if existing != record:
        raise FileExistsError("refusing to replace different live evidence")
    return LiveEvidenceWriteResult(
        status=LiveEvidenceWriteStatus.DUPLICATE,
        record_id=record.record_id,
    )


def _atomic_create(path: Path, serialized: bytes) -> None:
    if not path.parent.is_dir():
        raise FileNotFoundError("live evidence parent directory must exist")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.link(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recorded_at must be timezone-aware")
    return value.astimezone(UTC).replace(microsecond=0)


def _record_id(record: LiveEvidenceRecord) -> str:
    return _record_id_from_values(
        recorded_at=record.recorded_at,
        case_sha256=record.case_sha256,
        provider_status=record.provider_status,
        final_decision=record.final_decision,
        evidence_complete=record.evidence_complete,
        review_reasons=record.review_reasons,
        requested_model=record.requested_model,
        effective_model=record.effective_model,
        result_schema_version=record.result_schema_version,
        prompt_version=record.prompt_version,
        policy_version=record.policy_version,
        sop_sha256=record.sop_sha256,
        image_sha256=record.image_sha256,
    )


def _record_id_from_values(
    *,
    recorded_at: datetime,
    case_sha256: str,
    provider_status: ProviderStatus,
    final_decision: Decision,
    evidence_complete: bool,
    review_reasons: list[ReviewReason],
    requested_model: str,
    effective_model: str | None,
    result_schema_version: str,
    prompt_version: str,
    policy_version: str,
    sop_sha256: str,
    image_sha256: str,
) -> str:
    canonical = json.dumps(
        {
            "schema_version": "1.0",
            "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
            "case_sha256": case_sha256,
            "provider_status": provider_status.value,
            "final_decision": final_decision.value,
            "evidence_complete": evidence_complete,
            "review_reasons": [reason.value for reason in review_reasons],
            "requested_model": requested_model,
            "effective_model": effective_model,
            "result_schema_version": result_schema_version,
            "prompt_version": prompt_version,
            "policy_version": policy_version,
            "sop_sha256": sop_sha256,
            "image_sha256": image_sha256,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return sha256(canonical).hexdigest()


__all__ = [
    "MAX_LIVE_EVIDENCE_BYTES",
    "LiveEvidenceRecord",
    "LiveEvidenceWriteResult",
    "LiveEvidenceWriteStatus",
    "build_live_evidence",
    "load_live_evidence",
    "write_live_evidence",
]
