import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from inspection_copilot.demo import DemoScenario, load_demo_request, run_demo
from inspection_copilot.domain import (
    Decision,
    Evidence,
    InspectionRequest,
    ProviderOutcome,
    ProviderStatus,
)
from inspection_copilot.live_evidence import LiveEvidenceRecord, build_live_evidence
from inspection_copilot.live_validation import LIVE_EVIDENCE_RELATIVE_PATH
from inspection_copilot.service import Inspector, run_inspection
from inspection_copilot.ui import _automatic_record_html, _evidence_card_html

REPO_ROOT = Path(__file__).resolve().parents[1]


def _app() -> AppTest:
    return AppTest.from_file(str(REPO_ROOT / "streamlit_app.py")).run(timeout=10)


class FailureInspector(Inspector):
    model = "gpt-5.6"

    def inspect(self, request: InspectionRequest) -> ProviderOutcome:
        return ProviderOutcome(
            status=ProviderStatus.TIMEOUT,
            assessment=None,
            requested_model=self.model,
            effective_model=None,
            prompt_version="inspection-v1",
        )


def _success_record() -> LiveEvidenceRecord:
    return build_live_evidence(
        run_demo(REPO_ROOT),
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=datetime(2026, 7, 16, 8, 30, tzinfo=UTC),
    )


def _failure_record() -> LiveEvidenceRecord:
    result = run_inspection(load_demo_request(REPO_ROOT), provider=FailureInspector())
    return build_live_evidence(
        result,
        provider_status=ProviderStatus.TIMEOUT,
        recorded_at=datetime(2026, 7, 16, 8, 31, tzinfo=UTC),
    )


def _successful_review_record() -> LiveEvidenceRecord:
    return build_live_evidence(
        run_demo(REPO_ROOT, scenario=DemoScenario.AMBIGUOUS),
        provider_status=ProviderStatus.SUCCESS,
        recorded_at=datetime(2026, 7, 16, 8, 32, tzinfo=UTC),
    )


def _temporary_app(
    tmp_path: Path,
    *,
    record: LiveEvidenceRecord | None = None,
    invalid_evidence: str | None = None,
    full_workspace: bool = False,
) -> AppTest:
    repo_root = tmp_path / "repo"
    (repo_root / "evidence").mkdir(parents=True)
    if full_workspace:
        shutil.copytree(REPO_ROOT / "examples", repo_root / "examples")
    evidence_path = repo_root / LIVE_EVIDENCE_RELATIVE_PATH
    if record is not None:
        evidence_path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    elif invalid_evidence is not None:
        evidence_path.write_text(invalid_evidence, encoding="utf-8")

    app_script = tmp_path / "app.py"
    render_name = "render" if full_workspace else "render_live_validation_panel"
    app_script.write_text(
        "from pathlib import Path\n"
        f"from inspection_copilot.ui import {render_name}\n"
        f"{render_name}(Path({str(repo_root)!r}))\n",
        encoding="utf-8",
    )
    return AppTest.from_file(str(app_script)).run(timeout=10)


def test_main_screen_shows_case_verdict_and_evidence() -> None:
    app = _app()

    assert not app.exception
    assert app.title[0].value == "Inspection Copilot"
    assert any("AUTOMATIC RECORD" in item.value for item in app.markdown)
    assert any("FAIL" in item.value for item in app.markdown)
    assert any("SOLDER-BRIDGE-001" in item.value for item in app.markdown)
    assert len(app.image) == 1
    assert any("Live validation evidence" in item.value for item in app.markdown)
    assert any(
        "SCHEMA VERIFIED" in item.value and "SUCCESS" in item.value and "FAIL" in item.value
        for item in app.success
    )


def test_missing_live_evidence_shows_not_run(tmp_path: Path) -> None:
    app = _temporary_app(tmp_path)

    assert not app.exception
    assert any("NOT RUN" in item.value for item in app.info)
    assert not app.json


def test_verified_success_panel_shows_only_sanitized_record(tmp_path: Path) -> None:
    record = _success_record()
    app = _temporary_app(tmp_path, record=record)

    assert not app.exception
    assert any("SCHEMA VERIFIED" in item.value and "SUCCESS" in item.value for item in app.success)
    assert len(app.json) == 1
    payload = json.loads(app.json[0].value)
    assert payload == record.model_dump(mode="json")
    serialized_ui = json.dumps(payload) + "\n".join(item.value for item in app.success)
    assert "response_id" not in serialized_ui
    assert "usage" not in serialized_ui
    assert "raw" not in serialized_ui


def test_verified_provider_failure_stays_needs_review(tmp_path: Path) -> None:
    record = _failure_record()
    app = _temporary_app(tmp_path, record=record)

    assert not app.exception
    assert any(
        "SCHEMA VERIFIED" in item.value and "TIMEOUT" in item.value and "NEEDS_REVIEW" in item.value
        for item in app.warning
    )
    payload = json.loads(app.json[0].value)
    assert payload["provider_status"] == "timeout"
    assert payload["final_decision"] == "needs_review"
    assert payload["evidence_complete"] is False
    assert "provider_timeout" in payload["review_reasons"]


def test_successful_provider_needs_review_uses_warning_severity(tmp_path: Path) -> None:
    app = _temporary_app(tmp_path, record=_successful_review_record())

    assert not app.exception
    assert not app.success
    assert any(
        "SCHEMA VERIFIED" in item.value and "SUCCESS" in item.value and "NEEDS_REVIEW" in item.value
        for item in app.warning
    )


def test_invalid_live_evidence_is_untrusted_and_not_rendered(tmp_path: Path) -> None:
    app = _temporary_app(tmp_path, invalid_evidence='{"provider_status":"success"}')

    assert not app.exception
    assert any("UNTRUSTED / UNAVAILABLE" in item.value for item in app.error)
    assert not app.json


def test_live_evidence_does_not_replace_offline_or_human_records(tmp_path: Path) -> None:
    app = _temporary_app(tmp_path, record=_success_record(), full_workspace=True)

    assert any("AUTOMATIC RECORD" in item.value and "FAIL" in item.value for item in app.markdown)
    assert any("LIVE VALIDATION" in item.value and "VERIFIED" in item.value for item in app.success)

    app.text_area[0].input("Independent operator confirmation.").run(timeout=10)
    app.button[0].click().run(timeout=10)

    assert any("AUTOMATIC RECORD" in item.value and "FAIL" in item.value for item in app.markdown)
    assert any("HUMAN RECORD" in item.value for item in app.info)
    assert any("LIVE VALIDATION" in item.value and "VERIFIED" in item.value for item in app.success)


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


def test_ui_exposes_structured_audit_provenance() -> None:
    app = _app()
    expected = run_demo(REPO_ROOT).provenance.model_dump(mode="json")
    json_payloads = [json.loads(item.value) for item in app.json]

    assert any(expander.label == "Audit provenance" for expander in app.expander)
    assert expected in json_payloads


def test_human_review_does_not_leak_between_cases() -> None:
    app = _app()

    app.text_area[0].input("Confirmed bridge under manual review.").run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert app.info

    app.selectbox[0].select("Ambiguous / degraded image").run(timeout=10)

    assert not any("HUMAN RECORD" in item.value for item in app.info)
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
