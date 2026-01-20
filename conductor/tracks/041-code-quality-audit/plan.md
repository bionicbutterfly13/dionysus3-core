# Feature 041: Implementation Plan

## Phase 1: Neo4j Access Architecture Verification (P0) ✅

### T041-001: Verify no direct Neo4j driver usage in api/
- [x] Run: `grep -r "from neo4j import GraphDatabase" api/` → 0 matches ✓
- [x] Run: `grep -r "from neo4j import" api/` → 0 matches ✓
- [x] Verify dev scripts (`scripts/test_auth.py`, `scripts/test_bolt_connection.py`) are DEV-ONLY → confirmed
- [x] No violations in api/

### T041-002: Audit GraphitiService as sole Neo4j connector
- [x] `api/services/graphiti_service.py` is the ONLY file with Neo4j connection logic ✓
- [x] Destruction gate at line 833 blocks DELETE/DETACH/DROP/REMOVE ✓
- [x] Requires both `fingerprint_authorized` and `user_confirmed` flags
- [x] Error handling with timeout and exception logging

### T041-003: Verify MemEvolveAdapter routes to Graphiti
- [x] `memevolve_adapter.py` calls `graphiti.execute_cypher()` ✓
- [x] No direct Neo4j driver imports ✓
- [x] Pipeline: encode → extract → ingest → search via Graphiti

### T041-004: Verify WebhookNeo4jDriver is compatibility shim
- [x] `webhook_neo4j_driver.py` proxies all calls to MemEvolveAdapter → Graphiti ✓
- [x] No direct n8n webhook calls ✓
- [x] Documented as "REPAIRED" compatibility layer

### T041-005: Audit RemoteSyncService for n8n webhook routing
- [x] HMAC-SHA256 signature validation at line 399 ✓
- [x] Webhook URLs configured via environment variables
- [x] Endpoints: ingest, recall, traverse, cypher, skill, mosaeic, agent-run, evolve

### T041-006: Map direct Graphiti users (50+ locations)
- [x] 116 references across 28 files (tools, services, routers, agents)
- [x] These are authorized KG operations (search, extract, ingest)
- [x] MemEvolve pipeline adds: trajectory tracking, entity extraction, audit logging

### T041-007: Verify MOSAEIC constraints and schema compliance
- [x] Schema files: mosaeic-core.cypher, agent_execution_trace.cypher, mosaeic-narrative.cypher
- [x] Constraints: Capture, Pattern, Belief, Session, User uniqueness
- [x] Indexes: timestamp, emotional_intensity, domain, severity, adaptiveness

---

## Phase 2: Code Quality (P1) ✅

### T041-008: Run ruff for unused imports ✅
- [x] Run `ruff check api/services/ --select F401` → 1 error (intentional module check)
- [x] Run `ruff check api/agents/ --select F401` → fixed all errors
- [x] `coordination_service.py:345` - intentional import availability check, no fix needed

### T041-009: Verify Pydantic model validators ✅
- [x] 39 model files, 8 validators across 5 files
- [x] Key models have validators: beautiful_loop, belief_state, mental_model, metacognitive_particle, priors
- [x] Pydantic v2 patterns used correctly

### T041-010: Audit router error handling ✅
- [x] No bare `except:` clauses found
- [x] 146 proper HTTPException usages
- [x] Error handling standardized

### T041-011: Validate async/await patterns ✅
- [x] `time.sleep(0.1)` in graphiti_service.py is for thread init (correct)
- [x] All other sleeps use `asyncio.sleep()` properly
- [x] No blocking calls in async code paths

### T041-012: Run mypy type checking ✅
- [x] Fixed 9 type errors in `efe_engine.py` (seed_id typing)
- [x] Key files pass: efe_engine.py, prior_constraint_service.py, priors.py
- [x] Added type annotations: `dict[str, EFEResult]`

---

## Phase 3: Service Health (P1)

### T041-013: Verify singleton initialization ✅
- [x] Map service dependencies → 37 singleton services identified with `get_*_service()` pattern
- [x] Check initialization order → Safe: Most services use lazy imports inside methods
- [x] Test circular dependency scenarios → ✅ All 9 core services import successfully, no cycles
- [x] Document initialization flow → See findings below

