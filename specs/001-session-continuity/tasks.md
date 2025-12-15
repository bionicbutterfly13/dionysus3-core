# Tasks: Session Continuity

**Input**: Design documents from `/specs/001-session-continuity/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/mcp-tools.md

**Tests**: Included per Constitution Principle II (Test-Driven Development)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **API**: `api/` for FastAPI routers, services, models
- **MCP**: `mcp/` for MCP server tools
- **Tests**: `tests/` for all test types

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database schema

- [ ] T001 Create database migration file for journeys, sessions, journey_documents tables in migrations/001_session_continuity.sql
- [ ] T002 [P] Create api/models/ directory if not exists
- [ ] T003 [P] Create tests/contract/ directory if not exists
- [ ] T004 [P] Create tests/integration/ directory if not exists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Apply database migration (run migrations/001_session_continuity.sql against PostgreSQL)
- [ ] T006 Create Journey Pydantic model in api/models/journey.py (Journey, JourneyCreate classes)
- [ ] T007 [P] Create Session Pydantic model in api/models/journey.py (Session, SessionCreate, Message, Diagnosis classes)
- [ ] T008 [P] Create JourneyDocument Pydantic model in api/models/journey.py (JourneyDocument, JourneyDocumentCreate classes)
- [ ] T009 Create base SessionManager service structure in api/services/session_manager.py (class skeleton with DB pool)
- [ ] T010 Add structured logging setup for journey operations in api/services/session_manager.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Track Conversations Across Sessions (Priority: P1)

**Goal**: AGI tracks conversations across multiple sessions, linking related dialogues into a coherent journey

**Independent Test**: Create 3 sessions, send messages to each, verify all 3 appear in a single journey timeline with proper ordering

### Tests for User Story 1

> **TDD: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for get_or_create_journey MCP tool in tests/contract/test_journey_mcp.py
- [ ] T012 [P] [US1] Integration test: new user creates journey on first session in tests/integration/test_session_continuity.py
- [ ] T013 [P] [US1] Integration test: existing user links session to existing journey in tests/integration/test_session_continuity.py
- [ ] T014 [P] [US1] Integration test: journey timeline returns sessions in chronological order in tests/integration/test_session_continuity.py

### Implementation for User Story 1

- [ ] T015 [US1] Implement get_or_create_journey() in api/services/session_manager.py (check existing, create if needed)
- [ ] T016 [US1] Implement create_session() in api/services/session_manager.py (link to journey, store in DB)
- [ ] T017 [US1] Implement get_journey_timeline() in api/services/session_manager.py (return sessions in chrono order)
- [ ] T018 [US1] Implement get_or_create_journey MCP tool in mcp/tools/journey.py
- [ ] T019 [US1] Register journey MCP tools in mcp/server.py (import and wire up)
- [ ] T020 [US1] Update api/routers/ias.py create_session endpoint to use SessionManager.get_or_create_journey()
- [ ] T021 [US1] Add journey_id to SessionResponse model in api/routers/ias.py

**Checkpoint**: User Story 1 complete - sessions are tracked across conversations

---

## Phase 4: User Story 2 - Query Journey History (Priority: P2)

**Goal**: Users and AGI can query past conversations using keyword, time range, and metadata filters

**Independent Test**: Add 3 sessions with distinct topics, query "sessions about topic X", verify correct session returned

### Tests for User Story 2

> **TDD: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T022 [P] [US2] Contract test for query_journey_history MCP tool in tests/contract/test_journey_mcp.py
- [ ] T023 [P] [US2] Integration test: keyword search returns matching sessions in tests/integration/test_session_continuity.py
- [ ] T024 [P] [US2] Integration test: date range filter returns sessions within window in tests/integration/test_session_continuity.py
- [ ] T025 [P] [US2] Integration test: query returns diagnosis metadata when present in tests/integration/test_session_continuity.py

### Implementation for User Story 2

- [ ] T026 [US2] Implement generate_session_summary() in api/services/session_manager.py (summarize messages for search)
- [ ] T027 [US2] Implement query_journey_history() in api/services/session_manager.py (keyword + date filters)
- [ ] T028 [US2] Add full-text search using pg_trgm GIN index in query_journey_history()
- [ ] T029 [US2] Implement query_journey_history MCP tool in mcp/tools/journey.py
- [ ] T030 [US2] Update api/routers/ias.py /recall endpoint to use SessionManager.query_journey_history()

**Checkpoint**: User Stories 1 AND 2 complete - sessions tracked and queryable

---

## Phase 5: User Story 3 - Link Documents to Journey (Priority: P3)

**Goal**: AGI can link uploaded documents, generated artifacts, and external content to a journey

**Independent Test**: Add document to journey, query journey timeline, verify document appears alongside sessions

### Tests for User Story 3

> **TDD: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T031 [P] [US3] Contract test for add_document_to_journey MCP tool in tests/contract/test_journey_mcp.py
- [ ] T032 [P] [US3] Integration test: document appears in journey timeline in tests/integration/test_session_continuity.py
- [ ] T033 [P] [US3] Integration test: timeline interleaves sessions and documents by timestamp in tests/integration/test_session_continuity.py
- [ ] T034 [P] [US3] Integration test: deleting document cleans up journey reference in tests/integration/test_session_continuity.py

### Implementation for User Story 3

- [ ] T035 [US3] Implement add_document_to_journey() in api/services/session_manager.py
- [ ] T036 [US3] Implement delete_journey_document() in api/services/session_manager.py (with cascade cleanup)
- [ ] T037 [US3] Update get_journey_timeline() to include documents interleaved by timestamp
- [ ] T038 [US3] Implement add_document_to_journey MCP tool in mcp/tools/journey.py
- [ ] T039 [US3] Update api/routers/ias.py /woop endpoint to link generated plans to journey

**Checkpoint**: All user stories complete - full session continuity implemented

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Add performance logging for journey operations (measure <50ms creation, <200ms query)
- [ ] T041 [P] Add error handling for database unavailability in SessionManager
- [ ] T042 [P] Add concurrent session creation handling (race condition protection)
- [ ] T043 [P] Update CHANGELOG.md with new MCP tools and version bump to 1.1.0
- [ ] T044 Run all tests and verify 80%+ coverage for journey operations
- [ ] T045 Run quickstart.md validation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses sessions created by US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on journey/session from US1 but independently testable

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
- Models before services
- Services before MCP tools
- MCP tools before API integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004 can run in parallel (directory creation)
- T006, T007, T008 can run in parallel (Pydantic models)
- All tests within a user story (T011-T014, T022-T025, T031-T034) can run in parallel
- T040, T041, T042, T043 can run in parallel (polish tasks)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD - must fail first):
Task: "Contract test for get_or_create_journey MCP tool in tests/contract/test_journey_mcp.py"
Task: "Integration test: new user creates journey on first session in tests/integration/test_session_continuity.py"
Task: "Integration test: existing user links session to existing journey in tests/integration/test_session_continuity.py"
Task: "Integration test: journey timeline returns sessions in chronological order in tests/integration/test_session_continuity.py"

# After tests written and failing, implement sequentially:
# T015 → T016 → T017 → T018 → T019 → T020 → T021
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010)
3. Complete Phase 3: User Story 1 (T011-T021)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP)
3. Add User Story 2 → Test independently → Deploy
4. Add User Story 3 → Test independently → Deploy
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2 (can start tests, wait for US1 services)
   - Developer C: User Story 3 (can start tests, wait for US1 services)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per Constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
