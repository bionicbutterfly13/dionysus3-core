# Tasks: Mental Model Architecture

**Input**: Design documents from `/specs/005-mental-models/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Test tasks are included per Constitution II (Test-Driven Development).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md project structure:
- **API Models**: `api/models/`
- **API Services**: `api/services/`
- **API Routers**: `api/routers/`
- **MCP Tools**: `dionysus_mcp/tools/`
- **Migrations**: `migrations/`
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema and base infrastructure for all user stories

- [ ] T001 Create migration file migrations/008_create_mental_models.sql with tables: mental_models, model_predictions, model_revisions
- [ ] T002 Add indexes for mental_models (domain, status, constituent_basins GIN)
- [ ] T003 Add indexes for model_predictions (model_id, unresolved partial)
- [ ] T004 Add indexes for model_revisions (model_id, trigger_type)
- [ ] T005 Create views: active_models_summary, models_needing_revision
- [ ] T006 Add source_model_id column to active_inference_states table (ALTER)
- [ ] T007 Create SQL function create_mental_model() in migrations/008_create_mental_models.sql
- [ ] T008 Create SQL function generate_model_prediction() in migrations/008_create_mental_models.sql
- [ ] T009 Create SQL function resolve_prediction() in migrations/008_create_mental_models.sql
- [ ] T010 Create SQL function flag_model_revision() in migrations/008_create_mental_models.sql

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Pydantic models and service skeleton that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [P] Create Pydantic model MentalModel in api/models/mental_model.py
- [ ] T012 [P] Create Pydantic model ModelPrediction in api/models/mental_model.py
- [ ] T013 [P] Create Pydantic model ModelRevision in api/models/mental_model.py
- [ ] T014 [P] Create Pydantic request/response schemas (CreateModelRequest, UpdateModelRequest, ModelResponse, etc.) in api/models/mental_model.py
- [ ] T015 Create ModelService class skeleton in api/services/model_service.py with method stubs
- [ ] T016 [P] Create unit test file tests/unit/test_model_functions.py with test stubs
- [ ] T017 [P] Create contract test file tests/contract/test_model_mcp_tools.py with test stubs
- [ ] T018 [P] Create integration test file tests/integration/test_heartbeat_models.py with test stubs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Prediction Generation During Interaction (Priority: P1) 🎯 MVP

**Goal**: Enable the system to generate predictions from active mental models during context processing

**Independent Test**: Create a mental model from existing memory patterns, interact with the system in a context matching the model's domain, and verify that relevant predictions are generated and stored.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T019 [P] [US1] Write contract test for create_model MCP tool in tests/contract/test_model_mcp_tools.py
- [ ] T020 [P] [US1] Write contract test for list_models MCP tool in tests/contract/test_model_mcp_tools.py
- [ ] T021 [P] [US1] Write integration test for prediction generation in tests/integration/test_heartbeat_models.py

### Implementation for User Story 1

- [ ] T022 [US1] Implement ModelService.create_model() in api/services/model_service.py
- [ ] T023 [US1] Implement ModelService.get_model() in api/services/model_service.py
- [ ] T024 [US1] Implement ModelService.list_models() in api/services/model_service.py
- [ ] T025 [US1] Implement ModelService.get_relevant_models() in api/services/model_service.py (context matching)
- [ ] T026 [US1] Implement ModelService.generate_prediction() in api/services/model_service.py
- [ ] T027 [US1] Implement create_model MCP tool in dionysus_mcp/tools/models.py
- [ ] T028 [US1] Implement list_models MCP tool in dionysus_mcp/tools/models.py
- [ ] T029 [US1] Implement get_model MCP tool in dionysus_mcp/tools/models.py
- [ ] T030 [US1] Create REST router api/routers/models.py with POST /api/models endpoint
- [ ] T031 [US1] Add GET /api/models endpoint to api/routers/models.py
- [ ] T032 [US1] Add GET /api/models/{model_id} endpoint to api/routers/models.py
- [ ] T033 [US1] Integrate prediction generation into heartbeat OBSERVE phase
- [ ] T034 [US1] Add logging for model creation and prediction generation operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Prediction Error Tracking and Learning (Priority: P1)

**Goal**: Track prediction accuracy by comparing predictions to observed outcomes and maintain rolling accuracy scores

**Independent Test**: Generate a prediction, wait for the actual outcome, compare prediction to observation, and verify the error is recorded and affects the model's accuracy score.

### Tests for User Story 2 ⚠️

- [ ] T035 [P] [US2] Write unit test for resolve_prediction SQL function in tests/unit/test_model_functions.py
- [ ] T036 [P] [US2] Write integration test for prediction resolution in tests/integration/test_heartbeat_models.py

### Implementation for User Story 2

- [ ] T037 [US2] Implement ModelService.get_unresolved_predictions() in api/services/model_service.py
- [ ] T038 [US2] Implement ModelService.calculate_error() in api/services/model_service.py (LLM semantic comparison)
- [ ] T039 [US2] Implement ModelService.resolve_prediction() in api/services/model_service.py
- [ ] T040 [US2] Implement ModelService.get_model_accuracy() in api/services/model_service.py
- [ ] T041 [US2] Integrate prediction error checking into heartbeat ORIENT phase
- [ ] T042 [US2] Add GET /api/models/{model_id}/predictions endpoint to api/routers/models.py
- [ ] T043 [US2] Add prediction error logging and accuracy score updates

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Revision Based on Errors (Priority: P2)

**Goal**: Automatically revise models that show high prediction error to improve understanding over time

**Independent Test**: Create a model, simulate high prediction errors, trigger the revision process, and verify the model structure is updated and the new accuracy is tracked.

### Tests for User Story 3 ⚠️

- [ ] T044 [P] [US3] Write unit test for flag_model_revision SQL function in tests/unit/test_model_functions.py
- [ ] T045 [P] [US3] Write integration test for model revision lifecycle in tests/integration/test_model_revision_lifecycle.py

### Implementation for User Story 3

- [ ] T046 [US3] Implement ModelService.flag_for_revision() in api/services/model_service.py
- [ ] T047 [US3] Implement ModelService.get_models_needing_revision() in api/services/model_service.py
- [ ] T048 [US3] Implement ModelService.apply_revision() in api/services/model_service.py
- [ ] T049 [US3] Implement revise_model MCP tool in dionysus_mcp/tools/models.py
- [ ] T050 [US3] Create ReviseModelHandler action handler (REVISE_MODEL action type)
- [ ] T051 [US3] Add REVISE_MODEL to energy costs (3 energy) in energy_service.py
- [ ] T052 [US3] Integrate revision flagging into heartbeat DECIDE phase
- [ ] T053 [US3] Add POST /api/models/{model_id}/revisions endpoint to api/routers/models.py
- [ ] T054 [US3] Add GET /api/models/{model_id}/revisions endpoint to api/routers/models.py
- [ ] T055 [US3] Add revision logging and audit trail

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Manual Model Creation (Priority: P2)

**Goal**: Enable developers/administrators to manually create mental models by specifying basins

**Independent Test**: Specify a model name, domain, and list of existing memory basins; verify the model is created and can generate predictions.

### Tests for User Story 4 ⚠️

- [ ] T056 [P] [US4] Write contract test for model creation validation (invalid basins) in tests/contract/test_model_mcp_tools.py
- [ ] T057 [P] [US4] Write integration test for manual model creation workflow in tests/integration/test_heartbeat_models.py

### Implementation for User Story 4

- [ ] T058 [US4] Add basin existence validation to ModelService.create_model() in api/services/model_service.py
- [ ] T059 [US4] Add prediction_templates parameter support to create_model in api/services/model_service.py
- [ ] T060 [US4] Implement ModelService.update_model() in api/services/model_service.py
- [ ] T061 [US4] Implement ModelService.deprecate_model() in api/services/model_service.py (soft delete)
- [ ] T062 [US4] Add PUT /api/models/{model_id} endpoint to api/routers/models.py
- [ ] T063 [US4] Add DELETE /api/models/{model_id} endpoint (deprecation) to api/routers/models.py
- [ ] T064 [US4] Add model status transition validation (draft → active → deprecated)

**Checkpoint**: At this point, User Stories 1-4 should all work independently

---

## Phase 7: User Story 5 - Model Types and Domains (Priority: P3)

**Goal**: Support different model domains (user, self, world, task_specific) with appropriate categorization and context matching

**Independent Test**: Create models with different domains, verify they are retrieved when their domain matches the current context.

### Tests for User Story 5 ⚠️

- [ ] T065 [P] [US5] Write unit test for domain filtering in tests/unit/test_model_functions.py
- [ ] T066 [P] [US5] Write integration test for domain-based model selection in tests/integration/test_heartbeat_models.py

### Implementation for User Story 5

- [ ] T067 [US5] Add domain validation and enum support in api/models/mental_model.py
- [ ] T068 [US5] Implement domain-based filtering in ModelService.list_models() in api/services/model_service.py
- [ ] T069 [US5] Implement domain-based context matching in ModelService.get_relevant_models() in api/services/model_service.py
- [ ] T070 [US5] Add domain prioritization logic (user-domain models for user context)
- [ ] T071 [US5] Update list_models MCP tool to support domain parameter
- [ ] T072 [US5] Add domain query parameter to GET /api/models endpoint

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T073 [P] Add comprehensive docstrings to all public methods in api/services/model_service.py
- [ ] T074 [P] Add request/response validation for all REST endpoints
- [ ] T075 Configure max models per context (default: 5) for performance
- [ ] T076 Add prediction timeout handling (TTL for unresolved predictions)
- [ ] T077 Add degraded model handling (mark degraded if basins deleted)
- [ ] T078 [P] Performance optimization: ensure prediction generation <500ms
- [ ] T079 Run quickstart.md validation scenarios
- [ ] T080 Update CLAUDE.md with mental models feature documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 & US2 are both P1 priority - can run in parallel
  - US3 & US4 are both P2 priority - can run in parallel after US1/US2
  - US5 is P3 priority - can start after US1/US2
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Builds on prediction storage from US1 but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Uses prediction errors from US2 but independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 filtering but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints/MCP tools
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Setup Phase:**
- T002, T003, T004 can run in parallel (different indexes)
- T007, T008, T009, T010 can run in parallel (different functions, same file)

**Foundational Phase:**
- T011, T012, T013, T014 can run in parallel (different model classes)
- T016, T017, T018 can run in parallel (different test files)

**User Story Phases:**
- All tests within a story marked [P] can run in parallel
- Once Foundational phase completes, US1 and US2 can start in parallel
- After US1/US2, US3 and US4 can run in parallel
- US5 can start any time after Foundational

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write contract test for create_model MCP tool" (T019)
Task: "Write contract test for list_models MCP tool" (T020)
Task: "Write integration test for prediction generation" (T021)

# After tests fail, implement sequentially:
# Service methods first, then MCP tools, then REST endpoints, then heartbeat integration
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T010)
2. Complete Phase 2: Foundational (T011-T018)
3. Complete Phase 3: User Story 1 (T019-T034)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Predictions now have error tracking
4. Add User Story 3 → Test independently → Auto-revision enabled
5. Add User Story 4 → Test independently → Manual model management
6. Add User Story 5 → Test independently → Domain filtering
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1)
   - Developer B: User Story 2 (P1)
3. After P1 stories complete:
   - Developer A: User Story 3 (P2)
   - Developer B: User Story 4 (P2)
4. User Story 5 (P3) can be done by either developer

---

## Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | T001-T010 (10 tasks) | Indexes parallel, Functions parallel |
| Foundational | T011-T018 (8 tasks) | Models parallel, Tests parallel |
| US1 (P1) MVP | T019-T034 (16 tasks) | Tests parallel |
| US2 (P1) | T035-T043 (9 tasks) | Tests parallel |
| US3 (P2) | T044-T055 (12 tasks) | Tests parallel |
| US4 (P2) | T056-T064 (9 tasks) | Tests parallel |
| US5 (P3) | T065-T072 (8 tasks) | Tests parallel |
| Polish | T073-T080 (8 tasks) | Most parallel |
| **Total** | **80 tasks** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution: All additions are non-breaking (new tables, optional columns, new endpoints)
