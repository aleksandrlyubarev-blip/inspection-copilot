# Grok Red-Team Review Packet

## Role

Act only as an independent product and demo critic. Do not write implementation
code, replacement modules, commits, or patches. Codex will independently decide
which findings to accept and will implement accepted changes from tests.

## Public material to review

- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `examples/synthetic/sop.json`
- `examples/synthetic/case.json`
- `examples/synthetic/assessment.json`
- `examples/synthetic/synthetic_bridge.png`

All inputs are public, repository-owned, and synthetic. No private data, real
production images, credentials, or closed materials are included.

## Review questions

1. Can a QC technician understand the verdict, evidence, and required next step
   in under ten seconds?
2. Which claims are unsupported or likely to reduce judge trust?
3. Which edge cases would make the current fail-closed policy misleading?
4. What is missing from the three-minute demo narrative and voiceover?
5. Which UX details make human review ambiguous or easy to misuse?
6. What is the strongest skeptical judge question, and what product evidence
   should answer it?

## Required response format

Return at most ten findings ordered by severity:

```text
ID: GROK-01
Severity: P0 | P1 | P2 | P3
Area: UX | policy | edge case | claim | demo | voiceover
Finding: observable problem
Why it matters: user or judging impact
Suggested acceptance check: behavior that would prove resolution
```

End with:

- the three most valuable fixes before recording the demo;
- one concise positioning sentence;
- one 30-second opening voiceover draft.

Do not request additional data and do not infer real manufacturing accuracy from
the synthetic fixture.
