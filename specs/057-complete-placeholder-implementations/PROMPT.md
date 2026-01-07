# 057-complete-placeholder-implementations - Ralph Implementation Instructions

## Goal
Complete all mocked, placeholder, and TODO implementations identified in codebase audit to production-ready code with full test coverage, following TDD methodology and active inference architecture patterns.

## Current State
- **Branch**: 057-complete-placeholder-implementations (active)
- **Specification**: Complete in spec.md with 6 user stories, 12 functional requirements, 10 success criteria
- **Codebase**: Existing Dionysus cognitive engine with:
  - Active inference wrapper operational
  - OODA loop agents (Perception, Reasoning, Metacognition) deployed
  - Beautiful Loop services (HyperModel, BayesianBinder) present but untested
  - Test infrastructure with pytest + pytest-asyncio configured
  - Mocked/placeholder code in 5 locations + 2 empty test suites

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI, Pydantic v2, smolagents
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Architecture**: Active inference, attractor basins, OODA loops
- **Services**: Graphiti (knowledge graph), multi-tier memory, GHL API

## Working Rules

### Core Principles
1. **TDD MANDATORY**: Write tests BEFORE implementation for every component
2. **Read `@fix_plan.md`** for current task - work ONLY on current task
3. **ONE task per iteration** (5-15 min max) - resist batching temptation
4. **Run tests after EVERY change** - must pass before moving forward
5. **Commit with conventional format**: `test: add epistemic field depth scoring` or `feat: implement real basin count query`
6. **Update `@fix_plan.md`** after each task completion
7. **No new pytest.skip() or TODO** - if blocked, document in @fix_plan.md Blocked section

### Task Completion Criteria
Every task must satisfy ALL before marking complete:
- [ ] Tests written (if implementation task)
- [ ] Implementation complete
- [ ] All tests pass (no skipped, no failures)
- [ ] Code follows existing patterns (check similar services/tests)
- [ ] Changes committed with conventional commit message
- [ ] `@fix_plan.md` updated (move to Completed, update Current Task)

### Anti-Patterns (NEVER DO THIS)
- ❌ Implement without writing tests first
- ❌ Skip tests temporarily ("I'll fix later")
- ❌ Work on multiple tasks simultaneously
- ❌ Leave uncommitted working code
- ❌ Add TODO/FIXME comments instead of completing
- ❌ Copy-paste without understanding existing patterns
- ❌ Break existing tests to make new tests pass
- ❌ Use hardcoded values where real computation required

## Implementation Strategy

### Priority Order (P1 → P2 → P3)
**Phase 1: P1 - Core Functionality**
1. Meta-evolution real metrics (US1)
2. Active inference real scoring (US2)

**Phase 2: P2 - Validation**
3. EpistemicFieldService tests (US3)
4. Beautiful Loop OODA tests (US4)

**Phase 3: P3 - Operational**
5. GHL email sync (US5)
6. Metacognition storage (US6)

### TDD Pattern for Each Component
```
1. Read existing test file (if exists)
2. Un-skip ONE test or write ONE new test
3. Run test → confirm it fails
4. Write MINIMAL implementation to make test pass
5. Run test → confirm it passes
6. Run full test suite → confirm no regressions
7. Commit
8. Repeat for next test
```

## File References

### Specification
- `spec.md` - Complete requirements (READ THIS FIRST)
- `checklists/requirements.md` - Quality validation checklist

### Implementation Targets
**Priority 1 (P1):**
- `api/services/meta_evolution_service.py:116-117` - Replace energy_level/active_basins_count placeholders
- `api/core/engine/meta_tot.py:62` - Replace TODO with real active inference calls

**Priority 2 (P2):**
- `tests/unit/test_epistemic_field_service.py` - Un-skip 22 tests, implement EpistemicFieldService
- `tests/integration/test_beautiful_loop_ooda.py` - Un-skip 36 tests, verify OODA integration
- `api/services/epistemic_field_service.py` - Create (doesn't exist yet)

**Priority 3 (P3):**
- `scripts/ghl_sync.py:59-65` - Implement fetch_all_emails()
- `scripts/store_metacognition_memory.py:22-25, 86-91, 226-245, 316-322, 400-408` - Replace mocks with real calls

### Key Services to Reference
- `api/core/engine/active_inference.py` - Active inference wrapper interface
- `api/services/graphiti_service.py` - Knowledge graph storage
- `api/agents/consciousness_manager.py` - OODA agent hierarchy
- `api/services/hyper_model_service.py` - Beautiful Loop hyper-model
- `api/services/bayesian_binder.py` - Binding selection

## Build & Test Commands
See `@AGENT.md` for full commands.

Quick reference:
```bash
# Run specific test file
python -m pytest tests/unit/test_epistemic_field_service.py -v

# Run with coverage
python -m pytest tests/unit/test_epistemic_field_service.py --cov=api/services/epistemic_field_service --cov-report=term-missing

# Run integration tests
python -m pytest tests/integration/test_beautiful_loop_ooda.py -v

# Run all tests (regression check)
python -m pytest tests/ -v
```

## Exit Conditions
Ralph completes when ALL of these are true:
1. All tasks in @fix_plan.md marked ✓ Completed
2. Zero items in Blocked section (or documented as deferred)
3. All 10 success criteria in spec.md validated:
   - SC-001: Energy level variance >0 across 10 snapshots
   - SC-002: Thoughtseed selection >70% optimal alignment
   - SC-003: EpistemicFieldService >90% coverage, 22 tests pass
   - SC-004: Beautiful Loop OODA >90% coverage, 36 tests pass, <10% overhead
   - SC-005: Epistemic differentiation Cohen's d >0.8
   - SC-006: GHL sync retrieves 8+ emails <30s
   - SC-007: Metacognition storage 6+ entities, 7+ relationships
   - SC-008: TDD methodology followed (tests before code)
   - SC-009: Zero new pytest.skip() or TODO
   - SC-010: All existing tests still pass
4. Final validation: `python -m pytest tests/ --cov=api --cov-report=term-missing`

## Notes for Ralph
- This is a SpecKit-managed feature - honor the specification contract
- Check spec.md Assumptions section if services missing/unavailable
- Beautiful Loop services may have incomplete APIs - check source first
- GHL API credentials must be in .env (GHL_API_KEY, LOCATION_ID)
- Neo4j access ONLY via Graphiti service (never direct Cypher)
- When blocked, document clearly in @fix_plan.md with reason + proposed solution
- Estimate ~40-60 tasks total across 6 user stories
