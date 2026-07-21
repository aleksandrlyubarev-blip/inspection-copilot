# Grok Red-Team Review — 2026-07-15

## Provenance and boundary

Grok reviewed the public `agent/vertical-scaffold` branch after the offline CLI
and Streamlit mock flow were working. It received only the URLs listed in
`docs/GROK_REVIEW_PACKET.md`. The prompt explicitly prohibited implementation
code, patches, commits, private data, real photographs, credentials, and customer
SOPs.

This document is untrusted external review input. Acceptance decisions and all
implementation remain Codex-owned.

## Findings

### GROK-01 — P1 · claim

The repository describes the fixture flow as deterministic and fail-closed, but
the public narrative does not make the enforcement tests visible enough. A judge
could mistake the result for canned JSON.

Suggested acceptance check: repeated CLI runs are identical, and an invalid or
missing SOP reference forces `needs_review`.

### GROK-02 — P1 · UX

The UI separates automatic output and human review, but stronger record labels
and timing/context would reduce the risk that a technician treats model output
as the final operational decision. A `needs_review` case should make escalation
prominent.

Suggested acceptance check: clearly distinct automatic and human records,
mandatory rationale, and a highlighted escalation action for `needs_review`.

### GROK-03 — P2 · edge case

One clean stylized bridge fixture makes the demo look overly easy. A second
ambiguous or poor-image fixture should prove that the policy escalates instead
of forcing a verdict.

Suggested acceptance check: a second committed synthetic case deterministically
returns `needs_review`.

### GROK-04 — P2 · demo

The repository did not yet contain an explicit timed three-minute demo path.

Suggested acceptance check: publish a numbered run-of-show ending with automatic
and human decisions shown separately.

### GROK-05 — P2 · voiceover

The synthetic-only limitation should be spoken in the opening seconds so the
demo cannot be mistaken for model-accuracy evidence.

Suggested acceptance check: the first 15 seconds call the image a
repository-owned synthetic workflow fixture.

### GROK-06 — P3 · UX

The SOP language is abstract; examples or region-level visual callouts could
accelerate comprehension.

Suggested acceptance check: pair acceptance/rejection criteria with annotated
image regions.

### GROK-07 — P3 · policy

A single evidence item can support an automatic decision; Grok proposed a larger
minimum evidence count or multi-rule cross-validation.

Suggested acceptance check: enforce the chosen evidence threshold and SOP link
contract in policy tests.

## Grok's prioritized fixes

1. Add an ambiguous synthetic fixture that proves `needs_review`.
2. Strengthen visual separation and escalation affordance in the workspace.
3. Publish a timed demo script with an early synthetic-only disclaimer.

## Codex triage

| Finding | Decision | Rationale | Codex proof |
|---|---|---|---|
| GROK-01 | Accept | Judge-facing proof should be explicit even though the tests already exist. | README test evidence and deterministic/invalid-reference guards. |
| GROK-02 | Accept | Clear record ownership and escalation are core safety UX. | AppTests for labels, timestamped human record, and escalation CTA. |
| GROK-03 | Accept | A second case demonstrates the jagged frontier without accuracy claims. | Synthetic ambiguous fixture and `needs_review` E2E test. |
| GROK-04 | Accept | A timed path directly improves the submission demo. | `docs/DEMO_SCRIPT.md`. |
| GROK-05 | Accept | The disclaimer prevents an unsupported accuracy implication. | Opening voiceover check in the demo script. |
| GROK-06 | Defer | Region-level evidence schema is useful but wider than the first vertical slice. | Track after the bounded GPT-5.6 adapter. |
| GROK-07 | Reject as proposed | One relevant item can be sufficient; arbitrary count does not prove quality. Valid reference and evidence-direction consistency are already enforced. | Existing policy tests remain the quality gate. |

## Positioning and opening supplied by Grok

Positioning: Inspection Copilot delivers auditable, evidence-backed visual
inspection decisions that escalate ambiguity through a provider-neutral workflow.

Opening concept: identify the synthetic image and versioned SOP, show the
evidence-linked verdict, then demonstrate that ambiguity becomes `needs_review`
and remains separate from the human decision.
