# Feature 041: Implementation Plan

## Phase 1: Neo4j Access Architecture Verification (P0)

### T041-001: Verify no direct Neo4j driver usage in api/
- [ ] Run: `grep -r "from neo4j import GraphDatabase" api/` (expect 0 matches)
- [ ] Run: `grep -r "from neo4j import" api/` (document any findings)
- [ ] Verify dev scripts (`scripts/test_auth.py`, `scripts/test_bolt_connection.py`) are marked DEV-ONLY
- [ ] Document any violations

### T041-002: Audit GraphitiService as sole Neo4j connector
- [ ] Verify `api/services/graphiti_service.py` is the ONLY file with Neo4j connection logic
- [ ] Check destruction gate in `execute_cypher()` blocks DELETE/DROP/REMOVE
- [ ] Validate error handling for Cypher execution
- [ ] Document connection configuration (bolt URI, fallback logic)

### T041-003: Verify MemEvolveAdapter routes to Graphiti
- [ ] Audit `api/services/memevolve_adapter.py` - confirm it calls `graphiti.execute_cypher()`
- [ ] Verify no direct Neo4j driver imports
- [ ] Check trajectory context wrapping functionality
- [ ] Document MemEvolve pipeline: encode → store → retrieve → manage

### T041-004: Verify WebhookNeo4jDriver is compatibility shim
- [ ] Audit `api/services/webhook_neo4j_driver.py` - confirm it proxies to MemEvolve
- [ ] Verify no direct n8n webhook calls (should go through RemoteSyncService)
- [ ] Document shim behavior and deprecation status

### T041-005: Audit RemoteSyncService for n8n webhook routing
- [ ] Check `api/services/remote_sync.py` for HMAC signature validation
- [ ] Verify webhook URL configuration
- [ ] Document n8n webhook endpoints used

### T041-006: Map direct Graphiti users (50+ locations)
- [ ] Run: `grep -r "get_graphiti_service\|graphiti\." api/ --include="*.py" | grep -v memevolve`
- [ ] Categorize by: tools, services, routers, agents
- [ ] Document which operations bypass MemEvolve pipeline
- [ ] Assess impact: what's lost (trajectory tracking, webhook sync, audit logging)

### T041-007: Verify MOSAEIC constraints and schema compliance
- [ ] List all `neo4j/schema/*.cypher` files
- [ ] Map schema definitions to GraphitiService operations
- [ ] Check constraint enforcement in node operations
- [ ] Identify schema mismatches

---

## Phase 2: Code Quality (P1)

### T041-008: Run ruff for unused imports
- [ ] Run `ruff check api/services/ --select F401`
- [ ] Fix unused imports in each file
- [ ] Run `ruff check api/agents/ --select F401`
- [ ] Fix unused imports in agents

### T041-009: Verify Pydantic model validators
- [ ] List all models in `api/models/`
- [ ] Check for field validators
- [ ] Add missing validators for new models
- [ ] Test validator edge cases

### T041-010: Audit router error handling
- [ ] Check `api/routers/*.py` for bare except
- [ ] Standardize exception handling
- [ ] Implement consistent error responses
- [ ] Document error codes

### T041-011: Validate async/await patterns
- [ ] Check service layer async functions
- [ ] Identify blocking calls in async code
- [ ] Fix async context issues
- [ ] Add async tests

### T041-012: Run mypy type checking
- [ ] Run `mypy api/services/ --ignore-missing-imports`
- [ ] Fix type errors
- [ ] Add missing type hints
- [ ] Run full suite: `mypy api/ --ignore-missing-imports`

---

## Phase 3: Service Health (P1)

### T041-013: Verify singleton initialization
- [ ] Map service dependencies
- [ ] Check initialization order
- [ ] Test circular dependency scenarios
- [ ] Document initialization flow

### T041-014: Audit session_manager.py
- [ ] Check resource cleanup methods
- [ ] Verify session lifecycle
- [ ] Test cleanup on errors
- [ ] Add cleanup tests

