# Tasks: Beautiful Loop Hyper-Model Implementation

**Input**: Design documents from `/specs/056-beautiful-loop-hyper/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: TDD is **MANDATORY** per SC-008 (>90% test coverage with TDD methodology)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| Story | Priority | Title | Key Components |
|-------|----------|-------|----------------|
| US1 | P1 | Unified Consciousness State | UnifiedRealityModel, coherence |
| US2 | P1 | Bayesian Binding Selection | BayesianBinder, binding criteria |
| US3 | P1 | Precision Profile Forecasting | HyperModelService, PrecisionProfile |
| US4 | P2 | Second-Order Precision Learning | PrecisionError, hyper-model update |
| US5 | P2 | Epistemic Depth Measurement | EpistemicFieldService, EpistemicState |
| US6 | P2 | Beautiful Loop OODA Integration | ConsciousnessManager, EventBus |
| US7 | P3 | Consciousness State Modeling | State presets |

---

## Phase 1: Setup

**Purpose**: Project initialization and verification of existing dependencies

- [ ] T001 Verify existing dependencies in pyproject.toml (FastAPI, Pydantic v2, smolagents, NumPy)
- [ ] T002 [P] Verify EventBus exists and supports typed events in api/utils/event_bus.py
- [ ] T003 [P] Verify ActiveInferenceService reusable in api/services/active_inference_service.py
- [ ] T004 [P] Verify BeliefState model available in api/models/belief_state.py
- [ ] T005 [P] Verify MetaplasticityService extends correctly in api/services/metaplasticity_service.py
- [ ] T006 Create test directory structure for Beautiful Loop in tests/unit/ and tests/integration/

---

## Phase 2: Foundational Models (Blocking Prerequisites)

**Purpose**: Core Pydantic models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Models (TDD - Write FIRST)

- [ ] T007 [P] Write tests for PrecisionProfile model in tests/unit/test_beautiful_loop_models.py
- [ ] T008 [P] Write tests for EpistemicState model in tests/unit/test_beautiful_loop_models.py
- [ ] T009 [P] Write tests for PrecisionError model in tests/unit/test_beautiful_loop_models.py
- [ ] T010 [P] Write tests for BoundInference model in tests/unit/test_beautiful_loop_models.py
- [ ] T011 [P] Write tests for BindingConfig model in tests/unit/test_beautiful_loop_models.py
- [ ] T012 [P] Write tests for HyperModelConfig model in tests/unit/test_beautiful_loop_models.py
- [ ] T013 [P] Write tests for event types (PrecisionForecastEvent, PrecisionErrorEvent, etc.) in tests/unit/test_beautiful_loop_models.py

### Implementation for Foundational Models

- [ ] T014 Implement PrecisionProfile model in api/models/beautiful_loop.py (FR-009, FR-010, FR-011, FR-012)
- [ ] T015 Implement EpistemicState model in api/models/beautiful_loop.py (FR-017, FR-018, FR-019)
- [ ] T016 Implement PrecisionError model in api/models/beautiful_loop.py (FR-013, FR-014)
- [ ] T017 Implement BoundInference model in api/models/beautiful_loop.py (FR-005, FR-006)
- [ ] T018 Implement BindingConfig model in api/models/beautiful_loop.py (FR-007)
- [ ] T019 Implement HyperModelConfig model in api/models/beautiful_loop.py
- [ ] T020 Implement event types in api/models/beautiful_loop.py (FR-027)
- [ ] T021 Run tests to verify all models pass: pytest tests/unit/test_beautiful_loop_models.py -v

**Checkpoint**: All foundational models complete - user story implementation can now begin

---

## Phase 3: User Story 1 - Unified Consciousness State (Priority: P1) 🎯 MVP

**Goal**: Single container that unifies all active inference states, belief states, and metacognitive states with coherence scoring

**Independent Test**: Query unified state, verify all components accessible, measure coherence score

**Functional Requirements**: FR-001, FR-002, FR-003, FR-004

### Tests for User Story 1 (TDD - Write FIRST)

- [ ] T022 [P] [US1] Write unit tests for UnifiedRealityModel container in tests/unit/test_unified_reality_model.py
- [ ] T023 [P] [US1] Write tests for coherence computation (cosine similarity) in tests/unit/test_unified_reality_model.py
- [ ] T024 [P] [US1] Write tests for bound vs transparent process tracking in tests/unit/test_unified_reality_model.py
- [ ] T025 [P] [US1] Write tests for epistemic affordances derivation in tests/unit/test_unified_reality_model.py
- [ ] T026 [P] [US1] Write contract tests for /beautiful-loop/reality-model endpoint in tests/contract/test_beautiful_loop_api.py

### Implementation for User Story 1

- [ ] T027 [US1] Create UnifiedRealityModel service class in api/services/unified_reality_model.py
- [ ] T028 [US1] Implement state container with BeliefState, ActiveInferenceState, MetacognitiveParticle references
- [ ] T029 [US1] Implement coherence computation using cosine similarity on embeddings (FR-002)
- [ ] T030 [US1] Implement bound vs transparent process tracking (FR-003)
- [ ] T031 [US1] Implement epistemic affordances derivation from current state (FR-004)
- [ ] T032 [US1] Add EventBus integration for state change notifications
- [ ] T033 [US1] Run tests: pytest tests/unit/test_unified_reality_model.py -v

**Checkpoint**: User Story 1 complete - unified reality model can be tested independently

---

## Phase 4: User Story 2 - Bayesian Binding Selection (Priority: P1)

**Goal**: Precision-weighted inferential competition determining what enters consciousness

**Independent Test**: Present multiple competing inferences, verify binding criteria applied correctly

**Functional Requirements**: FR-005, FR-006, FR-007, FR-008

### Tests for User Story 2 (TDD - Write FIRST)

- [ ] T034 [P] [US2] Write unit tests for BayesianBinder.bind() method in tests/unit/test_bayesian_binder.py
- [ ] T035 [P] [US2] Write tests for precision threshold check in tests/unit/test_bayesian_binder.py
- [ ] T036 [P] [US2] Write tests for coherence check in tests/unit/test_bayesian_binder.py
- [ ] T037 [P] [US2] Write tests for uncertainty reduction check (FR-008) in tests/unit/test_bayesian_binder.py
- [ ] T038 [P] [US2] Write tests for binding strength calculation in tests/unit/test_bayesian_binder.py
- [ ] T039 [P] [US2] Write tests for capacity limit enforcement in tests/unit/test_bayesian_binder.py
- [ ] T040 [P] [US2] Write contract tests for /beautiful-loop/binding/evaluate endpoint in tests/contract/test_beautiful_loop_api.py

### Implementation for User Story 2

- [ ] T041 [US2] Create BayesianBinder service class in api/services/bayesian_binder.py
- [ ] T042 [US2] Implement precision check (candidate.precision >= threshold)
- [ ] T043 [US2] Implement coherence check using compute_coherence() from research.md
- [ ] T044 [US2] Implement uncertainty reduction check - reject if increases uncertainty (FR-008)
- [ ] T045 [US2] Implement binding strength = precision * coherence * max(0, uncertainty_reduction) (FR-006)
- [ ] T046 [US2] Implement capacity limit enforcement - top N by binding strength (FR-007)
- [ ] T047 [US2] Add BindingCompletedEvent emission via EventBus
- [ ] T048 [US2] Integration with UnifiedRealityModel.integrate() method
- [ ] T049 [US2] Run tests: pytest tests/unit/test_bayesian_binder.py -v

**Checkpoint**: User Story 2 complete - Bayesian binding can be tested independently

---

## Phase 5: User Story 3 - Precision Profile Forecasting (Priority: P1)

**Goal**: Proactively forecast precision levels across inference layers BEFORE processing begins

**Independent Test**: Provide context, verify precision profile generated with per-layer and per-modality weights

**Functional Requirements**: FR-009, FR-010, FR-011, FR-012

### Tests for User Story 3 (TDD - Write FIRST)

- [ ] T050 [P] [US3] Write unit tests for HyperModelService.forecast_precision_profile() in tests/unit/test_hyper_model_service.py
- [ ] T051 [P] [US3] Write tests for per-layer precision generation (FR-010) in tests/unit/test_hyper_model_service.py
- [ ] T052 [P] [US3] Write tests for per-modality precision generation (FR-011) in tests/unit/test_hyper_model_service.py
- [ ] T053 [P] [US3] Write tests for meta-precision inclusion (FR-012) in tests/unit/test_hyper_model_service.py
- [ ] T054 [P] [US3] Write performance test for <50ms forecast (SC-001) in tests/unit/test_hyper_model_service.py
- [ ] T055 [P] [US3] Write contract tests for /beautiful-loop/precision/forecast endpoint in tests/contract/test_beautiful_loop_api.py

### Implementation for User Story 3

- [ ] T056 [US3] Create HyperModelService class in api/services/hyper_model_service.py
- [ ] T057 [US3] Implement forecast_precision_profile(context, internal_states, recent_errors) method
- [ ] T058 [US3] Implement per-layer precision weight generation using EMA (FR-010)
- [ ] T059 [US3] Implement per-modality precision weight generation (FR-011)
- [ ] T060 [US3] Implement meta-precision (confidence in forecast) calculation (FR-012)
- [ ] T061 [US3] Add context embedding storage for learning
- [ ] T062 [US3] Emit PrecisionForecastEvent via EventBus
- [ ] T063 [US3] Run tests including performance: pytest tests/unit/test_hyper_model_service.py -v

**Checkpoint**: User Story 3 complete - precision forecasting can be tested independently

---

## Phase 6: User Story 4 - Second-Order Precision Learning (Priority: P2)

**Goal**: Detect precision forecast errors and update the hyper-model for improved future predictions

**Independent Test**: Provide mismatched forecasts, verify second-order error computed, verify hyper-model updates

**Functional Requirements**: FR-013, FR-014, FR-015, FR-016

### Tests for User Story 4 (TDD - Write FIRST)

- [ ] T064 [P] [US4] Write tests for compute_precision_errors() in tests/unit/test_hyper_model_service.py
- [ ] T065 [P] [US4] Write tests for error direction classification (over/under confident) in tests/unit/test_hyper_model_service.py
- [ ] T066 [P] [US4] Write tests for update_hyper_model() EMA learning in tests/unit/test_hyper_model_service.py
- [ ] T067 [P] [US4] Write tests for learning rate bounds (0.01-0.3) in tests/unit/test_hyper_model_service.py
- [ ] T068 [P] [US4] Write learning curve test (SC-003: 20% error reduction after 100 cycles) in tests/unit/test_hyper_model_service.py
- [ ] T069 [P] [US4] Write contract tests for /beautiful-loop/precision/errors endpoint in tests/contract/test_beautiful_loop_api.py

### Implementation for User Story 4

- [ ] T070 [US4] Implement compute_precision_errors(predicted_phi, actual_errors) in api/services/hyper_model_service.py
- [ ] T071 [US4] Implement error direction classification (FR-014)
- [ ] T072 [US4] Implement update_hyper_model(precision_errors) with EMA (FR-015)
- [ ] T073 [US4] Implement bounded learning rate: alpha = clip(base * surprise, 0.01, 0.3)
- [ ] T074 [US4] Implement broadcast_phi() for updated profiles (FR-016)
- [ ] T075 [US4] Emit PrecisionErrorEvent and PrecisionUpdateEvent via EventBus
- [ ] T076 [US4] Run tests including learning curve: pytest tests/unit/test_hyper_model_service.py::test_learning_curve -v

**Checkpoint**: User Story 4 complete - second-order learning can be tested independently

---

## Phase 7: User Story 5 - Epistemic Depth Measurement (Priority: P2)

**Goal**: Measure system's "awareness" of its own processing (luminosity)

**Independent Test**: Trigger different cognitive states, verify depth scores reflect expected patterns

**Functional Requirements**: FR-017, FR-018, FR-019

### Tests for User Story 5 (TDD - Write FIRST)

- [ ] T077 [P] [US5] Write tests for EpistemicFieldService in tests/unit/test_epistemic_field_service.py
- [ ] T078 [P] [US5] Write tests for recursive sharing depth tracking (FR-017) in tests/unit/test_epistemic_field_service.py
- [ ] T079 [P] [US5] Write tests for depth score computation (FR-018) in tests/unit/test_epistemic_field_service.py
- [ ] T080 [P] [US5] Write tests for aware vs transparent process distinction (FR-019) in tests/unit/test_epistemic_field_service.py
- [ ] T081 [P] [US5] Write state differentiation test (SC-005: effect size d > 0.8) in tests/unit/test_epistemic_field_service.py
- [ ] T082 [P] [US5] Write contract tests for /beautiful-loop/epistemic/state endpoint in tests/contract/test_beautiful_loop_api.py

### Implementation for User Story 5

- [ ] T083 [US5] Create EpistemicFieldService class in api/services/epistemic_field_service.py
- [ ] T084 [US5] Implement recursive sharing depth tracking (FR-017)
- [ ] T085 [US5] Implement luminosity factors: hyper_model_active, bidirectional_sharing, meta_precision_level, binding_coherence
- [ ] T086 [US5] Implement depth_score = weighted average of luminosity_factors (FR-018)
- [ ] T087 [US5] Implement aware/transparent process classification (FR-019)
- [ ] T088 [US5] Integrate with HyperModelService for hyper_model_active factor
- [ ] T089 [US5] Run tests including differentiation: pytest tests/unit/test_epistemic_field_service.py -v

**Checkpoint**: User Story 5 complete - epistemic depth can be tested independently

---

## Phase 8: User Story 6 - Beautiful Loop OODA Integration (Priority: P2)

**Goal**: Integrate 5-step beautiful loop into existing OODA cycle

**Independent Test**: Run OODA cycle, verify precision forecast at start, errors at end, hyper-model updates

**Functional Requirements**: FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027

### Tests for User Story 6 (TDD - Write FIRST)

- [ ] T090 [P] [US6] Write integration tests for enhanced OODA cycle in tests/integration/test_beautiful_loop_ooda.py
- [ ] T091 [P] [US6] Write test for precision forecast at cycle START (FR-020) in tests/integration/test_beautiful_loop_ooda.py
- [ ] T092 [P] [US6] Write test for precision application in OBSERVE/ORIENT (FR-021) in tests/integration/test_beautiful_loop_ooda.py
- [ ] T093 [P] [US6] Write test for precision error collection at cycle END (FR-022) in tests/integration/test_beautiful_loop_ooda.py
- [ ] T094 [P] [US6] Write test for hyper-model update before next cycle (FR-023) in tests/integration/test_beautiful_loop_ooda.py
- [ ] T095 [P] [US6] Write latency test (SC-006: <10% increase) in tests/integration/test_beautiful_loop_ooda.py
- [ ] T096 [P] [US6] Write regression test (SC-007: existing tests pass) in tests/integration/test_beautiful_loop_ooda.py

### Implementation for User Story 6

- [ ] T097 [US6] Add HyperModelService dependency to ConsciousnessManager in api/agents/consciousness_manager.py
- [ ] T098 [US6] Add BayesianBinder dependency to ConsciousnessManager
- [ ] T099 [US6] Add UnifiedRealityModel dependency to ConsciousnessManager
- [ ] T100 [US6] Modify _run_ooda_cycle() OBSERVE phase: add precision forecast at start (FR-020)
- [ ] T101 [US6] Modify _run_ooda_cycle() ORIENT phase: apply precision to perception (FR-021)
- [ ] T102 [US6] Modify _run_ooda_cycle() ORIENT phase: integrate Bayesian binding
- [ ] T103 [US6] Modify _run_ooda_cycle() DECIDE phase: collect precision errors (FR-022)
- [ ] T104 [US6] Modify _run_ooda_cycle() ACT phase: update hyper-model and broadcast (FR-023)
- [ ] T105 [US6] Add EventBus subscriptions for precision events
- [ ] T106 [US6] Run integration tests: pytest tests/integration/test_beautiful_loop_ooda.py -v
- [ ] T107 [US6] Run full test suite for regression check: pytest tests/ --ignore=tests/unit/test_beautiful_loop* -v

**Checkpoint**: User Story 6 complete - Beautiful Loop fully integrated with OODA

---

## Phase 9: User Story 7 - Consciousness State Modeling (Priority: P3)

**Goal**: Model different states of consciousness (focused attention, open awareness, minimal phenomenal)

**Independent Test**: Configure precision profiles for each state, verify system behavior matches expected patterns

**Functional Requirements**: (Research/exploration features - no mandatory FRs)

### Tests for User Story 7 (TDD - Write FIRST)

- [ ] T108 [P] [US7] Write tests for focused attention profile in tests/unit/test_hyper_model_service.py
- [ ] T109 [P] [US7] Write tests for open awareness profile in tests/unit/test_hyper_model_service.py
- [ ] T110 [P] [US7] Write tests for minimal phenomenal profile in tests/unit/test_hyper_model_service.py

### Implementation for User Story 7

- [ ] T111 [US7] Implement create_focused_attention_profile() in api/services/hyper_model_service.py
- [ ] T112 [US7] Implement create_open_awareness_profile() in api/services/hyper_model_service.py
- [ ] T113 [US7] Implement create_minimal_phenomenal_profile() in api/services/hyper_model_service.py
- [ ] T114 [US7] Add apply_preset_profile(preset_name) method to HyperModelService
- [ ] T115 [US7] Run tests: pytest tests/unit/test_hyper_model_service.py::test_*_profile -v

**Checkpoint**: User Story 7 complete - consciousness state presets available

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T116 [P] Add API router for Beautiful Loop endpoints in api/routers/beautiful_loop.py
- [ ] T117 [P] Register router in api/main.py
- [ ] T118 [P] Run full contract test suite: pytest tests/contract/test_beautiful_loop_api.py -v
- [ ] T119 Run coverage report: pytest --cov=api.models.beautiful_loop --cov=api.services --cov-report=term-missing --cov-fail-under=90
- [ ] T120 [P] Update quickstart.md with actual usage examples
- [ ] T121 [P] Add docstrings to all public methods following existing patterns
- [ ] T122 Run full test suite for final validation: pytest tests/ -v
- [ ] T123 Performance validation: verify SC-001 (<50ms) and SC-006 (<10% latency) across 100 cycles

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational Models) ◄── BLOCKS ALL USER STORIES
    │
    ├──────────────────────────────────────────────┐
    ▼                   ▼                   ▼      │
Phase 3 (US1)     Phase 4 (US2)     Phase 5 (US3) │ P1 Stories
    │                   │                   │      │ (can parallelize)
    └───────────────────┴───────────────────┘      │
                        │                          │
    ┌───────────────────┼───────────────────┐      │
    ▼                   ▼                   ▼      │
Phase 6 (US4)     Phase 7 (US5)     Phase 8 (US6) │ P2 Stories
    │                   │                   │      │ (US6 needs US1-5)
    └───────────────────┴───────────────────┘      │
                        │                          │
                        ▼                          │
                 Phase 9 (US7)                     │ P3 Story
                        │                          │
                        ▼                          │
                 Phase 10 (Polish)                 │
```

