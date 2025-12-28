# Tasks: DAEDALUS Coordination Pool (smolagents-backed)

**Input**: spec.md, plan.md
**Synced from**: Archon (2025-12-27)

---

## Phase 1: Foundation (P1)

- [ ] T001 Add pool constants to coordination_service.py
- [ ] T002 Add TaskType enum
- [ ] T003 Add custom exceptions (PoolFullError, QueueFullError)
- [ ] T004 Extend Task dataclass (task_type, attempt_count, failed_agent_ids)
- [ ] T005 Add assignment_latency_ms tracking
- [ ] T006 Create test directory structure

## Phase 2: US1 - Background Worker Pool (P1)

### Contract Tests (TDD)
- [ ] T007 [US1] Contract test POST/GET /agents
- [ ] T008 [US1] Contract test POST /pool/initialize

### Unit Tests (TDD)
- [ ] T009 [US1] Unit test spawn_agent pool limit
- [ ] T010 [US1] Unit test isolation check

### Implementation
- [ ] T011 [US1] Implement initialize_pool()
- [ ] T012 [US1] Add pool size limit to spawn_agent()
- [ ] T013 [US1] Add POST /pool/initialize endpoint
- [ ] T014 [US1] Update POST /agents for 503 on PoolFullError
- [ ] T015 [US1] Add initialize_pool tool
- [ ] T016 [US1] Add structured logging for pool
- [ ] T016a [US1] Implement shutdown_pool()
- [ ] T016b [US1] Add DELETE /pool endpoint
- [ ] T016c [US1] Add shutdown_pool tool

## Phase 3: US2 - Task Routing & Queueing (P1)

### Contract Tests (TDD)
- [ ] T017 [US2] Contract test POST /tasks 429
- [ ] T018 [US2] Contract test POST /agents/{id}/fail

### Unit Tests (TDD)
- [ ] T019 [US2] Unit test task queueing (auto-route on agent free)
- [ ] T020 [US2] Unit test retry logic (3 attempts with failover)
- [ ] T021 [US2] Integration test task lifecycle

### Implementation
- [ ] T022 [US2] Add queue depth check (QueueFullError at MAX_QUEUE_DEPTH)
- [ ] T023 [US2] Update submit_task for task_type
- [ ] T024 [US2] Implement handle_agent_failure() (retry with failover)
- [ ] T025 [US2] Implement _reassign_task() (exclude failed agents)
- [ ] T025a [US2] Implement preferred-agent logic (affinity + history)
- [ ] T026 [US2] Track assignment latency in complete_task
- [ ] T027 [US2] Add POST /agents/{id}/fail endpoint
- [ ] T028 [US2] Update POST /tasks for 429 on QueueFullError
- [ ] T029 [US2] Add GET /tasks/{task_id} endpoint
- [ ] T030 [US2] Update submit_coordination_task tool
- [ ] T031 [US2] Add fail_coordination_agent tool
- [ ] T032 [US2] Add structured logging for queue/retry

## Phase 4: US3 - Metrics & Health (P2)

### Contract Tests (TDD)
- [ ] T033 [US3] Contract test GET /metrics
- [ ] T034 [US3] Contract test GET /isolation-report

### Unit Tests (TDD)
- [ ] T035 [US3] Unit test metrics calculation

### Implementation
- [ ] T036 [US3] Extend metrics() method (utilization, latency, counts)
- [ ] T037 [US3] Update MetricsResponse model
- [ ] T038 [US3] Add GET /isolation-report endpoint
- [ ] T039 [US3] Add isolation_report tool
- [ ] T040 [US3] Add logging for health/metrics

## Phase 5: Graceful Degradation (P1)

- [ ] T041 Add _is_discovery_service_available() check
- [ ] T042 Implement _should_process_task() (route by type + availability)
- [ ] T043 Update _assign_task() for degradation (skip discovery when unavailable)
- [ ] T044 Unit test graceful degradation
- [ ] T045 Add logging for degradation events

## Phase 6: Integration (P1)

- [ ] T046 Add Pydantic models for new endpoints
- [ ] T047 Run all tests and verify pass
- [ ] T048 Run quickstart.md validation
- [ ] T049 Add trace_id to all log entries
- [ ] T050 [FR-006] Integrate with Spec 019 discovery/migration outputs

## Phase 7: Docs (P3)

- [ ] T051 Usage doc snippet (API + tool examples)

---

**Total**: 51 tasks | **Status**: 0 done, 51 todo
