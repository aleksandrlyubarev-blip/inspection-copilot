# Architecture

## Product boundary

Inspection Copilot is a standalone, provider-neutral workflow. The UI never
turns free-form model text directly into an operational decision.

```text
Synthetic image + versioned SOP
              │
              ▼
      InspectionRequest
              │
              ▼
     Inspector interface
        ├─ FixtureInspector (current offline demo)
        └─ GPT-5.6 Responses provider (bounded live adapter)
              │
              ▼
          Assessment
              │
              ▼
  deterministic fail-closed policy
              │
              ▼
       InspectionResult
        ├─ verdict + evidence
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
- Human review is stored separately and cannot rewrite the fixture/model record.

## Runtime modes

### Offline fixture mode

The current runnable mode loads only committed synthetic JSON/PNG files. It does
not inspect environment credentials or access the network. This mode proves the
full product flow and gives judges a reproducible setup path.

### GPT-5.6 mode

The live adapter will use the Responses API with image input and strict JSON
Schema output. The request boundary will set `model=gpt-5.6`, `store=false`, no
automatic retries, and explicit timeout/output limits. Model/API failures will
produce a sanitized `needs_review`, not a fallback automatic verdict.

## UI boundary

Streamlit renders the repository-owned image, automatic verdict, confidence,
image quality, evidence, and cited SOP rule on one screen. A human can record a
session-local decision only after entering a rationale.

## Data policy

The Build Week MVP accepts only repository-owned synthetic data. Real production
photos, customer SOPs, secrets, personal data, persistent storage, deployment,
and production auth are explicitly out of scope.
