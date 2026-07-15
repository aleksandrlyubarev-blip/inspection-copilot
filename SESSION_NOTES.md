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

## Next steps

1. Complete Devpost join after the user login takeover.
2. Commit and publish the Codex remediation slice.
3. Add the bounded GPT-5.6 request contract behind the provider interface.
4. Run a separately authorized, cost-bounded live model smoke.
