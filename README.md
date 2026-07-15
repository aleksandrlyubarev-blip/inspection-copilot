# Inspection Copilot

Evidence-backed visual inspection for manufacturing quality teams, built for
**OpenAI Build Week 2026 — Work & Productivity**.

Inspection Copilot turns an image and a versioned SOP into a structured
`pass`, `fail`, or `needs_review` decision. Every automatic verdict must carry
observable evidence and a valid SOP rule reference. Ambiguity is escalated to a
human instead of being hidden behind model confidence.

## Build Week status

This is a new standalone repository created during Build Week. Its first
credential-free synthetic mock flow is runnable now; the GPT-5.6 Responses API
adapter and web experience follow behind the same typed contract.

- Codex owns architecture, implementation, tests, documentation, and commits.
- GPT-5.6 runtime will analyze images and return strict structured assessments.
- Grok participates only after the working mock flow as an external red-team
  reviewer of public documentation and synthetic scenarios.
- No application code is copied from prior RoboQC, Claude, or Grok work.

## Run the synthetic mock flow

```bash
python -m pip install -e '.[dev]'
inspection-copilot-demo --repo-root .
inspection-copilot-demo --repo-root . --scenario ambiguous
```

The first command returns an evidence-backed `fail`; the second uses a degraded
fixture and deterministically fails closed to `needs_review`. Both commands read
only repository-owned synthetic fixtures and emit strict JSON. They do not read
API credentials or access the network. Regenerate both deterministic images with:

```bash
python scripts/generate_synthetic_demo.py
```

Run the local inspection workspace:

```bash
streamlit run streamlit_app.py
```

The scenario selector demonstrates both supported automation and ambiguity. The
screen keeps the automatic verdict, cited SOP evidence, and timestamped human
review as separate records. Human review is session-local in this MVP.

## Fail-closed proof

- `tests/test_demo.py` repeats the offline flows and checks identical structured
  results, including `needs_review` for the degraded scenario.
- `tests/test_policy.py` proves that missing evidence and an invalid SOP rule
  reference force `needs_review` even when the proposed verdict is `fail`.
- `tests/test_ui.py` guards distinct automatic/human record labels, mandatory
  rationale, a human timestamp, and the escalation action.

## Local quality gate

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
pytest -q
```

## Official platform references

- [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model)
- [Responses API](https://developers.openai.com/api/docs/api-reference/responses)
- [Images and vision](https://developers.openai.com/api/docs/guides/images-vision)
- [OpenAI Build Week](https://openai.devpost.com/)

## Architecture and external review

- [Architecture](docs/ARCHITECTURE.md)
- [Three-minute demo script](docs/DEMO_SCRIPT.md)
- [Grok red-team packet](docs/GROK_REVIEW_PACKET.md)
- [Grok review and Codex triage](docs/reviews/GROK_RED_TEAM_2026-07-15.md)

## License

MIT
