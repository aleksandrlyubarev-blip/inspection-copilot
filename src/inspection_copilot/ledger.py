"""Sanitized, deterministic local inspection ledger."""

from __future__ import annotations

import json
import os
import tempfile
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from inspection_copilot.domain import (
    Decision,
    InspectionProvenance,
    InspectionResult,
    ReviewReason,
    StrictModel,
)

MAX_LEDGER_BYTES = 1024 * 1024
MAX_LEDGER_ENTRIES = 1000


class LedgerAppendStatus(StrEnum):
    APPENDED = "appended"
    DUPLICATE = "duplicate"


class InspectionLedgerEntry(StrictModel):
    entry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    case_id: str = Field(min_length=1)
    final_decision: Decision
    evidence_complete: bool
    review_reasons: list[ReviewReason]
    provenance: InspectionProvenance

    @model_validator(mode="after")
    def require_consistent_entry(self) -> Self:
        if self.entry_id != _entry_id(
            case_id=self.case_id,
            final_decision=self.final_decision,
            evidence_complete=self.evidence_complete,
            review_reasons=self.review_reasons,
            provenance=self.provenance,
        ):
            raise ValueError("entry_id must match the sanitized entry content")
        if len(self.review_reasons) != len(set(self.review_reasons)):
            raise ValueError("review reasons must be unique")
        if self.final_decision is Decision.NEEDS_REVIEW:
            if self.evidence_complete or not self.review_reasons:
                raise ValueError("needs_review ledger entry requires review reasons")
        elif not self.evidence_complete or self.review_reasons:
            raise ValueError("automatic ledger entry requires complete evidence")
        return self


class InspectionLedger(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    entries: list[InspectionLedgerEntry] = Field(
        default_factory=list,
        max_length=MAX_LEDGER_ENTRIES,
    )

    @model_validator(mode="after")
    def require_unique_entry_ids(self) -> Self:
        entry_ids = [entry.entry_id for entry in self.entries]
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("ledger entry IDs must be unique")
        return self


class LedgerAppendResult(StrictModel):
    status: LedgerAppendStatus
    entry_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    total_entries: int = Field(ge=0, le=MAX_LEDGER_ENTRIES)


def entry_from_result(result: InspectionResult) -> InspectionLedgerEntry:
    return InspectionLedgerEntry(
        entry_id=_entry_id(
            case_id=result.case_id,
            final_decision=result.final_decision,
            evidence_complete=result.evidence_complete,
            review_reasons=result.review_reasons,
            provenance=result.provenance,
        ),
        case_id=result.case_id,
        final_decision=result.final_decision,
        evidence_complete=result.evidence_complete,
        review_reasons=result.review_reasons,
        provenance=result.provenance,
    )


def load_ledger(path: Path) -> InspectionLedger:
    if not path.exists():
        return InspectionLedger()
    with path.open("rb") as ledger_file:
        serialized = ledger_file.read(MAX_LEDGER_BYTES + 1)
    if len(serialized) > MAX_LEDGER_BYTES:
        raise ValueError("inspection ledger exceeds the 1 MiB size limit")
    return InspectionLedger.model_validate_json(serialized)


def append_result(path: Path, result: InspectionResult) -> LedgerAppendResult:
    ledger = load_ledger(path)
    entry = entry_from_result(result)
    for existing in ledger.entries:
        if existing.entry_id == entry.entry_id:
            return LedgerAppendResult(
                status=LedgerAppendStatus.DUPLICATE,
                entry_id=entry.entry_id,
                total_entries=len(ledger.entries),
            )

    updated = InspectionLedger(entries=[*ledger.entries, entry])
    serialized = (updated.model_dump_json(indent=2) + "\n").encode()
    if len(serialized) > MAX_LEDGER_BYTES:
        raise ValueError("inspection ledger exceeds the 1 MiB size limit")
    _atomic_write(path, serialized)
    return LedgerAppendResult(
        status=LedgerAppendStatus.APPENDED,
        entry_id=entry.entry_id,
        total_entries=len(updated.entries),
    )


def _entry_id(
    *,
    case_id: str,
    final_decision: Decision,
    evidence_complete: bool,
    review_reasons: list[ReviewReason],
    provenance: InspectionProvenance,
) -> str:
    canonical = json.dumps(
        {
            "case_id": case_id,
            "final_decision": final_decision.value,
            "evidence_complete": evidence_complete,
            "review_reasons": [reason.value for reason in review_reasons],
            "provenance": provenance.model_dump(mode="json"),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return sha256(canonical).hexdigest()


def _atomic_write(path: Path, serialized: bytes) -> None:
    if not path.parent.is_dir():
        raise FileNotFoundError("inspection ledger parent directory must exist")
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
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


__all__ = [
    "MAX_LEDGER_BYTES",
    "MAX_LEDGER_ENTRIES",
    "InspectionLedger",
    "InspectionLedgerEntry",
    "LedgerAppendResult",
    "LedgerAppendStatus",
    "append_result",
    "entry_from_result",
    "load_ledger",
]
