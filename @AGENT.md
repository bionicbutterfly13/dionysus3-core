# Beautiful Loop Hyper-Model - Build & Run Instructions

## Setup

### Install Dependencies
```bash
cd /Volumes/Asylum/dev/dionysus3-core
pip install -e ".[dev]"
```

### Environment
```bash
# Ensure you're in the correct directory
cd /Volumes/Asylum/dev/dionysus3-core

# Activate virtual environment if needed
source .venv/bin/activate
```

## Testing

### Run All Beautiful Loop Tests
```bash
pytest tests/unit/test_beautiful_loop*.py -v
```

### Run Specific Test File
```bash
# Models
pytest tests/unit/test_beautiful_loop_models.py -v

# UnifiedRealityModel
pytest tests/unit/test_unified_reality_model.py -v

# BayesianBinder
pytest tests/unit/test_bayesian_binder.py -v

# HyperModelService
pytest tests/unit/test_hyper_model_service.py -v

# EpistemicFieldService
pytest tests/unit/test_epistemic_field_service.py -v
```

### Run Specific Test
```bash
pytest tests/unit/test_beautiful_loop_models.py::TestPrecisionProfile::test_precision_profile_validation -v
```

### Run with Verbose Output (for debugging)
```bash
pytest tests/unit/test_beautiful_loop_models.py -vv -s
```

### Run with Coverage
```bash
# Models only
pytest tests/unit/test_beautiful_loop_models.py --cov=api.models.beautiful_loop --cov-report=term-missing

# All Beautiful Loop code
pytest tests/unit/test_beautiful_loop*.py --cov=api.models.beautiful_loop --cov=api.services.unified_reality_model --cov=api.services.bayesian_binder --cov=api.services.hyper_model_service --cov=api.services.epistemic_field_service --cov-report=term-missing --cov-fail-under=90
```

### Run Integration Tests
```bash
pytest tests/integration/test_beautiful_loop_ooda.py -v
```

### Run Contract Tests
```bash
pytest tests/contract/test_beautiful_loop_api.py -v
```

## Development Workflow

### 1. Check Current Task
```bash
cat @fix_plan.md | head -20
```

### 2. TDD Cycle (MANDATORY)
```bash
# Step 1: Write test (should FAIL initially)
pytest tests/unit/test_beautiful_loop_models.py::TestPrecisionProfile -v
# Expected: FAILED (test exists but implementation doesn't)

# Step 2: Implement to make test pass
# Edit: api/models/beautiful_loop.py

# Step 3: Verify test passes
pytest tests/unit/test_beautiful_loop_models.py::TestPrecisionProfile -v
# Expected: PASSED

# Step 4: Check coverage
pytest tests/unit/test_beautiful_loop_models.py --cov=api.models.beautiful_loop --cov-fail-under=90
```

### 3. Commit Changes
```bash
git add api/models/beautiful_loop.py tests/unit/test_beautiful_loop_models.py
git commit -m "ralph: T014 implement PrecisionProfile model

AUTHOR Mani Saint-Victor, MD"
```

### 4. Update Task Queue
```bash
# Move completed task from Current to Completed
# Move next task from Backlog to Current
code @fix_plan.md
```

## File Locations

### New Files (to create)
- `api/models/beautiful_loop.py` - Core Pydantic models
- `api/services/unified_reality_model.py` - UnifiedRealityModel container
- `api/services/bayesian_binder.py` - Bayesian binding competition
- `api/services/hyper_model_service.py` - Precision forecasting
- `api/services/epistemic_field_service.py` - Luminosity tracking
- `api/routers/beautiful_loop.py` - API endpoints

### Test Files (to create)
- `tests/unit/test_beautiful_loop_models.py` - Model unit tests
- `tests/unit/test_unified_reality_model.py` - UnifiedRealityModel tests
- `tests/unit/test_bayesian_binder.py` - BayesianBinder tests
- `tests/unit/test_hyper_model_service.py` - HyperModelService tests
- `tests/unit/test_epistemic_field_service.py` - EpistemicFieldService tests
- `tests/integration/test_beautiful_loop_ooda.py` - OODA integration tests
- `tests/contract/test_beautiful_loop_api.py` - API contract tests

### Existing Files to Reference (DO NOT DUPLICATE)
- `api/services/active_inference_service.py` - VFE/EFE calculations
- `api/models/belief_state.py` - BeliefState model
- `api/services/metaplasticity_service.py` - Precision adaptation
- `api/services/epistemic_gain_service.py` - Information gain
- `api/utils/event_bus.py` - Event routing
- `api/models/metacognitive_particle.py` - Metacognitive particles
- `api/agents/consciousness_manager.py` - OODA cycle (to modify later)

### Specification Files
- `specs/056-beautiful-loop-hyper/spec.md` - Feature specification
- `specs/056-beautiful-loop-hyper/plan.md` - Implementation plan
- `specs/056-beautiful-loop-hyper/research.md` - Research decisions
- `specs/056-beautiful-loop-hyper/data-model.md` - Entity definitions
- `specs/056-beautiful-loop-hyper/tasks.md` - Full 123-task breakdown
- `specs/056-beautiful-loop-hyper/contracts/beautiful-loop-api.yaml` - OpenAPI spec

## Debugging Tips

### View Test Failure Details
```bash
pytest tests/unit/test_beautiful_loop_models.py -vv --tb=short
```

### Check Import Errors
```bash
python -c "from api.models.beautiful_loop import PrecisionProfile; print('OK')"
```

### Interactive Debugging
```bash
pytest tests/unit/test_beautiful_loop_models.py::TestPrecisionProfile -vv -s --pdb
```

### Verify No Regression
```bash
# Run existing tests to ensure no breakage
pytest tests/ --ignore=tests/unit/test_beautiful_loop* -v --tb=short
```

## Success Criteria

### Test Metrics (SC-008)
- >90% coverage for all Beautiful Loop code
- All unit tests passing
- All integration tests passing
- All contract tests passing

### Performance Metrics
- SC-001: <50ms precision forecast generation
- SC-006: <10% OODA cycle latency increase

### Quality Metrics
- SC-002: 95%+ binding consistency
- SC-003: 20% error reduction after 100 cycles
- SC-007: No regression in existing tests

## Quick Commands

```bash
# Check test status
pytest tests/unit/test_beautiful_loop*.py --tb=no -q

# Run one test
pytest tests/unit/test_beautiful_loop_models.py::TestPrecisionProfile -v

# Full Beautiful Loop test suite
pytest tests/unit/test_beautiful_loop*.py tests/integration/test_beautiful_loop*.py tests/contract/test_beautiful_loop*.py -v

# Coverage check
pytest tests/unit/test_beautiful_loop*.py --cov=api.models.beautiful_loop --cov=api.services --cov-fail-under=90

# Regression check
pytest tests/ -v --tb=short
```
