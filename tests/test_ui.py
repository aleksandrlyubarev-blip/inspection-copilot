from pathlib import Path

from streamlit.testing.v1 import AppTest

from inspection_copilot.demo import run_demo
from inspection_copilot.domain import Decision, Evidence
from inspection_copilot.ui import _automatic_record_html, _evidence_card_html

REPO_ROOT = Path(__file__).resolve().parents[1]


def _app() -> AppTest:
    return AppTest.from_file(str(REPO_ROOT / "streamlit_app.py")).run(timeout=10)


def test_main_screen_shows_case_verdict_and_evidence() -> None:
    app = _app()

    assert not app.exception
    assert app.title[0].value == "Inspection Copilot"
    assert any("AUTOMATIC RECORD" in item.value for item in app.markdown)
    assert any("FAIL" in item.value for item in app.markdown)
    assert any("SOLDER-BRIDGE-001" in item.value for item in app.markdown)
    assert len(app.image) == 1


def test_human_review_requires_rationale() -> None:
    app = _app()

    app.button[0].click().run(timeout=10)

    assert any("rationale" in item.value.lower() for item in app.warning)


def test_human_review_can_be_recorded_in_session() -> None:
    app = _app()

    app.selectbox[1].select("fail").run(timeout=10)
    app.text_area[0].input("Confirmed bridge under manual review.").run(timeout=10)
    app.button[0].click().run(timeout=10)

    assert any("recorded" in item.value.lower() for item in app.success)
    assert any("Recorded at" in item.value for item in app.info)


def test_ambiguous_scenario_prominently_escalates() -> None:
    app = _app()

    app.selectbox[0].select("Ambiguous / degraded image").run(timeout=10)

    assert any("NEEDS_REVIEW" in item.value for item in app.markdown)
    assert any(button.label == "Escalate to human review" for button in app.button)


def test_human_review_does_not_leak_between_cases() -> None:
    app = _app()

    app.text_area[0].input("Confirmed bridge under manual review.").run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert app.info

    app.selectbox[0].select("Ambiguous / degraded image").run(timeout=10)

    assert not app.info
    assert app.text_area[0].value == ""


def test_untrusted_inspection_fields_are_html_escaped() -> None:
    evidence = Evidence(
        observation='<img src=x onerror="alert(1)">',
        location="<script>alert(2)</script>",
        sop_rule_id="RULE</code><b>unsafe</b>",
        supports=Decision.FAIL,
    )
    result = run_demo(REPO_ROOT).model_copy(
        update={
            "case_id": '<svg onload="alert(3)">',
            "model": "<b>untrusted-model</b>",
            "summary": "<iframe>unsafe</iframe>",
        }
    )

    evidence_html = _evidence_card_html(evidence)
    record_html = _automatic_record_html(result, verdict_class="verdict")

    assert "<img" not in evidence_html
    assert "<script" not in evidence_html
    assert "</code><b>" not in evidence_html
    assert "&lt;img" in evidence_html
    assert "&lt;script" in evidence_html
    assert "<svg" not in record_html
    assert "<b>untrusted-model" not in record_html
    assert "<iframe" not in record_html
