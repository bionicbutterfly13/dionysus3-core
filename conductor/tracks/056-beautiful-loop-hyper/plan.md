# Track Plan: Beautiful Loop Hyper-Model Implementation

**Track ID**: 056-beautiful-loop-hyper
**Status**: Planned (0%)
**TDD Mandate**: Tests MUST be written BEFORE implementation per SC-008 (>90% coverage)

---

## Phase 1: Setup

**Goal**: Project initialization and dependency verification

- [ ] **Task 1.1**: Verify existing dependencies in pyproject.toml (FastAPI, Pydantic v2, smolagents, NumPy)
- [ ] **Task 1.2**: Verify EventBus exists in `api/utils/event_bus.py`
- [ ] **Task 1.3**: Verify ActiveInferenceService reusable in `api/services/active_inference_service.py`
- [ ] **Task 1.4**: Verify BeliefState model in `api/models/belief_state.py`
- [ ] **Task 1.5**: Verify MetaplasticityService in `api/services/metaplasticity_service.py`
- [ ] **Task 1.6**: Create test directory structure in `tests/unit/` and `tests/integration/`

---

## Phase 2: Foundational Models (BLOCKING)

**Goal**: Core Pydantic models that ALL user stories depend on

### Tests (TDD - Write FIRST)
- [ ] **Task 2.1**: Write tests for PrecisionProfile model
- [ ] **Task 2.2**: Write tests for EpistemicState model
- [ ] **Task 2.3**: Write tests for PrecisionError model
- [ ] **Task 2.4**: Write tests for BoundInference model
- [ ] **Task 2.5**: Write tests for BindingConfig model
- [ ] **Task 2.6**: Write tests for HyperModelConfig model
- [ ] **Task 2.7**: Write tests for event types

### Implementation
- [ ] **Task 2.8**: Implement PrecisionProfile model in `api/models/beautiful_loop.py`
- [ ] **Task 2.9**: Implement EpistemicState model
- [ ] **Task 2.10**: Implement PrecisionError model
- [ ] **Task 2.11**: Implement BoundInference model
- [ ] **Task 2.12**: Implement BindingConfig model
- [ ] **Task 2.13**: Implement HyperModelConfig model
- [ ] **Task 2.14**: Implement event types
- [ ] **Task 2.15**: Run tests: `pytest tests/unit/test_beautiful_loop_models.py -v`

---

## Phase 3: US1 - Unified Consciousness State (P1)

**Goal**: Single container unifying all active inference states

### Tests (TDD)
- [ ] **Task 3.1**: Write unit tests for UnifiedRealityModel container
- [ ] **Task 3.2**: Write tests for coherence computation
- [ ] **Task 3.3**: Write tests for bound vs transparent tracking
- [ ] **Task 3.4**: Write tests for epistemic affordances
- [ ] **Task 3.5**: Write contract tests for `/beautiful-loop/reality-model`

### Implementation
- [ ] **Task 3.6**: Create UnifiedRealityModel service in `api/services/unified_reality_model.py`
- [ ] **Task 3.7**: Implement state container with BeliefState, ActiveInferenceState refs
- [ ] **Task 3.8**: Implement coherence computation (cosine similarity)
- [ ] **Task 3.9**: Implement bound vs transparent tracking
- [ ] **Task 3.10**: Implement epistemic affordances derivation
- [ ] **Task 3.11**: Add EventBus integration
- [ ] **Task 3.12**: Run tests: `pytest tests/unit/test_unified_reality_model.py -v`

---

## Phase 4: US2 - Bayesian Binding Selection (P1)

**Goal**: Precision-weighted inferential competition

### Tests (TDD)
- [ ] **Task 4.1**: Write tests for BayesianBinder.bind()
- [ ] **Task 4.2**: Write tests for precision threshold check
- [ ] **Task 4.3**: Write tests for coherence check
- [ ] **Task 4.4**: Write tests for uncertainty reduction check
- [ ] **Task 4.5**: Write tests for binding strength calculation
- [ ] **Task 4.6**: Write tests for capacity limit enforcement
- [ ] **Task 4.7**: Write contract tests for `/beautiful-loop/binding/evaluate`

