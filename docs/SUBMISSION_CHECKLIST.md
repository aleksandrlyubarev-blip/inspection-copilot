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
- [x] Separate automatic verdict, operator review, and read-only live-evidence
  panels.
- [x] Pre-smoke local gate: 110 tests, Ruff lint/format, strict Mypy, `pip check`,
  and `git diff --check` are green.
- [x] Three-minute walkthrough in [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

## Human-gated critical path

- [ ] Make `OPENAI_API_KEY` available to the process through a secure local
  environment. Never paste it into chat, logs, source files, or commits.
- [ ] Confirm that neither the canonical evidence file nor its reservation
  marker exists, then run exactly once:

  ```bash
  inspection-copilot-live-smoke \
    --repo-root . \
    --confirm-one-live-request
  ```

- [ ] Do not retry. If the command reports uncertainty or leaves a reservation,
  inspect it manually before requesting new authorization.
- [ ] Open the Streamlit app and confirm the live panel reports `SCHEMA VERIFIED`
  for the sanitized record. Keep raw model output, response IDs, usage, and
  credentials out of the repository.
- [ ] Re-authenticate GitHub CLI with `gh auth login -h github.com`, then update
  the existing draft PR description. Do not create a duplicate PR.
- [ ] Run the quality gate from a fresh clone and rehearse the walkthrough.
- [ ] Record a video under three minutes using only synthetic data and the
  scripted trust-state explanation.
- [ ] Run `/feedback` in the primary Codex session and enter its identifier
  directly in Devpost. Do not commit the identifier.
- [ ] Add the final public repository and video links to Devpost, proofread the
  submission, and submit only with explicit human approval.
- [ ] Review the draft PR and merge only with explicit human approval.

## Schedule

- Saturday: obtain the single sanitized live-validation record and verify its UI
  state.
- Sunday: freeze features, finish judge-facing copy, and rehearse the demo.
- Monday: fresh-clone proof, video recording, and Devpost draft.
- Tuesday: buffer and final human submission only; no architectural work.

If live validation cannot be completed safely, preserve the honest `NOT RUN`
state. Never substitute fixture output or a hand-written file as live evidence.
