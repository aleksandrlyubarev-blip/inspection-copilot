# Session Notes

## Current goal

Finish the deadline-safe submission package on the existing Streamlit
architecture after the completed one-request GPT-5.6 smoke: preserve the
canonical evidence, keep judge-facing claims exact, record the video, prepare the
Devpost draft, and capture `/feedback`. Stop before secret access, a second API
request, merge, deploy, or final submission.

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
- A deterministic evaluation command and committed offline ledger now track
  policy matches and escalation rate without making model-accuracy claims.
- Untrusted case, model, summary, location, observation, and SOP-reference fields
  are HTML-escaped before custom Streamlit rendering.
- The provider boundary returns a validated `ProviderOutcome` instead of a bare
  assessment. Timeout, rate limit, unavailability, refusal, and invalid output
  remain distinct fail-closed reasons; raw exception details are not returned.
- Results now carry deterministic provenance: schema/prompt/policy versions,
  requested/effective model, canonical SOP SHA-256, and exact image SHA-256. The
  live provider verifies the image fingerprint before crossing the API boundary.
- A typed local ledger contract now derives content-addressed entries from only
  sanitized result metadata. Exact replays are byte-identical no-ops; ledger
  size/count are bounded and updates use same-directory atomic replacement.
- The Streamlit workspace exposes the result's sanitized provenance in a native
  JSON audit panel; it does not pass provenance fields through custom HTML.
- The `inspection-copilot-ledger` CLI atomically rebuilds a deterministic
  two-entry fixture ledger at an explicit output path. The committed artifact is
  strict-schema checked and contains no raw case IDs or assessment/evidence free
  text. Fixture orchestration is separated from generic ledger persistence.
- The strict `LiveEvidenceRecord` contract is now exercised by the single
  authorized smoke. It records only provider/result routing metadata, UTC time,
  and fingerprints; exact replay is a byte-identical no-op and different
  evidence cannot overwrite the first atomically published record.
- `InspectionExecution` now binds a single actual `ProviderOutcome` to the policy
  result derived from it. The dedicated live-smoke CLI reserves the attempt
  before provider construction, rejects occupied/broken-symlink evidence names,
  makes one provider invocation, and persists success or typed failure without
  retry. Uncertain post-boundary exceptions retain a fixed reservation marker.
- Goal 3 has a read-only fixed-path live-validation loader. Missing canonical
  evidence is `not_run`; only a strict `LiveEvidenceRecord` is `verified`; invalid,
  oversized, linked/non-regular, raced, or unreadable inputs fail closed as
  `untrusted_or_unavailable` without exposing partial data.
- The Streamlit live-validation panel renders those three trust states with no
  controls. Schema-verified success and typed failure expose only the existing
  sanitized record; the offline automatic verdict and session-local human record
  remain separate and unchanged.
- The visible label is `SCHEMA VERIFIED`: schema/content-hash consistency is not
  an origin signature. `needs_review` always uses warning severity even when the
  provider transport status is `success`.
- Goal 3 commit `d3ef1a9` passed review, was fast-forwarded into
  `agent/vertical-scaffold`, and was pushed to its existing draft PR branch.
- Judge-facing README copy now separates Codex development episodes, the tested
  GPT-5.6 runtime contract, and the verified sanitized live-validation claim. A
  deadline checklist records the frozen scope and human-only gates.
- Submission documentation commit `93e2e49` is pushed to the existing draft PR
  #1. Its body now matches the 110-test scope and both GitHub Actions quality
  checks are green.
- A clean public-remote clone of `agent/vertical-scaffold` at `93e2e49` installs
  under Python 3.11, passes the complete gate, runs both fixture scenarios, and
  renders the expected fail-closed `NOT RUN` live-evidence panel.
- `docs/DEVPOST_DRAFT.md` contains paste-ready English submission copy aligned to
  the official rules: Work and Productivity, public licensed repository, public
  YouTube demo under three minutes with audio, explicit Codex/GPT-5.6 coverage,
  and a private `/feedback` form field. No Devpost state was changed.