### T041-015: Validate embedding service
- [ ] Check initialization logic
- [ ] Verify error handling
- [ ] Test service recovery
- [ ] Document configuration

### T041-016: Audit heartbeat_scheduler.py
- [ ] Review lifecycle management
- [ ] Check graceful shutdown
- [ ] Test restart scenarios
- [ ] Validate timing accuracy

### T041-017: Check coordination_service.py
- [ ] Verify pool creation
- [ ] Check connection limits
- [ ] Test pool exhaustion
- [ ] Validate cleanup

---

## Phase 4: Test Coverage (P0)

### T041-018: Run coverage analysis
- [ ] Activate venv: `source .venv/bin/activate`
- [ ] Run `pytest tests/ --cov=api --cov-report=term-missing --cov-report=html`
- [ ] Generate coverage report
- [ ] Identify <80% coverage files

### T041-019: Add tests for low coverage files
- [ ] Create tests for identified files
- [ ] Aim for >80% coverage
- [ ] Focus on critical paths

### T041-020: Create contract tests for routers
- [ ] List routers without contract tests
- [ ] Create contract test suite
- [ ] Validate API contracts
- [ ] Test error responses

### T041-021: Verify test isolation
- [ ] Check for shared state in tests
- [ ] Run tests in random order
- [ ] Fix isolation issues
- [ ] Add isolation markers

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

- [HIGH] Archetype-to-basin linkage broken: `strange_attractor_id` uses archetype string values that do not match memory basin names, so `RESONATES_WITH` edges never attach to an `AttractorBasin`. refs: `api/services/autobiographical_service.py:79`, `api/services/autobiographical_service.py:110`, `api/services/memory_basin_router.py:22`
- [HIGH] `predict_and_calibrate` returns `(new_facts, residue)` but `ConsciousnessMemoryCore` treats it as a list, dropping residue and logging the wrong count. refs: `api/agents/consciousness_memory_core.py:67`, `api/services/nemori_river_flow.py:237`
- [MEDIUM] Nemori distillation only classifies to a basin name; it does not route facts to `MemoryBasinRouter` or integrate symbolic residue into context cells/retrieval cues. refs: `api/services/nemori_river_flow.py:247`, `api/services/nemori_river_flow.py:280`, `api/services/memory_basin_router.py:130`, `api/services/context_packaging.py:53`
- [MEDIUM] Context packaging implements decay/resonance/attractor strength but is not wired to memory operations or basin updates; only unit tests exist. refs: `api/services/context_packaging.py:80`, `api/services/context_packaging.py:127`, `tests/unit/test_context_packaging.py:1`
- [MEDIUM] Basin activation only strengthens and increments counters; no decay, importance signals, or cross-basin connection creation. refs: `api/services/memory_basin_router.py:200`
- [MEDIUM] Episode archetype prompt includes `hero`, which is not in the `DevelopmentArchetype` enum and causes fallback behavior that drops LLM outputs. refs: `api/services/nemori_river_flow.py:123`, `api/services/nemori_river_flow.py:162`, `api/models/autobiographical.py:42`
- [LOW] `stabilizing_attractor` is computed during episode synthesis but `DevelopmentEpisode` has no field, so the value is discarded. refs: `api/services/nemori_river_flow.py:164`, `api/models/autobiographical.py:164`
- [LOW] `DevelopmentEvent` declares `resonance_score` twice, suggesting unused/overwritten data. ref: `api/models/autobiographical.py:133`
- [LOW] Nemori unit coverage exists for linking (`tests/unit/test_nemori_linking.py:9`) and flow (`tests/unit/test_consciousness_river.py:11`), but neither asserts the tuple-handling bug in `ConsciousnessMemoryCore`. refs: `tests/unit/test_nemori_linking.py:9`, `tests/unit/test_consciousness_river.py:11`, `api/agents/consciousness_memory_core.py:67`
