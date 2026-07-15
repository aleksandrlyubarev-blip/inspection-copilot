# Three-Minute Demo Script

## 0:00–0:15 — Scope and safety

Voiceover: “This is Inspection Copilot. The images you will see are
repository-owned synthetic workflow fixtures, not evidence of model accuracy or
production readiness.”

Show the public repository and the synthetic-fixture notice in the workspace.

## 0:15–0:45 — The inspection contract

Show the versioned SOP. Explain that an automatic decision requires observable
evidence, a location, a valid SOP rule, adequate image quality, and confidence
above the deterministic policy threshold. Anything incomplete becomes
`needs_review`.

## 0:45–1:20 — Supported automatic failure

Select **Clear solder bridge**. Show the automatic `FAIL`, confidence, image
quality, observation, location, and `SOLDER-BRIDGE-001`. Point out the
**AUTOMATIC RECORD** label and that this record is not silently overwritten by a
human.

## 1:20–1:55 — Ambiguity fails closed

Select **Ambiguous / degraded image**. Show that the system returns
`NEEDS_REVIEW` instead of inventing a pass/fail answer. Read the visible review
gates and show the prominent **Escalate to human review** action.

## 1:55–2:20 — Human decision remains separate

Enter a short rationale and record a human decision. Show the separate
timestamped **HUMAN RECORD** while the automatic record remains unchanged.

## 2:20–2:45 — Reproducible evidence

Show the two offline commands and the test suite. Explain that repeated fixture
runs produce identical structured JSON, while missing evidence and invalid SOP
references are regression-tested to force `needs_review`.

## 2:45–3:00 — Build Week contribution

Close on the architecture: Codex owns the implementation, tests, documentation,
and commit history; GPT-5.6 runs behind a bounded one-request vision provider and
typed evidence boundary; Grok contributed only an independent public-material
red-team review whose accepted findings were reimplemented and tested in Codex.
