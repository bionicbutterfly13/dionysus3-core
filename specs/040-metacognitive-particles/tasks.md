# Tasks: Metacognitive Particles Integration

**Input**: Design documents from `/specs/040-metacognitive-particles/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/metacognitive_api.yaml

**Tests**: Integration tests included as specified in FR-021, FR-022, FR-023.

**Organization**: Tasks grouped by user story to enable independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Include exact file paths in descriptions

## Path Conventions

- **API**: `api/` at repository root
- **Tests**: `tests/unit/`, `tests/integration/`
- **Specs**: `specs/040-metacognitive-particles/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [x] T001 Add scipy to requirements.txt if not present
- [x] T002 [P] Verify numpy is available in environment
- [x] T003 [P] Verify existing infrastructure: api/models/markov_blanket.py, api/agents/metacognition_agent.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and enums that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create ParticleType enum in api/models/metacognitive_particle.py (COGNITIVE, PASSIVE_METACOGNITIVE, ACTIVE_METACOGNITIVE, STRANGE_METACOGNITIVE, NESTED_N_LEVEL)
- [x] T005 Create MentalActionType enum in api/models/metacognitive_particle.py (PRECISION_DELTA, SET_PRECISION, FOCUS_TARGET, SPOTLIGHT_PRECISION)
- [x] T006 [P] Create MetacognitiveParticle model in api/models/metacognitive_particle.py (id, type, level, has_agency, agent_id, blanket_id, belief_state_id, parent_id)
- [x] T007 [P] Create BeliefState model in api/models/belief_state.py (mean, precision, entropy, dimension) with computed entropy property
- [x] T008 [P] Create precision bounds utilities in api/models/belief_state.py (MIN_PRECISION=0.01, MAX_PRECISION=100.0, clamp_precision())
- [x] T009 Create MarkovBlanketPartition helper in api/models/markov_blanket.py (external_paths, sensory_paths, active_paths, internal_paths)
- [x] T010 Create API router scaffold in api/routers/metacognition.py with FastAPI router registration

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Particle Classification (Priority: P1) MVP

**Goal**: Classify cognitive processes into particle types based on Markov blanket structure

**Independent Test**: POST to /api/v1/metacognition/classify with blanket structure returns particle_type and confidence

### Tests for User Story 1

- [x] T011 [P] [US1] Unit test for ParticleClassifier in tests/unit/test_particle_classifier.py
- [x] T012 [P] [US1] Integration test for classification endpoint in tests/integration/test_metacognitive_flow.py

### Implementation for User Story 1

- [x] T013 [US1] Create ParticleClassifier service in api/services/particle_classifier.py
- [x] T014 [US1] Implement has_belief_mapping() check in ParticleClassifier (FR-001)
- [x] T015 [US1] Implement has_internal_blanket() check in ParticleClassifier (FR-002)
- [x] T016 [US1] Implement has_active_paths_to_internal() check in ParticleClassifier
- [x] T017 [US1] Implement is_strange_configuration() check in ParticleClassifier (FR-003)
- [x] T018 [US1] Implement count_nested_blankets() for N-level detection in ParticleClassifier
- [x] T019 [US1] Add confidence score calculation based on blanket clarity
- [x] T020 [US1] Implement POST /api/v1/metacognition/classify endpoint in api/routers/metacognition.py
- [x] T021 [US1] Add request/response validation per contracts/metacognitive_api.yaml

**Checkpoint**: Classification system functional - can classify any agent's blanket structure

---

## Phase 4: User Story 2 - Mental Actions (Priority: P1) MVP

**Goal**: Execute mental actions that modulate lower-level precision

**Independent Test**: POST to /api/v1/metacognition/mental-action returns prior_state and new_state with applied modulation

### Tests for User Story 2

- [x] T022 [P] [US2] Unit test for mental action execution in tests/unit/test_mental_actions.py
- [x] T023 [P] [US2] Integration test for mental action endpoint in tests/integration/test_metacognitive_flow.py

### Implementation for User Story 2

- [x] T024 [US2] Create MentalAction model in api/models/mental_action.py (action_type, source_agent, target_agent, modulation_params, prior_state, new_state)
- [x] T025 [US2] Extend MetacognitionAgent.mental_action() to support precision_delta and set_precision (FR-004, FR-005)
- [x] T026 [US2] Implement hierarchy validation (higher cannot target lower) with 403 error (FR-007)
- [x] T027 [US2] Add prior_state capture before modulation (FR-006)
- [x] T028 [US2] Add new_state capture after modulation (FR-006)
- [x] T029 [US2] Implement POST /api/v1/metacognition/mental-action endpoint in api/routers/metacognition.py
- [x] T030 [US2] Add logging for all mental action executions

