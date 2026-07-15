# Architecture

## Product boundary

Inspection Copilot is a standalone, provider-neutral workflow. The UI never
turns free-form model text directly into an operational decision.

```text
Synthetic image + versioned SOP
              │
              ▼
 InspectionRequest + image SHA-256
              │
              ▼
     Inspector interface
        ├─ FixtureInspector (current offline demo)
        └─ GPT-5.6 Responses provider (bounded live adapter)
              │
              ▼
       ProviderOutcome
        ├─ success + Assessment
        └─ typed provider failure
              │
              ▼
  deterministic fail-closed policy
              │
              ▼
       InspectionResult
        ├─ verdict + evidence
        ├─ input-bound provenance
        └─ separate human review
```

## Trust boundaries

- SOP, case context, image input, model output, and external reviews are
  untrusted data.
- Pydantic rejects unknown fields and invalid enum/range values.
- Automatic verdicts require evidence, a valid SOP reference, adequate image
  quality, consistent evidence direction, and confidence at or above the policy
  threshold.
- Any failed gate returns `needs_review`; the UI does not reinterpret the result.
- Timeout, rate limit, provider unavailability, model refusal, and invalid
  structured output are distinct provider states. The service converts each to
  a sanitized `needs_review` reason without exposing exception text.
- Human review is stored separately and cannot rewrite the fixture/model record.
- Case, model, and evidence fields are HTML-escaped before entering the small
  `unsafe_allow_html` presentation templates.
- Every result carries schema, prompt, and deterministic policy versions; the
  requested and effective model identifiers; and SHA-256 fingerprints of the
  canonical SOP and exact image bytes.
- The live adapter re-hashes the image immediately before request construction
  and stops before the API boundary if it differs from the request fingerprint.

## Runtime modes

### Offline fixture mode

The current runnable mode loads only committed synthetic JSON/PNG files. It does
not inspect environment credentials or access the network. This mode proves the
full product flow and gives judges a reproducible setup path.

### GPT-5.6 mode

The implemented adapter uses the Responses API with high-detail image input and
strict JSON Schema output. The request boundary sets `model=gpt-5.6`,
`store=false`, no automatic retries, medium reasoning effort, a 60-second
timeout, and a 2,000-token output limit. It validates local image containment,
format, and size before sending a request. Model/API/schema failures produce a
typed `ProviderOutcome`; the service produces a sanitized `needs_review`, not a
fallback automatic verdict.

The default CLI and UI do not select the adapter, and no live request is part of
the test suite. `inspection-copilot-live-smoke` requires
`--confirm-one-live-request`; the older demo live flags delegate to that same
runner. The exact serialized HTTP payload is verified through a local mock
transport.

## Result provenance

`InspectionResult.model` remains the compatibility alias for the requested
model. The nested `provenance` record distinguishes that alias from the model
reported by the provider, and binds the verdict to workflow versions and input
fingerprints. It is deterministic and contains no timestamps, response IDs,
credentials, raw images, or SOP bodies.

## Local inspection ledger

The offline ledger is a versioned JSON document containing only a case-ID
fingerprint, decision routing metadata, and `InspectionProvenance`; it does not
persist the raw case ID. Each entry ID is SHA-256 over its canonical sanitized
content. Appending the exact same result is a byte-identical no-op; tampered IDs
and duplicate entries fail validation.

Writes use a bounded same-directory temporary file, `fsync`, and atomic replace.
Reads are limited to 1 MiB and the schema permits at most 1,000 entries. The MVP
is deliberately single-writer: it has no cross-process lock, database, or claim
of concurrent update safety. Fixture construction lives in the CLI adapter, not
the provider-neutral persistence module. The CLI rebuilds the complete two-entry
offline evidence file rather than incrementally merging unknown data.

## Live validation evidence boundary

`LiveEvidenceRecord` is a separate single-smoke contract, not the deterministic
offline ledger. It stores a content-derived record ID, UTC whole-second
timestamp, SHA-256 case/SOP/image fingerprints, provider status, decision route,
requested/effective model, and schema/prompt/policy versions. Provider failures
must match their typed fail-closed review reason.

The writer is limited to 64 KiB and publishes a same-directory fsynced temporary
file through an atomic no-clobber hard link. Exact replay does not touch the
file; different existing evidence is a conflict. This prevents an accidental
second smoke or race from overwriting the first record. The contract does not
authorize an API request and no live evidence exists until the separately
approved smoke succeeds or returns a typed provider failure.

`InspectionExecution` binds the exact `ProviderOutcome` to the policy result
derived from it, so the runner cannot supply a different status while building
evidence. Before provider construction, the runner creates an atomic exclusive
reservation beside the target and rejects any occupied target name, including a
broken symbolic link. The reservation changes to a fixed
`request-may-have-started` marker immediately before the single provider call.
It is removed only after strict evidence is published. A typed provider failure
is evidence and is never retried; an unexpected post-boundary exception leaves
the marker in place and blocks another request pending explicit review.

The reservation is a local single-host guard, not a distributed lock or a claim
of automatic crash recovery. A stale marker is deliberately never cleared by
the application because the process cannot prove whether a request crossed the
network boundary; inspection and new approval are required.

The SHA-256 case fingerprint is not an anonymization guarantee. The MVP accepts
only repository-owned synthetic cases, and identifier-like metadata is restricted
to a bounded identifier alphabet rather than arbitrary free text.

## UI boundary

Streamlit renders the repository-owned image, automatic verdict, confidence,
image quality, evidence, and cited SOP rule on one screen. A human can record a
session-local decision only after entering a rationale.

## Data policy

The Build Week MVP accepts only repository-owned synthetic data. Real production
photos, customer SOPs, secrets, personal data, persistent storage, deployment,
and production auth are explicitly out of scope.