- The current official Build Week FAQ was rechecked on 2026-07-19. The video
  contract is a public YouTube demo of 3:00 or less with a working product,
  English voiceover or translation, concrete Codex workflow/decisions, and a
  meaningful explanation of GPT-5.6 integration and runtime behavior.
- `docs/VIDEO_PRODUCTION.md` now provides a 2:45–2:50 shot plan, recording safety
  guardrails, paste-ready YouTube metadata, acceptance checks, and the exact
  current `SCHEMA VERIFIED · SUCCESS · FAIL` narration. The matching demo script
  leaves ten seconds of deadline margin and no longer relies on generic tool
  attribution.
- The user executed the fixed-target live-smoke runner exactly once on
  2026-07-19. The canonical sanitized record reports requested model `gpt-5.6`,
  effective model `gpt-5.6-sol`, provider success, complete evidence, and final
  `fail`. No reservation marker remains, and a second request is forbidden.

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
- Evaluation gate: 4 focused tests verify deterministic and internally consistent
  metrics, schema-valid CLI output, and exact agreement between the committed
  ledger and a fresh run. The current baseline is 2/2 policy matches with one
  escalation; the 34-test full suite is green.
- UI trust-boundary gate: a malicious-markup regression test verifies escaping
  before custom HTML rendering; 6 focused UI tests and the 35-test full suite pass.
- Provider-outcome gate: 11 focused tests cover success, the real SDK schema
  boundary, timeout, rate limit, unavailability, refusal, invalid output, and
  contract validation. Ruff, strict Mypy, all 39 tests, and `pip check` pass.
- Provenance gate: the synthetic loader hashes exact image bytes, canonical SOP
  serialization is stable, the live adapter rejects a hash mismatch without an
  API call, policy rejects mismatched provenance, invalid hashes fail schema
  validation, and all 44 tests pass.
- Ledger-contract gate: 9 focused tests cover sanitization, deterministic IDs,
  duplicate no-op behavior, ordered append, tamper/duplicate rejection, size and
  count bounds, missing parents, atomic failure recovery, and strict read-back.
- UI provenance gate: 7 Streamlit AppTests pass, including structured equality
  between the audit panel and the typed `InspectionResult.provenance` record.
- Fixture-ledger gate: 12 focused tests prove deterministic build/CLI output,
  committed-evidence equality, and the ledger contract's safety properties.
- Goal final gate: installed console entry point output is byte-identical to the
  committed ledger; Ruff, formatting, strict Mypy, all 57 tests, `pip check`, and
  `git diff --check` pass. Review replaced raw case IDs with SHA-256 fingerprints
  and separated fixture CLI orchestration from provider-neutral persistence.
- Live-evidence contract gate: 18 focused tests cover the sanitized schema,
  timestamp normalization, tamper/provider-state checks, exact replay, conflict,
  identifier-only metadata, size/parent bounds, atomic publish failure cleanup,
  and strict read-back across all provider failure statuses.
- Goal 1 final gate: Ruff lint/format, strict Mypy across 19 source files, all
  75 tests, `pip check`, and `git diff --check` pass. Adversarial self-review
  tightened all model/workflow metadata to identifier-only values and expanded
  exact failure-reason coverage to every non-success provider status. No live
  request or live-evidence artifact was produced.
- Goal 2 readiness gate: 17 focused live-smoke cases plus legacy CLI routing
  prove single invocation, all typed failure states, preflight ordering,
  reservation behavior, broken-symlink rejection, sanitized output, and marker
  retention after an uncertain boundary failure. Ruff, format, strict Mypy, all
  94 tests, `pip check`, and the installed CLI dry guard pass without an API call.
  A confirmed installed-CLI run with `OPENAI_API_KEY` explicitly absent also
  exits through the sanitized construction error, removes its reservation, and
  creates neither stdout evidence nor a repository artifact.