**Initialization Findings:**
- **Safe Pattern**: Services use lazy imports inside methods (`from api.services.X import get_X_service`)
- **Module-level imports**: `heartbeat_service.py` (lines 27-28) imports `action_executor` and `energy_service` at module level, but these don't create cycles because their dependencies don't import back
- **Dependency chains verified**:
  - `graphiti_service` → foundation (no service imports)
  - `embedding_service` → foundation (external libs only)
  - `heartbeat_service` → `action_executor` → `energy_service` → no cycles
  - `autobiographical_service` → `conversation_moment_service` → no back-import
- **No circular dependencies at import time** - verified via Python import test

### T041-014: Audit session_manager.py ✅
- [x] Check resource cleanup methods → ⚠️ FINDING: No `close()` or cleanup methods exist
- [x] Verify session lifecycle → ✅ Sessions have timestamps, `record_session_end()` persists timing
- [x] Test cleanup on errors → ✅ try/except throughout, custom exceptions (`SessionManagerError`, `DatabaseUnavailableError`)
- [x] Add cleanup tests → SKIPPED: No cleanup methods to test

**Findings:**
- **Missing**: No `close()`, `cleanup()`, or `async with` context manager support
- **Driver held indefinitely**: `_driver` reference never explicitly released
- **Singleton in router**: `get_session_manager()` is in `api/routers/ias.py:34`, not in service
- **Recommendation**: Add shutdown hook if long-running sessions are a concern (currently acceptable for API lifecycle)

### T041-015: Validate embedding service ✅
- [x] Check initialization logic → ✅ Lazy client creation, sensible defaults from env vars
- [x] Verify error handling → ✅ Custom `EmbeddingError`, proper try/except, dimension validation
- [x] Test service recovery → ✅ `_get_client()` recreates if closed, `health_check()` for monitoring
- [x] Document configuration → See findings below

**Findings:**
- **Well-designed**: Clean singleton pattern at line 356, `close()` method exists
- **Config vars**: `EMBEDDINGS_PROVIDER`, `OLLAMA_URL`, `OLLAMA_EMBED_MODEL`, `OPENAI_EMBED_MODEL`, `EMBEDDING_DIM`
- **Minor issue**: Lines 177-180 have DUPLICATE `except Exception` handlers (harmless but should clean up)
- **Health check**: `health_check()` and `check_model_available()` methods for monitoring
- **Overall**: ✅ Production-ready, well-documented service

### T041-016: Audit heartbeat_scheduler.py ✅
- [x] Review lifecycle management → ✅ State machine: STOPPED→RUNNING→PAUSED→USER_SESSION
- [x] Check graceful shutdown → ✅ Uses `asyncio.Event` for clean shutdown, awaits task cancellation
- [x] Test restart scenarios → ✅ `stop()` then `start()` works, double-start guarded
- [x] Validate timing accuracy → ✅ `asyncio.wait_for()` with interruptible sleep, configurable jitter

**Findings:**
- **Well-designed**: Clean state machine, proper asyncio patterns
- **User session awareness**: Auto-pause during user activity, configurable cooldown
- **Error recovery**: Loop catches exceptions and retries after 60s sleep
- **Overall**: ✅ Production-ready scheduler with proper lifecycle management

### T041-017: Check coordination_service.py ✅
- [x] Verify pool creation → ✅ `initialize_pool()` caps at MAX_POOL_SIZE, `spawn_agent()` creates unique IDs
- [x] Check connection limits → ✅ MAX_POOL_SIZE=16, MAX_QUEUE_DEPTH=100, custom exceptions
- [x] Test pool exhaustion → ✅ Queue system, Dead Letter Queue, exponential backoff retries
- [x] Validate cleanup → ✅ `shutdown_pool()` clears all state (agents, tasks, queue, DLQ)

**Findings:**
- **Well-designed**: DAEDALUS-style coordination with isolation breach detection
- **Error handling**: `PoolFullError`, `QueueFullError`, MAX_RETRIES=3 with DLQ
- **Metrics**: `metrics()`, `get_pool_stats()`, `agent_health_report()`
- **Overall**: ✅ Production-ready coordination service

