# Feature Specification: Inner Screen (Phenomenal Workspace)

**Feature Branch**: `038-thoughtseeds-framework`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Thoughtseeds (Kavi et al.), Global Workspace Theory.

## User Scenarios & Testing

### User Story 1 (US1) - Serial Conscious Processing (Priority: P2)

As the Dionysus system, I want an explicit "Inner Screen" to project the dominant ThoughtSeed, so that I have a unified data structure for current serial conscious attention.

**Why this priority**: Replaces crude "River Metaphor" proxies with a formal phenomenal model, enabling better serial reasoning and "attentional spotlight" mechanisms.

**Independent Test**:
- Trigger OODA loop with multiple candidate ThoughtSeeds.
- Verify that only the ThoughtSeed with the lowest EFE is "projected" to the Inner Screen.
- Verify that the Inner Screen content is the primary input for the next "Decide" step.

**Acceptance Scenarios**:

1. **Given** multiple competing thoughts, **When** winner-take-all finishes, **Then** the winner is serialized to the `InnerScreen`.
2. **Given** an active `InnerScreen`, **When** observations change, **Then** the "spotlight" updates its brightness/clarity scores based on resonance.

---

## Requirements

### Functional Requirements

- **FR-001**: Implement `InnerScreen` class.
- **FR-002**: Add `attentional_spotlight` mechanism (weighting of projected content).
- **FR-003**: Implement serial serialization: only one high-level object dominates the screen at time `t`.

### Key Entities

- **Inner Screen**: The locus of conscious experience.
- **Attentional Spotlight**: The mechanism selecting screen content.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Decision coherence score > 0.9 (measured by next-step predictability).
- **SC-002**: Elimination of "Thought Overlap" errors in agent reasoning.
