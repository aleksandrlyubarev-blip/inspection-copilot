from pathlib import Path

from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _app() -> AppTest:
    return AppTest.from_file(str(REPO_ROOT / "streamlit_app.py")).run(timeout=10)


def test_main_screen_shows_case_verdict_and_evidence() -> None:
    app = _app()

    assert not app.exception
    assert app.title[0].value == "Inspection Copilot"
    assert any("FAIL" in item.value for item in app.markdown)
    assert any("SOLDER-BRIDGE-001" in item.value for item in app.markdown)
    assert len(app.image) == 1


def test_human_review_requires_rationale() -> None:
    app = _app()

    app.button[0].click().run(timeout=10)

    assert any("rationale" in item.value.lower() for item in app.warning)


def test_human_review_can_be_recorded_in_session() -> None:
    app = _app()

    app.selectbox[0].select("fail").run(timeout=10)
    app.text_area[0].input("Confirmed bridge under manual review.").run(timeout=10)
    app.button[0].click().run(timeout=10)

    assert any("recorded" in item.value.lower() for item in app.success)
