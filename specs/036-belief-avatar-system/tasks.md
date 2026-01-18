# Tasks: Belief Avatar System

**Input**: Design documents from `/specs/036-belief-avatar-system/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests included per constitution gate requirements (Test-First).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **API**: `api/routers/`, `api/services/`, `api/models/`
- **Tests**: `tests/integration/`, `tests/unit/`
- **Skills**: `/Volumes/Asylum/skills-library/personal/bionicbutterfly13/consciousness/`

---

## Phase 1: Setup

**Purpose**: Project initialization and router structure

- [X] T001 Create router file skeleton in api/routers/belief_journey.py
- [X] T002 [P] Create request/response Pydantic models in api/routers/belief_journey.py (imports from api/models/belief_journey.py)
- [X] T003 Register router in api/main.py with prefix /belief-journey

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user story endpoints

**⚠️ CRITICAL**: No endpoint implementation can begin until this phase is complete

- [X] T004 Implement health endpoint GET /health in api/routers/belief_journey.py
- [X] T005 [P] Add error handling helpers (404, 400) following ias.py patterns in api/routers/belief_journey.py
- [X] T006 [P] Create test fixtures for BeliefTrackingService in tests/conftest.py
- [X] T007 Verify BeliefTrackingService singleton works with async in tests/unit/test_belief_tracking_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Belief Journey Management via API (Priority: P1) 🎯 MVP

**Goal**: Create, get, and advance journeys; identify and dissolve limiting beliefs; propose empowering beliefs

**Independent Test**: HTTP requests to journey/belief endpoints return correct data with Graphiti persistence

### Tests for User Story 1

- [X] T008 [P] [US1] Integration test for journey creation in tests/integration/test_belief_journey_router.py
- [X] T009 [P] [US1] Integration test for limiting belief lifecycle in tests/integration/test_belief_journey_router.py
- [X] T010 [P] [US1] Integration test for empowering belief lifecycle in tests/integration/test_belief_journey_router.py

### Implementation for User Story 1

- [X] T011 [US1] Implement POST /journey/create endpoint in api/routers/belief_journey.py (FR-001)
- [X] T012 [US1] Implement GET /journey/{journey_id} endpoint in api/routers/belief_journey.py (FR-002)
- [X] T013 [US1] Implement POST /journey/{journey_id}/advance endpoint in api/routers/belief_journey.py (FR-003)
- [X] T014 [P] [US1] Implement POST /beliefs/limiting/identify endpoint in api/routers/belief_journey.py (FR-004)
- [X] T015 [P] [US1] Implement POST /beliefs/limiting/{belief_id}/map endpoint in api/routers/belief_journey.py (FR-005)
- [X] T016 [P] [US1] Implement POST /beliefs/limiting/{belief_id}/evidence endpoint in api/routers/belief_journey.py (FR-006)
- [X] T017 [US1] Implement POST /beliefs/limiting/{belief_id}/dissolve endpoint in api/routers/belief_journey.py (FR-007)
- [X] T018 [P] [US1] Implement POST /beliefs/empowering/propose endpoint in api/routers/belief_journey.py (FR-008)
- [X] T019 [P] [US1] Implement POST /beliefs/empowering/{belief_id}/strengthen endpoint in api/routers/belief_journey.py (FR-009)
- [X] T020 [US1] Implement POST /beliefs/empowering/{belief_id}/anchor endpoint in api/routers/belief_journey.py (FR-010)

**Checkpoint**: Journey and belief lifecycle fully functional via API

---

## Phase 4: User Story 2 - Progress Metrics Retrieval (Priority: P1)

**Goal**: Query comprehensive journey analytics with calculated rates

**Independent Test**: Metrics endpoint returns dissolution_rate, experiment_success_rate, resolution times

### Tests for User Story 2

- [X] T021 [P] [US2] Integration test for metrics with populated journey in tests/integration/test_belief_journey_router.py
- [X] T022 [P] [US2] Integration test for metrics with empty journey in tests/integration/test_belief_journey_router.py

### Implementation for User Story 2

- [X] T023 [US2] Implement GET /journey/{journey_id}/metrics endpoint in api/routers/belief_journey.py (FR-020)
- [X] T024 [US2] Add metrics response model with all calculated fields in api/routers/belief_journey.py

**Checkpoint**: Facilitators can view participant progress analytics

---

## Phase 5: User Story 3 - Avatar Simulation with Theory of Mind (Priority: P2)

**Goal**: Simulate [LEGACY_AVATAR_HOLDER] experience of course content with Shell/Core dynamics

**Independent Test**: Skill invocation returns structured response with internal_thoughts, emotional_reactions, shell_core_dynamics

### Implementation for User Story 3

- [ ] T025 [P] [US3] Create avatar-simulation.md skill with YAML frontmatter in /Volumes/Asylum/skills-library/personal/bionicbutterfly13/consciousness/avatar-simulation.md
- [ ] T026 [US3] Define Theory of Mind model structure in avatar-simulation.md (Shell/Core architecture)
- [ ] T027 [US3] Add 5 self-sabotage pattern definitions in avatar-simulation.md
- [ ] T028 [US3] Add Voice of Market exact language reference in avatar-simulation.md
- [ ] T029 [US3] Define simulation output format with all required sections (FR-024, FR-025, FR-026, FR-027, FR-028)
- [ ] T030 [US3] Add Prime Directive language constraints (FR-032)
- [ ] T031 [US3] Add market-saturation detection rules (FR-033)

**Checkpoint**: Avatar simulation skill produces structured responses

---

## Phase 6: User Story 4 - Response Prediction Model (Priority: P2)

**Goal**: Predict avatar response to stimulus with confidence score

**Independent Test**: Prediction query returns response_type, confidence_score, reasoning

### Implementation for User Story 4

- [ ] T032 [P] [US4] Create response-prediction.md skill in /Volumes/Asylum/skills-library/personal/bionicbutterfly13/consciousness/response-prediction.md
- [ ] T033 [US4] Define prediction categories (SKEPTICAL, ENGAGED, SHELL_RESPONSE, CORE_RESPONSE) in response-prediction.md
- [ ] T034 [US4] Add confidence scoring rubric in response-prediction.md (FR-030)
- [ ] T035 [US4] Add reasoning template for each prediction type in response-prediction.md

**Checkpoint**: Response prediction provides actionable content optimization guidance

---

## Phase 7: User Story 5 - Replay Loop Lifecycle Management (Priority: P3)

**Goal**: Track rumination patterns from identification through resolution

**Independent Test**: Loop endpoints handle ACTIVE → INTERRUPTED → RESOLVED transitions with time tracking

### Tests for User Story 5

- [X] T036 [P] [US5] Integration test for replay loop lifecycle in tests/integration/test_belief_journey_router.py

### Implementation for User Story 5

- [X] T037 [US5] Implement POST /loops/identify endpoint in api/routers/belief_journey.py (FR-013)
- [X] T038 [US5] Implement POST /loops/{loop_id}/interrupt endpoint in api/routers/belief_journey.py (FR-014)
- [X] T039 [US5] Implement POST /loops/{loop_id}/resolve endpoint in api/routers/belief_journey.py (FR-015)

**Checkpoint**: Replay loop tracking complete with resolution time capture

---

## Phase 8: User Story 6 - Shell/Core Dynamics Tracking (Priority: P3)

**Goal**: Track which operating system is active during content consumption

**Independent Test**: Simulation captures Shell/Core activation scores per content segment

### Implementation for User Story 6

- [ ] T040 [US6] Add Shell/Core scoring algorithm to avatar-simulation.md
- [ ] T041 [US6] Add segment-level dynamics capture to avatar-simulation.md
- [ ] T042 [US6] Add overall arc mapping output to avatar-simulation.md

**Checkpoint**: Shell/Core dynamics provide content optimization insights

---

## Phase 9: Remaining Endpoints (Supporting Features)

**Purpose**: Complete API surface for full IAS journey support

- [X] T043 Implement POST /experiments/design endpoint in api/routers/belief_journey.py (FR-011)
- [X] T044 Implement POST /experiments/{experiment_id}/record endpoint in api/routers/belief_journey.py (FR-012)
- [X] T045 [P] Implement POST /mosaeic/capture endpoint in api/routers/belief_journey.py (FR-016)
- [X] T046 [P] Implement POST /vision/add endpoint in api/routers/belief_journey.py (FR-017)
- [X] T047 [P] Implement POST /support/circle/create endpoint in api/routers/belief_journey.py (FR-018)
- [X] T048 Implement POST /support/circle/{circle_id}/member endpoint in api/routers/belief_journey.py (FR-019)

**Checkpoint**: Full API surface complete

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [X] T049 [P] Add docstrings to all router endpoints in api/routers/belief_journey.py
- [ ] T050 Run quickstart.md validation scenarios manually
- [ ] T051 Verify OpenAPI spec matches implementation via /docs endpoint
- [ ] T052 Update api/models/__init__.py with belief_journey exports

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-8)**: All depend on Foundational phase completion
  - US1/US2 are both P1 priority - can proceed in parallel
  - US3/US4 are P2 priority - can proceed after US1/US2 or in parallel
  - US5/US6 are P3 priority - can proceed after US3/US4 or in parallel
- **Remaining Endpoints (Phase 9)**: Can start after Foundational, parallel to user stories
- **Polish (Phase 10)**: Depends on all implementation complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - Core API functionality
- **User Story 2 (P1)**: Can start after Phase 2 - Extends US1 with metrics
- **User Story 3 (P2)**: Can start after Phase 2 - Independent skills-library work
- **User Story 4 (P2)**: Can start after Phase 2 - Extends US3 with prediction
- **User Story 5 (P3)**: Can start after Phase 2 - Uses router from US1
- **User Story 6 (P3)**: Depends on US3 - Extends avatar simulation

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Endpoints depend on request/response models (T002)
- All endpoints use BeliefTrackingService singleton

### Parallel Opportunities

- T002, T003 can run in parallel after T001
- T005, T006 can run in parallel after T004
- All US1 tests (T008, T009, T010) can run in parallel
- US3 and US4 skills work can run in parallel with API implementation
- T045, T046, T047 can run in parallel (different entity types)

---

## Parallel Example: User Story 1

```bash
# Launch all tests together:
Task: T008 "Integration test for journey creation"
Task: T009 "Integration test for limiting belief lifecycle"
Task: T010 "Integration test for empowering belief lifecycle"

