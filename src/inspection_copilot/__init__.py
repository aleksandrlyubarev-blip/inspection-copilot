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
    ReviewReason,
    SOPRule,
)
from inspection_copilot.policy import MIN_AUTOMATIC_CONFIDENCE, finalize_assessment

__version__ = "0.1.0"

__all__ = [
    "MIN_AUTOMATIC_CONFIDENCE",
    "Assessment",
    "Decision",
    "Evidence",
    "ImageQuality",
    "InspectionCase",
    "InspectionRequest",
    "InspectionResult",
    "ReviewReason",
    "SOP",
    "SOPRule",
    "__version__",
    "finalize_assessment",
]