### User Story Dependencies

| Story | Can Start After | Notes |
|-------|-----------------|-------|
| US1 | Phase 2 | No dependencies on other stories |
| US2 | Phase 2 | Uses compute_coherence from US1, but independently testable |
| US3 | Phase 2 | No dependencies on other stories |
| US4 | US3 | Extends HyperModelService from US3 |
| US5 | Phase 2 | Uses HyperModelService but independently testable |
| US6 | US1-US5 | Integration - needs all components |
| US7 | US3 | Extends HyperModelService |

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Implementation follows test structure
3. All tests MUST pass before checkpoint

### Parallel Opportunities

**Phase 2 (all tests in parallel, then all implementations in parallel)**:
```bash
# All model tests (T007-T013) in parallel
# Then all implementations (T014-T020) in parallel
```

**P1 Stories (US1, US2, US3) can run in parallel**:
```bash
# After Phase 2 completes:
# Team A: Phase 3 (US1 - UnifiedRealityModel)
# Team B: Phase 4 (US2 - BayesianBinder)
# Team C: Phase 5 (US3 - HyperModelService)
```

**P2 Stories (US4, US5 can parallel, US6 waits)**:
```bash
# After P1 Stories complete:
# Team A: Phase 6 (US4 - Second-Order Learning)
# Team B: Phase 7 (US5 - Epistemic Depth)
# Then: Phase 8 (US6 - OODA Integration)
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational Models (CRITICAL - blocks all stories)
3. Complete Phase 3: US1 - UnifiedRealityModel
4. Complete Phase 4: US2 - BayesianBinder
5. Complete Phase 5: US3 - HyperModelService
6. **STOP and VALIDATE**: Run pytest --cov, verify >90% coverage on new code
7. Deploy/demo MVP

### Incremental Delivery

1. MVP (US1-US3) → Core Beautiful Loop functioning
2. Add US4 (Learning) → System improves over time
3. Add US5 (Epistemic Depth) → Observability into consciousness
4. Add US6 (OODA Integration) → Full integration with existing system
5. Add US7 (State Presets) → Research applications

### TDD Enforcement

**For every task group**:
1. Write ALL tests first (marked with "TDD - Write FIRST")
2. Run tests - verify they FAIL
3. Implement production code
4. Run tests - verify they PASS
5. Check coverage: `pytest --cov --cov-fail-under=90`

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[Story]** label maps task to specific user story for traceability
- SC-008 mandates TDD: tests MUST be written before implementation
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Run `pytest --cov` frequently to track coverage progress
- Target: >90% coverage on all new code

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 123 |
| Setup Tasks | 6 |
| Foundational Tasks | 15 |
| US1 Tasks | 12 |
| US2 Tasks | 16 |
| US3 Tasks | 14 |
| US4 Tasks | 13 |
| US5 Tasks | 13 |
| US6 Tasks | 18 |
| US7 Tasks | 8 |
| Polish Tasks | 8 |
| Parallel Opportunities | 67 tasks marked [P] |
| MVP Scope | US1 + US2 + US3 (47 tasks) |
