"""Streamlit presentation for the synthetic Inspection Copilot flow."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path

import streamlit as st

from inspection_copilot.demo import DemoScenario, load_demo_request, run_demo
from inspection_copilot.domain import Decision, Evidence, InspectionResult, ProviderStatus
from inspection_copilot.live_validation import LiveValidationState, load_live_validation

_SCENARIOS = {
    "Clear solder bridge": DemoScenario.BRIDGE_FAIL,
    "Ambiguous / degraded image": DemoScenario.AMBIGUOUS,
}


def _automatic_record_html(result: InspectionResult, *, verdict_class: str) -> str:
    case_id = escape(result.case_id)
    model = escape(result.model)
    decision = escape(result.final_decision.value.upper())
    summary = escape(result.summary)
    safe_class = escape(verdict_class, quote=True)
    return f"""
        <div class="record-label">
          AUTOMATIC RECORD · {case_id} · {model}
        </div>
        <div class="{safe_class}">
          <h3>{decision}</h3>
          <div>{summary}</div>
        </div>
    """


def _evidence_card_html(item: Evidence) -> str:
    observation = escape(item.observation)
    location = escape(item.location)
    sop_rule_id = escape(item.sop_rule_id)
    return f"""
        <div class="evidence-card">
          <strong>{observation}</strong><br/>
          <small>{location} · SOP <code>{sop_rule_id}</code></small>
        </div>
    """


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #081b18; color: #eefbf7; }
        .block-container { max-width: 1180px; padding-top: 2.2rem; }
        [data-testid="stMetric"] {
            background: #102a25;
            border: 1px solid #2f665b;
            border-radius: 14px;
            padding: 0.9rem 1rem;
        }
        .verdict {
            background: linear-gradient(135deg, #3b1718, #251112);
            border: 1px solid #ff6b5f;
            border-radius: 18px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1rem;
        }
        .verdict h3 { color: #ff8c83; margin: 0 0 0.35rem 0; }
        .verdict.review {
            background: linear-gradient(135deg, #3a2b13, #241c0e);
            border-color: #ffd28c;
        }
        .verdict.review h3 { color: #ffd28c; }
        .evidence-card {
            background: #102a25;
            border: 1px solid #2f665b;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin: 0.65rem 0;
        }
        .eyebrow { color: #69d3b8; font-weight: 700; letter-spacing: 0.08em; }
        .record-label {
            color: #9adac9;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            margin-bottom: 0.45rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_live_validation_panel(repo_root: Path) -> None:
    """Render only strictly validated data from the fixed live-evidence path."""

    st.markdown("### Live validation evidence")
    st.caption(
        "Read-only trust state for the separately authorized one-request smoke. "
        "It never changes the offline automatic verdict or the human record."
    )
    snapshot = load_live_validation(repo_root)
    if snapshot.state is LiveValidationState.NOT_RUN:
        st.info("LIVE VALIDATION · NOT RUN — no canonical sanitized evidence is present.")
        return
    if snapshot.state is LiveValidationState.UNTRUSTED_OR_UNAVAILABLE:
        st.error(
            "LIVE VALIDATION · UNTRUSTED / UNAVAILABLE — the artifact is ignored and "
            "no partial fields are displayed."
        )
        return

    record = snapshot.record
    if record is None:
        st.error("LIVE VALIDATION · UNTRUSTED / UNAVAILABLE — no verified record.")
        return

    status = record.provider_status.value.upper()
    decision = record.final_decision.value.upper()
    message = f"LIVE VALIDATION · SCHEMA VERIFIED · {status} · {decision}"
    if (
        record.provider_status is ProviderStatus.SUCCESS
        and record.final_decision is not Decision.NEEDS_REVIEW
    ):
        st.success(message)
    else:
        st.warning(message)
    st.caption(
        "Strict schema and content consistency only, not proof of origin. Sanitized typed "
        "metadata only; no response ID, usage, or raw model output."
    )
    st.json(record.model_dump(mode="json"), expanded=False)


def render(repo_root: Path) -> None:
    st.set_page_config(page_title="Inspection Copilot", page_icon="🔎", layout="wide")
    _inject_styles()

    st.markdown(
        '<div class="eyebrow">OPENAI BUILD WEEK · WORK & PRODUCTIVITY</div>',
        unsafe_allow_html=True,
    )
    st.title("Inspection Copilot")
    st.caption("Evidence-backed visual QC · synthetic offline demonstration")
    scenario_label = st.selectbox("Synthetic scenario", options=list(_SCENARIOS))
    scenario = _SCENARIOS[scenario_label]

    request = load_demo_request(repo_root, scenario=scenario)
    result = run_demo(repo_root, scenario=scenario)
    image_path = repo_root / "examples" / "synthetic" / request.case.image_ref

    image_column, verdict_column = st.columns([1.35, 1])
    with image_column:
        st.image(image_path, caption="Repository-owned synthetic inspection fixture")
    with verdict_column:
        verdict_class = "verdict review" if result.review_reasons else "verdict"
        st.markdown(
            _automatic_record_html(result, verdict_class=verdict_class),
            unsafe_allow_html=True,
        )
        metric_left, metric_right = st.columns(2)
        metric_left.metric("Confidence", f"{result.assessment.confidence:.0%}")
        metric_right.metric("Image quality", result.assessment.image_quality.value.title())

        st.markdown("#### Why this verdict")
        if result.assessment.evidence:
            for item in result.assessment.evidence:
                st.markdown(
                    _evidence_card_html(item),
                    unsafe_allow_html=True,
                )
        else:
            reasons = ", ".join(reason.value for reason in result.review_reasons)
            st.warning(f"No defensible automatic evidence. Review gates: {reasons}.")

    with st.expander("SOP rule used by the decision"):
        for rule in request.sop.rules:
            st.markdown(f"**{rule.rule_id} — {rule.description}**")
            st.write(f"Accept: {rule.acceptance}")
            st.write(f"Reject: {rule.rejection}")

    with st.expander("Audit provenance"):
        st.caption("Sanitized workflow versions and input fingerprints for this result.")
        st.json(result.provenance.model_dump(mode="json"), expanded=False)

    st.divider()
    render_live_validation_panel(repo_root)

    st.divider()
    st.markdown("### Human review")
    st.caption("The model result remains unchanged; this records a separate operator decision.")
    review_decision = st.selectbox(
        "Human decision",
        options=["pass", "fail", "needs_review"],
        index=1,
        key=f"human_decision_{result.case_id}",
    )
    rationale = st.text_area(
        "Review rationale",
        placeholder="Describe the observation that supports the human decision.",
        key=f"review_rationale_{result.case_id}",
    )
    action_label = "Escalate to human review" if result.review_reasons else "Record human review"
    if st.button(action_label, type="primary", key=f"review_action_{result.case_id}"):
        if not rationale.strip():
            st.warning("Add a review rationale before recording the decision.")
        else:
            reviews = dict(st.session_state.get("human_reviews", {}))
            reviews[result.case_id] = {
                "decision": review_decision,
                "rationale": rationale.strip(),
                "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
            st.session_state["human_reviews"] = reviews
            st.success("Human review recorded in this local session.")

    saved_review = st.session_state.get("human_reviews", {}).get(result.case_id)
    if saved_review:
        st.info(
            "HUMAN RECORD · "
            f"{result.case_id} · "
            f"Recorded at {saved_review['recorded_at']} · "
            f"Effective operator decision: {saved_review['decision']} — "
            f"{saved_review['rationale']}"
        )


__all__ = ["render", "render_live_validation_panel"]
