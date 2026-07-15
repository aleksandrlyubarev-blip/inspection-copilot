# Evaluation Ledger

## What this baseline proves

The offline baseline is a deterministic workflow regression check over two
repository-owned synthetic cases. It proves that the typed provider boundary and
fail-closed policy produce the expected operational routes:

| Scenario | Expected | Actual | Route |
|---|---|---|---|
| Clear solder bridge | `fail` | `fail` | automatic |
| Degraded image | `needs_review` | `needs_review` | human escalation |

Current result: 2/2 policy matches, one automatic case, and one escalated case.

This is **not model-accuracy evidence**. The fixture provider returns committed
assessments so the policy and presentation layers can be tested without network
access, API credentials, nondeterminism, or cost.

## Reproduce it

```bash
inspection-copilot-eval --repo-root .
```

The command emits a strict JSON report. The committed
`evidence/offline_evaluation.json` is checked against a fresh run in the test
suite, so stale baseline numbers fail CI.

## Live evidence boundary

A later, separately authorized live smoke may record only sanitized evidence:
model, case hash, structured decision, policy outcome, and a timezone-aware
timestamp. It must not store the raw image, SOP body, free-form response,
response ID, usage details, or credentials. One live result will validate the
integration boundary; it will still not establish manufacturing accuracy.
