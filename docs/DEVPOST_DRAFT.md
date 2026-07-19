# Devpost Submission Draft

This is paste-ready English copy for the submission form. Add the public YouTube
URL after upload. The primary Codex `/feedback` Session ID is a human-only field:
enter it directly in Devpost and do not commit it here.

## Core fields

**Project name:** Inspection Copilot

**Tagline:** Evidence-backed visual inspection that fails closed when an AI
verdict cannot be defended.

**Track:** Work and Productivity

**Repository:** https://github.com/aleksandrlyubarev-blip/inspection-copilot

**Public YouTube demo:** PENDING — add the final public URL after upload.

**Primary Codex `/feedback` Session ID:** PENDING — collect it from the build
thread and enter it in Devpost only.

## Project description

Manufacturing quality teams often have to choose between slow manual inspection
and AI outputs that are difficult to audit. Inspection Copilot demonstrates a
safer middle path: every automatic visual verdict must cite observable evidence
and a valid rule from a versioned SOP. If the image, provider response, evidence,
or SOP reference cannot support a defensible decision, the workflow escalates to
`needs_review` instead of guessing.

The Streamlit workspace presents three deliberately separate records. The first
is the automatic inspection result with image evidence, SOP traceability, and
content fingerprints. The second is a rationale-gated operator review with its
own timestamp. The third is a read-only trust state for a separately authorized
GPT-5.6 validation. It shows `NOT RUN` when no canonical evidence exists,
`SCHEMA VERIFIED` only for a strict sanitized record, and fails closed for
tampered, linked, raced, oversized, or unreadable artifacts.

The default demonstration is credential-free and uses repository-owned synthetic
images so judges can reproduce both a supported `fail` and an ambiguous
`needs_review` result without an API key or customer data. The bounded live path
uses the OpenAI Responses API with model alias `gpt-5.6`, high-detail vision input,
medium reasoning effort, strict Pydantic structured output, disabled storage,
disabled SDK retries, and a 60-second timeout. A deterministic policy layer then
revalidates the model's evidence and SOP references. Provider refusal, timeout,
rate limiting, unavailability, or invalid output remains a typed escalation
rather than being flattened into a successful verdict.

## How Codex was used

Codex was the primary engineering collaborator throughout the Build Week commit
history. It helped turn the product idea into explicit contracts and acceptance
criteria, wrote focused tests before behavior changes, implemented the offline
vertical slice and Streamlit workflow, and built the bounded GPT-5.6 provider
behind an injected interface. Codex also triaged an external red-team review,
implemented accepted findings independently, and ran repeated adversarial review
cycles against the live-request and evidence trust boundaries. Those cycles
closed symlink, race, output-path, retry, and unsafe-rendering failure modes before
the project was called ready.

The most important product decision was to keep automatic judgment, operator
review, and live-validation provenance separate. The most important engineering
decision was to fail closed at every untrusted boundary. Codex accelerated both
the implementation and the evidence needed to defend those decisions: 110 tests,
strict typing, deterministic synthetic fixtures, a public commit trail, a
fresh-clone proof, and green GitHub Actions.

## How GPT-5.6 was used

GPT-5.6 is the runtime vision reasoner for the bounded live inspection path. It
receives a synthetic image and a typed request containing the versioned SOP, then
returns a strict assessment with a proposed decision, image quality, visible
observations, locations, and SOP rule references. The application does not accept
that assessment on faith: deterministic policy decides whether it is complete
enough to become `pass` or `fail`, otherwise it becomes `needs_review`.

The repository proves the exact Responses API request and structured-output
boundary with local HTTP mock transport. A real live result must not be claimed
until the one-request runner creates the canonical sanitized record and the UI
validates it. Fixture outputs and the evaluation ledger demonstrate workflow
behavior, not model or manufacturing accuracy.

## What is technically notable

- A single typed contract is shared by the deterministic fixture and GPT-5.6
  provider.
- SHA-256 fingerprints bind results to exact image bytes, canonical SOP content,
  and versioned prompt/policy metadata.
- The live runner reserves one fixed evidence target before provider construction,
  makes at most one request, never retries automatically, and preserves uncertain
  boundary state for manual review.
- Sanitized evidence excludes images, SOP bodies, free text, response IDs, token
  usage, credentials, and raw customer identifiers.
- The evidence reader rejects symlinks, non-regular or oversized files, mutation
  races, invalid schemas, and content-hash mismatches without showing partial data.

## Impact and next steps

The immediate audience is manufacturing quality teams that need AI assistance
without losing operator control or auditability. The MVP shows how a visual model
can shorten first-pass triage while preserving a clear human escalation path and
evidence trail. A production continuation would validate performance on approved,
representative data; add authenticated multi-user review and durable storage; and
integrate with a quality-management workflow. Those production features are
intentionally outside this synthetic Build Week scope.

## Judge testing instructions

Use Python 3.11 or 3.12:

```bash
python -m pip install -e '.[dev]'
inspection-copilot-demo --repo-root .
inspection-copilot-demo --repo-root . --scenario ambiguous
streamlit run streamlit_app.py
```

No API key or network access is required for these paths. The first CLI command
returns an evidence-backed `fail`; the second deterministically escalates to
`needs_review`. The web app exposes the same two scenarios plus separate human
review and live-validation panels.

Run the complete local gate with:

```bash
ruff check .
ruff format --check .
mypy
pytest -q
```

## Built with

Python, Streamlit, OpenAI Responses API, GPT-5.6, Pydantic, Pillow, Pytest, Ruff,
Mypy, GitHub Actions, and Codex.

## Submission assets still requiring a human

- Record the audio walkthrough from [DEMO_SCRIPT.md](DEMO_SCRIPT.md) using the
  setup, honest trust-state wording, and paste-ready YouTube metadata in
  [VIDEO_PRODUCTION.md](VIDEO_PRODUCTION.md). Keep it at 3:00 or less, upload it
  publicly to YouTube, verify the URL while signed out, and enter it above.
- Run `/feedback` in the primary Codex build thread and enter that Session ID
  directly in the form.
- Proofread the saved Devpost draft and perform the final submission before
  Tuesday, July 21, 2026 at 17:00 PT.

## Official requirements checked

- [OpenAI Build Week official rules](https://openai.devpost.com/rules)
- [OpenAI Build Week submission FAQ](https://openai.devpost.com/details/faqs)
