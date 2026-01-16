# Feature Specification: Thoughtseeds Framework Enhancement

**Track ID**: 038-thoughtseeds-framework
**Created**: 2025-12-30
**Status**: In Progress
**Input**: Thoughtseeds (Kavi et al., 2025), Bayesian Inference (Context-Engineering), smolagents architecture.
**Terminology**: See [docs/TERMINOLOGY.md](../../../docs/TERMINOLOGY.md) - this spec uses "trajectory" to mean STATE-SPACE paths (theoretical), not execution traces (operational)

## Clarifications

### Session 2025-12-30
- Q: How should Markov Blankets be persisted in Neo4j to enforce context isolation? → A: Graph Relationships: Model sensory/active surfaces as typed edges to specific environmental or action nodes.
- Q: What is the format for constraints passed between layers in the Prior Hierarchy? → A: Probability Values (0-1): Each layer provides a "Precision" weight that scales the surprise level of layers below.
- Q: Should the Inner Screen state be persistent or transient? → A: Transient with Logging: Screen state is real-time, but every dominant thought projection is logged to Neo4j as an EpisodicMemory node.

## Overview
This feature implements missing components from the Thoughtseeds paper to enhance neuronal packets, active inference, and salient cognition models. It introduces an EFE-driven decision engine, hierarchical evolutionary priors, Markov blanket isolation, and an explicit Inner Screen for conscious serial attention.

## User Scenarios & Testing

### User Story 1 (US1) - Epistemic vs Pragmatic Triage (Priority: P1)
As an autonomous agent, I want to use Expected Free Energy (EFE) to decide whether to "Research" (Epistemic) or "Execute" (Pragmatic), so that I proactively reduce uncertainty before taking high-stakes actions.

### User Story 2 (US2) - Context Isolation via Markov Blankets (Priority: P1)
As the Dionysus system, I want every ThoughtSeed to have a "Markov Blanket" (Sensory and Active states), so that I can isolate internal reasoning from external context bleed and maintain computational autonomy.

### User Story 3 (US3) - Grounded Decision Making via Priors (Priority: P1)
As the Dionysus system, I want my decisions to be constrained by a hierarchy of "Priors" (Basal, Dispositional, Learned), so that I don't "drift" into behaviors that conflict with my core identity or project goals.

### User Story 4 (US4) - Serial Conscious Processing via Inner Screen (Priority: P2)
As the Dionysus system, I want an explicit "Inner Screen" to project the dominant ThoughtSeed, so that I have a unified data structure for current serial conscious attention.

### User Story 5 (US5) - Full Cognitive Loop Integration (Priority: P1)
As the Dionysus system, I want all Thoughtseed components (EFE, Blankets, Priors, Screen) to work together in a single OODA cycle, so that I have a unified biologically-grounded cognitive process.

**Acceptance Scenarios**:
1. **Given** a new observation, **When** processed through the full loop, **Then** the system isolates context via Markov Blankets, checks against the Prior Hierarchy, calculates EFE for candidate plans, and projects the winner to the Inner Screen.

## Requirements

### Functional Requirements
- **FR-001**: Implement `EFEEngine` class. Formula: `EFE = H(Prediction) + D_kl(Goal || Result)`.
- **FR-002**: Define `MarkovBlanket` structure. Boundary enforcement MUST use native Neo4j edges: `[:SENSORY]` for inputs and `[:ACTIVE]` for outputs.
- **FR-003**: Implement `PriorHierarchy` class with levels: `BASAL`, `DISPOSITIONAL`, `LEARNED`. Reciprocal message passing MUST use continuous probability values (0-1) to scale "Precision" weights across layers.
- **FR-004**: Implement `InnerScreen` class with `attentional_spotlight` mechanism. Projections to the screen MUST be logged to Neo4j as `EpisodicMemory` nodes to preserve the stream of consciousness.
- **FR-005**: Integrate EFE winner-take-all dynamics to select the dominant ThoughtSeed for screen projection.

### Non-Functional Requirements
- **NFR-001**: EFE calculations MUST complete in <50ms per thoughtseed.
- **NFR-002**: Prior hierarchy checks MUST be non-bypassable by the `Decide` phase.

## Success Criteria
- **SC-001**: 30% reduction in agent hallucinations due to EFE-driven curiosity.
- **SC-002**: 50% reduction in "Context Noise" observed in agent traces via blanket isolation.
- **SC-003**: 0 "Core Value Violations" in agent trajectory audits via Basal Priors.
