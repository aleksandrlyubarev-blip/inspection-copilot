"""Provider-neutral inspection service boundary."""

from __future__ import annotations

from typing import Protocol

from inspection_copilot.domain import Assessment, InspectionRequest, InspectionResult
from inspection_copilot.policy import finalize_assessment


class Inspector(Protocol):
    model: str

    def inspect(self, request: InspectionRequest) -> Assessment: ...


class FixtureInspector:
    """Deterministic provider for tests, demos, and judge setup."""

    model = "fixture-inspector-v1"

    def __init__(self, assessment: Assessment) -> None:
        self._assessment = assessment.model_copy(deep=True)

    def inspect(self, request: InspectionRequest) -> Assessment:
        return self._assessment.model_copy(deep=True)


def run_inspection(
    request: InspectionRequest,
    *,
    provider: Inspector,
) -> InspectionResult:
    assessment = provider.inspect(request)
    return finalize_assessment(request, assessment, model=provider.model)


__all__ = ["FixtureInspector", "Inspector", "run_inspection"]
