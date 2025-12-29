# Tasks: Network Reification and Self-Modeling

**Input**: Design documents from `/specs/034-network-self-modeling/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Tests included per quickstart.md testing checklist.

**Organization**: Tasks grouped by user story (US1-US5) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

Following existing api/ structure per plan.md:
- Models: `api/models/`
- Services: `api/services/`
- Routers: `api/routers/`
- Tests: `tests/unit/`, `tests/integration/`, `tests/contract/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Feature flags and base configuration for opt-in functionality

- [X] T001 Add feature flags to config for NETWORK_STATE_ENABLED, SELF_MODELING_ENABLED, HEBBIAN_LEARNING_ENABLED, ROLE_MATRIX_ENABLED in api/config.py
- [X] T002 [P] Create SnapshotTrigger enum (CHANGE_EVENT, DAILY_CHECKPOINT, MANUAL) in api/models/network_state.py
- [X] T003 [P] Create AdaptationMode enum (ACCELERATING, STABLE, DECELERATING, STRESSED) in api/models/network_state.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared utilities that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement state_to_vector() utility for L2 norm delta calculation in api/services/network_state_service.py
- [X] T005 [P] Implement weight_bounds_enforcer() using sigmoid squashing (0.01, 0.99) in api/utils/math_utils.py
- [X] T006 [P] Create base webhook persistence helper for Neo4j network state storage in api/services/network_state_service.py
- [X] T007 Add network-state router registration in api/main.py (conditional on feature flag)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Network State Observation (Priority: P1) 🎯 MVP

**Goal**: Enable system operators to observe internal network states (W/T/H values) for debugging and diagnostics

**Independent Test**: Query any agent's network state and receive structured W/T/H snapshot within 100ms

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for NetworkState model validation in tests/unit/test_network_state.py
- [X] T009 [P] [US1] Unit test for delta calculation (5% threshold) in tests/unit/test_network_state.py
- [X] T010 [P] [US1] Contract test for GET /network-state/{agent_id} in tests/contract/test_network_state_api.py
- [X] T011 [P] [US1] Contract test for GET /network-state/{agent_id}/history in tests/contract/test_network_state_api.py
- [X] T012 [P] [US1] Contract test for POST /network-state/{agent_id}/snapshot in tests/contract/test_network_state_api.py

### Implementation for User Story 1

- [X] T013 [P] [US1] Create NetworkState Pydantic model with W/T/H fields in api/models/network_state.py
- [X] T014 [US1] Implement NetworkStateService.get_current() in api/services/network_state_service.py
- [X] T015 [US1] Implement NetworkStateService.should_snapshot() with 5% delta threshold in api/services/network_state_service.py
- [X] T016 [US1] Implement NetworkStateService.create_snapshot() with Neo4j persistence in api/services/network_state_service.py
- [X] T017 [US1] Implement NetworkStateService.get_history() with time range filtering in api/services/network_state_service.py
- [X] T018 [US1] Create GET /network-state/{agent_id} endpoint in api/routers/network_state.py
- [X] T019 [US1] Create GET /network-state/{agent_id}/history endpoint in api/routers/network_state.py
- [X] T020 [US1] Create POST /network-state/{agent_id}/snapshot endpoint with rate limiting in api/routers/network_state.py
- [X] T021 [US1] Create GET /network-state/{agent_id}/diff endpoint in api/routers/network_state.py
- [X] T022 [US1] Add RBAC check using existing audit log permissions in api/routers/network_state.py
- [ ] T023 [P] [US1] Integration test for NetworkState Neo4j persistence in tests/integration/test_network_state_neo4j.py

**Checkpoint**: User Story 1 complete - network state observation fully functional

---

## Phase 4: User Story 2 - Self-Prediction for Agent Regularization (Priority: P2)

**Goal**: Enable agents to predict their own next internal states for automatic complexity reduction

**Independent Test**: Compare weight distribution width before/after enabling self-prediction (expect 15-25% reduction)

### Tests for User Story 2

- [X] T024 [P] [US2] Unit test for PredictionRecord model in tests/unit/test_self_modeling.py
- [X] T025 [P] [US2] Unit test for prediction error calculation in tests/unit/test_self_modeling.py
- [X] T026 [P] [US2] Contract test for GET /self-modeling/{agent_id}/predictions in tests/contract/test_network_state_api.py
- [X] T027 [P] [US2] Contract test for GET /self-modeling/{agent_id}/accuracy in tests/contract/test_network_state_api.py

### Implementation for User Story 2

