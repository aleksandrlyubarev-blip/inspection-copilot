"""Provider-neutral inspection service boundary."""

from __future__ import annotations

from typing import Protocol, Self

from pydantic import model_validator

from inspection_copilot.domain import (
    Assessment,
    Decision,
    ImageQuality,
    InspectionProvenance,
    InspectionRequest,
    InspectionResult,
    ProviderOutcome,
    ProviderStatus,
    ReviewReason,
    StrictModel,
)
from inspection_copilot.policy import POLICY_VERSION, canonical_sop_sha256, finalize_assessment

FIXTURE_PROMPT_VERSION = "fixture-v1"

_PROVIDER_REVIEW_REASONS = {
    ProviderStatus.TIMEOUT: ReviewReason.PROVIDER_TIMEOUT,
    ProviderStatus.RATE_LIMITED: ReviewReason.PROVIDER_RATE_LIMITED,
    ProviderStatus.UNAVAILABLE: ReviewReason.PROVIDER_UNAVAILABLE,
    ProviderStatus.REFUSAL: ReviewReason.MODEL_REFUSAL,
    ProviderStatus.INVALID_OUTPUT: ReviewReason.INVALID_PROVIDER_OUTPUT,
}


class Inspector(Protocol):
    model: str

    def inspect(self, request: InspectionRequest) -> ProviderOutcome: ...


class InspectionExecution(StrictModel):
    """One provider outcome bound to the policy result derived from it."""

    outcome: ProviderOutcome
    result: InspectionResult

    @model_validator(mode="after")
    def require_bound_outcome(self) -> Self:
        provenance = self.result.provenance
        if (
            provenance.requested_model != self.outcome.requested_model
            or provenance.effective_model != self.outcome.effective_model
            or provenance.prompt_version != self.outcome.prompt_version
        ):
            raise ValueError("outcome does not match result provenance")
        if self.outcome.status is ProviderStatus.SUCCESS:
            if self.outcome.assessment != self.result.assessment:
                raise ValueError("successful outcome does not match result assessment")
        elif provider_review_reason(self.outcome.status) not in self.result.review_reasons:
            raise ValueError("failed outcome does not match result review reasons")
        return self


class FixtureInspector:
    """Deterministic provider for tests, demos, and judge setup."""

    model = "fixture-inspector-v1"

    def __init__(self, assessment: Assessment) -> None:
        self._assessment = assessment.model_copy(deep=True)

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        return ProviderOutcome(
            status=ProviderStatus.SUCCESS,
            assessment=self._assessment.model_copy(deep=True),
            requested_model=self.model,
            effective_model=self.model,
            prompt_version=FIXTURE_PROMPT_VERSION,
        )


def run_inspection(
    request: InspectionRequest,
    *,
    provider: Inspector,
) -> InspectionResult:
    return execute_inspection(request, provider=provider).result


def execute_inspection(
    request: InspectionRequest,
    *,
    provider: Inspector,
) -> InspectionExecution:
    outcome = provider.inspect(request)
    result = _result_from_outcome(request, outcome)
    return InspectionExecution(outcome=outcome, result=result)


def _result_from_outcome(
    request: InspectionRequest,
    outcome: ProviderOutcome,
) -> InspectionResult:
    if outcome.assessment is None:
        assessment = _provider_failure_assessment()
        additional_reasons = [provider_review_reason(outcome.status)]
    else:
        assessment = outcome.assessment
        additional_reasons = []
    return finalize_assessment(
        request,
        assessment,
        provenance=_build_provenance(request, outcome),
        additional_review_reasons=additional_reasons,
    )


def provider_review_reason(status: ProviderStatus) -> ReviewReason:
    if status is ProviderStatus.SUCCESS:
        raise ValueError("success provider status has no failure review reason")
    return _PROVIDER_REVIEW_REASONS[status]


def _build_provenance(
    request: InspectionRequest,
    outcome: ProviderOutcome,
) -> InspectionProvenance:
    return InspectionProvenance(
        sop_sha256=canonical_sop_sha256(request.sop),
        image_sha256=request.image_sha256,
        requested_model=outcome.requested_model,
        effective_model=outcome.effective_model,
        prompt_version=outcome.prompt_version,
        policy_version=POLICY_VERSION,
    )


def _provider_failure_assessment() -> Assessment:
    return Assessment(
        proposed_decision=Decision.NEEDS_REVIEW,
        image_quality=ImageQuality.UNUSABLE,
        evidence=[],
        unknown_defect=False,
        confidence=0.0,
        summary="Inspection provider did not return a valid assessment.",
    )


__all__ = [
    "FIXTURE_PROMPT_VERSION",
    "FixtureInspector",
    "InspectionExecution",
    "Inspector",
    "execute_inspection",
    "provider_review_reason",
    "run_inspection",
]