- The degraded adversarial pre-request review found and fixed two request-budget
  bypasses: broken evidence symlinks were not treated as occupied, and a public
  output-path override could create multiple independent targets. The public CLI
  now has one fixed per-repository target. The remaining local marker is
  intentionally fail-closed rather than auto-recovered after an uncertain crash.
- Goal 3 loader slice: 7 focused tests pass for missing/decoy, valid success,
  valid typed failure, tamper, oversize, symlink/non-regular, and unreadable
  evidence. Focused Ruff and strict Mypy pass; no canonical evidence was created.
- Goal 3 UI slice: 18 focused loader/AppTests pass, including verified success,
  typed timeout routed to `needs_review`, invalid evidence suppression, and
  simultaneous independent offline/live/human records. Focused Ruff and strict
  Mypy pass.
- Goal 3 final gate: 110 tests pass with Ruff lint/format, strict Mypy, `pip
  check`, and `git diff --check`. The adversarial review found and the regression
  suite now guards file replacement/in-place mutation, canonical directory swap,
  false origin claims, green `needs_review` severity, and writer/reader path drift.
  A third review cycle found no remaining substantive contract violation. No API
  request, provider construction, canonical evidence artifact, dependency change,
  push, or PR occurred.
- Submission-documentation slice: README claims were reconciled with the actual
  evidence state, concrete Codex/GPT-5.6 usage was documented, the official model
  guidance link was corrected, and the deadline checklist was added. Markdown
  targets and the full local quality gate pass without a provider construction or
  API request.
- Fresh-clone gate: public remote HEAD `93e2e49` installed into a new Python 3.11
  virtual environment with current allowed dependencies. Both installed fixture
  commands returned the expected `fail` and `needs_review` records; Ruff,
  formatting, strict Mypy, all 110 tests, `pip check`, and `git diff --check`
  passed. A localhost browser smoke confirmed the independent offline verdict,
  `LIVE VALIDATION · NOT RUN` state, and human-review panel. The server and
  temporary clone were removed; no provider was constructed and no live evidence
  was created.
- Devpost-copy gate: current official rules and FAQ were checked against the local
  README, demo script, repository license, track, and testing path. The draft
  preserves the pending live-evidence claim and leaves the YouTube URL and private
  `/feedback` field unfilled. Ruff, formatting, strict Mypy, all 110 tests, `pip
  check`, and `git diff --check` remain green without an API request.
- Video-readiness gate: both installed offline scenarios were rehearsed and
  returned the expected evidence-backed `fail` and four-reason `needs_review`.
  A localhost browser smoke visibly confirmed the automatic `FAIL`, independent
  `LIVE VALIDATION · NOT RUN`, and separate human-review form. Ruff lint and
  format, strict Mypy, all 110 tests, `pip check`, and `git diff --check` pass.
  At that pre-smoke gate no provider was constructed and no canonical evidence
  existed; the completed live-validation gate below supersedes that state.
- Live-validation gate: the fixed-path fail-closed loader reports `verified` for
  record `121810d71ec6c927da842846edc0abbc2241180fbb805c0c4d6184cf35d8397e`.
  Its content-derived ID validates, the image and SOP fingerprints match the
  built-in synthetic case, and the file is a 703-byte regular file with no
  reservation marker. A credential-free localhost browser smoke visibly
  confirmed `LIVE VALIDATION · SCHEMA VERIFIED · SUCCESS · FAIL` alongside the
  independent offline verdict and human-review form. No second provider request
  was made during validation or documentation updates. The UI test harness now
  isolates the absent-artifact state while the main-app test guards the committed
  verified state; the suite contains 111 tests.

## Next steps

1. Preserve the canonical live evidence and do not run the provider again.
2. Record the public YouTube video, then paste the prepared English copy into a
   saved Devpost draft using the frozen documentation and three-minute script.
3. Capture the primary Codex `/feedback` ID privately. Stop before merge, deploy,
   or final Devpost submission pending explicit human approval.