**Checkpoint**: Mental actions functional - can modulate any agent's precision

---

## Phase 5: User Story 3 - Sense of Agency (Priority: P2)

**Goal**: Compute sense of agency strength using KL divergence

**Independent Test**: GET /api/v1/metacognition/agency/{agent_id} returns agency_strength as float

### Tests for User Story 3

- [x] T031 [P] [US3] Unit test for KL divergence calculation in tests/unit/test_agency_service.py
- [x] T032 [P] [US3] Integration test for agency endpoint in tests/integration/test_metacognitive_flow.py

### Implementation for User Story 3

- [x] T033 [US3] Create AgencyService in api/services/agency_service.py
- [x] T034 [US3] Implement compute_agency_strength() using scipy.stats.entropy for discrete case (FR-008)
- [x] T035 [US3] Implement kl_divergence_gaussian() for continuous case using analytical formula (FR-008)
- [x] T036 [US3] Implement has_agency() threshold check (default threshold=1e-6) (FR-009)
- [x] T037 [US3] Add cognitive particle bypass (return 0.0 for ParticleType.COGNITIVE) (FR-010)
- [x] T038 [US3] Implement GET /api/v1/metacognition/agency/{agent_id} endpoint in api/routers/metacognition.py
- [x] T039 [US3] Ensure <100ms response time per SC-001 - Achieved 2.2ms avg

**Checkpoint**: Agency computation functional - can measure any agent's sense of agency

---

## Phase 6: User Story 4 - Epistemic Gain Detection (Priority: P2)

**Goal**: Detect "Aha!" moments when uncertainty significantly reduces

**Independent Test**: POST to /api/v1/metacognition/epistemic-gain/check with prior/posterior beliefs returns gain event if threshold exceeded

### Tests for User Story 4

- [x] T040 [P] [US4] Unit test for epistemic gain detection in tests/unit/test_epistemic_gain.py
- [x] T041 [P] [US4] Integration test for gain check endpoint in tests/integration/test_metacognitive_flow.py

### Implementation for User Story 4

- [x] T042 [US4] Create EpistemicGainEvent model in api/models/epistemic_gain.py (magnitude, prior_entropy, posterior_entropy, noetic_quality)
- [x] T043 [US4] Create EpistemicGainService in api/services/epistemic_gain_service.py
- [x] T044 [US4] Implement check_gain() with configurable threshold (default 0.3) (FR-011)
- [x] T045 [US4] Implement magnitude calculation: (prior_entropy - posterior_entropy) / prior_entropy (FR-012)
- [x] T046 [US4] Implement noetic_quality detection (certainty without proportional evidence) (FR-013)
- [x] T047 [US4] Add adaptive threshold support via EPISTEMIC_GAIN_ADAPTIVE env var (FR-014)
- [x] T048 [US4] Implement POST /api/v1/metacognition/epistemic-gain/check endpoint in api/routers/metacognition.py
- [x] T049 [US4] Ensure <50ms response time per SC-003 - Achieved 2.4ms avg

**Checkpoint**: Epistemic gain detection functional - can identify learning moments

---

## Phase 7: User Story 5 - Cognitive Core (Priority: P3)

**Goal**: Enforce maximum nesting depth for metacognitive hierarchies

**Independent Test**: Attempt to create level > MAX_DEPTH raises CognitiveCoreViolation error

### Tests for User Story 5

- [x] T050 [P] [US5] Unit test for cognitive core enforcement in tests/unit/test_cognitive_core.py

### Implementation for User Story 5

- [x] T051 [US5] Create CognitiveCoreViolation exception in api/models/metacognitive_particle.py
- [x] T052 [US5] Implement enforce_cognitive_core() validator in MetacognitiveParticle (FR-015)
- [x] T053 [US5] Add MAX_NESTING_DEPTH env var support (default 5) (FR-016)
- [x] T054 [US5] Add validation in ParticleClassifier for nested_n_level type (FR-017)
- [x] T055 [US5] Add clear error message: "Cannot create metacognitive level N+1. Cognitive core reached."

**Checkpoint**: Cognitive core enforced - prevents infinite metacognitive regress

