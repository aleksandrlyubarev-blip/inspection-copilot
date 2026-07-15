# Session Notes

## Current goal

Complete the first five governance and implementation steps for a standalone
Inspection Copilot Build Week project.

## Decisions

- Track: Work & Productivity.
- Repository: `aleksandrlyubarev-blip/inspection-copilot`.
- Implementation is written from scratch in Codex; the prior RoboQC repository is
  requirements-only context.
- Grok is an external reviewer after a working mock flow, never a code author.
- Only repository-owned synthetic data is allowed in the MVP.

## Current state

- The remote repository was created public and empty on 2026-07-15.
- Devpost registration is waiting for user login takeover.
- Bootstrap/spec is the first local Codex-authored slice.
- Contract/policy TDD slice is green: strict SOP/evidence/result schemas and
  deterministic fail-closed reasons are implemented from scratch.
- Offline vertical slice is green: synthetic SOP/case/assessment/PNG flow runs
  through an injected fixture provider and emits a schema-valid JSON verdict.
- Web vertical slice is green: the Streamlit workspace presents the image,
  automatic verdict, evidence/SOP link, and rationale-gated human review.
- Public architecture and a non-coding Grok red-team packet are ready.
- GitHub Actions mirrors the local Ruff, Mypy, and pytest quality gate.
- Grok completed a non-coding public-material red-team review with seven findings.
  Codex accepted GROK-01 through GROK-05, deferred GROK-06, and rejected the
  arbitrary evidence-count proposal in GROK-07.
- Codex remediation implements the five accepted findings: public fail-closed
  proof, distinct automatic/human records, a degraded-image escalation scenario,
  and a timed demo script with an opening synthetic-only disclaimer.
- The bounded GPT-5.6 provider is implemented behind the existing `Inspector`
  interface. Default CLI/UI execution remains offline and credential-free.
- The CLI live path requires the explicit pair `--provider openai` and
  `--confirm-live-request`; without both, it does not construct the live provider.

## Verification

- GitHub read-back before the first commit: `isPrivate=false`, `isEmpty=true`.
- Python 3.11 `.venv` install completed with OpenAI SDK 2.45.0.
- Bootstrap gate: Ruff lint/format, strict Mypy, one package test, `pip check`,
  and `git diff --check` pass.
- Contract/policy gate: 9 focused tests and 10 full tests pass; Ruff and strict
  Mypy pass for three source files.
- Offline vertical gate: 3 focused tests and 13 full tests pass; the CLI JSON is
  valid, `pip check` passes, and regenerated PNG SHA-256 remains
  `46276da8d0052df523e3af09b01cdfc7c1b42b2fa1cea4be4c580ec64d70bdca`.
- Web vertical gate: 3 Streamlit AppTests and 16 full tests pass. A localhost
  browser smoke confirmed the verdict/evidence screen and recorded a separate
  human review with rationale.
- Remediation focused gate: 10 CLI/UI tests and the 20-test full suite pass under
  the repository Python 3.11 environment. The original bridge PNG remains
  byte-identical; the second image is generated deterministically by the same
  repository script.
- GPT-5.6 provider gate: 7 focused tests verify the high-detail image request,
  strict HTTP JSON Schema, `store=false`, timeout/output bounds, zero SDK retries,
  path and size validation, and sanitized failure behavior. The 27-test full
  suite, Ruff, and strict Mypy pass without a live request.
- Runtime-selector gate: CLI tests prove that missing confirmation stops before
  provider construction and the confirmed path performs one inspection. The
  credential-construction error is sanitized. The 30-test full suite, Ruff,
  strict Mypy, and dependency check pass.

## Next steps

1. Complete Devpost join after the user login takeover.
2. Run a separately authorized, cost-bounded live model smoke.
3. Add a small evaluation ledger for fixture and live results.
4. Expose the live result in the UI only after the CLI smoke is validated.