---

## Phase 4: Test Coverage (P0)

### T041-018: Run coverage analysis ✅
- [x] Run pytest with coverage on key services
- [x] Generate coverage reports
- [x] Identify <80% coverage files → See findings below

**Coverage Findings (86 unit test files, 79+ tests passing):**

| Service | Coverage | Status |
|---------|----------|--------|
| `bootstrap_recall_service.py` | 85% | ✅ Above target |
| `coordination_service.py` | 73% | ⚠️ Below 80% |
| `efe_engine.py` | 71% | ⚠️ Below 80% |
| `prior_constraint_service.py` | 70% | ⚠️ Below 80% |
| `autobiographical_service.py` | 33% | ❌ Needs tests |
| `graphiti_service.py` | 27% | ❌ Needs tests |

**Low coverage services needing attention:**
1. `graphiti_service.py` - Core KG operations, mostly async methods
2. `autobiographical_service.py` - Memory persistence, async Neo4j calls
3. `prior_constraint_service.py` - Some edge cases untested
4. `efe_engine.py` - Multi-agent selection paths untested

### T041-019: Add tests for low coverage files
- [ ] Create tests for `graphiti_service.py` (27% → 80%+)
- [ ] Create tests for `autobiographical_service.py` (33% → 80%+)
- [ ] Create tests for `prior_constraint_service.py` (70% → 80%+)
- [ ] Create tests for `efe_engine.py` (71% → 80%+)

### T041-020: Create contract tests for routers
- [ ] List routers without contract tests
- [ ] Create contract test suite
- [ ] Validate API contracts
- [ ] Test error responses

### T041-021: Verify test isolation ✅
- [x] Check for shared state in tests → Tests pass in both orders
- [x] Run tests in different order → 70 tests pass consistently
- [x] No isolation issues detected

### T041-022: Mock Neo4j in integration tests
- [ ] Identify tests requiring live Neo4j
- [ ] Create Neo4j mocks
- [ ] Update tests to use mocks
- [ ] Verify test behavior

---

## Phase 5: Dead Code & Type Hints (P2)

### T041-023: Identify dead code in agents
- [ ] Use `vulture` for dead code detection
- [ ] Review flagged code manually
- [ ] Remove confirmed dead code
- [ ] Add deprecation warnings if needed

### T041-024: Complete type hints in services
- [ ] Check all public functions in `api/services/`
- [ ] Add missing type hints
- [ ] Use generics where appropriate
- [ ] Run mypy to verify

---

## Phase 6: MCP Server Validation (P2)

### T041-025: Validate MCP tool registry
- [ ] Check `dionysus_mcp/tools/` registry
- [ ] Verify all tools registered
- [ ] Test tool discovery

### T041-026: Check MCP parameter validation
- [ ] Review tool parameter schemas
- [ ] Add validation where missing
- [ ] Test invalid parameters

### T041-027: Verify MCP resource handlers
- [ ] Review `dionysus_mcp/resources/`
- [ ] Check error handling
- [ ] Test resource lifecycle

---

## Phase 7: Nemori + MemEvolve Integration (P1)

**Context:** Nemori stores to `consolidated_memory_store`, NOT Graphiti. Predict-calibrate facts are generated but not persisted to temporal knowledge graph.

### T041-028: Connect Nemori facts to Graphiti [P0]
- [ ] Audit `api/services/nemori_river_flow.py` - locate `predict_and_calibrate()`
- [ ] Add Graphiti integration to persist distilled facts
- [ ] Implement `graphiti.add_fact()` method in GraphitiService
- [ ] Facts should include: source_episode_id, valid_at timestamp
- [ ] Test bi-temporal tracking of learned facts

### T041-029: Episode-to-Trajectory bridge [P0]
- [ ] Map `DevelopmentEpisode` model to `TrajectoryData` format
- [ ] After `construct_episode()`, create corresponding trajectory
- [ ] Route through MemEvolveAdapter for entity extraction
- [ ] Test: episodic narratives get Graphiti temporal tracking

