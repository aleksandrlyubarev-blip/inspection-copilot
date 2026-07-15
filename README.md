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
```

The command reads only repository-owned synthetic fixtures and emits a strict
JSON result. It does not read API credentials or access the network. Regenerate
the deterministic demo image with:

```bash
python scripts/generate_synthetic_demo.py
```

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

## License

MIT
