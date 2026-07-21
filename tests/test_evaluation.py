import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from inspection_copilot.domain import Decision
from inspection_copilot.evaluation import EvaluationReport, run_offline_evaluation

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_offline_evaluation_is_deterministic_and_policy_labeled() -> None:
    first = run_offline_evaluation(REPO_ROOT)
    second = run_offline_evaluation(REPO_ROOT)

    assert first == second
    assert first.provider == "fixture-inspector-v1"
    assert first.total_cases == 2
    assert first.matched_cases == 2
    assert first.match_rate == 1.0
    assert first.automatic_cases == 1
    assert first.escalated_cases == 1
    assert [case.expected_decision for case in first.cases] == [
        Decision.FAIL,
        Decision.NEEDS_REVIEW,
    ]
    assert all(case.matched for case in first.cases)
    assert "not model-accuracy evidence" in first.disclaimer.lower()


def test_evaluation_cli_emits_schema_valid_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "inspection_copilot.evaluation",
            "--repo-root",
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = EvaluationReport.model_validate_json(completed.stdout)
    assert report.total_cases == 2
    assert report.matched_cases == 2


def test_committed_evaluation_evidence_matches_current_fixture_run() -> None:
    committed = EvaluationReport.model_validate_json(
        (REPO_ROOT / "evidence" / "offline_evaluation.json").read_text(encoding="utf-8")
    )

    assert committed == run_offline_evaluation(REPO_ROOT)


def test_evaluation_report_rejects_inconsistent_metrics() -> None:
    payload = run_offline_evaluation(REPO_ROOT).model_dump()
    payload["matched_cases"] = 0

    with pytest.raises(ValidationError, match="matched_cases"):
        EvaluationReport.model_validate(payload)
