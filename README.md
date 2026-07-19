# Inspection Copilot

Evidence-backed visual inspection for manufacturing quality teams, built for
**OpenAI Build Week 2026 — Work & Productivity**.

Inspection Copilot turns an image and a versioned SOP into a structured
`pass`, `fail`, or `needs_review` decision. Every automatic verdict must carry
observable evidence and a valid SOP rule reference. Ambiguity is escalated to a
human instead of being hidden behind model confidence.

Each result also includes deterministic audit provenance: SHA-256 fingerprints
for the canonical SOP and exact image bytes, requested and effective model IDs,
and schema, prompt, and policy versions.

## Build Week status

This is a new standalone repository created during Build Week. Its first
credential-free synthetic mock flow, GPT-5.6 Responses API adapter, and web
experience are runnable behind the same typed contract.

- Codex owns architecture, implementation, tests, documentation, and commits.
- The GPT-5.6 runtime adapter is implemented and mock-transport verified. The
  canonical one-request live validation is not claimed until its sanitized
  evidence record exists and passes the repository validator.
- Grok participates only after the working mock flow as an external red-team
  reviewer of public documentation and synthetic scenarios.
- No application code is copied from prior RoboQC, Claude, or Grok work.

## How Codex was used

Codex developed the product in small, reviewable slices rather than generating
one unverified application dump. The public commit history records the concrete
episodes:

- Contract-first TDD established strict SOP, evidence, assessment, and
  fail-closed policy behavior before the UI (`eb0c765`, `560d768`).
- Codex built the deterministic synthetic inspection flow and Streamlit operator
  workspace, then guarded automatic and human decisions as separate records.
- The bounded GPT-5.6 provider and explicit live-request gate were added behind
  the existing injected interface (`549d730`, `65cc948`).
- Codex triaged an external Grok red-team review, independently implemented the
  accepted remediations, and rejected unsupported accuracy-style claims
  (`bd5146a`, `3382b78`).
- Adversarial review closed live-smoke bypasses and added a read-only,
  fail-closed evidence panel (`88d1026`, `d3ef1a9`).

The Build Week `/feedback` identifier is submission metadata, not application
data. It is intentionally not committed; it must be collected from the primary
Codex session and entered directly in Devpost.

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
review as separate records. Human review is session-local in this MVP. A third,
read-only **Live validation evidence** panel is also separate: it reports `NOT
RUN` when the canonical file is absent, `SCHEMA VERIFIED` only for a strict
sanitized `LiveEvidenceRecord`, and `UNTRUSTED / UNAVAILABLE` for any present
artifact that cannot be safely read and validated. Schema verification proves
structure and internal content consistency, not who produced the local file. The
panel has no request or file controls.

## Fail-closed proof

- `tests/test_demo.py` repeats the offline flows and checks identical structured
  results, including `needs_review` for the degraded scenario.
- `tests/test_policy.py` proves that missing evidence and an invalid SOP rule
  reference force `needs_review` even when the proposed verdict is `fail`.
- `tests/test_ui.py` guards distinct automatic/human record labels, mandatory
  rationale, a human timestamp, the escalation action, and separation from the
  read-only live-validation panel.
- `tests/test_live_validation.py` rejects tampered, oversized, linked,
  non-regular, raced, and unreadable live evidence without displaying partial
  fields.

## GPT-5.6 provider boundary

The typed provider adapter is implemented behind the same `Inspector` interface
used by the offline fixture. Its mock-transport tests verify the serialized
Responses API boundary: `model=gpt-5.6`, high-detail image input, strict JSON
Schema output, `store=false`, a 60-second timeout, 2,000 output tokens, and zero
automatic SDK retries. The adapter returns an explicit `ProviderOutcome`.
Timeout, rate limiting, provider unavailability, model refusal, and invalid
structured output remain distinct states and become sanitized `needs_review`
reasons.

The default CLI and UI remain credential-free fixture flows. Installation and
tests never make a live model call. The separately approved smoke uses a
dedicated one-request runner.