- [X] T028 [P] [US2] Create PredictionRecord Pydantic model in api/models/prediction.py
- [X] T029 [US2] Implement PredictionService.predict() for next state prediction in api/services/self_modeling_service.py
- [X] T030 [US2] Implement PredictionService.resolve() to compare prediction vs actual in api/services/self_modeling_service.py
- [X] T031 [US2] Implement PredictionService.calculate_error() using L2 norm in api/services/self_modeling_service.py
- [X] T032 [US2] Implement PredictionService.get_accuracy_metrics() for time-windowed aggregation in api/services/self_modeling_service.py
- [X] T033 [US2] Create SelfModelingCallback for smolagents integration in api/agents/self_modeling_callback.py
- [X] T034 [US2] Implement callback.on_step() with prediction/resolution cycle in api/agents/self_modeling_callback.py
- [X] T035 [US2] Create GET /self-modeling/{agent_id}/predictions endpoint in api/routers/network_state.py
- [X] T036 [US2] Create GET /self-modeling/{agent_id}/accuracy endpoint in api/routers/network_state.py
- [ ] T037 [US2] Add opt-in self-modeling callback to agent initialization (conditional on flag) in api/agents/consciousness_manager.py

**Checkpoint**: User Story 2 complete - self-prediction regularization functional

---

## Phase 5: User Story 3 - Hebbian Learning for Knowledge Relationships (Priority: P2)

**Goal**: Enable knowledge graph relationships to strengthen/weaken based on co-activation patterns

**Independent Test**: Verify co-activation frequency correlates > 0.8 with connection strength

### Tests for User Story 3

- [X] T038 [P] [US3] Unit test for HebbianConnection model in tests/unit/test_hebbian.py
- [X] T039 [P] [US3] Unit test for Hebbian weight update formula in tests/unit/test_hebbian.py
- [X] T040 [P] [US3] Unit test for exponential decay calculation in tests/unit/test_hebbian.py
- [X] T041 [P] [US3] Unit test for weight boundary enforcement in tests/unit/test_hebbian.py

### Implementation for User Story 3

- [X] T042 [P] [US3] Create HebbianConnection Pydantic model in api/models/hebbian.py
- [X] T043 [US3] Implement HebbianConnection.apply_hebbian_update() with Treur formula in api/models/hebbian.py
- [X] T044 [US3] Implement HebbianConnection.apply_decay() with exponential decay in api/models/hebbian.py
- [X] T045 [US3] Implement HebbianService.record_coactivation() in api/services/hebbian_service.py
- [X] T046 [US3] Implement HebbianService.apply_decay_batch() for scheduled decay in api/services/hebbian_service.py
- [X] T047 [US3] Implement HebbianService._persist() for Neo4j relationship property updates in api/services/hebbian_service.py
- [ ] T048 [US3] Add Hebbian weight updates to kg_learning_service retrieval callbacks in api/services/kg_learning_service.py (conditional on flag)

**Checkpoint**: User Story 3 complete - Hebbian learning functional

---

## Phase 6: User Story 4 - Role Matrix Network Specification (Priority: P3)

**Goal**: Enable declarative network topology specification stored in Neo4j for reproducible agent configurations

**Independent Test**: Export agent state as role matrix, import to new agent, verify state divergence < 1%

### Tests for User Story 4

- [ ] T049 [P] [US4] Unit test for RoleMatrix validation rules in tests/unit/test_role_matrix.py
- [ ] T050 [P] [US4] Unit test for inhibitory cycle detection in tests/unit/test_role_matrix.py
- [ ] T051 [P] [US4] Contract test for GET /role-matrix/{agent_id} in tests/contract/test_network_state_api.py
- [ ] T052 [P] [US4] Contract test for PUT /role-matrix/{agent_id} in tests/contract/test_network_state_api.py
- [ ] T053 [P] [US4] Contract test for GET /role-matrix/{agent_id}/export in tests/contract/test_network_state_api.py

### Implementation for User Story 4

- [ ] T054 [P] [US4] Create RoleMatrixSpec, RoleNode, RoleConnection Pydantic models in api/models/role_matrix.py
- [ ] T055 [US4] Implement RoleMatrixService.validate() for internal consistency checks in api/services/role_matrix_service.py
- [ ] T056 [US4] Implement RoleMatrixService.create_from_state() to export agent state in api/services/role_matrix_service.py
- [ ] T057 [US4] Implement RoleMatrixService.instantiate_agent() to create agent from spec in api/services/role_matrix_service.py
- [ ] T058 [US4] Implement RoleMatrixService._persist_to_neo4j() with Graphiti in api/services/role_matrix_service.py
- [ ] T059 [US4] Create GET /role-matrix/{agent_id} endpoint in api/routers/network_state.py
- [ ] T060 [US4] Create PUT /role-matrix/{agent_id} endpoint with validation in api/routers/network_state.py
- [ ] T061 [US4] Create GET /role-matrix/{agent_id}/export endpoint in api/routers/network_state.py
- [ ] T062 [US4] Setup Neo4j constraints and indexes for RoleMatrix via Graphiti in scripts/setup_role_matrix_schema.py

**Checkpoint**: User Story 4 complete - role matrix specification functional

---

## Phase 7: User Story 5 - Multi-Level Adaptation Control (Priority: P3)

**Goal**: Enable second-order learning controls where adaptation speed adapts based on context

**Independent Test**: Verify 2x faster learning on novel patterns vs fixed-rate baseline

### Tests for User Story 5

