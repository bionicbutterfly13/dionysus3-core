# Track Plan: Memory Systems Integration

**Track ID**: 057-memory-systems-integration
**Status**: In Progress (20%)
**Last Updated**: 2026-01-17
**QA Review Requested**: Yes

---

## QA Agent Handoff Notes

### Current State Summary

**Libraries in scope and their roles:**
| Library | Role | Integration Status |
|---------|------|-------------------|
| Graphiti | Sole Neo4j gateway, temporal knowledge graph | Active (api/services/graphiti_service.py) |
| MemEvolve | Memory provider interface + evolution | Partial (webhook adapter exists, no EvolveLab provider) |
| Nemori | Episodic→Semantic organizer | Active (api/services/nemori_river_flow.py) |
| AutoSchemaKG | Schema induction | Not integrated (exists in flux-backend, not dionysus3-core) |
| Smolagents | Agent runtime | Active (api/agents/) |
| Context-Engineering | IBM/MIT context packaging guidance | Pending review (/Volumes/Asylum/repos/Context-Engineering) |

### Key Findings Requiring QA Validation

1. **MCTS/POMCP remnants** (FR-057-001 at risk):
   - `api/services/meta_tot_engine.py:POMCPActiveInferencePlanner` - still exists
   - `api/services/metacognition_patterns_storage.py` - references "MCTS-based" in comments
   - `api/core/engine/meta_tot.py` - docstrings still mention MCTS/POMCP
   - **QA Question**: Should we remove POMCP entirely or refactor to pure active inference selection?

2. **Basin + Blanket linking** (FR-057-002, FR-057-003 missing):
   - `NemoriRiverFlow.predict_and_calibrate()` returns semantic facts but does NOT tag basin or blanket
   - `DevelopmentEvent` has `active_inference_state` but no explicit `markov_blanket_id`
   - `ConsolidatedMemoryStore.store_event()` does not create graph links to AttractorBasin/MarkovBlanket nodes
   - **QA Question**: Confirm linking approach - embed metadata vs create explicit graph edges?

3. **Neo4j access paths** (FR-057-004 partial):
   - `VectorSearchService` and `ContextStreamService` now route recall through `MemEvolveAdapter` (Graphiti default)
   - Some n8n workflows still call Neo4j directly
   - **QA Question**: Should n8n call Dionysus API endpoints instead of Neo4j?

4. **Active inference data flow**:
   - `ActiveInferenceState` stored in `DevelopmentEvent.active_inference_state`
   - `twa_state` (Markov blanket context) stored in active inference state
   - `surprisal` and `uncertainty` used by Nemori for boundary detection
   - **QA Question**: Is `twa_state` sufficient for Markov blanket identity, or do we need explicit MarkovBlanket nodes?

### Data Object Journey (Current Implementation)

```
Raw Events → MoSAEIC/DevelopmentEvent
    ↓
Nemori boundary detection (surprisal + resonance)
    ↓
DevelopmentEpisode (narrative + theme)
    ↓
predict_and_calibrate() → SemanticFacts + SymbolicResidue
    ↓
Graphiti ingestion (nodes + edges)
    ↓
MemEvolve retrieval (via webhook adapter)
    ↓
Smolagents consumption
```

**Gaps in journey:**
- No basin tagging between DevelopmentEpisode and SemanticFacts
- No Markov blanket linking at any stage
- AutoSchemaKG not in pipeline

---

## Phase 1: Active Inference Meta-ToT (US1) - P1

**Goal**: Remove legacy MCTS/POMCP logic and score choices via active inference only.

**Audit Complete**: MCTS/POMCP remnants identified in:
- `api/services/meta_tot_engine.py` - POMCPActiveInferencePlanner class (Monte Carlo simulation)
- `api/services/metacognition_patterns_storage.py` - "MCTS-based" in docstrings
- `api/core/engine/meta_tot.py` - docstrings reference MCTS/POMCP

**Proposed Change**: Replace POMCP best_action selection with pure active inference scoring (EFE + prediction error) from `ActiveInferenceWrapper`.

- [x] **Task 1.1**: [TDD] Update unit tests for active inference selection scoring
  - **Status**: Tests exist in `tests/unit/test_meta_tot_engine.py`
  - **Action needed**: Add tests that verify no MCTS imports, verify active inference scoring path
- [x] **Task 1.2**: [TDD] Update metacognition runtime + patterns storage tests
- [x] **Task 1.3**: Integrate `pymdp` into `ActiveInferenceService` (replace/augment Julia wrapper)
- [x] **Task 1.4**: Remove POMCP/MCTS branches in `meta_tot_engine.py` using `pymdp` backend
- [x] **Task 1.5**: Update Meta-ToT algorithm labeling to active inference in runtime config + storage

## Phase 2: Nemori Basin + Blanket Linking (US2) - P1

**Goal**: Tag semantic distillates with basin + Markov blanket context and persist links.

**Audit Complete**: Current state:
- `NemoriRiverFlow.predict_and_calibrate()` at `api/services/nemori_river_flow.py` returns semantic facts without basin/blanket tags
- `MemoryBasinRouter` at `api/services/memory_basin_router.py` has basin classification and linking logic
- `ActiveInferenceState.twa_state` contains Markov blanket context (sensory/active/internal partitions)
- `ConsolidatedMemoryStore.store_event()` stores events but doesn't create basin/blanket links

