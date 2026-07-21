# Submission Checklist

Deadline: Tuesday, July 21, 2026 at 17:00 PT. The scope is frozen around the
existing Streamlit application. Do not start a FastAPI rewrite, add CAD or
hardware integration, create another repository, or add unrelated features.

## Ready now

- [x] Public `inspection-copilot` repository with an MIT license.
- [x] Credential-free synthetic `fail` and `needs_review` demo flows.
- [x] Bounded GPT-5.6 adapter with strict structured output and fail-closed
  provider outcomes.
- [x] Fixed-target, at-most-one-request live-smoke runner with no SDK retries.
- [x] The single authorized GPT-5.6 request completed on 2026-07-19 with provider
  success and an evidence-backed `fail`; the canonical record ID begins
  `121810d71ec6`.
- [x] The fixed-path loader validates the sanitized canonical record and the UI
  reports `SCHEMA VERIFIED · SUCCESS · FAIL`; no reservation marker remains.
- [x] Separate automatic verdict, operator review, and read-only live-evidence
  panels.
- [x] Current local gate: 111 tests, Ruff lint/format, strict Mypy, `pip check`,
  and `git diff --check` are green.
- [x] Fresh clone of public branch `agent/vertical-scaffold` at `93e2e49`
  installs on Python 3.11, passes the same gate, runs both fixture scenarios, and
  renders the expected `NOT RUN` live-evidence state.
- [x] Existing draft PR #1 has current scope/verification text and green GitHub
  Actions checks; no duplicate PR was created.
- [x] 2:50 walkthrough in [DEMO_SCRIPT.md](DEMO_SCRIPT.md), leaving ten seconds
  of margin under the three-minute limit.
- [x] Recording setup, trust-state variants, YouTube metadata, and acceptance
  checks in [VIDEO_PRODUCTION.md](VIDEO_PRODUCTION.md).
- [x] Paste-ready English Devpost copy in [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md),
  reconciled with the current official rules and explicit human-only fields.

## Human-gated critical path

- [x] Preserve the validated canonical evidence exactly as written. Do not run
  the live-smoke command again, request another model response, or expose the
  credential, raw output, response ID, or usage.
- [ ] Record a public YouTube video of 3:00 or less using only synthetic data and
  the scripted trust-state explanation. Include an English voiceover or English
  translation, a clear working demo, concrete Codex workflow/decisions, and
  GPT-5.6's integration and runtime role. Follow
  [VIDEO_PRODUCTION.md](VIDEO_PRODUCTION.md).
- [ ] Open the public YouTube URL while signed out and confirm that no secret,
  customer data, response metadata, or `/feedback` ID is visible.
- [ ] Run `/feedback` in the primary Codex session and enter its identifier
  directly in Devpost. Do not commit the identifier.
- [ ] Add the final public repository and video links to Devpost, proofread the
  submission, and submit only with explicit human approval.
- [ ] Review the draft PR and merge only with explicit human approval.

## Schedule

- Saturday: completed the single sanitized live validation and verified its UI
  state.
- Sunday: freeze features, finish judge-facing copy, and rehearse the demo.
- Monday: fresh-clone proof, video recording, and Devpost draft.
- Tuesday: buffer and final human submission only; no architectural work.

The canonical record now exists and is immutable for this submission. If its UI
state changes from `SCHEMA VERIFIED · SUCCESS · FAIL`, stop and investigate;
never replace it with fixture output or a hand-written file.
