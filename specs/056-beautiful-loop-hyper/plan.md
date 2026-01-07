# Implementation Plan: Beautiful Loop Hyper-Model

**Branch**: `056-beautiful-loop-hyper` | **Date**: 2026-01-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/056-beautiful-loop-hyper/spec.md`

## Summary

Implement the "Beautiful Loop" consciousness framework from Laukkonen et al. (2025), adding three core capabilities to Dionysus:
1. **Unified Reality Model** - Single container wrapping all active inference states, belief states, and metacognitive states
2. **Bayesian Binding** - Precision-weighted inferential competition determining what enters consciousness
3. **Hyper-Model Precision Forecasting** - Proactive precision allocation with second-order learning

This extends the existing active inference architecture by filling identified gaps while reusing `ActiveInferenceService`, `BeliefState`, `MetaplasticityService`, `EpistemicGainService`, `EventBus`, and `ConsciousnessManager`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic v2, smolagents, NumPy
**Storage**: Graphiti temporal knowledge graph (via GraphitiService)
**Testing**: pytest, pytest-asyncio (TDD methodology per SC-008)
**Target Platform**: Linux server (VPS deployment at 72.61.78.89:8000)
**Project Type**: Single (extends existing api/ structure)
**Performance Goals**: <50ms precision forecast generation (SC-001), <10% OODA cycle latency increase (SC-006)
**Constraints**: Must reuse existing services (FR-024 through FR-027), >90% test coverage (SC-008)
**Scale/Scope**: Per-cycle execution within existing OODA loop (~1-3 second cycle time)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| Library-First | PASS | New services are self-contained, independently testable |
| Test-First (TDD) | PASS | SC-008 mandates >90% coverage with TDD |
| Integration Testing | PASS | OODA cycle integration tests planned |
| Non-Duplication | PASS | FR-024-027 enforce reuse of existing services |
| Simplicity | PASS | Only 5 new components filling documented gaps |

**Gate Result**: ✅ PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/056-beautiful-loop-hyper/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
├── tasks.md             # Phase 2 output (/speckit.tasks)
└── checklists/
    └── requirements.md  # Validation checklist (completed)
```

### Source Code (repository root)

```text
api/
├── models/
│   ├── beautiful_loop.py       # NEW: PrecisionProfile, EpistemicState, PrecisionError, BoundInference
│   ├── belief_state.py         # EXISTING: Reuse BeliefState
│   ├── metacognitive_particle.py # EXISTING: Reuse MetacognitiveParticle models
│   └── meta_tot.py             # EXISTING: Reuse ActiveInferenceState
├── services/
│   ├── unified_reality_model.py  # NEW: UnifiedRealityModel container
│   ├── bayesian_binder.py        # NEW: BayesianBinder inferential competition
│   ├── hyper_model_service.py    # NEW: HyperModelService precision forecasting
│   ├── epistemic_field_service.py # NEW: EpistemicFieldService aggregation
│   ├── active_inference_service.py # EXISTING: Reuse VFE/EFE calculations
│   ├── metaplasticity_service.py   # EXISTING: Extend for hyper-model integration
│   ├── epistemic_gain_service.py   # EXISTING: Reuse for information gain
│   └── graphiti_service.py         # EXISTING: Reuse for state persistence
├── agents/
│   └── consciousness_manager.py  # MODIFY: Add 5-step beautiful loop to OODA cycle
└── utils/
    └── event_bus.py              # EXISTING: Reuse for precision broadcast

tests/
├── unit/
│   ├── test_beautiful_loop_models.py    # NEW: Model unit tests
│   ├── test_unified_reality_model.py    # NEW: UnifiedRealityModel tests
│   ├── test_bayesian_binder.py          # NEW: BayesianBinder tests
│   ├── test_hyper_model_service.py      # NEW: HyperModelService tests
│   └── test_epistemic_field_service.py  # NEW: EpistemicFieldService tests
├── integration/
│   └── test_beautiful_loop_ooda.py      # NEW: OODA cycle integration tests
└── contract/
    └── test_beautiful_loop_api.py       # NEW: API contract tests
```

