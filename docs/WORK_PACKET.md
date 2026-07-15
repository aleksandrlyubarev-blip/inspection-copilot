# First Five Steps — Work Packet

## Target outcome

Create a standalone, publicly auditable Inspection Copilot project with a working
synthetic mock flow, an independent Grok red-team review, and Codex-authored fixes.

## Execution sequence

### 1. Devpost registration

- Join OpenAI Build Week under the user's Devpost account.
- Stop at login, MFA, CAPTCHA, newsletter consent, or unexpected permissions for
  direct user confirmation.
- Proof: the challenge page shows the participant state.

### 2. Empty public repository

- Create `aleksandrlyubarev-blip/inspection-copilot` as a public repository without
  generated starter files.
- Proof: GitHub reports `isPrivate=false` and `isEmpty=true` before the first commit.

### 3. Codex vertical scaffold

- Commit 1: governance, product contract, toolchain.
- Commit 2: typed contracts and fail-closed policy, test-first.
- Commit 3: deterministic end-to-end mock CLI and synthetic fixture.
- Commit 4: coherent local web experience and browser smoke.
- Proof: focused tests and the full local gate pass; commits are public.

### 4. Grok red-team review

- Send only the public README, architecture summary, and synthetic scenarios.
- Ask for prioritized findings on UX, unsupported claims, edge cases, demo clarity,
  and voiceover.
- Save the response as untrusted review input with no secrets or private data.

### 5. Codex remediation

- Triage each finding as accept, defer, or reject with rationale.
- For accepted behavior findings, write a failing test first and implement the fix
  independently in Codex.
- Proof: review ledger, regression tests, green full gate, and public commits.

## External approval boundaries

- User login is required for Devpost and Grok if no authenticated session exists.
- GitHub public repository creation is authorized by the current request.
- Live GPT-5.6 calls, deploys, and final Devpost submission are separate gates.