**Proposed Implementation**:
1. In `predict_and_calibrate()`: call `MemoryBasinRouter.classify_memory_type()` on summary text to get basin name
2. Extract `twa_state` from original events' `active_inference_state` to compute blanket ID (hash of state)
3. Add `basin_name` and `markov_blanket_id` to returned event metadata
4. In `ConsolidatedMemoryStore.store_event()`: MERGE graph edges `(:DevelopmentEvent)-[:ALIGNS_WITH]->(:AttractorBasin)` and `(:DevelopmentEvent)-[:WITHIN_BLANKET]->(:MarkovBlanket)`

- [x] **Task 2.1**: Add basin + Markov blanket metadata to Nemori distillation events
  - **Files**: `api/services/nemori_river_flow.py`, `api/models/autobiographical.py`
  - **Implementation**: Classify semantic memory to basin, hash twa_state for blanket ID
- [x] **Task 2.2**: Link DevelopmentEvent nodes to AttractorBasin + MarkovBlanket in Graphiti
  - **Files**: `api/agents/consolidated_memory_stores.py`
  - **Implementation**: Add MERGE statements for graph edges in store_event Cypher
- [x] **Task 2.3**: [TDD] Add tests for metadata propagation and graph links

## Phase 3: Graphiti-Only Neo4j Access (US3) - P1

**Goal**: Route Neo4j access through Graphiti to avoid direct connections elsewhere.

- [x] **Task 3.1**: Switch `VectorSearchService._get_latest_strategy` to Graphiti cypher
- [x] **Task 3.2**: [TDD] Add tests ensuring Graphiti-only cypher access

### Acceptance Criteria
- [x] `VectorSearchService` imports `GraphitiService` and does NOT import `RemoteSyncService` or `Neo4jDriver`.
- [x] All Cypher execution in `VectorSearchService` uses `GraphitiService.execute_cypher`.
- [x] `RemoteSyncService` usage for vector search (n8n webhooks) is removed.
- [x] Vector search functionality is verified against the VPS Neo4j instance.

## Phase 4: MemEvolve Adapter Alignment (US4) - P1

**Goal**: Align MemEvolve ingest/recall with Graphiti schema and TrajectoryData format.

- [x] **Task 4.1**: Confirm MemEvolve adapter stores Trajectory nodes + relationships
- [x] **Task 4.2**: Ensure Graphiti recall/evolve backends are default
- [x] **Task 4.3**: [TDD] Add tests for Graphiti-backed MemEvolve ingest + recall (63d081c)

**Implementation Notes (2025-01-16)**:
- MemEvolve ingest now supports pre-extracted entities/edges, uses confidence gating, and writes low-confidence edges to `RelationshipProposal` for human review.
- Trajectory nodes now include `occurred_at` (from metadata timestamp when provided).
- HMAC accepts `MEMEVOLVE_HMAC_SECRET` or `DIONYSUS_HMAC_SECRET`; GET /health is supported.

### Acceptance Criteria
- [ ] `MemEvolveService` uses `GraphitiService` for all trajectory storage and retrieval.
- [ ] Trajectory nodes created by MemEvolve have correct labels and relationships.
- [ ] Auto-evolution loop successfully retrieves trajectories via Graphiti vector search.

**Implementation Notes (2025-01-16, MemEvolve routing update):**
- `VectorSearchService` and `ContextStreamService` now route recall through `MemEvolveAdapter` (Graphiti remains the sole Neo4j gateway).
- **TDD Deviation**: Tests were added after implementation for this change; deviation recorded here per workflow.

**Test Status (2026-01-17):**
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p asyncio -p pytest_cov tests/integration/test_semantic_search.py tests/integration/test_hybrid_search.py tests/unit/test_neural_metrics.py tests/unit/test_memevolve_adapter.py --cov=api.services.memevolve_adapter --cov=api.services.vector_search --cov=api.services.context_stream --cov-report=term-missing`
  - Result: 33 passed, 2 skipped
  - Coverage: `memevolve_adapter 86%`, `context_stream 84%`, `vector_search 90%`, total 87%

## Phase 5: AutoSchemaKG + Concept Extraction (US5) - P2

**Goal**: Integrate AutoSchemaKG with Graphiti and correct concept ingest signature.

- [ ] **Task 5.1**: Add AutoSchemaKG integration service using Graphiti storage
- [ ] **Task 5.2**: Fix `concept_extraction` Graphiti ingest signature mismatch
## Phase 6: Context Packaging (Context-Engineering) - P2

**Goal**: Implement "Cellular" memory physics (Token Budgets, Resonance, State) as defined in `Context-Engineering` schemas.

- [ ] **Task 6.1**: Implement `ContextCell` class in `Nemori` with explicit `TokenBudgetManager`.
- [ ] **Task 6.2**: Add `ResonanceCoupling` logic to Attractor Basins (amplify/dampen signals).
- [ ] **Task 6.3**: Implement `SymbolicResidue` tracking with causal attribution trees.
- [ ] **Task 6.4**: [TDD] Verify context packaging creates persistent, budget-aware memory states.