- [X] T063 [P] [US5] Unit test for SelfModelState model in tests/unit/test_network_state.py
- [X] T064 [P] [US5] Unit test for TimingState model in tests/unit/test_network_state.py
- [X] T065 [P] [US5] Unit test for adaptation mode transitions in tests/unit/test_network_state.py

### Implementation for User Story 5

- [X] T066 [P] [US5] Create SelfModelState Pydantic model in api/models/network_state.py
- [X] T067 [P] [US5] Create TimingState Pydantic model in api/models/network_state.py
- [ ] T068 [US5] Extend MetaplasticityController with optional H-state tracking in api/services/metaplasticity_service.py
- [ ] T069 [US5] Implement second-order speed modulation based on prediction error in api/services/metaplasticity_service.py
- [ ] T070 [US5] Implement stress-reduces-adaptation principle (configurable) in api/services/metaplasticity_service.py
- [ ] T071 [US5] Connect TimingState updates to NetworkState snapshots in api/services/network_state_service.py

**Checkpoint**: User Story 5 complete - multi-level adaptation functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and regression verification

- [ ] T072 [P] Run all existing tests to verify zero regression (SC-009)
- [ ] T073 [P] Verify agents without features enabled behave identically (SC-010)
- [ ] T074 [P] Add inline documentation to all new models in api/models/
- [ ] T075 [P] Add inline documentation to all new services in api/services/
- [ ] T076 Run quickstart.md validation scenarios
- [ ] T077 Performance test: verify 100ms query time for 1000 connections (SC-001)
- [ ] T078 [P] Update CLAUDE.md with feature completion note

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1): Foundation only - no other story dependencies
  - US2 (P2): Foundation + US1 (needs NetworkState model)
  - US3 (P2): Foundation only - independent of US1/US2
  - US4 (P3): Foundation + US1 (needs NetworkState model)
  - US5 (P3): Foundation + US1 + US2 (needs prediction errors for adaptation)
- **Polish (Phase 8)**: Depends on desired user stories being complete

### User Story Dependencies

```
Foundation (Phase 2)
    │
    ├──▶ US1: Network State Observation (P1) 🎯 MVP
    │        │
    │        ├──▶ US2: Self-Prediction (P2)
    │        │        │
    │        │        └──▶ US5: Multi-Level Adaptation (P3)
    │        │
    │        └──▶ US4: Role Matrix (P3)
    │
    └──▶ US3: Hebbian Learning (P2) [Independent]
```

### Within Each User Story

1. Tests written first (if included)
2. Models before services
3. Services before endpoints
4. Core implementation before integration

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003 can run in parallel (different enums)

**Phase 2 (Foundational)**:
- T005, T006 can run in parallel (different utilities)

**Phase 3 (US1)**:
- T008-T012 tests can run in parallel
- T013 model in parallel with tests
- T023 integration test after service implementation

**Phase 4 (US2)**:
- T024-T027 tests can run in parallel
- T028 model in parallel with tests

**Phase 5 (US3)**:
- T038-T041 tests can run in parallel
- T042 model in parallel with tests

**Phase 6 (US4)**:
- T049-T053 tests can run in parallel
- T054 models in parallel with tests

**Phase 7 (US5)**:
- T063-T065 tests can run in parallel
- T066, T067 models in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests in parallel:
Task: T008 "Unit test for NetworkState model validation in tests/unit/test_network_state.py"
Task: T009 "Unit test for delta calculation in tests/unit/test_network_state.py"
Task: T010 "Contract test for GET /network-state/{agent_id} in tests/contract/test_network_state_api.py"
Task: T011 "Contract test for GET /network-state/{agent_id}/history in tests/contract/test_network_state_api.py"
Task: T012 "Contract test for POST /network-state/{agent_id}/snapshot in tests/contract/test_network_state_api.py"

# Then model (can run with tests):
Task: T013 "Create NetworkState Pydantic model in api/models/network_state.py"

# Then services (sequential - depend on model):
Task: T014 "Implement NetworkStateService.get_current()"
Task: T015 "Implement NetworkStateService.should_snapshot()"
...
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 - Network State Observation
4. **STOP and VALIDATE**: Test US1 independently
5. Deploy/demo if ready - operators can now observe agent states

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → **MVP: Network observability**
3. Add US2 → Test independently → **Increment: Self-prediction regularization**
4. Add US3 → Test independently → **Increment: Hebbian learning**
5. Add US4 → Test independently → **Increment: Declarative configs**
6. Add US5 → Test independently → **Increment: Adaptive learning**

### Parallel Team Strategy

With multiple developers after Foundational phase:
- Developer A: US1 (P1) → US2 (P2) → US5 (P3)
- Developer B: US3 (P2) → US4 (P3)

---

## Notes

- All features are opt-in via configuration flags (default: disabled)
- All new code is additive - no modifications to existing behavior
- Zero regression requirement (SC-009, SC-010)
- Neo4j access via webhooks + Graphiti (approved exception)
- Performance target: 100ms queries for ≤1000 connections