### Implementation
- [ ] **Task 4.8**: Create BayesianBinder service in `api/services/bayesian_binder.py`
- [ ] **Task 4.9**: Implement precision check
- [ ] **Task 4.10**: Implement coherence check
- [ ] **Task 4.11**: Implement uncertainty reduction check (FR-008)
- [ ] **Task 4.12**: Implement binding strength calculation (FR-006)
- [ ] **Task 4.13**: Implement capacity limit enforcement (FR-007)
- [ ] **Task 4.14**: Add BindingCompletedEvent via EventBus
- [ ] **Task 4.15**: Integration with UnifiedRealityModel
- [ ] **Task 4.16**: Run tests

---

## Phase 5: US3 - Precision Profile Forecasting (P1)

**Goal**: Proactive precision allocation BEFORE processing

### Tests (TDD)
- [ ] **Task 5.1**: Write tests for HyperModelService.forecast_precision_profile()
- [ ] **Task 5.2**: Write tests for per-layer precision (FR-010)
- [ ] **Task 5.3**: Write tests for per-modality precision (FR-011)
- [ ] **Task 5.4**: Write tests for meta-precision (FR-012)
- [ ] **Task 5.5**: Write performance test (<50ms, SC-001)
- [ ] **Task 5.6**: Write contract tests for `/beautiful-loop/precision/forecast`

### Implementation
- [ ] **Task 5.7**: Create HyperModelService in `api/services/hyper_model_service.py`
- [ ] **Task 5.8**: Implement forecast_precision_profile()
- [ ] **Task 5.9**: Implement per-layer precision (EMA)
- [ ] **Task 5.10**: Implement per-modality precision
- [ ] **Task 5.11**: Implement meta-precision calculation
- [ ] **Task 5.12**: Add context embedding storage
- [ ] **Task 5.13**: Emit PrecisionForecastEvent
- [ ] **Task 5.14**: Run tests including performance

---

## Phase 6: US4 - Second-Order Precision Learning (P2)

**Goal**: Learn from precision forecast errors

### Tests (TDD)
- [ ] **Task 6.1**: Write tests for compute_precision_errors()
- [ ] **Task 6.2**: Write tests for error direction classification
- [ ] **Task 6.3**: Write tests for update_hyper_model() EMA
- [ ] **Task 6.4**: Write tests for learning rate bounds
- [ ] **Task 6.5**: Write learning curve test (SC-003: 20% reduction)
- [ ] **Task 6.6**: Write contract tests for `/beautiful-loop/precision/errors`

### Implementation
- [ ] **Task 6.7**: Implement compute_precision_errors()
- [ ] **Task 6.8**: Implement error direction classification
- [ ] **Task 6.9**: Implement update_hyper_model() with EMA
- [ ] **Task 6.10**: Implement bounded learning rate
- [ ] **Task 6.11**: Implement broadcast_phi()
- [ ] **Task 6.12**: Emit PrecisionErrorEvent and PrecisionUpdateEvent
- [ ] **Task 6.13**: Run tests including learning curve

---

## Phase 7: US5 - Epistemic Depth Measurement (P2)

**Goal**: Measure "awareness" of own processing (luminosity)

### Tests (TDD)
- [ ] **Task 7.1**: Write tests for EpistemicFieldService
- [ ] **Task 7.2**: Write tests for recursive sharing depth (FR-017)
- [ ] **Task 7.3**: Write tests for depth score computation (FR-018)
- [ ] **Task 7.4**: Write tests for aware vs transparent distinction (FR-019)
- [ ] **Task 7.5**: Write state differentiation test (SC-005: d > 0.8)
- [ ] **Task 7.6**: Write contract tests for `/beautiful-loop/epistemic/state`

