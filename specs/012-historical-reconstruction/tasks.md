# Tasks: Historical Task Reconstruction

**Input**: Design documents from `/specs/012-historical-reconstruction/`
**Prerequisites**: spec.md (required)

## Phase 1: Foundational (Blocking Prerequisites)

- [ ] T001 Implement `fetch_all_historical_tasks` in `ArchonIntegrationService`
- [ ] T002 Implement `reconstruct_task_history` in `ReconstructionService`

---

## Phase 2: User Story 1 - Task History Mirroring (Priority: P1) 🎯 MVP

**Goal**: Full mirroring of Archon history to Neo4j.

- [ ] T003 Implement idempotent UNWIND Cypher query for batch task merging
- [ ] T004 Link tasks to project nodes via `BELONGS_TO` relationships
- [ ] T005 Create `POST /api/maintenance/reconstruct-tasks` endpoint

---

## Phase 3: Polish

- [ ] T006 Add detailed logging for reconstruction progress
- [ ] T007 Implement a 'dry-run' mode for reconstruction verification