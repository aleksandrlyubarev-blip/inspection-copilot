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

## Sanitized inspection ledger

`evidence/offline_inspection_ledger.json` binds a SHA-256 case fingerprint for
each fixture route to its SOP and image fingerprints plus schema, prompt, policy,
requested-model, and effective-model versions. Rebuild it deterministically with:

```bash
inspection-copilot-ledger \
  --repo-root . \
  --output evidence/offline_inspection_ledger.json
```

The test suite reads the committed file through the strict ledger schema and
requires exact equality with a fresh in-memory fixture build. This is audit and
workflow evidence, not model-accuracy evidence.

## Live evidence boundary

Every inspection result now carries sanitized deterministic provenance: model,
prompt/policy/schema versions, and SOP/image hashes. The prepared
`LiveEvidenceRecord` adds provider status, decision routing, a SHA-256 case
fingerprint, and a timezone-aware timestamp normalized to UTC whole seconds.

The separately authorized `inspection-copilot-live-smoke` runner may create
exactly one sanitized `evidence/live_validation_evidence.json`. It reserves the
attempt before provider construction, calls the provider once, and will not
overwrite an occupied target or retry after auth, rate-limit, timeout, refusal,
or schema failure. An uncertain post-request exception retains a fixed marker
instead of silently permitting another attempt. The record must not store the
raw case ID, image, SOP body, free-form response/assessment, response ID, usage
details, or credentials. One live result validates only the integration
boundary; it does not establish manufacturing accuracy.
