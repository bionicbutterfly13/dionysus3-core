# Feature Specification: Project-Wide Distillation & Wisdom Extraction

**Feature Branch**: `031-wisdom-distillation`  
**Created**: 2025-12-27  
**Status**: Draft  
**Input**: Full archive of 709 conversations and orphaned folders (014-028). Goal: Extract core system wisdom and unify all codebases into a distilled Neo4j-native structure.

## User Scenarios & Testing

### User Story 1 - Archive Wisdom Extraction (Priority: P1)
As the system, I want to analyze the full conversation history in batches, so I can identify recurring principles, successful OODA patterns, and project-specific "Mental Models" to be persisted in Neo4j.

**Independent Test**: Process 50 conversations; verify that ≥5 new `WisdomInsight` nodes are created in Neo4j with correct attribution to the original session IDs.

### User Story 2 - Orphaned Folder Cleanup (Priority: P1)
As a maintainer, I want "Explorer Agents" to review the task lists and specs in folders 014-028, so that outdated or redundant elements are merged into the new Feature 030 architecture or deleted.

**Independent Test**: Run discovery on folder 014; verify that it produces a "Distillation Plan" recommended by the explorer tool.

## Requirements

### Functional Requirements
- **FR-031-001**: Deploy a fleet of parallel `ArchiveAnalysts` via the DAEDALUS pool.
- **FR-031-002**: Analysts MUST use the `/research.agent` protocol from Context-Engineering to extract structured "Neuronal Packets" from conversations.
- **FR-031-003**: Implement a `WisdomConsolidator` that merges overlapping insights into unified `KnowledgeDomain` nodes in Neo4j.
- **FR-031-004**: Each extraction MUST preserve "Provenance" (Session ID, Date, Agent Type).
- **FR-031-005**: Explorer agents MUST identify "Redundancies" between Spec 014-028 and the active Dionysus 3 engine.

### Non-Functional Requirements
- **NFR-031-001**: Fleet processing MUST prevent "Context Pollution" by using isolated `tool_session_ids` for each batch.
- **NFR-031-002**: extraction latency per batch (10md files) MUST be < 2 minutes.

## Success Criteria

### Measurable Outcomes
- **SC-031-001**: 709 conversations processed and distilled into ≤ 50 core `NeuronalPacket` attractors in Neo4j.
- **SC-031-002**: 100% of orphaned folders (014-028) reviewed and either merged or archived.
- **SC-031-003**: System "Surprise" levels decrease by 20% in subsequent OODA cycles due to improved grounding.
