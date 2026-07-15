"""Provider-neutral inspection service boundary."""

from __future__ import annotations

from typing import Protocol

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
    outcome = provider.inspect(request)
    if outcome.assessment is None:
        assessment = _provider_failure_assessment()
        additional_reasons = [_PROVIDER_REVIEW_REASONS[outcome.status]]
    else:
        assessment = outcome.assessment
        additional_reasons = []
    return finalize_assessment(
        request,
        assessment,
        provenance=_build_provenance(request, outcome),
        additional_review_reasons=additional_reasons,
    )


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


__all__ = ["FIXTURE_PROMPT_VERSION", "FixtureInspector", "Inspector", "run_inspection"]
