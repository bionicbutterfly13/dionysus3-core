# Tasks: Critical D3 Bug Fixes

**Input**: Design documents from `/specs/064-critical-d3-fixes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md

**Tests**: No additional tests requested - verification via existing tests and grep commands.

**Organization**: Tasks grouped by bug fix (user story). Each fix is independent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify current state before changes

- [x] T001 Verify branch is 064-critical-d3-fixes: `git branch --show-current`
- [ ] T002 Run existing tests to establish baseline: `python -m pytest tests/ -v --tb=short`

---

## Phase 2: Foundational

**Purpose**: No foundational work needed - all fixes are independent

**⚠️ Note**: This feature has no shared foundational tasks. Each user story (bug fix) is independent.

**Checkpoint**: Baseline established - bug fixes can proceed in parallel

---

## Phase 3: User Story 1 - Fix Undefined Variables (Priority: P1) ✅ COMPLETED

**Goal**: Fix undefined variables `memory_record` and `s` in ObserveHandler

**Independent Test**: `ObserveHandler.execute()` returns valid `ActionResult` without `NameError`

**Status**: COMPLETED

### Implementation for User Story 1

- [x] T003 [US1] Replace `memory_record["recent_count"]` with `recent_memories_count` in api/services/action_executor.py:136
- [x] T004 [US1] Replace `s.get("current_energy", 10.0)` with `current_energy` in api/services/action_executor.py:140
- [x] T005 [US1] Replace `s.get("heartbeat_count", 0)` with `heartbeat_count` in api/services/action_executor.py:141

**Checkpoint**: User Story 1 complete - ObserveHandler no longer crashes

---

## Phase 4: User Story 2 - Remove Duplicate Endpoint (Priority: P1) ✅ COMPLETED

**Goal**: Remove duplicate `/api/monitoring/cognitive` endpoint that overwrites trace_id support

**Independent Test**: OpenAPI spec shows single `/cognitive` endpoint; trace_id appears in response

**Status**: COMPLETED

### Implementation for User Story 2

- [x] T006 [US2] Delete duplicate endpoint definition (lines 60-72) in api/routers/monitoring.py
- [x] T007 [US2] Verify single endpoint remains with trace_id support in api/routers/monitoring.py:45-58

**Checkpoint**: User Story 2 complete - monitoring endpoint has trace_id support

---

## Phase 5: User Story 3 - Replace Direct Neo4j Access (Priority: P1) ✅ COMPLETED

**Goal**: Replace direct Neo4j Cypher queries with Graphiti service in IAS router

**Independent Test**: `grep -r "_driver.execute_query" api/routers/ias.py` returns zero matches

**Status**: COMPLETED

### Implementation for User Story 3

- [x] T008 [US3] Add Graphiti service import to api/routers/ias.py
- [x] T009 [US3] Rewrite `update_persistent_session()` function to use Graphiti in api/routers/ias.py:142-162
- [x] T010 [US3] Remove raw Cypher query construction in api/routers/ias.py
- [x] T011 [US3] Add error handling for Graphiti service unavailability in api/routers/ias.py

**Checkpoint**: User Story 3 complete - IAS uses Graphiti, no direct Neo4j access

---

## Phase 6: Verification & Polish

**Purpose**: Verify all fixes work together

- [ ] T012 Run full test suite: `python -m pytest tests/ -v`
- [ ] T013 Start API server and verify no errors: `uvicorn api.main:app --reload`
- [ ] T014 Verify OpenAPI spec at `/docs` shows single `/cognitive` endpoint
- [x] T015 Verify no direct Neo4j access in ias.py: `grep -r "_driver.execute_query" api/routers/ias.py`
- [x] T016 Verify no Neo4j imports in routers: `grep -r "from neo4j import" api/routers/`
- [ ] T017 Update spec.md to mark all user stories COMPLETED

**Note**: `kg_learning.py` has `_driver.execute_query` but is OUT OF SCOPE per spec.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - establish baseline
- **Foundational (Phase 2)**: N/A - no shared infrastructure
- **User Stories (Phases 3-5)**: All independent - can run in parallel
- **Verification (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: ✅ COMPLETED - no dependencies
- **User Story 2 (P1)**: ✅ COMPLETED - different file (monitoring.py)
- **User Story 3 (P1)**: ✅ COMPLETED - different file (ias.py)

### Parallel Opportunities

All three bug fixes can be done in parallel since they touch different files:
- US1: api/services/action_executor.py ✅ COMPLETED
- US2: api/routers/monitoring.py ✅ COMPLETED
- US3: api/routers/ias.py ✅ COMPLETED

---

## Implementation Strategy

### Current State

1. ✅ Phase 1: Setup (branch verified)
2. ✅ Phase 2: N/A
3. ✅ Phase 3: User Story 1 COMPLETED
4. ✅ Phase 4: User Story 2 COMPLETED
5. ✅ Phase 5: User Story 3 COMPLETED
6. ⏳ Phase 6: Verification in progress

### Remaining Work

1. ✅ Complete User Story 2 (monitoring.py) - DONE
2. ✅ Complete User Story 3 (ias.py) - DONE
3. ⏳ Run verification - 3 tasks remaining (T012, T013, T014, T017)

---

## Notes

- All user stories completed
- T015, T016 verification passed
- `kg_learning.py` has similar Neo4j access but is out of scope
- Remaining: Test suite, server startup, OpenAPI verification, spec update
