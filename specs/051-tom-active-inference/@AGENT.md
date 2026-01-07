# Build & Run Instructions - Feature 051

## Project Root
```bash
cd /Volumes/Asylum/dev/dionysus3-core
```

## Environment Setup
```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # or your venv path

# Install dependencies (if needed)
pip install -r requirements.txt

# Verify Graphiti connection
python -c "from api.services.graphiti_service import get_graphiti_service; import asyncio; asyncio.run(get_graphiti_service())"
```

## Build Commands
```bash
# No explicit build step (Python interpreted)
# Type checking (optional)
mypy api/services/tom_*.py --ignore-missing-imports

# Linting (optional)
black api/services/tom_*.py api/models/tom_*.py --check
```

## Test Commands

### Run All ToM Tests
```bash
python -m pytest tests/unit/test_tom_*.py -v
```

### Run Specific Test File
```bash
# ToM hypothesis generation
python -m pytest tests/unit/test_tom_hypothesis_generator.py -v

# Active inference integration
python -m pytest tests/unit/test_tom_active_inference.py -v

# Social memory
python -m pytest tests/unit/test_social_memory_integration.py -v

# Response validation
python -m pytest tests/unit/test_response_validation.py -v

# Identity coherence
python -m pytest tests/unit/test_identity_coherence_monitoring.py -v
```

### Run Specific Test
```bash
python -m pytest tests/unit/test_tom_hypothesis_generator.py::test_generate_seven_hypotheses -v
```

### Run with Coverage
```bash
python -m pytest tests/unit/test_tom_*.py --cov=api/services --cov=api/models --cov-report=term-missing
```

### Run Integration Tests (when ready)
```bash
python -m pytest tests/integration/test_tom_integration.py -v
```

## Quick Validation Commands

### Import Check (verify no syntax errors)
```bash
# Check ToM service
python -c "from api.services.tom_active_inference import ToMActiveInferenceService"

# Check models
python -c "from api.models.tom_hypothesis import ToMHypothesis, ThoughtSeedToM"

# Check tool
python -c "from api.agents.tools.tom_hypothesis_generator import ToMHypothesisTool"
```

### Run Dionysus API (for manual testing)
```bash
# Start API server
uvicorn api.main:app --reload --port 8000

# In another terminal, test ToM endpoint
curl -X POST http://localhost:8000/api/v1/tom/generate \
  -H "Content-Type: application/json" \
  -d '{"user_utterance": "I hit all my metrics but feel like I am failing", "user_id": "test-user"}'
```

## Database Commands

### Neo4j (via Graphiti - DO NOT access directly)
```bash
# Verify Graphiti connection
python -c "from api.services.graphiti_service import get_graphiti_service; import asyncio; asyncio.run(get_graphiti_service())"

# Query ToM hypothesis storage (via Graphiti)
python scripts/query_tom_hypotheses.py --user-id test-user --days 30
```

## Debugging Commands

### Check EFE Engine
```bash
python -c "from api.services.efe_engine import EFEEngine; e = EFEEngine(); print('EFE Engine OK')"
```

### Check Metaplasticity Service
```bash
python -c "from api.services.metaplasticity_service import MetaplasticityService; m = MetaplasticityService(); print(m.get_agent_precision('test-agent'))"
```

### Check ThoughtSeed Integration
```bash
python -c "from api.services.thoughtseed_integration import ThoughtseedIntegrationService; print('ThoughtSeed OK')"
```

## Log Locations

### Ralph Execution Logs
```bash
# View Ralph progress
tail -f specs/051-tom-active-inference/logs/ralph_execution.log

# View test output
tail -f specs/051-tom-active-inference/logs/test_output.log
```

### Dionysus API Logs
```bash
# API logs (if running locally)
tail -f logs/dionysus_api.log

# Docker logs (if running in container)
docker logs dionysus-api --tail 100 -f
```

## Performance Profiling

### Latency Testing (SC-003: <2s target)
```bash
# Run latency benchmark
python scripts/benchmark_tom_latency.py --iterations 100

# Expected output:
# p50: <1.5s
# p95: <2.0s
# p99: <2.5s
```

### Concurrent Load Testing (SC-007: 500 concurrent)
```bash
# Run load test (requires locust or similar)
locust -f tests/load/test_tom_load.py --users 500 --spawn-rate 50
```

## Git Workflow

### Commit After Each Task
```bash
# Stage changes
git add api/services/tom_*.py api/models/tom_*.py tests/unit/test_tom_*.py

# Commit with Ralph prefix
git commit -m "ralph: [task description from @fix_plan.md]"

# Example:
git commit -m "ralph: Implement ToM hypothesis generation with round-robin diversity (TOM-002)"
```

### Check Branch Status
```bash
git status
git log --oneline -5
```

## Cleanup Commands

### Remove Test Artifacts
```bash
rm -rf .pytest_cache __pycache__ tests/unit/__pycache__
```

### Reset ToM Data (for fresh start)
```bash
# WARNING: Deletes all ToM hypotheses
python scripts/cleanup_tom_data.py --confirm
```

## Success Criteria Validation

### Run All Success Criteria Checks
```bash
python scripts/validate_success_criteria.py --feature 051
```

### Individual SC Checks
```bash
# SC-001: Empathy quality (requires human eval)
python scripts/validate_sc001_empathy.py

# SC-002: Validation pass rate
python -m pytest tests/integration/test_validation_pass_rate.py

# SC-003: Latency
python scripts/benchmark_tom_latency.py --target-p95 2.0

# SC-004: Memory accuracy
python -m pytest tests/integration/test_social_memory_accuracy.py

# SC-005: Identity violations
python scripts/check_identity_violations.py --baseline-path logs/identity_baseline.json
```

## Emergency Rollback

### If Ralph Gets Stuck
```bash
# Check current task
cat specs/051-tom-active-inference/@fix_plan.md | head -20

# View recent commits
git log --oneline -10

# Rollback last commit (if needed)
git reset --soft HEAD~1

# Force stop Ralph
pkill -f ralph
```

## Health Check

### Pre-Task Validation
```bash
# Before starting next task, verify:
python -m pytest tests/unit/test_tom_*.py -v  # All tests pass
git status                                     # No uncommitted changes
python -c "from api.services.tom_active_inference import ToMActiveInferenceService"  # Imports OK
```
