# Build & Test Commands - 057-complete-placeholder-implementations

## Environment Setup

```bash
# Ensure you're on the feature branch
git checkout 057-complete-placeholder-implementations

# Verify Python environment (3.11+)
python --version

# Install dependencies if needed
pip install -r requirements.txt

# Verify pytest installed
pytest --version
```

## Test Commands

### Run Specific Test Files
```bash
# Meta-evolution service (P1)
python -m pytest api/services/test_meta_evolution_service.py -v

# Meta-ToT engine (P1)
python -m pytest tests/unit/test_meta_tot.py -v

# EpistemicFieldService (P2)
python -m pytest tests/unit/test_epistemic_field_service.py -v

# Beautiful Loop OODA integration (P2)
python -m pytest tests/integration/test_beautiful_loop_ooda.py -v

# All unit tests
python -m pytest tests/unit/ -v

# All integration tests
python -m pytest tests/integration/ -v

# Full test suite (regression check)
python -m pytest tests/ -v
```

### Run Tests with Coverage

```bash
# Coverage for specific service
python -m pytest tests/unit/test_epistemic_field_service.py \
  --cov=api/services/epistemic_field_service \
  --cov-report=term-missing \
  -v

# Coverage for meta-evolution
python -m pytest api/services/test_meta_evolution_service.py \
  --cov=api/services/meta_evolution_service \
  --cov-report=term-missing \
  -v

# Coverage for all new/modified code
python -m pytest tests/ \
  --cov=api/services/meta_evolution_service \
  --cov=api/core/engine/meta_tot \
  --cov=api/services/epistemic_field_service \
  --cov-report=term-missing \
  --cov-report=html \
  -v

# View HTML coverage report
open htmlcov/index.html
```

### Run Tests with Markers

```bash
# Run only async tests
python -m pytest tests/ -m asyncio -v

# Run only P1 tests (if marked)
python -m pytest tests/ -m p1 -v

# Skip slow integration tests
python -m pytest tests/ -m "not slow" -v
```

### Test Output Options

```bash
# Verbose output with test names
python -m pytest tests/ -v

# Show local variables on failure
python -m pytest tests/ -l

# Stop on first failure
python -m pytest tests/ -x

# Show print statements
python -m pytest tests/ -s

# Show warnings
python -m pytest tests/ -W all
```

## Manual Verification Scripts

### Test Meta-Evolution Metrics (SC-001)
```bash
# Run script to capture 10 system moments and verify variance
python scripts/verify_energy_variance.py
# Expected: energy_level variance >0, not all 100.0
```

### Test Active Inference Scoring (SC-002)
```bash
# Run thoughtseed competition with annotated test cases
python scripts/verify_thoughtseed_selection.py
# Expected: >70% alignment with optimal paths
```

### Test GHL Email Sync (SC-006)
```bash
# Run GHL sync script
python scripts/ghl_sync.py
# Expected: 8+ emails retrieved in <30 seconds
```

### Test Metacognition Storage (SC-007)
```bash
# Run storage script and verify persistence
python scripts/store_metacognition_memory.py
# Then query Graphiti to verify 6 entities + 7 relationships
```

## Performance Testing

### Measure Beautiful Loop Overhead (SC-004)
```bash
# Baseline OODA cycle time (without Beautiful Loop)
python scripts/benchmark_ooda_baseline.py

# OODA cycle time with Beautiful Loop
python scripts/benchmark_ooda_with_beautiful_loop.py

# Compare results - overhead should be <10%
```

### Measure Test Execution Time
```bash
# Time all tests
time python -m pytest tests/ -v

# Profile slow tests
python -m pytest tests/ --durations=10
```

## Code Quality Checks

### Linting (if configured)
```bash
# Run flake8
flake8 api/services/epistemic_field_service.py

# Run black (formatting)
black --check api/services/

# Run mypy (type checking)
mypy api/services/epistemic_field_service.py
```

### Check for TODOs/Skips (SC-009)
```bash
# Find any remaining pytest.skip()
grep -r "pytest.skip" tests/

# Find any TODO comments in modified files
grep -r "TODO" api/services/meta_evolution_service.py
grep -r "TODO" api/core/engine/meta_tot.py
grep -r "TODO" api/services/epistemic_field_service.py

# Expected: Zero results after feature completion
```

## Git Workflow

### Commit After Each Task
```bash
# Stage changes
git add <files>

# Commit with conventional format
git commit -m "test: add epistemic field depth scoring test"
git commit -m "feat: implement real basin count query"
git commit -m "fix: handle None return from active inference wrapper"

# Push to remote
git push origin 057-complete-placeholder-implementations
```

### Check Status
```bash
# View uncommitted changes
git status

# View diff
git diff

# View commit history
git log --oneline -10
```

## Debugging

### Run Tests with Debugger
```bash
# Run specific test with pdb
python -m pytest tests/unit/test_epistemic_field_service.py::TestEpistemicFieldService::test_get_epistemic_state -v --pdb

# Drop into debugger on failure
python -m pytest tests/ --pdb -x
```

### Check Service Health
```bash
# Verify Graphiti service
python -c "from api.services.graphiti_service import get_graphiti_service; import asyncio; asyncio.run(get_graphiti_service())"

# Verify active inference wrapper
python -c "from api.core.engine.active_inference import get_active_inference_wrapper; wrapper = get_active_inference_wrapper(); print(wrapper)"

# Check multi-tier service
python -c "from api.services.multi_tier_service import MultiTierMemoryService; svc = MultiTierMemoryService(); print(svc)"
```

### Check Environment Variables
```bash
# Verify GHL credentials
echo $GHL_API_KEY
echo $LOCATION_ID

# Verify database connections
echo $NEO4J_URI
```

## CI/CD Commands (if applicable)

```bash
# Run tests exactly as CI does
python -m pytest tests/ --cov=api --cov-report=xml --cov-report=term-missing -v

# Generate coverage badge data
coverage report --format=total
```

## Quick Reference

**Most Common Commands During Development:**
```bash
# 1. Run relevant test file
python -m pytest tests/unit/test_epistemic_field_service.py -v

# 2. Check coverage
python -m pytest tests/unit/test_epistemic_field_service.py --cov=api/services/epistemic_field_service --cov-report=term-missing -v

# 3. Run full suite (regression check)
python -m pytest tests/ -v

# 4. Commit
git add . && git commit -m "test: add epistemic depth test"

# 5. Update @fix_plan.md
```

## Exit Validation Checklist

Before marking feature complete, run:
```bash
# 1. All tests pass
python -m pytest tests/ -v

# 2. Coverage >90% for new code
python -m pytest tests/ --cov=api --cov-report=term-missing | grep -E "(meta_evolution|meta_tot|epistemic_field)"

# 3. No pytest.skip() in modified tests
grep -r "pytest.skip" tests/unit/test_epistemic_field_service.py tests/integration/test_beautiful_loop_ooda.py

# 4. No TODO in modified code
grep -r "TODO" api/services/meta_evolution_service.py api/core/engine/meta_tot.py

# 5. Manual success criteria validation
python scripts/validate_success_criteria.py

# Expected: All checks pass, ready for PR
```
