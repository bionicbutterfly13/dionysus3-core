# Feature Specification: Autobiographical Memory (System Self-Story)

**Feature Branch**: `028-autobiographical-memory`  
**Status**: Draft  
**Input**: Port the "Autobiographical Memory" system from Dionysus 2.0 to ensure Dionysus 3 remembers its own evolution and rationale.

## Overview
Dionysus 2.0 had a rudimentary autobiographical system. In Dionysus 3, we implement a robust "Self-Story" layer in Neo4j. The system records its own "Genesis," major architectural decisions, and lessons learned from the user.

## User Scenarios & Testing

### User Story 1 - Rationale Recall (Priority: P1)
As a user, I want to ask "Why did you switch to Claude Opus for writing?", and have the agent recall the specific `DevelopmentEvent` and the `Rationale` recorded during that change.

**Independent Test**: Record a change using the `record_self_memory` tool. Query the graph for `DevelopmentEvent`. Verify the reasoning is persistent.

## Functional Requirements
- **FR-001**: Implement `DevelopmentEvent` nodes in Neo4j with properties: `Rationale`, `Impact`, `LessonsLearned`, `EventType`.
- **FR-002**: Create an `AutobiographicalAgent` (or tool) that automatically records major `spec` completions and `main.py` mutations.
- **FR-003**: Implement the "Genesis Moment" node to preserve the core purpose of the system (Dr. Mani's Crisis Handoff).

## Success Criteria
- **SC-001**: System can provide a coherent narrative of its own development.
- **SC-002**: Zero amnesia regarding major architectural pivots (e.g., PostgreSQL removal).