---

## Phase 8: User Story 6 - Procedural Metacognition (Priority: P3)

**Goal**: Monitor and control cognitive processes for self-regulation

**Independent Test**: GET /api/v1/metacognition/monitoring/{agent_id} returns CognitiveAssessment with progress, confidence, issues

### Tests for User Story 6

- [x] T056 [P] [US6] Unit test for monitoring in tests/unit/test_procedural_metacognition.py
- [x] T057 [P] [US6] Integration test for monitoring/control endpoints in tests/integration/test_metacognitive_flow.py

### Implementation for User Story 6

- [x] T058 [US6] Create CognitiveAssessment model in api/models/cognitive_assessment.py (progress, confidence, prediction_error, issues, recommendations)
- [x] T059 [US6] Create ProceduralMetacognition service in api/services/procedural_metacognition.py
- [x] T060 [US6] Implement monitor() function for non-invasive assessment (FR-018)
- [x] T061 [US6] Implement issue detection: HIGH_PREDICTION_ERROR, LOW_CONFIDENCE, STALLED_PROGRESS, ATTENTION_SCATTERED
- [x] T062 [US6] Implement control() function returning recommended MentalActions (FR-019)
- [x] T063 [US6] Add observable events for logging (FR-020)
- [x] T064 [US6] Implement GET /api/v1/metacognition/monitoring/{agent_id} endpoint in api/routers/metacognition.py
- [x] T065 [US6] Implement POST /api/v1/metacognition/control endpoint in api/routers/metacognition.py

**Checkpoint**: Procedural metacognition functional - agents can self-regulate

---

## Phase 9: Integration & Bridge

**Purpose**: Connect to ThoughtSeed system (Spec 038)

- [x] T066 Create ThoughtSeedParticleBridge in api/services/thoughtseed_particle_bridge.py
- [x] T067 Implement thoughtseed_to_particle() conversion (FR-021)
- [x] T068 Implement particle_to_thoughtseed() conversion (FR-021)
- [x] T069 Add round-trip consistency validation
- [x] T070 [P] Integration test for bridge in tests/integration/test_thoughtseed_particle_bridge.py

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [x] T071 [P] Add comprehensive docstrings to all new services
- [x] T072 [P] Add type hints throughout new code
- [x] T073 Run quickstart.md validation - verify all examples work
- [x] T074 Validate API contract compliance with contracts/metacognitive_api.yaml
- [x] T075 Performance validation: all endpoints <200ms (SC-006) - Achieved <7ms avg
- [ ] T076 [P] Add Neo4j indexes from data-model.md if using Graphiti persistence

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational completion
  - US1 (Classification) and US2 (Mental Actions) can run in parallel
  - US3 (Agency) depends on US1 (needs ParticleClassifier)
  - US4 (Epistemic Gain) depends on BeliefState model only
  - US5 (Cognitive Core) depends on US1 (ParticleClassifier integration)
  - US6 (Procedural) depends on US2 (uses MentalAction)
- **Integration (Phase 9)**: Depends on US1 and existing ThoughtSeed system
- **Polish (Phase 10)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 2 (Foundational)
    │
    ├──► US1 (Classification) ──┬──► US3 (Agency)
    │                           │
    │                           └──► US5 (Cognitive Core)
    │
    ├──► US2 (Mental Actions) ────► US6 (Procedural)
    │
    └──► US4 (Epistemic Gain)
```

### Parallel Opportunities

- T002, T003 (Setup verification)
- T006, T007, T008 (Foundation models)
- T011, T012 (US1 tests)
- T022, T023 (US2 tests)
- T031, T032 (US3 tests)
- T040, T041 (US4 tests)
- US1 and US2 can proceed in parallel after Foundation
- US4 can proceed in parallel with US1, US2

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Classification)
4. Complete Phase 4: User Story 2 (Mental Actions)
5. **VALIDATE**: Test classification and mental actions independently
6. Deploy/demo if ready

### Full Feature Delivery

1. MVP (above)
2. Add US3 (Agency) + US4 (Epistemic Gain) in parallel
3. Add US5 (Cognitive Core) + US6 (Procedural)
4. Add Phase 9 (ThoughtSeed Bridge)
5. Phase 10 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story independently completable and testable
- Commit after each task or logical group
- Total: 76 tasks across 10 phases
- Estimated effort: ~30 hours (3-4 days focused work)
