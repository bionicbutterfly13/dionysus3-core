# Feature Specification: Nested Markov Blankets

**Feature Branch**: `038-thoughtseeds-framework`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Thoughtseeds (Kavi et al.), active inference principles.

## User Scenarios & Testing

### User Story 1 (US1) - Context Isolation (Priority: P1)

As the Dionysus system, I want every ThoughtSeed to have a "Markov Blanket" (Sensory and Active states), so that I can isolate internal reasoning from external context bleed and maintain computational autonomy.

**Why this priority**: Prevents "Cognitive Flooding" where too much irrelevant graph context degrades reasoning performance.

**Independent Test**:
- Create two unrelated ThoughtSeeds.
- Verify that changes in the internal state of ThoughtSeed A do not affect ThoughtSeed B unless they pass through the "Active" boundary of the blanket.

**Acceptance Scenarios**:

1. **Given** a ThoughtSeed, **When** it receives input, **Then** only states defined in the "Sensory" part of the blanket are accessible to its internal model.
2. **Given** a reasoning outcome, **When** it is projected to the system, **Then** it must pass through the "Active" part of the blanket.

---

## Requirements

### Functional Requirements

- **FR-001**: Define `MarkovBlanket` data structure with `sensory`, `active`, and `internal` partitions.
- **FR-002**: Implement conditional independence logic: Internal states are independent of External states given the blanket.
- **FR-003**: Enforce strict mapping of input data to `sensory` states in `ThoughtSeed`.

### Key Entities

- **Markov Blanket**: The boundary separating internal agency from the environment.
- **Sensory States**: The input surface.
- **Active States**: The output surface.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 50% reduction in "Context Noise" observed in agent traces.
- **SC-002**: 100% of ThoughtSeeds possess a formal blanket structure.
