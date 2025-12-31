# Feature Specification: EFE-Driven Decision Engine

**Feature Branch**: `038-thoughtseeds-framework`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Thoughtseeds (Kavi et al.), Bayesian Inference (Context-Engineering Module 00.4)

## User Scenarios & Testing

### User Story 1 (US1) - Epistemic vs Pragmatic Triage (Priority: P1)

As an autonomous agent, I want to use Expected Free Energy (EFE) to decide whether to "Research" (Epistemic) or "Execute" (Pragmatic), so that I proactively reduce uncertainty before taking high-stakes actions.

**Why this priority**: Directly addresses the "Impulsive Hallucination" problem where agents act on incomplete or wrong info.

**Independent Test**:
- Set agent uncertainty (entropy) to > 0.8.
- Trigger decision cycle.
- Verify agent selects "Recall" or "Research" tools (Epistemic) instead of "Write" or "Execute" tools (Pragmatic).

**Acceptance Scenarios**:

1. **Given** a high-entropy state, **When** EFE is calculated, **Then** the epistemic term (information gain) dominates the utility function.
2. **Given** a low-entropy state with a clear goal, **When** EFE is calculated, **Then** the pragmatic term (goal fulfillment) dominates.

---

## Requirements

### Functional Requirements

- **FR-001**: Implement `EFEEngine` class.
- **FR-002**: Formula implementation: `EFE = H(Prediction) + D_kl(Goal || Result)`.
- **FR-003**: Integrate `Uncertainty_Boost` from Bayesian principles to increase learning rates when entropy is high.
- **FR-004**: Add `efe_score` to agent step metadata for observability.

### Key Entities

- **EFEEngine**: Calculates the energetic cost/benefit of a proposed thought.
- **Uncertainty (Entropy)**: Derived from the softmax distribution of candidate thoughtseeds.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 30% reduction in "Hallucinated Tools" by forcing epistemic checks.
- **SC-002**: Decision latency < 50ms per EFE calculation.
