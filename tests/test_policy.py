import pytest
from pydantic import ValidationError

from inspection_copilot.domain import (
    SOP,
    Assessment,
    Decision,
    Evidence,
    ImageQuality,
    InspectionCase,
    InspectionRequest,
    ReviewReason,
    SOPRule,
)
from inspection_copilot.policy import finalize_assessment


def _request() -> InspectionRequest:
    return InspectionRequest(
        sop=SOP(
            sop_id="IPC-DEMO-001",
            version="1.0",
            title="Synthetic solder inspection",
            rules=[
                SOPRule(
                    rule_id="SOLDER-BRIDGE-001",
                    description="Adjacent pads must not be electrically bridged.",
                    acceptance="Visible separation exists between adjacent pads.",
                    rejection="A continuous solder path connects adjacent pads.",
                )
            ],
        ),
        case=InspectionCase(
            case_id="synthetic-bridge-001",
            image_ref="synthetic_bridge.png",
            product_type="SMT PCB",
            context="Repository-owned synthetic demo only.",
        ),
    )


def _assessment(**overrides: object) -> Assessment:
    values: dict[str, object] = {
        "proposed_decision": Decision.FAIL,
        "image_quality": ImageQuality.ADEQUATE,
        "evidence": [
            Evidence(
                observation="A continuous metallic path joins two adjacent pads.",
                location="U1 pins 3-4",
                sop_rule_id="SOLDER-BRIDGE-001",
                supports=Decision.FAIL,
            )
        ],
        "unknown_defect": False,
        "confidence": 0.94,
        "summary": "Visible bridge conflicts with the rejection rule.",
    }
    values.update(overrides)
    return Assessment.model_validate(values)


def test_sop_rejects_duplicate_rule_ids() -> None:
    rule = _request().sop.rules[0]

    with pytest.raises(ValidationError, match="unique"):
        SOP(
            sop_id="duplicate-demo",
            version="1.0",
            title="Invalid duplicate SOP",
            rules=[rule, rule],
        )


def test_supported_assessment_keeps_automatic_fail() -> None:
    result = finalize_assessment(_request(), _assessment(), model="fixture-v1")

    assert result.final_decision is Decision.FAIL
    assert result.evidence_complete is True
    assert result.review_reasons == []


@pytest.mark.parametrize(
    ("assessment", "reason"),
    [
        (_assessment(evidence=[]), ReviewReason.INSUFFICIENT_EVIDENCE),
        (_assessment(image_quality=ImageQuality.DEGRADED), ReviewReason.POOR_IMAGE_QUALITY),
        (_assessment(unknown_defect=True), ReviewReason.UNKNOWN_DEFECT),
        (_assessment(confidence=0.49), ReviewReason.LOW_CONFIDENCE),
        (
            _assessment(
                evidence=[
                    Evidence(
                        observation="Possible bridge.",
                        location="U1 pins 3-4",
                        sop_rule_id="MISSING-RULE",
                        supports=Decision.FAIL,
                    )
                ]
            ),
            ReviewReason.INVALID_SOP_REFERENCE,
        ),
        (
            _assessment(
                evidence=[
                    Evidence(
                        observation="Pads appear separated.",
                        location="U1 pins 3-4",
                        sop_rule_id="SOLDER-BRIDGE-001",
                        supports=Decision.PASS,
                    )
                ]
            ),
            ReviewReason.EVIDENCE_CONFLICT,
        ),
    ],
)
def test_unsafe_assessment_fails_closed(
    assessment: Assessment,
    reason: ReviewReason,
) -> None:
    result = finalize_assessment(_request(), assessment, model="fixture-v1")

    assert result.final_decision is Decision.NEEDS_REVIEW
    assert result.evidence_complete is False
    assert reason in result.review_reasons


def test_model_requested_review_remains_human_review() -> None:
    result = finalize_assessment(
        _request(),
        _assessment(proposed_decision=Decision.NEEDS_REVIEW),
        model="fixture-v1",
    )

    assert result.final_decision is Decision.NEEDS_REVIEW
    assert ReviewReason.MODEL_REQUESTED_REVIEW in result.review_reasons