### Implementation
- [ ] **Task 7.7**: Create EpistemicFieldService in `api/services/epistemic_field_service.py`
- [ ] **Task 7.8**: Implement recursive sharing depth tracking
- [ ] **Task 7.9**: Implement luminosity factors
- [ ] **Task 7.10**: Implement depth_score calculation
- [ ] **Task 7.11**: Implement aware/transparent classification
- [ ] **Task 7.12**: Integrate with HyperModelService
- [ ] **Task 7.13**: Run tests

---

## Phase 8: US6 - Beautiful Loop OODA Integration (P2)

**Goal**: Integrate 5-step beautiful loop into existing OODA cycle

### Tests (TDD)
- [ ] **Task 8.1**: Write integration tests for enhanced OODA
- [ ] **Task 8.2**: Write test for precision forecast at cycle START (FR-020)
- [ ] **Task 8.3**: Write test for precision in OBSERVE/ORIENT (FR-021)
- [ ] **Task 8.4**: Write test for error collection at cycle END (FR-022)
- [ ] **Task 8.5**: Write test for hyper-model update (FR-023)
- [ ] **Task 8.6**: Write latency test (SC-006: <10% increase)
- [ ] **Task 8.7**: Write regression test (SC-007)

### Implementation
- [ ] **Task 8.8**: Add HyperModelService to ConsciousnessManager
- [ ] **Task 8.9**: Add BayesianBinder to ConsciousnessManager
- [ ] **Task 8.10**: Add UnifiedRealityModel to ConsciousnessManager
- [ ] **Task 8.11**: Modify OBSERVE: precision forecast at start
- [ ] **Task 8.12**: Modify ORIENT: apply precision, integrate binding
- [ ] **Task 8.13**: Modify DECIDE: collect precision errors
- [ ] **Task 8.14**: Modify ACT: update hyper-model, broadcast
- [ ] **Task 8.15**: Add EventBus subscriptions
- [ ] **Task 8.16**: Run integration tests
- [ ] **Task 8.17**: Run full regression suite

---

## Phase 9: US7 - Consciousness State Modeling (P3)

**Goal**: Model different states (focused, open awareness, minimal phenomenal)

### Tests (TDD)
- [ ] **Task 9.1**: Write tests for focused attention profile
- [ ] **Task 9.2**: Write tests for open awareness profile
- [ ] **Task 9.3**: Write tests for minimal phenomenal profile

### Implementation
- [ ] **Task 9.4**: Implement create_focused_attention_profile()
- [ ] **Task 9.5**: Implement create_open_awareness_profile()
- [ ] **Task 9.6**: Implement create_minimal_phenomenal_profile()
- [ ] **Task 9.7**: Add apply_preset_profile() method
- [ ] **Task 9.8**: Run tests

---

## Phase 10: Polish & API

**Goal**: Finalize endpoints and documentation

- [ ] **Task 10.1**: Add API router in `api/routers/beautiful_loop.py`
- [ ] **Task 10.2**: Register router in `api/main.py`
- [ ] **Task 10.3**: Run full contract test suite
- [ ] **Task 10.4**: Run coverage report: `pytest --cov --cov-fail-under=90`
- [ ] **Task 10.5**: Update quickstart.md
- [ ] **Task 10.6**: Add docstrings to public methods
- [ ] **Task 10.7**: Run full test suite for final validation
- [ ] **Task 10.8**: Performance validation (SC-001, SC-006)

---

## Summary

| Phase | Tasks | MVP? |
|-------|-------|------|
| 1. Setup | 6 | Yes |
| 2. Foundational Models | 15 | Yes |
| 3. US1 Unified State | 12 | Yes |
| 4. US2 Bayesian Binding | 16 | Yes |
| 5. US3 Precision Forecasting | 14 | Yes |
| 6. US4 Learning | 13 | No |
| 7. US5 Epistemic Depth | 13 | No |
| 8. US6 OODA Integration | 17 | No |
| 9. US7 State Presets | 8 | No |
| 10. Polish | 8 | No |
| **Total** | **122** | MVP: 63 tasks |
