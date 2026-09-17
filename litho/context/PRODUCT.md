# Inspection Copilot — product canon

Human-maintained authority for documentation. Preserve these boundaries; cite code for implementation claims.
If code and intent differ, document the gap instead of inventing implementation.

## Product thesis
We do not build a humanoid body. We put an evidence-backed inspection brain (SOP + visual agents + CAD bridge) onto a purchased mobile/manipulator platform for EMS / SMT incoming QC.

## Container contract
Repository: aleksandrlyubarev-blip/inspection-copilot
System role: evidence-backed SOP inspection and fail-closed policy.
Actor: manufacturing quality inspector and human reviewer.
Input: inspection request with image SHA-256, a versioned SOP and a provider assessment.
Output: InspectionResult with pass, fail or needs_review, evidence, review reasons and provenance.
Implemented: src/inspection_copilot/policy.py applies deterministic evidence and SOP-reference gates.
Fail-closed invariant: no evidence -> needs_review; poor images, uncertainty and invalid references also require review.
Provider failures and invalid model output must not become automatic PASS decisions.
Implemented: src/inspection_copilot/domain.py declares the actual Decision enum.
Implemented: src/inspection_copilot/ledger.py and live_evidence.py implement bounded provenance/evidence records.
Image/SOP hashes and record fingerprints support integrity checks; hashes do not prove accuracy or origin.
Synthetic fixtures demonstrate workflow behavior, not factory accuracy or escape-rate reduction.
System mapping is proposed: pass -> PASS; needs_review -> HUMAN REVIEW; fail -> HOLD pending human disposition.
A fail is not automatically REWORK; that requires an authorized rework decision.
Not demonstrated: an end-to-end hardware adapter, production integration with all siblings or one shared audit store.

## System flow
Camera (External) -> FlexVision Checker capture/frame QA -> Romeo task routing -> Neuron Vision observations -> Inspection Copilot SOP/evidence policy -> human review/disposition -> PASS | REWORK | HOLD | HUMAN REVIEW; Buxter optionally proposes validated CAD/rework geometry.
Romeo owns orchestration and HITL; Neuron Vision owns five visual roles; Copilot owns the deterministic SOP gate.
Buxter defaults to FreeCAD, with optional Fusion and explicit validate/printability checks.
This flow is the target integration; the five repositories do not yet prove one connected deployment.
Target: verdict plus SHA-256 evidence pack including provenance and human disposition.

## External boundary
Purchased mobile base + manipulator + camera: External hardware, not our IP.
Flex line, Technion lab and Israel Physical AI testbed: External target environments, not asserted deployments.
Robot platform drivers and the unified hardware integration are not implemented by this documentation scaffold.

## Source snapshot
Initial audit: 428002eecad248a4e1879639b53ba46f75f76699 (2026-09-17).
Regeneration must cite the checkout being analyzed and distinguish new code from this initial audit.
Only public source code and synthetic examples may enter documentation generation.