### T041-030: Predict-Calibrate → Meta-Evolution loop [P1]
- [ ] Compute gap_score between predicted_episode and actual_events
- [ ] If gap > threshold, call `memevolve.trigger_evolution()`
- [ ] Pass gap_context and episode_id to evolution trigger
- [ ] Test: system adapts retrieval based on prediction errors

### T041-031: Hybrid retrieval for Nemori episodes [P1]
- [ ] Refactor episode retrieval to use Graphiti hybrid search
- [ ] Enable: semantic + BM25 + graph traversal
- [ ] Add graph distance re-ranking
- [ ] Test: related episodes found via relationship proximity

### T041-032: Implement k/m retrieval ratio [P2]
- [ ] Configure k=10 episodic + m=20 semantic (per Nemori paper)
- [ ] Top-2 episodes include full text, rest titles only
- [ ] Create `recall_with_nemori_ratio()` wrapper
- [ ] Benchmark against current retrieval

### T041-033: Context cell persistence [P2]
- [ ] Identify CRITICAL/HIGH priority cells in ContextPackaging
- [ ] Persist to Graphiti with resonance_score, basin_id
- [ ] Enable cross-session context survival
- [ ] Test: symbolic residue tracking across sessions

---

## Dependencies

```
T041-018 → T041-019 (Coverage analysis before adding tests)
T041-008 → T041-012 (Fix imports before type checking)
T041-001 → T041-002 → T041-003 (Sequential Neo4j verification)
T041-028 → T041-029 (Facts to Graphiti before episode bridge)
T041-029 → T041-030 (Episode bridge before meta-evolution loop)
T041-031 → T041-032 (Hybrid retrieval before k/m ratio tuning)
```

## Acceptance Criteria

1. All P0 tasks completed (Neo4j patterns, error handling, test coverage)
2. Test coverage >80% on api/services/ and api/agents/
3. Zero linting errors from ruff
4. Zero type errors from mypy (with --ignore-missing-imports)
5. All Neo4j operations confirmed to use webhooks
6. Documentation updated with audit findings

---

## Review Findings: Context Engineering + Jungian Archetypes

- [HIGH] ~~Archetype-to-basin linkage broken~~ **FIXED by Track 061 (099359e, ce11465)**: Added `ARCHETYPE_TO_BASIN` mapping in `autobiographical_service.py:36-56` that maps archetypes to proper basin names (`experiential-basin`, `conceptual-basin`, `procedural-basin`, `strategic-basin`).
- [HIGH] ~~`predict_and_calibrate` tuple handling~~ **FIXED by Track 061 (9ee3f49)**: `ConsciousnessMemoryCore` now correctly unpacks `(new_facts, symbolic_residue)` tuple at line 69.
- [MEDIUM] ~~Nemori distillation only classifies to a basin name~~ **FIXED by Track 061 (099359e)**: `predict_and_calibrate()` now routes facts through `MemoryBasinRouter` and integrates symbolic residue into `ContextCell` with `SymbolicResidueTracker`.
- [MEDIUM] ~~Context packaging not wired to memory operations~~ **FIXED by Track 061 (099359e)**: Integrated `TokenBudgetManager` in `predict_and_calibrate()` for budget-aware context cell creation.
- [MEDIUM] ~~Basin activation only strengthens, no decay~~ **FIXED by Track 061 (099359e, cf182cf)**: Added `_apply_decay_to_other_basins()` for Hebbian forgetting and `_link_basins()` for cross-basin connections.
- [MEDIUM] ~~Episode archetype prompt includes `hero`~~ **FIXED by Track 061 (099359e)**: Aligned Nemori archetype prompt to valid `DevelopmentArchetype` enum values.
- [LOW] ~~`stabilizing_attractor` discarded~~ **FIXED by Track 061 (099359e)**: Added `stabilizing_attractor` field to `DevelopmentEpisode` model.
- [LOW] ~~`DevelopmentEvent` declares `resonance_score` twice~~ **VERIFIED OK**: `resonance_score` appears only once at line 133. The related field `basin_r_score` at line 136 is a distinct property for basin-specific resonance.
- [LOW] ~~Nemori unit coverage missing tuple-handling assertion~~ **FIXED by Track 061 (9ee3f49)**: Added proper tuple unpacking test coverage for `ConsciousnessMemoryCore`.
