# Tasks: Meta-ToT Engine Integration

**Input**: Design documents from `/specs/041-meta-tot-engine/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in spec; no explicit test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create Meta-ToT data models in `api/models/meta_tot.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Implement active inference state + Meta-ToT node primitives in `api/services/meta_tot_engine.py`
- [X] T003 Implement POMCP planning and MCTS scaffolding in `api/services/meta_tot_engine.py`
- [X] T004 Implement Meta-ToT trace persistence service in `api/services/meta_tot_trace_service.py`
- [X] T005 Implement threshold decision service in `api/services/meta_tot_decision.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Multi-branch planning with Meta-ToT (Priority: P1) 🎯 MVP

**Goal**: Deliver the Meta-ToT engine and agent-accessible execution pathway

**Independent Test**: Run Meta-ToT for a planning task and receive ranked branches with a selected path and confidence

### Implementation for User Story 1

- [X] T006 [US1] Implement CPA domain expansion and scoring in `api/services/meta_tot_engine.py`
- [X] T007 [US1] Implement Meta-ToT execution orchestration in `api/services/meta_tot_engine.py`
- [X] T008 [US1] Add Meta-ToT tool wrapper in `api/agents/tools/meta_tot_tools.py`
- [X] T009 [US1] Wire Meta-ToT tool into `api/agents/consciousness_manager.py`
- [X] T010 [US1] Add MCP Meta-ToT tool in `dionysus_mcp/tools/meta_tot.py` and register in `dionysus_mcp/server.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Thresholded reasoning mode selection (Priority: P2)

**Goal**: Activate Meta-ToT only when complexity or uncertainty thresholds are met

**Independent Test**: Low-complexity tasks skip Meta-ToT; high-complexity tasks run Meta-ToT

### Implementation for User Story 2

- [X] T011 [US2] Implement complexity/uncertainty scoring in `api/services/meta_tot_decision.py`
- [X] T012 [US2] Integrate decision output into Meta-ToT tool response in `api/agents/tools/meta_tot_tools.py`
- [X] T013 [US2] Apply decision gating in `api/agents/consciousness_manager.py`

**Checkpoint**: User Stories 1 and 2 are independently functional

---

## Phase 5: User Story 3 - Consciousness and strategy traceability (Priority: P3)

**Goal**: Persist Meta-ToT traces and make them retrievable

**Independent Test**: Meta-ToT run returns a trace id and payload is retrievable

### Implementation for User Story 3

- [X] T014 [US3] Persist Meta-ToT traces in `api/services/meta_tot_trace_service.py`
- [X] T015 [US3] Add Meta-ToT API router in `api/routers/meta_tot.py` and register in `api/main.py`
- [X] T016 [US3] Add MCP trace retrieval helper in `dionysus_mcp/tools/meta_tot.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

 - [X] T017 [P] Update documentation references in `docs/` or `README.md` if needed
 - [X] T018 Run quickstart.md validation in `specs/041-meta-tot-engine/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 tooling
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses US1/US2 outputs

### Within Each User Story

- Models before services
- Services before tools/endpoints
- Core implementation before integration

### Parallel Opportunities

- Phase 2 tasks can be parallelized if multiple engineers are available
- User stories can proceed in parallel once foundation is complete