# Launch parallel endpoints (different belief types):
Task: T014 "POST /beliefs/limiting/identify"
Task: T018 "POST /beliefs/empowering/propose"
```

---

## Parallel Example: Skills Development

```bash
# Launch both skills in parallel (different files):
Task: T025 "Create avatar-simulation.md"
Task: T032 "Create response-prediction.md"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (journey/belief management)
4. Complete Phase 4: User Story 2 (metrics)
5. **STOP and VALIDATE**: Test journey creation and metrics independently
6. Deploy/demo if ready - facilitators can track participants

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 + US2 → API MVP for facilitator tracking
3. Add US3 + US4 → Avatar simulation for course design
4. Add US5 + US6 → Advanced tracking (replay loops, Shell/Core)
5. Add Phase 9 → Complete API surface
6. Each increment adds value without breaking previous

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Stories 1 + 2 (API endpoints)
   - Developer B: User Stories 3 + 4 (skills-library)
3. Stories complete and integrate independently

---

## Task Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| Setup | - | 3 | 2 |
| Foundational | - | 4 | 2 |
| US1 (P1) | Journey/Belief API | 13 | 8 |
| US2 (P1) | Metrics | 4 | 2 |
| US3 (P2) | Avatar Simulation | 7 | 1 |
| US4 (P2) | Response Prediction | 4 | 1 |
| US5 (P3) | Replay Loops | 4 | 1 |
| US6 (P3) | Shell/Core Dynamics | 3 | 0 |
| Remaining | Support Endpoints | 6 | 3 |
| Polish | - | 4 | 1 |
| **Total** | | **52** | **21** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently completable and testable
- BeliefTrackingService and models already exist (T002 imports, doesn't recreate)
- Skills-library work is fully parallel to API work
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
