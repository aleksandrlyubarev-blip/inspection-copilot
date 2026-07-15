"""Deterministic fail-closed decision policy."""

from __future__ import annotations

import json
from collections.abc import Sequence
from hashlib import sha256

from inspection_copilot.domain import (
    SOP,
    Assessment,
    Decision,
    ImageQuality,
    InspectionProvenance,
    InspectionRequest,
    InspectionResult,
    ReviewReason,
)

MIN_AUTOMATIC_CONFIDENCE = 0.80
POLICY_VERSION = "evidence-policy-v1"


def canonical_sop_sha256(sop: SOP) -> str:
    canonical_sop = json.dumps(
        sop.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return sha256(canonical_sop).hexdigest()


def finalize_assessment(
    request: InspectionRequest,
    assessment: Assessment,
    *,
    provenance: InspectionProvenance,
    additional_review_reasons: Sequence[ReviewReason] = (),
) -> InspectionResult:
    """Apply deterministic evidence gates to one model or fixture assessment."""

    if provenance.image_sha256 != request.image_sha256:
        raise ValueError("provenance image hash must match the inspection request")
    if provenance.sop_sha256 != canonical_sop_sha256(request.sop):
        raise ValueError("provenance SOP hash must match the inspection request")
    if provenance.policy_version != POLICY_VERSION:
        raise ValueError("provenance policy version must match the active policy")

    reasons = list(additional_review_reasons)
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
        model=provenance.requested_model,
        summary=summary,
        provenance=provenance,
    )


__all__ = [
    "MIN_AUTOMATIC_CONFIDENCE",
    "POLICY_VERSION",
    "canonical_sop_sha256",
    "finalize_assessment",
]
