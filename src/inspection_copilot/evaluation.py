"""Deterministic policy-level evaluation for repository-owned fixtures."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from inspection_copilot.demo import DemoScenario, run_demo
from inspection_copilot.domain import Decision, ReviewReason, StrictModel

_EXPECTED_DECISIONS = (
    (DemoScenario.BRIDGE_FAIL, Decision.FAIL),
    (DemoScenario.AMBIGUOUS, Decision.NEEDS_REVIEW),
)


class EvaluationCaseResult(StrictModel):
    scenario: DemoScenario
    case_id: str = Field(min_length=1)
    expected_decision: Decision
    actual_decision: Decision
    matched: bool
    review_reasons: list[ReviewReason]

    @model_validator(mode="after")
    def require_consistent_match_flag(self) -> Self:
        if self.matched is not (self.actual_decision is self.expected_decision):
            raise ValueError("matched must reflect expected and actual decisions")
        return self


class EvaluationReport(StrictModel):
    provider: str = Field(min_length=1)
    total_cases: int = Field(ge=1)
    matched_cases: int = Field(ge=0)
    match_rate: float = Field(ge=0.0, le=1.0)
    automatic_cases: int = Field(ge=0)
    escalated_cases: int = Field(ge=0)
    cases: list[EvaluationCaseResult] = Field(min_length=1)
    disclaimer: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_consistent_metrics(self) -> Self:
        expected_total = len(self.cases)
        expected_matches = sum(case.matched for case in self.cases)
        expected_escalations = sum(
            case.actual_decision is Decision.NEEDS_REVIEW for case in self.cases
        )
        if self.total_cases != expected_total:
            raise ValueError("total_cases must equal the number of case results")
        if self.matched_cases != expected_matches:
            raise ValueError("matched_cases must equal matching case results")
        if self.match_rate != expected_matches / expected_total:
            raise ValueError("match_rate must equal matched_cases / total_cases")
        if self.escalated_cases != expected_escalations:
            raise ValueError("escalated_cases must equal needs_review case results")
        if self.automatic_cases != expected_total - expected_escalations:
            raise ValueError("automatic_cases must equal non-escalated case results")
        return self


def run_offline_evaluation(repo_root: Path) -> EvaluationReport:
    case_results: list[EvaluationCaseResult] = []
    provider = ""
    for scenario, expected_decision in _EXPECTED_DECISIONS:
        result = run_demo(repo_root, scenario=scenario)
        provider = result.model
        case_results.append(
            EvaluationCaseResult(
                scenario=scenario,
                case_id=result.case_id,
                expected_decision=expected_decision,
                actual_decision=result.final_decision,
                matched=result.final_decision is expected_decision,
                review_reasons=result.review_reasons,
            )
        )

    total_cases = len(case_results)
    matched_cases = sum(case.matched for case in case_results)
    escalated_cases = sum(case.actual_decision is Decision.NEEDS_REVIEW for case in case_results)
    return EvaluationReport(
        provider=provider,
        total_cases=total_cases,
        matched_cases=matched_cases,
        match_rate=matched_cases / total_cases,
        automatic_cases=total_cases - escalated_cases,
        escalated_cases=escalated_cases,
        cases=case_results,
        disclaimer=(
            "Deterministic repository-owned fixture workflow; not model-accuracy evidence."
        ),
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    print(run_offline_evaluation(args.repo_root).model_dump_json(indent=2))


if __name__ == "__main__":
    main()


__all__ = ["EvaluationCaseResult", "EvaluationReport", "main", "run_offline_evaluation"]
