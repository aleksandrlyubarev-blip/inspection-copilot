"""Deterministic fail-closed decision policy."""

from __future__ import annotations

from inspection_copilot.domain import (
    Assessment,
    Decision,
    ImageQuality,
    InspectionRequest,
    InspectionResult,
    ReviewReason,
)

MIN_AUTOMATIC_CONFIDENCE = 0.80


def finalize_assessment(
    request: InspectionRequest,
    assessment: Assessment,
    *,
    model: str,
) -> InspectionResult:
    """Apply deterministic evidence gates to one model or fixture assessment."""

    reasons: list[ReviewReason] = []
    if assessment.proposed_decision is Decision.NEEDS_REVIEW:
        reasons.append(ReviewReason.MODEL_REQUESTED_REVIEW)
    if assessment.image_quality is not ImageQuality.ADEQUATE:
        reasons.append(ReviewReason.POOR_IMAGE_QUALITY)
    if not assessment.evidence:
        reasons.append(ReviewReason.INSUFFICIENT_EVIDENCE)
    if assessment.unknown_defect:
        reasons.append(ReviewReason.UNKNOWN_DEFECT)
    if assessment.confidence < MIN_AUTOMATIC_CONFIDENCE:
        reasons.append(ReviewReason.LOW_CONFIDENCE)
    if any(item.sop_rule_id not in request.sop.rule_ids for item in assessment.evidence):
        reasons.append(ReviewReason.INVALID_SOP_REFERENCE)
    if assessment.proposed_decision is not Decision.NEEDS_REVIEW and any(
        item.supports is not assessment.proposed_decision for item in assessment.evidence
    ):
        reasons.append(ReviewReason.EVIDENCE_CONFLICT)

    evidence_complete = not reasons
    final_decision = assessment.proposed_decision if evidence_complete else Decision.NEEDS_REVIEW
    summary = (
        f"Automatic {final_decision.value} supported by complete evidence."
        if evidence_complete
        else "Human review required: " + ", ".join(reason.value for reason in reasons) + "."
    )
    return InspectionResult(
        case_id=request.case.case_id,
        final_decision=final_decision,
        evidence_complete=evidence_complete,
        review_reasons=reasons,
        assessment=assessment,
        model=model,
        summary=summary,
    )


__all__ = ["MIN_AUTOMATIC_CONFIDENCE", "finalize_assessment"]
