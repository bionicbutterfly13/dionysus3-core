# 064-critical-d3-fixes - Ralph Instructions

## Goal
Fix 3 critical bugs in Dionysus 3 codebase to establish stable foundation before D2 migration:
1. Undefined variables in action_executor.py
2. Duplicate endpoint in monitoring.py
3. Direct Neo4j access in ias.py

## Current State
- All 3 bug fixes IMPLEMENTED
- Verification in progress
- Ready for acceptance testing

## Tech Stack
- Language: Python 3.11+
- Framework: FastAPI, Pydantic v2
- Database: Neo4j via Graphiti service (NO direct access)
- Testing: pytest with asyncio_mode=auto

## Acceptance Criteria

### AC-1: Zero NameError in action_executor.py
```bash
# Verify no undefined variables
python -c "from api.services.action_executor import ObserveHandler; print('OK')"
```
**Expected**: No NameError, prints "OK"

### AC-2: Single /cognitive endpoint in OpenAPI spec
```bash
# Count /cognitive endpoint definitions
grep -c "@router.get(\"/cognitive\"" api/routers/monitoring.py
```
**Expected**: Returns `1` (not `2`)

### AC-3: Zero _driver.execute_query in ias.py
```bash
grep -c "_driver.execute_query" api/routers/ias.py
```
**Expected**: Returns `0`

### AC-4: All existing tests pass
```bash
python -m pytest tests/ -v --tb=short
```
**Expected**: All tests pass (no failures)

## Working Rules
1. Read `@fix_plan.md` for current task
2. Complete ONE task per iteration (2-5 min max)
3. Run acceptance tests after each verification
4. Commit with: `ralph: [description]`
5. Update `@fix_plan.md` after each task
6. If blocked, document and move to next task

## Task Completion Criteria
- [ ] Acceptance criteria verified
- [ ] Tests pass
- [ ] Changes committed
- [ ] `@fix_plan.md` updated

## Anti-Patterns (DO NOT)
- Skip acceptance criteria verification
- Batch multiple verifications
- Assume tests pass without running
- Mark complete without evidence
