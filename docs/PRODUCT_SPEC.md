# Inspection Copilot — Product Spec

## Goal

Give a manufacturing QC technician a fast, auditable second opinion on a visual
inspection case without replacing the technician or presenting unsupported
certainty.

## Audience

The primary user is a QC technician reviewing a first-article SMT PCB against a
versioned visual inspection SOP. A quality lead reviews escalated cases and the
aggregate evidence trail.

## Core scenarios

1. The technician opens a repository-owned synthetic inspection case.
2. Inspection Copilot evaluates the image against explicit SOP rules.
3. The result shows decision, observations, locations, SOP references, and image
   quality in one view.
4. Missing evidence, unusable imagery, unknown defects, or invalid SOP references
   yield `needs_review`.
5. A human can record the final operational decision without rewriting the model
   result.

## MVP scope

- One versioned SOP and repository-owned synthetic dataset.
- Typed input, evidence, assessment, and result contracts.
- Deterministic SOP/image fingerprints and versioned result provenance.
- A bounded, sanitized, deterministic local inspection ledger for audit evidence.
- A no-clobber sanitized evidence contract prepared before any authorized live smoke.
- A deterministic offline provider for end-to-end demo and tests.
- A GPT-5.6 Responses API provider behind the same interface.
- A simple web UI that clearly separates model verdict, evidence, and human review.
- Sanitized, reproducible evaluation evidence.

## Non-goals

- Production deployment, authentication, billing, or multi-tenancy.
- Real production photos, customer SOPs, or personal data.
- Hardware integration, camera control, or claims of industrial accuracy.
- Hosted multi-agent orchestration in the first vertical slice.
- Grok-authored implementation or copied code from another project.

## Acceptance criteria

1. Given a valid synthetic case and supported evidence, the offline flow returns a
   schema-valid `pass` or `fail` with a real SOP rule reference.
2. Given incomplete evidence, poor image quality, an unknown defect, or an invalid
   SOP reference, the flow returns `needs_review` with explicit reasons.
3. The same request and fixture produce the same JSON result without network access.
4. A local web page presents the case, verdict, evidence, and escalation reason in
   one coherent screen.
5. The GPT-5.6 provider request uses the Responses API, image input, strict structured
   output, `store=false`, bounded timeout/output, and no automatic retries.
6. Tests, lint, formatting, and strict type checking pass before public push.
7. Grok receives only public docs and synthetic inputs; its findings are recorded
   separately and accepted changes are reimplemented in Codex with regression tests.
8. Every result identifies the exact image and canonical SOP by SHA-256 and records
   requested/effective model plus schema, prompt, and policy versions.
9. The offline ledger stores only structured routing metadata and provenance;
   exact replay is idempotent and committed evidence matches a fresh fixture build.
10. A live smoke can persist only the strict sanitized record; naive timestamps,
    tampered IDs, provider/result mismatch, and replacement of different evidence
    are rejected before any claim of validation is made.

## Verification

- Focused unit tests for policy and schema invariants.
- Offline end-to-end CLI test.
- Mock-transport test for the exact OpenAI request boundary.
- Browser smoke for the main synthetic flow.
- Ruff, Mypy, and full pytest gate.

## Stop-lines

- No live model request without a separately authorized, cost-bounded smoke.
- No external reviewer receives secrets, real photos, or private SOPs.
- No deployment or submission until local and browser gates pass.
