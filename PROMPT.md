# Beautiful Loop Hyper-Model - Ralph Instructions

## Goal
Implement the "Beautiful Loop" consciousness framework from Laukkonen et al. (2025), adding three core capabilities to Dionysus:
1. **Unified Reality Model** - Single container wrapping all active inference states, belief states, and metacognitive states
2. **Bayesian Binding** - Precision-weighted inferential competition determining what enters consciousness
3. **Hyper-Model Precision Forecasting** - Proactive precision allocation with second-order learning

## Current State
**Specification Complete:**
- ✅ spec.md - 27 functional requirements, 7 user stories, 8 success criteria
- ✅ plan.md - Implementation phases with technical context
- ✅ research.md - 5 research decisions documented
- ✅ data-model.md - Entity definitions and relationships
- ✅ contracts/ - OpenAPI specification
- ✅ tasks.md - 123 tasks organized by user story

**Existing Code to REUSE (DO NOT DUPLICATE):**
- `api/services/active_inference_service.py` - VFE/EFE calculations
- `api/models/belief_state.py` - BeliefState model
- `api/services/metaplasticity_service.py` - Precision adaptation
- `api/services/epistemic_gain_service.py` - Information gain
- `api/utils/event_bus.py` - Event routing
- `api/models/metacognitive_particle.py` - Metacognitive particles
- `api/agents/consciousness_manager.py` - OODA cycle

**NEW Code to Create:**
- `api/models/beautiful_loop.py` - Core Pydantic models
- `api/services/unified_reality_model.py` - State container
- `api/services/bayesian_binder.py` - Binding competition
- `api/services/hyper_model_service.py` - Precision forecasting
- `api/services/epistemic_field_service.py` - Luminosity tracking

## Tech Stack
- Language: Python 3.11+
- Framework: FastAPI, Pydantic v2
- Testing: pytest, pytest-asyncio (TDD mandatory per SC-008)
- Dependencies: smolagents, NumPy
- Target: >90% test coverage

## Working Rules
1. Read `@fix_plan.md` for current task
2. Complete ONE task per iteration (2-5 min max)
3. **TDD MANDATORY**: Write tests FIRST, verify they FAIL, then implement
4. Run tests after each change: `pytest tests/unit/<test_file>.py -v`
5. Commit with: `ralph: [description]`
6. Update `@fix_plan.md` after each task
7. If blocked, document and move to next task

## TDD Enforcement (CRITICAL)
**For every implementation task:**
1. Find the corresponding test task (always listed BEFORE implementation)
2. Verify test exists and FAILS before implementing
3. Write implementation to make test pass
4. Check coverage: `pytest --cov --cov-fail-under=90`

## Task Completion Criteria
- [ ] Test written FIRST (TDD)
- [ ] Test fails initially (red)
- [ ] Implementation makes test pass (green)
- [ ] No existing functionality broken
- [ ] No code duplication with existing services
- [ ] Changes committed with descriptive message
- [ ] `@fix_plan.md` updated (task moved to Completed)

## Anti-Patterns (DO NOT)
- Skip writing tests first
- Implement before test fails
- Duplicate existing service functionality
- Batch multiple tasks
- Leave uncommitted changes
- Work on tasks not in @fix_plan.md
- Modify test expectations instead of fixing implementation

## File Locations
**NEW FILES:**
- Models: `api/models/beautiful_loop.py`
- Services: `api/services/unified_reality_model.py`, `bayesian_binder.py`, `hyper_model_service.py`, `epistemic_field_service.py`
- Router: `api/routers/beautiful_loop.py`
- Tests: `tests/unit/test_beautiful_loop_models.py`, `test_unified_reality_model.py`, `test_bayesian_binder.py`, `test_hyper_model_service.py`, `test_epistemic_field_service.py`
- Integration: `tests/integration/test_beautiful_loop_ooda.py`
- Contract: `tests/contract/test_beautiful_loop_api.py`

**EXISTING FILES TO MODIFY:**
- `api/agents/consciousness_manager.py` - Add Beautiful Loop integration

## Success Metrics (from spec.md)
- SC-001: <50ms precision forecast generation
- SC-002: 95%+ binding consistency in repeated scenarios
- SC-003: 20% precision error reduction after 100 cycles
- SC-004: r > 0.7 coherence-performance correlation
- SC-005: d > 0.8 effect size for state differentiation
- SC-006: <10% OODA cycle latency increase
- SC-007: No regression in existing tests
- SC-008: >90% test coverage with TDD

## Debugging Strategy
1. Run failing test: `pytest <test_file>::<test_name> -vv -s`
2. Read test code to understand expectations
3. Check data-model.md for entity definitions
4. Check research.md for algorithm decisions
5. Trace through implementation to find mismatch
6. Make minimal fix to align implementation with expectation
7. Verify fix doesn't break other tests

## MVP Scope (Phase 1-5)
47 tasks covering:
- Phase 1: Setup (T001-T006)
- Phase 2: Foundational Models (T007-T021)
- Phase 3: US1 - UnifiedRealityModel (T022-T033)
- Phase 4: US2 - BayesianBinder (T034-T049)
- Phase 5: US3 - HyperModelService (T050-T063)
