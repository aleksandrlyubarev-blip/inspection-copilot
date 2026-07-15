"""Inspection Copilot package."""

from inspection_copilot.domain import (
    SOP,
    Assessment,
    Decision,
    Evidence,
    ImageQuality,
    InspectionCase,
    InspectionRequest,
    InspectionResult,
    ProviderOutcome,
    ProviderStatus,
    ReviewReason,
    SOPRule,
)
from inspection_copilot.policy import MIN_AUTOMATIC_CONFIDENCE, finalize_assessment
from inspection_copilot.service import FixtureInspector, Inspector, run_inspection

__version__ = "0.1.0"

__all__ = [
    "MIN_AUTOMATIC_CONFIDENCE",
    "Assessment",
    "Decision",
    "Evidence",
    "FixtureInspector",
    "ImageQuality",
    "InspectionCase",
    "InspectionRequest",
    "InspectionResult",
    "Inspector",
    "ProviderOutcome",
    "ProviderStatus",
    "ReviewReason",
    "SOP",
    "SOPRule",
    "__version__",
    "finalize_assessment",
    "run_inspection",
]
