# 2:50 Demo Script (3:00 Maximum)

## 0:00–0:12 — Scope and safety

Voiceover: “This is Inspection Copilot. The images you will see are
repository-owned synthetic workflow fixtures, not evidence of model accuracy or
production readiness.”

Show the public repository and the synthetic-fixture notice in the workspace.

## 0:12–0:32 — The inspection contract

Show the versioned SOP. Explain that an automatic decision requires observable
evidence, a location, a valid SOP rule, adequate image quality, and confidence
above the deterministic policy threshold. Anything incomplete becomes
`needs_review`.

## 0:32–1:00 — Supported automatic failure

Select **Clear solder bridge**. Show the automatic `FAIL`, confidence, image
quality, observation, location, and `SOLDER-BRIDGE-001`. Point out the
**AUTOMATIC RECORD** label and that this record is not silently overwritten by a
human.

## 1:00–1:25 — Ambiguity fails closed

Select **Ambiguous / degraded image**. Show that the system returns
`NEEDS_REVIEW` instead of inventing a pass/fail answer. Read the visible review
gates and show the prominent **Escalate to human review** action.

## 1:25–1:48 — Human decision remains separate

Enter a short rationale and record a human decision. Show the separate
timestamped **HUMAN RECORD** while the automatic record remains unchanged.

## 1:48–2:15 — Reproducible and live-validation evidence

Show the two offline commands and the test suite. Explain that repeated fixture
runs produce identical structured JSON, while missing evidence and invalid SOP
references are regression-tested to force `needs_review`. Point to the separate
**Live validation evidence** panel: `NOT RUN` means no canonical evidence exists;
only a strict sanitized artifact can become `SCHEMA VERIFIED`; this proves
internal consistency, not origin or model accuracy. A verified provider failure
still ends in `needs_review`. Any unsafe or invalid artifact is ignored as
`UNTRUSTED / UNAVAILABLE`. If authentic one-request evidence is not present, show
and say `NOT RUN`; do not simulate or imply a live result.

## 2:15–2:38 — How Codex was used

Briefly show the public commit history or README. Explain that Codex established
the typed inspection contract with tests first, built the vertical slice in
reviewable commits, and made the product decision to keep automatic, human, and
live-validation records separate. Its adversarial review then closed symlink,
race, retry, output-path, and unsafe-rendering failure modes. Grok contributed
only a public-material red-team review; Codex independently implemented and
tested accepted findings.

## 2:38–2:50 — How GPT-5.6 was used

Close on the workspace. Explain that GPT-5.6 is the bounded live vision reasoner:
one high-detail Responses API request receives a synthetic image and versioned
SOP and returns strict structured evidence. Deterministic policy rechecks that
evidence and escalates anything incomplete to `needs_review`. End on the value:
faster inspection triage without hiding uncertainty or removing operator control.

Use [VIDEO_PRODUCTION.md](VIDEO_PRODUCTION.md) for the recording setup, exact
live-state wording, YouTube metadata, and final acceptance check.
