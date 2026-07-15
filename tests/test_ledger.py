import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from inspection_copilot.demo import DemoScenario, run_demo
from inspection_copilot.ledger import (
    MAX_LEDGER_BYTES,
    MAX_LEDGER_ENTRIES,
    InspectionLedger,
    InspectionLedgerEntry,
    LedgerAppendStatus,
    append_result,
    entry_from_result,
    load_ledger,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_entry_is_deterministic_and_contains_only_sanitized_metadata() -> None:
    result = run_demo(REPO_ROOT)

    first = entry_from_result(result)
    second = entry_from_result(result)
    payload = first.model_dump(mode="json")

    assert first == second
    assert len(first.entry_id) == 64
    assert first.case_id == result.case_id
    assert first.final_decision == result.final_decision
    assert first.provenance == result.provenance
    assert set(payload) == {
        "entry_id",
        "case_id",
        "final_decision",
        "evidence_complete",
        "review_reasons",
        "provenance",
    }
    serialized = first.model_dump_json()
    assert result.assessment.summary not in serialized
    assert result.assessment.evidence[0].observation not in serialized
    assert "assessment" not in payload
    assert "summary" not in payload


def test_duplicate_append_is_a_byte_identical_no_op(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    result = run_demo(REPO_ROOT)

    first = append_result(ledger_path, result)
    original_bytes = ledger_path.read_bytes()
    second = append_result(ledger_path, result)

    assert first.status is LedgerAppendStatus.APPENDED
    assert first.total_entries == 1
    assert second.status is LedgerAppendStatus.DUPLICATE
    assert second.entry_id == first.entry_id
    assert second.total_entries == 1
    assert ledger_path.read_bytes() == original_bytes
    assert load_ledger(ledger_path).entries == [entry_from_result(result)]


def test_distinct_fixture_results_append_in_order(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    bridge = run_demo(REPO_ROOT)
    ambiguous = run_demo(REPO_ROOT, scenario=DemoScenario.AMBIGUOUS)

    append_result(ledger_path, bridge)
    appended = append_result(ledger_path, ambiguous)
    ledger = load_ledger(ledger_path)

    assert appended.total_entries == 2
    assert [entry.case_id for entry in ledger.entries] == [
        "synthetic-bridge-001",
        "synthetic-ambiguous-001",
    ]


def test_ledger_rejects_duplicate_or_tampered_entry_ids() -> None:
    entry = entry_from_result(run_demo(REPO_ROOT))

    with pytest.raises(ValidationError, match="unique"):
        InspectionLedger(entries=[entry, entry])

    payload = entry.model_dump()
    payload["entry_id"] = "f" * 64
    with pytest.raises(ValidationError, match="entry_id"):
        InspectionLedgerEntry.model_validate(payload)


def test_oversized_ledger_is_rejected_before_json_parsing(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_bytes(b"{" + b" " * MAX_LEDGER_BYTES)

    with pytest.raises(ValueError, match="size limit"):
        load_ledger(ledger_path)


def test_ledger_entry_count_is_bounded() -> None:
    entry = entry_from_result(run_demo(REPO_ROOT))

    with pytest.raises(ValidationError, match=str(MAX_LEDGER_ENTRIES)):
        InspectionLedger(entries=[entry] * (MAX_LEDGER_ENTRIES + 1))


def test_append_requires_an_existing_parent_directory(tmp_path: Path) -> None:
    ledger_path = tmp_path / "missing" / "ledger.json"

    with pytest.raises(FileNotFoundError, match="parent directory"):
        append_result(ledger_path, run_demo(REPO_ROOT))

    assert not ledger_path.exists()


def test_failed_atomic_replace_preserves_original_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger_path = tmp_path / "ledger.json"
    append_result(ledger_path, run_demo(REPO_ROOT))
    original = ledger_path.read_bytes()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError(f"cannot replace {source.name} with {destination.name}")

    monkeypatch.setattr("inspection_copilot.ledger.os.replace", fail_replace)

    with pytest.raises(OSError, match="cannot replace"):
        append_result(
            ledger_path,
            run_demo(REPO_ROOT, scenario=DemoScenario.AMBIGUOUS),
        )

    assert ledger_path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [ledger_path]


def test_committed_json_shape_can_be_read_back(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.json"
    append_result(ledger_path, run_demo(REPO_ROOT))

    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    validated = InspectionLedger.model_validate(payload)

    assert payload["schema_version"] == "1.0"
    assert validated == load_ledger(ledger_path)
