from pathlib import Path

import pytest
from pydantic import ValidationError

from inspection_copilot.demo import load_demo_request, run_demo
from inspection_copilot.domain import (
    InspectionRequest,
    ProviderOutcome,
    ProviderStatus,
)
from inspection_copilot.service import InspectionExecution, execute_inspection

REPO_ROOT = Path(__file__).resolve().parents[1]


class CountingInspector:
    model = "gpt-5.6"

    def __init__(self, outcome: ProviderOutcome) -> None:
        self.outcome = outcome
        self.calls = 0

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        self.calls += 1
        return self.outcome


def _success_outcome() -> ProviderOutcome:
    return ProviderOutcome(
        status=ProviderStatus.SUCCESS,
        assessment=run_demo(REPO_ROOT).assessment,
        requested_model="gpt-5.6",
        effective_model="gpt-5.6-sol",
        prompt_version="inspection-v1",
    )


def test_execute_inspection_binds_one_actual_provider_outcome() -> None:
    provider = CountingInspector(_success_outcome())

    execution = execute_inspection(load_demo_request(REPO_ROOT), provider=provider)

    assert provider.calls == 1
    assert execution.outcome == provider.outcome
    assert execution.outcome.assessment is not None
    assert execution.result.final_decision == execution.outcome.assessment.proposed_decision
    assert execution.result.provenance.requested_model == provider.outcome.requested_model
    assert execution.result.provenance.effective_model == provider.outcome.effective_model
    assert execution.result.provenance.prompt_version == provider.outcome.prompt_version


def test_execution_contract_rejects_drift_between_outcome_and_result() -> None:
    result = run_demo(REPO_ROOT)

    with pytest.raises(ValidationError, match="outcome does not match result provenance"):
        InspectionExecution(outcome=_success_outcome(), result=result)
