# Repository Instructions

## Project Shape

- `src/inspection_copilot/` contains the standalone Build Week product.
- `tests/` contains deterministic tests; external API calls must be injected or mocked.
- `examples/synthetic/` contains only repository-owned synthetic demo data.
- `docs/PRODUCT_SPEC.md` is the product contract and `docs/WORK_PACKET.md` is the execution plan.
- `SESSION_NOTES.md` is the durable handoff for the main Codex thread.

## Common Commands

- Install: `python -m pip install -e '.[dev]'`
- Lint: `ruff check .`
- Format: `ruff format --check .`
- Typecheck: `mypy`
- Test: `pytest -q`

## Coding Rules

- Build new implementation in this repository; do not copy application code from RoboQC,
  Claude, Grok, or another repository.
- Define behavior with a focused failing test before implementation.
- Keep GPT-5.6 behind an injected provider boundary and keep the offline mock flow runnable
  without credentials or network access.
- Every automatic verdict must cite evidence and an SOP rule; uncertainty fails closed to
  `needs_review`.
- Never commit secrets, real customer data, private SOPs, or production photographs.
- Grok is an external red-team reviewer only. Store its critique as review input; implement
  accepted changes independently in Codex with new tests.

## Verification

- Run the narrowest affected test first, then Ruff, Mypy, and the complete test suite before
  calling a slice complete.
- Keep commits small and intentional so the Build Week history is reviewable.
- Record external smoke evidence without raw model output, response IDs, usage, or secrets.

## Safety And Stop-Lines

- Stop before live API calls, deploys, billing changes, auth changes, customer data, or
  destructive GitHub operations unless the user explicitly authorizes the bounded action.
- Do not push or publish a failing slice.
- Do not send non-public material to Grok or any other external reviewer.
- Do not revert unrelated user changes.

## Session Notes

- Update `SESSION_NOTES.md` after each verified slice and before handoff.
