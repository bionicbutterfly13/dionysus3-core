---
track_id: "044"
title: "Criticality Trigger Integration"
status: "active"
priority: "high"
owner: "ConsciousnessManager"
started_at: "2026-01-26"
---

# Track 044: Criticality Trigger Integration

## Goal
Connect the `ActiveInferenceState.uncertainty` (Shannon Entropy) to the `ConsciousnessManager` to trigger a system-wide "Criticality State" when uncertainty exceeds a defined threshold, enabling phase transitions in cognitive dynamics.

## Constraints
- **Neuro-Symbolic Alignment**: Must use `ActiveInferenceService` for entropy logic.
- **Event-Driven**: Should emit a signal (EventBus) or update state, not just log.
- **Non-Blocking**: Calculation should not stall the OODA loop significantly.

## Tasks
- [ ] **T044-01**: Inject `ActiveInferenceService` into `ConsciousnessManager`.
- [ ] **T044-02**: Implement entropy calculation step in OODA loop.
- [ ] **T044-03**: Define and implement `CriticalityThreshold` logic.
- [ ] **T044-04**: Verify with unit tests.