The sanitized evidence contract for that smoke is implemented. Until the runner
is actually executed, no live-evidence file is committed or implied. It permits
only a UTC timestamp, content-derived record/case IDs, provider and decision
routing fields, model and workflow versions, and SOP/image fingerprints. It
excludes raw case IDs, images, SOP bodies, model/assessment free text, response
IDs, usage, and credentials. Exact replay is a byte-identical no-op; different
evidence cannot replace the first atomically published record.

At startup, the UI performs a read-only check of only
`evidence/live_validation_evidence.json` under the repository root. It does not
follow symbolic links, accepts only a bounded regular file whose complete JSON
passes the strict record schema and content-derived ID check, and never constructs
a provider. A schema-verified typed provider failure is displayed as
`needs_review`, not as a successful inspection or an offline verdict. Local write
access remains outside this validation boundary; authenticity depends on review
of the Goal 2 artifact and commit provenance.

The case fingerprint is pseudonymous routing evidence, not anonymization; real
customer identifiers remain outside the MVP and must not be supplied.

The dedicated CLI exposes the live path only through explicit confirmation:

```bash
inspection-copilot-live-smoke \
  --repo-root . \
  --confirm-one-live-request
```

This command requires `OPENAI_API_KEY` in the process environment and performs
at most one provider inspection for a built-in synthetic scenario. Before the
provider is constructed, it atomically reserves the attempt and refuses an
existing evidence file or reservation. Any typed provider failure is persisted
without retry; an uncertain exception after the request boundary retains the
reservation and requires manual review before any new authorization. The legacy
`inspection-copilot-demo --provider openai --confirm-live-request` path routes
through the same runner. Do not use either command merely to verify installation;
use the fixture commands above for credential-free checks.

## How GPT-5.6 was used

GPT-5.6 is the runtime vision reasoner for the bounded live path, while the
default demo remains deterministic and credential-free. One Responses API call
receives the repository-owned synthetic image plus the typed inspection request,
including the versioned SOP rules. It requests model alias `gpt-5.6`, high image
detail, medium reasoning effort, and strict Pydantic structured output, with
`store=false`, a 60-second timeout, 2,000 output tokens, and SDK retries disabled.

The returned assessment is not trusted directly. The deterministic policy layer
revalidates evidence and SOP references; refusal, timeout, rate limiting,
unavailability, or invalid structured output becomes a typed `needs_review`
outcome. Mock-transport tests prove this SDK boundary without spending API
credits. A real GPT-5.6 outcome is claimed only after the one-request runner
creates `evidence/live_validation_evidence.json` and the UI reports `SCHEMA
VERIFIED`. The synthetic fixture results and evaluation ledger are workflow
proof, not measurements of model or manufacturing accuracy.

Run the deterministic policy-level evaluation:

```bash
inspection-copilot-eval --repo-root .
```

The committed report is a workflow regression baseline, not a claim about model
or manufacturing accuracy.

Rebuild the sanitized offline inspection ledger:

```bash
inspection-copilot-ledger \
  --repo-root . \
  --output evidence/offline_inspection_ledger.json
```

The ledger contains only structured routing metadata and provenance. It excludes
raw case IDs, images, SOP bodies, observations, assessment summaries, response
IDs, usage, timestamps, and secrets. The same fixture build produces identical
JSON.

## Local quality gate

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy
pytest -q
```

## Official platform references

- [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/model-guidance?model=gpt-5.6)
- [Responses API](https://developers.openai.com/api/docs/api-reference/responses)
- [Images and vision](https://developers.openai.com/api/docs/guides/images-vision)
- [OpenAI Build Week](https://openai.devpost.com/)

## Architecture and external review

- [Architecture](docs/ARCHITECTURE.md)
- [Evaluation ledger](docs/EVALUATION.md)
- [Sanitized inspection ledger](evidence/offline_inspection_ledger.json)
- [2:50 demo script](docs/DEMO_SCRIPT.md)
- [Video production and YouTube runbook](docs/VIDEO_PRODUCTION.md)
- [Submission checklist](docs/SUBMISSION_CHECKLIST.md)
- [Devpost submission draft](docs/DEVPOST_DRAFT.md)
- [Grok red-team packet](docs/GROK_REVIEW_PACKET.md)
- [Grok review and Codex triage](docs/reviews/GROK_RED_TEAM_2026-07-15.md)

## License

MIT
