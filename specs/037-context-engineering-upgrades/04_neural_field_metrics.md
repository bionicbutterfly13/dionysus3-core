# Feature Specification: Neural Field Metrics

**Feature Branch**: `037-context-engineering-upgrades`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Context-Engineering/context-schemas/context_v7.0.json

## Clarifications

### Session 2025-12-30
- Q: Should the compression formula be inverted to match the test case expectation (concise summary = high score)? → A: Invert Formula: Define Compression as `tokens_in / tokens_out` (Ratio > 1 means compression).

## User Scenarios & Testing

### User Story 1 - Flow Efficiency Monitoring (Priority: P2)

As the Context Stream Service, I want to measure the "compression" and "resonance" of the system's processing, so that I can detect when the agents are "spinning" (low compression) or "hallucinating" (low resonance).

**Why this priority**: Efficiency. Allows the system to auto-throttle or sleep when it's just generating noise, saving energy and API costs.

**Independent Test**:
- Feed the service a verbose, repetitive text -> Expect low compression score.
- Feed the service a concise summary of the same text -> Expect high compression score (Ratio > 1.0).
- Feed the service a text unrelated to current goals -> Expect low resonance score.

**Acceptance Scenarios**:

1. **Given** a stream of agent outputs, **When** processed by `ContextStreamService`, **Then** it calculates `compression` (tokens_in / tokens_out) and `resonance` (embedding similarity to active goal).
2. **Given** high "drift" (low resonance/compression), **When** detected, **Then** the service flags the `FlowState` as `STAGNANT` or `DRIFTING`.

---

## Requirements

### Functional Requirements

- **FR-001**: Update `ContextStreamService` to calculate `compression_ratio` as `tokens_in / tokens_out`.
- **FR-002**: Update `ContextStreamService` to calculate `resonance` using `sentence-transformers` (already available) to compare Action output vs Goal description.
- **FR-003**: Update `FlowState` enum and logic to include these new metrics.

### Key Entities

- **ContextStreamService**: The analyzer of information flow.
- **FlowState**: The categorization of the current cognitive process (Flowing, Turbulent, Stagnant, etc.).

## Success Criteria

### Measurable Outcomes

- **SC-001**: `ContextFlow` objects contain valid `compression` and `resonance` float values.
- **SC-002**: System correctly identifies a "spinning" loop (high input, high output, low info gain) as `STAGNANT` or `TURBULENT`.
