# Tasks: Coordination Pool

**Input**: Design documents from `/specs/020-coordination-pool/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/coordination-api.yaml

**Tests**: Included per Constitution Principle II (Test-Driven Development).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project structure**: `api/` for source, `tests/` for tests (per plan.md)
- Enhancing existing files where noted

---

## Phase 1: Setup

**Purpose**: Verify existing infrastructure and add missing constants

- [X] T001 Add pool constants (DEFAULT_POOL_SIZE=4, MAX_POOL_SIZE=16, MAX_QUEUE_DEPTH=100, MAX_RETRIES=3) to api/services/coordination_service.py
- [X] T002 [P] Add TaskType enum (DISCOVERY, MIGRATION, HEARTBEAT, INGEST, RESEARCH, GENERAL) to api/services/coordination_service.py
- [X] T003 [P] Add custom exceptions (PoolFullError, QueueFullError) to api/services/coordination_service.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend Task dataclass with required fields before user story implementation

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Extend Task dataclass with task_type, attempt_count, failed_agent_ids fields in api/services/coordination_service.py
- [X] T005 Add assignment_latency_ms tracking to Task dataclass in api/services/coordination_service.py
- [X] T006 Create test directory structure: tests/unit/, tests/integration/, tests/contract/ if not exists

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Background Worker Pool (Priority: P1) MVP

**Goal**: Pool of background smolagents with isolated context windows, supporting concurrent jobs without cross-talk

**Independent Test**: Spawn N agents, assign tasks; verify queued tasks are picked up when an agent frees and each task logs agent assignment

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Contract test for POST /agents (spawn) and GET /agents (list) in tests/contract/test_coordination_api.py
- [X] T008 [P] [US1] Contract test for POST /pool/initialize in tests/contract/test_coordination_api.py
- [X] T009 [P] [US1] Unit test for spawn_agent with pool size limit enforcement in tests/unit/test_coordination_service.py
- [X] T010 [P] [US1] Unit test for isolation check between concurrent agents in tests/unit/test_coordination_service.py

### Implementation for User Story 1

- [X] T011 [US1] Implement initialize_pool(size: int) method in api/services/coordination_service.py
- [X] T012 [US1] Add pool size limit check to spawn_agent() - raise PoolFullError when at MAX_POOL_SIZE in api/services/coordination_service.py
- [X] T013 [US1] Add POST /pool/initialize endpoint in api/routers/coordination.py
- [X] T014 [US1] Update POST /agents to return 429 on PoolFullError in api/routers/coordination.py
- [X] T015 [P] [US1] Add initialize_pool smolagent tool in api/agents/tools/coordination_tools.py
- [X] T016 [US1] Add structured logging for pool initialization and agent spawn events in api/services/coordination_service.py
- [X] T016a [US1] Implement shutdown_pool() method in api/services/coordination_service.py (clears agents, tasks, and queue)
- [X] T016b [US1] Add DELETE /pool endpoint for graceful shutdown in api/routers/coordination.py
- [X] T016c [P] [US1] Add shutdown_coordination_pool smolagent tool in api/agents/tools/coordination_tools.py

**Checkpoint**: Pool initialization and agent spawning with isolation works independently

---

## Phase 4: User Story 2 - Task Routing & Queueing (Priority: P1)

**Goal**: Tasks queue when no agent is free and auto-route when capacity opens; no work dropped

**Independent Test**: Fill the pool, submit an extra task, then free one agent; verify the queued task starts automatically

### Tests for User Story 2

- [X] T017 [P] [US2] Contract test for POST /tasks with queue overflow (429) in tests/contract/test_coordination_api.py
- [X] T018 [P] [US2] Contract test for POST /agents/{agent_id}/fail in tests/contract/test_coordination_api.py
- [X] T019 [P] [US2] Unit test for task queueing and auto-routing on agent free in tests/unit/test_coordination_service.py
- [X] T020 [P] [US2] Unit test for retry logic (3 attempts, failover to different agent) in tests/unit/test_coordination_service.py
- [X] T021 [P] [US2] Integration test for full task lifecycle (submit → queue → assign → complete) in tests/integration/test_coordination_pool.py

### Implementation for User Story 2

- [X] T022 [US2] Add queue depth check to submit_task() - raise QueueFullError when at MAX_QUEUE_DEPTH in api/services/coordination_service.py
- [X] T023 [US2] Update submit_task() to accept and store task_type in api/services/coordination_service.py
- [X] T024 [US2] Implement handle_agent_failure(agent_id) method with retry logic in api/services/coordination_service.py
- [X] T025 [US2] Implement _reassign_task() method excluding previously failed agents in api/services/coordination_service.py
- [X] T025a [US2] Implement preferred-agent logic in _assign_task() using task_type affinity and performance history
- [X] T026 [US2] Update complete_task() to track assignment latency in api/services/coordination_service.py
- [X] T027 [US2] Add POST /agents/{agent_id}/fail endpoint in api/routers/coordination.py
- [X] T028 [US2] Update POST /tasks to return 429 on QueueFullError in api/routers/coordination.py
- [X] T029 [US2] Add GET /tasks/{task_id} endpoint in api/routers/coordination.py
- [X] T030 [P] [US2] Update submit_coordination_task tool to accept task_type in api/agents/tools/coordination_tools.py
- [X] T031 [P] [US2] Add fail_coordination_agent tool in api/agents/tools/coordination_tools.py
- [X] T032 [US2] Add structured logging for queue events, retry attempts, and task lifecycle in api/services/coordination_service.py

**Checkpoint**: Task queueing, routing, and retry logic works independently

---

## Phase 5: User Story 3 - Coordination Metrics & Health (Priority: P2)

**Goal**: Coordination metrics (tasks completed/failed, utilization, latency) and agent health for debugging and scaling

**Independent Test**: Call /api/coordination/metrics and observe non-zero counts; agent health shows context isolation status

### Tests for User Story 3

- [X] T033 [P] [US3] Contract test for GET /metrics with all required fields in tests/contract/test_coordination_api.py
- [X] T034 [P] [US3] Contract test for GET /isolation-report in tests/contract/test_coordination_api.py
- [X] T035 [P] [US3] Unit test for metrics calculation (utilization, latency avg) in tests/unit/test_coordination_service.py

### Implementation for User Story 3

- [X] T036 [US3] Extend metrics() to include tasks_pending, tasks_completed, tasks_failed, avg_assignment_latency_ms, utilization in api/services/coordination_service.py
- [X] T037 [US3] Update MetricsResponse Pydantic model with new fields in api/routers/coordination.py
- [X] T038 [US3] Add GET /isolation-report endpoint in api/routers/coordination.py
- [X] T039 [P] [US3] Add isolation_report smolagent tool in api/agents/tools/coordination_tools.py
- [X] T040 [US3] Add structured logging for health check and metrics queries in api/services/coordination_service.py

**Checkpoint**: Metrics and health reporting works independently

---

## Phase 6: Graceful Degradation (Cross-Cutting for EH-003)

**Purpose**: Handle Spec 019 discovery service unavailability

- [X] T041 Add _is_discovery_service_available() check method in api/services/coordination_service.py
- [X] T042 Implement _should_process_task() routing based on task_type and discovery availability in api/services/coordination_service.py
- [X] T043 Update _assign_task() to skip discovery/migration tasks when service unavailable in api/services/coordination_service.py
- [X] T044 Unit test for graceful degradation (discovery tasks queue, others process) in tests/unit/test_coordination_service.py
- [X] T045 Add structured logging for degradation events in api/services/coordination_service.py

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Add Pydantic request/response models for new endpoints in api/routers/coordination.py
- [X] T047 Run all tests and verify pass in tests/
- [X] T048 Run quickstart.md validation against running API
- [X] T049 Add trace_id to all structured log entries in api/services/coordination_service.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 priority; US2 builds on US1 concepts but tests independently
  - US3 (P2) can proceed in parallel with US1/US2
- **Graceful Degradation (Phase 6)**: Depends on US2 (task routing infrastructure)
- **Polish (Phase 7)**: Depends on all user stories and degradation being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Extends US1 patterns but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent of US1/US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Service methods before API endpoints
- Core implementation before smolagent tools
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003 can run in parallel (different additions to same file, no conflict)
- T007, T008, T009, T010 can run in parallel (test files)
- T017, T018, T019, T020, T021 can run in parallel (test files)
- T033, T034, T035 can run in parallel (test files)
- T015 can run in parallel with T011-T014 (different file)
- T030, T031 can run in parallel with T022-T029 (different file)
- T039 can run in parallel with T036-T038 (different file)

---

## Parallel Example: User Story 2 Tests

```bash
# Launch all tests for User Story 2 together:
Task: "Contract test for POST /tasks with queue overflow (429) in tests/contract/test_coordination_api.py"
Task: "Contract test for POST /agents/{agent_id}/fail in tests/contract/test_coordination_api.py"
Task: "Unit test for task queueing and auto-routing on agent free in tests/unit/test_coordination_service.py"
Task: "Unit test for retry logic (3 attempts, failover to different agent) in tests/unit/test_coordination_service.py"
Task: "Integration test for full task lifecycle in tests/integration/test_coordination_pool.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: User Story 1 (T007-T016)
4. **STOP and VALIDATE**: Test pool initialization and agent spawning independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Pool works (MVP!)
3. Add User Story 2 → Test independently → Queueing and retry works
4. Add User Story 3 → Test independently → Metrics available
5. Add Graceful Degradation → Full resilience
6. Polish → Production ready

### Single Developer Strategy

Execute in phase order:
1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing files (coordination_service.py, coordination.py, coordination_tools.py) are being enhanced, not replaced