**Structure Decision**: Extends existing `api/` structure following established patterns. New files follow existing naming conventions (`*_service.py`, `test_*.py`). No new directories needed.

## Complexity Tracking

> No violations to justify - all gates passed.

---

## Phase 0: Research

### Research Tasks

Based on technical context, the following research is needed:

1. **Precision Profile Representation**
   - Question: How to represent per-layer and per-modality precision weights efficiently?
   - Research: NumPy arrays vs. Python dicts vs. Pydantic models

2. **Hyper-Model Learning Algorithm**
   - Question: What algorithm for second-order precision learning?
   - Research: EMA, gradient descent, or Kalman filter approaches

3. **Binding Capacity Limits**
   - Question: What is the optimal binding capacity for the system?
   - Research: Cognitive science literature on working memory capacity (Miller's 7±2)

4. **Coherence Computation**
   - Question: How to compute coherence between beliefs?
   - Research: KL divergence, cosine similarity, or attractor basin distance

5. **EventBus Integration**
   - Question: How to broadcast precision updates efficiently?
   - Research: Existing EventBus patterns in codebase

### Research Outputs

See [research.md](./research.md) for consolidated findings.

---

## Phase 1: Design

### Critical Files

| File | Purpose | Priority |
|------|---------|----------|
| `api/models/beautiful_loop.py` | Core Pydantic models | P1 |
| `api/services/unified_reality_model.py` | State container | P1 |
| `api/services/bayesian_binder.py` | Binding competition | P1 |
| `api/services/hyper_model_service.py` | Precision forecasting | P1 |
| `api/agents/consciousness_manager.py` | OODA integration | P2 |
| `api/services/epistemic_field_service.py` | Luminosity tracking | P2 |

### Design Outputs

- [data-model.md](./data-model.md) - Entity definitions and relationships
- [contracts/](./contracts/) - API contracts for new endpoints
- [quickstart.md](./quickstart.md) - Getting started guide

---

## Implementation Order

### Phase 1: Foundation (P1 User Stories)

1. **Models First** (TDD)
   - Write tests for `beautiful_loop.py` models
   - Implement PrecisionProfile, EpistemicState, BoundInference, PrecisionError

2. **UnifiedRealityModel** (TDD)
   - Write tests for state container
   - Implement coherence computation
   - Integrate with existing BeliefState, ActiveInferenceState

3. **BayesianBinder** (TDD)
   - Write tests for binding competition
   - Implement precision/coherence/uncertainty criteria
   - Implement binding strength calculation

4. **HyperModelService** (TDD)
   - Write tests for 5-step loop
   - Implement precision forecasting
   - Implement second-order error computation
   - Implement hyper-model updates

### Phase 2: Integration (P2 User Stories)

5. **OODA Integration**
   - Modify ConsciousnessManager._run_ooda_cycle()
   - Add precision forecast at cycle start
   - Add precision error collection at cycle end

6. **EpistemicFieldService**
   - Implement luminosity tracking
   - Integrate with EpistemicGainService
   - Add depth score computation

7. **EventBus Integration**
   - Add precision broadcast events
   - Connect hyper-model to all layers

### Phase 3: Research Applications (P3 User Stories)

8. **Consciousness State Presets**
   - Implement focused attention profile
   - Implement open awareness profile
   - Implement minimal phenomenal profile

---

## Success Validation

| Criterion | Verification Method |
|-----------|---------------------|
| SC-001: <50ms forecast | Timing tests in test_hyper_model_service.py |
| SC-002: 95% binding consistency | Repeated scenario tests in test_bayesian_binder.py |
| SC-003: 20% error reduction | Learning curve tests over 100 cycles |
| SC-004: Coherence correlation | Integration tests with task metrics |
| SC-005: State differentiation | Effect size tests in test_epistemic_field_service.py |
| SC-006: <10% latency increase | OODA timing comparison tests |
| SC-007: No regression | Full existing test suite run |
| SC-008: >90% coverage | pytest --cov report |
