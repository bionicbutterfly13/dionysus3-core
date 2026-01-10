# Task Queue - 064-critical-d3-fixes

## Acceptance Criteria Status

| ID | Criterion | Command | Expected | Status |
|----|-----------|---------|----------|--------|
| AC-1 | Zero NameError in action_executor.py | `python -c "from api.services.action_executor import ObserveHandler"` | No error | ✅ PASS |
| AC-2 | Single /cognitive endpoint | `grep -c "@router.get(\"/cognitive\"" api/routers/monitoring.py` | `1` | ✅ PASS |
| AC-3 | Zero _driver.execute_query in ias.py | `grep -c "_driver.execute_query" api/routers/ias.py` | `0` | ✅ PASS |
| AC-4 | All tests pass | `python -m pytest tests/ -v --tb=short` | 0 new failures | ✅ PASS (741 passed, 36 pre-existing failures) |

---

## Current Task
> **All acceptance criteria verified - Ready for commit**

## Backlog
- [ ] Commit all changes with feature summary

## Completed
- [x] T003-T005: Fix undefined variables in action_executor.py
- [x] T006-T007: Remove duplicate endpoint in monitoring.py
- [x] T008-T011: Replace Neo4j access with Graphiti in ias.py
- [x] T015-T016: Grep verification (preliminary)
- [x] T017: Update spec.md status
- [x] AC-1: Zero NameError in action_executor.py
- [x] AC-2: Single /cognitive endpoint (grep returns 1)
- [x] AC-3: Zero _driver.execute_query in ias.py (grep returns 0)
- [x] AC-4: Test suite passes (741 passed, 36 pre-existing failures)

## Discovered
_Tasks found during implementation:_
- `kg_learning.py` also has `_driver.execute_query` (OUT OF SCOPE per spec)

## Blocked
_None_

---

## Verification Commands

```bash
# AC-1: No NameError
python -c "from api.services.action_executor import ObserveHandler; print('AC-1 PASS')"

# AC-2: Single endpoint (should return 1)
grep -c "@router.get(\"/cognitive\"" api/routers/monitoring.py

# AC-3: No direct Neo4j (should return 0)
grep -c "_driver.execute_query" api/routers/ias.py

# AC-4: Full test suite
python -m pytest tests/ -v --tb=short

# All-in-one verification script
echo "=== AC-1 ===" && python -c "from api.services.action_executor import ObserveHandler; print('PASS')" && \
echo "=== AC-2 ===" && [ $(grep -c "@router.get(\"/cognitive\"" api/routers/monitoring.py) -eq 1 ] && echo "PASS" && \
echo "=== AC-3 ===" && [ $(grep -c "_driver.execute_query" api/routers/ias.py) -eq 0 ] && echo "PASS" && \
echo "=== All criteria verified ==="
```
