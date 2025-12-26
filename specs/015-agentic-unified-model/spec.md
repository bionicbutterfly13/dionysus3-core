# Feature Specification: Agentic Unified Model

**Feature Branch**: `015-agentic-unified-model`  
**Created**: 2025-12-26  
**Status**: Draft  
**Input**: User description: "Build agentic unified model for all projects using smolagents. Port all pending features from Archon. All projects smolagent built. Unified source of truth for aspects with Graphiti temporal tracking. Low-confidence content to human review."

## User Scenarios & Testing

### User Story 1 - Unified Agentic Orchestration (Priority: P1)

As a system, I want all sub-projects (Engine, Marketing, KB) to be driven by specialized `smolagents`, so that I can maintain a consistent cognitive architecture across all domains.

**Why this priority**: Core requirement for system integrity and "code-first" intelligence.

**Independent Test**: Trigger tasks in each of the three pillars and verify via logs that a `smolagents.CodeAgent` handled the high-level reasoning and execution.

**Acceptance Scenarios**:

1. **Given** a marketing copy task, **When** processed, **Then** the `MarketingAgent` (CodeAgent) generates the output.
2. **Given** a knowledge mapping task, **When** processed, **Then** the `KnowledgeAgent` (CodeAgent) extract facts and updates the graph.

---

### User Story 2 - Temporal Aspect Integrity (Priority: P1)

As a cognitive system, I want a single source of truth for boardroom aspects that tracks every change over time, so that I can maintain a coherent and historically accurate inner state.

**Why this priority**: Prevents state drift and enables longitudinal therapy/growth tracking.

**Independent Test**: Add an aspect, update its role, and verify that Graphiti returns the full history of these changes with correct timestamps.

**Acceptance Scenarios**:

1. **Given** a new aspect 'Protector', **When** added, **Then** a node is created in Neo4j and an episode is recorded in Graphiti.
2. **Given** an existing aspect, **When** its role is updated, **Then** the current state reflects the change and Graphiti preserves the previous role data.

---

### User Story 3 - Human-in-the-Loop Review (Priority: P2)

As a system, I want to flag low-confidence outputs for human review, so that I don't ingest "hallucinations" or incorrect mappings into the long-term knowledge graph.

**Why this priority**: Ensures data quality and system safety during autonomous operation.

**Independent Test**: Provide ambiguous input to an agent and verify it appears in the `HumanReviewCandidate` queue with a confidence score.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement `MarketingAgent` and `KnowledgeAgent` as `smolagents.CodeAgent` subclasses.
- **FR-002**: All agents MUST use `AspectService` as the single source of truth for inner state.
- **FR-003**: `AspectService` MUST record every addition, modification, or removal of an aspect in the Graphiti temporal graph.
- **FR-004**: System MUST provide a `HumanReviewCandidate` mechanism for any agent task with confidence < 0.7.
- **FR-005**: All core cognitive loop tools MUST be accessible via the MCP bridge.

### Key Entities

- **Aspect**: Boardroom member node (Protector, Inner CEO, etc.).
- **HumanReviewCandidate**: Low-confidence output needing oversight.
- **GraphitiEpisode**: Temporal record of a state change.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of projects (Engine, Marketing, KB) utilize smolagents for reasoning.
- **SC-002**: Aspect history retrieval via Graphiti has 100% accuracy for all changes.
- **SC-003**: Human review queue captures 100% of failed JSON parsing or low-confidence extractions.