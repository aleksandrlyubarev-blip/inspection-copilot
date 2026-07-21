"""Strict domain contracts for Inspection Copilot."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Decision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


class ImageQuality(StrEnum):
    ADEQUATE = "adequate"
    DEGRADED = "degraded"
    UNUSABLE = "unusable"


class ReviewReason(StrEnum):
    MODEL_REQUESTED_REVIEW = "model_requested_review"
    POOR_IMAGE_QUALITY = "poor_image_quality"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNKNOWN_DEFECT = "unknown_defect"
    LOW_CONFIDENCE = "low_confidence"
    INVALID_SOP_REFERENCE = "invalid_sop_reference"
    EVIDENCE_CONFLICT = "evidence_conflict"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_RATE_LIMITED = "provider_rate_limited"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    MODEL_REFUSAL = "model_refusal"
    INVALID_PROVIDER_OUTPUT = "invalid_provider_output"


class ProviderStatus(StrEnum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    REFUSAL = "refusal"
    INVALID_OUTPUT = "invalid_output"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SOPRule(StrictModel):
    rule_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    acceptance: str = Field(min_length=1)
    rejection: str = Field(min_length=1)


class SOP(StrictModel):
    sop_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rules: list[SOPRule] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_rule_ids(self) -> Self:
        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("SOP rule IDs must be unique")
        return self

    @property
    def rule_ids(self) -> frozenset[str]:
        return frozenset(rule.rule_id for rule in self.rules)


class InspectionCase(StrictModel):
    case_id: str = Field(min_length=1)
    image_ref: str = Field(min_length=1)
    product_type: str = Field(min_length=1)
    context: str = ""


class InspectionRequest(StrictModel):
    sop: SOP
    case: InspectionCase
    image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Evidence(StrictModel):
    observation: str = Field(min_length=1)
    location: str = Field(min_length=1)
    sop_rule_id: str = Field(min_length=1)
    supports: Decision

    @field_validator("supports")
    @classmethod
    def evidence_must_support_a_verdict(cls, value: Decision) -> Decision:
        if value is Decision.NEEDS_REVIEW:
            raise ValueError("evidence must support pass or fail")
        return value


class Assessment(StrictModel):
    proposed_decision: Decision
    image_quality: ImageQuality
    evidence: list[Evidence]
    unknown_defect: bool
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)


class ProviderOutcome(StrictModel):
    status: ProviderStatus
    assessment: Assessment | None
    requested_model: str = Field(min_length=1)
    effective_model: str | None
    prompt_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_status_consistency(self) -> Self:
        if self.status is ProviderStatus.SUCCESS:
            if self.assessment is None or self.effective_model is None:
                raise ValueError("success requires assessment and effective_model")
            return self
        if self.assessment is not None:
            raise ValueError("provider failure cannot include an assessment")
        return self

    @property
    def retryable(self) -> bool:
        return self.status in {
            ProviderStatus.TIMEOUT,
            ProviderStatus.RATE_LIMITED,
            ProviderStatus.UNAVAILABLE,
        }


class InspectionProvenance(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    sop_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    requested_model: str = Field(min_length=1)
    effective_model: str | None
    prompt_version: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)


class InspectionResult(StrictModel):
    case_id: str = Field(min_length=1)
    final_decision: Decision
    evidence_complete: bool
    review_reasons: list[ReviewReason]
    assessment: Assessment
    model: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    provenance: InspectionProvenance

    @model_validator(mode="after")
    def require_consistent_decision(self) -> Self:
        if self.model != self.provenance.requested_model:
            raise ValueError("model must match provenance requested_model")
        if self.final_decision is Decision.NEEDS_REVIEW:
            if self.evidence_complete or not self.review_reasons:
                raise ValueError("needs_review requires reasons and incomplete evidence")
            return self
        if (
            not self.evidence_complete
            or self.review_reasons
            or self.assessment.proposed_decision is not self.final_decision
        ):
            raise ValueError("automatic verdict requires complete matching evidence")
        return self


__all__ = [
    "Assessment",
    "Decision",
    "Evidence",
    "ImageQuality",
    "InspectionCase",
    "InspectionProvenance",
    "InspectionRequest",
    "InspectionResult",
    "ProviderOutcome",
    "ProviderStatus",
    "ReviewReason",
    "SOP",
    "SOPRule",
]
