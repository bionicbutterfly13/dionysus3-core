# Feature Specification: Fractal Metacognition

**Feature Branch**: `037-context-engineering-upgrades`
**Created**: 2025-12-30
**Status**: Draft
**Input**: Context-Engineering/06_schema_design.py (FractalSchema)

## Clarifications

### Session 2025-12-30
- Q: How should recursive thoughts be persisted in Neo4j? → A: Link by Reference (ID): Store a list of child `ThoughtSeed` UUIDs in the parent metadata/property.

## User Scenarios & Testing

### User Story 1 - Recursive Thought Encapsulation (Priority: P2)

As the Metacognition Agent, I want to create thoughts that contain other reasoning traces as "child" content, so that I can evaluate and critique entire chains of reasoning as a single object.

**Why this priority**: Enables "Level 3" consciousness (reporting on internal states) by strictly modeling the containment relationship between "thinking about X" and "X".

**Independent Test**:
- Create a "Reasoning Trace" about a topic.
- Create a "Metacognitive Critique" that *contains* that Reasoning Trace ID/content.
- Verify in Neo4j (or mock) that the relationship is strictly hierarchical/recursive.

**Acceptance Scenarios**:

1. **Given** a reasoning step produced by the Reasoning Agent, **When** the Metacognition Agent reflects on it, **Then** it produces a `ThoughtSeed` that structurally includes the target thought as a child node.
2. **Given** a recursive `ThoughtSeed`, **When** it is persisted, **Then** the containment relationship is preserved (either via JSON nesting or graph relationships).

---

## Requirements

### Functional Requirements

- **FR-001**: Update `ThoughtSeed` Pydantic model to support recursive definition (a `ThoughtSeed` can contain a list of `ThoughtSeed`s or references).
- **FR-002**: Update `MetacognitionAgent` to generate these recursive structures when critiquing reasoning.
- **FR-003**: Persistence MUST use the **Link by Reference** strategy, where child `ThoughtSeed` IDs are stored in the parent's metadata.

### Key Entities

- **ThoughtSeed**: Now defined recursively using `FractalSchema` principles.
- **FractalSchema**: A helper to validate recursive depth and structure.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Successfully persist and retrieve a 3-level deep thought structure (Meta -> Reasoning -> Observation).
- **SC-002**: Metacognition Agent can reference specific sub-parts of a reasoning chain in its critique.
