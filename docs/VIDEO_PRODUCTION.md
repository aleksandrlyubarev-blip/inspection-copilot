# Video Production Runbook

Use this runbook for the final public YouTube demo. The target runtime is
**2:45–2:50**; the hard submission limit is **3:00 or less**. Record an English
voiceover, or provide an English translation. Background music alone does not
meet the voiceover requirement.

The demo must use only repository-owned synthetic fixtures. Never show an API
key, environment output, terminal history containing credentials, customer data,
raw provider output, a response ID, token usage, or the private Codex
`/feedback` identifier.

## Before recording

- Confirm the public repository and README are visible without signing in.
- Run both credential-free scenarios and the complete local quality gate.
- Open the Streamlit workspace with **Clear solder bridge** selected.
- Prepare a terminal with only the fixture and test commands visible; do not
  show environment variables.
- Disable notifications, use a readable browser zoom, and record at 1080p when
  available.
- Check the live-validation panel before writing the voiceover. Its recorded
  claim must match the canonical artifact state described below.

## Shot list and spoken content

Follow the exact timing and narration in [DEMO_SCRIPT.md](DEMO_SCRIPT.md). The
recording must visibly demonstrate:

1. The synthetic-only scope and versioned inspection contract.
2. A supported automatic `fail` with evidence, location, and SOP rule.
3. An ambiguous image becoming `needs_review` instead of a guessed verdict.
4. A separate rationale-gated human record.
5. Reproducible offline commands, tests, and the read-only live trust state.
6. Specific Codex workflow and product decisions, not a generic tooling claim.
7. GPT-5.6's bounded vision role and the deterministic policy that rechecks it.

A brief repository commit-history or Codex-interface shot is useful evidence for
item 6, but the application demo remains the center of the video.

## Required live-state narration

Show `LIVE VALIDATION · SCHEMA VERIFIED · SUCCESS · FAIL`. Say that one separately
authorized request using alias `gpt-5.6` produced an evidence-backed `fail` and a
sanitized record whose schema, fingerprints, and internal content hashes passed
the repository validator. The recorded effective model is `gpt-5.6-sol`. Do
**not** describe this as proof of origin, model accuracy, or production readiness.

If the panel reports anything else, stop recording and investigate. Do not edit,
replace, regenerate, or rerun the canonical evidence.

## Paste-ready YouTube metadata

**Title**

> Inspection Copilot | Evidence-backed visual QC with Codex + GPT-5.6

**Description**

> Inspection Copilot is a synthetic-only OpenAI Build Week project for the Work
> and Productivity track. It turns a visual inspection request and versioned SOP
> into an evidence-backed `pass`, `fail`, or `needs_review` decision, while
> keeping the automatic result, operator review, and live-validation provenance
> separate. Built with Codex and a bounded GPT-5.6 vision path.
>
> Public repository:
> https://github.com/aleksandrlyubarev-blip/inspection-copilot
>
> The included images are repository-owned synthetic workflow fixtures. This
> demo is not evidence of model accuracy or production readiness.

Recommended visibility: **Public**. Do not put the private `/feedback` identifier
in the title, description, captions, or comments.

## Final acceptance check

- [ ] Runtime is 3:00 or less, with a target of 2:45–2:50.
- [ ] YouTube visibility is Public and the link opens in a signed-out window.
- [ ] English voiceover or English translation is present and intelligible.
- [ ] The working app and both fixture outcomes are visible.
- [ ] Codex usage includes concrete workflow, decisions, or implementation
  episodes.
- [ ] GPT-5.6's integration and runtime role are explained.
- [ ] The live-state wording matches the actual canonical evidence state.
- [ ] No credential, customer data, raw response metadata, or `/feedback` ID is
  visible.
- [ ] The public repository URL is in the YouTube description.

## Official requirements checked

- [OpenAI Build Week submission FAQ](https://openai.devpost.com/details/faqs)
- [OpenAI Build Week official rules](https://openai.devpost.com/rules)
