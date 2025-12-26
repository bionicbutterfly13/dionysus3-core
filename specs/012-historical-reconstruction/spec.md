# Feature Specification: Historical Task Reconstruction

**Feature Branch**: `012-historical-reconstruction`  
**Created**: 2025-12-26  
**Status**: Draft  
**Input**: User description: "Mirror local Archon task history into VPS Neo4j graph."

## User Scenarios & Testing

### User Story 1 - Task History Mirroring (Priority: P1)

As a cognitive system, I want to access my complete historical task context, so that I can maintain continuity across sessions even after a local environment reset.

**Why this priority**: Crucial for long-term session persistence and longitudinal memory.

**Independent Test**: Run the reconstruction service and verify that 100+ tasks from Archon are now represented as `ArchonTask` nodes in Neo4j.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a `MaintenanceService` capable of batch-fetching tasks from Archon.
- **FR-002**: System MUST mirror `ArchonTask` nodes and link them to `ArchonProject` nodes in Neo4j.
- **FR-003**: Reconstruction MUST be idempotent (subsequent runs update existing nodes).

## Key Entities

- **ArchonTask**: Node representing a task from the local environment.
- **ArchonProject**: Node representing a project/repository association.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of historical Archon tasks are queryable in Neo4j via `semantic_recall`.
- **SC-002**: Reconstruction of 100 tasks takes less than 30 seconds.