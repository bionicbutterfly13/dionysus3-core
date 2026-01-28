# Track Plan: Jungian Cognitive Archetypes

**Track ID**: 002-jungian-archetypes
**Status**: In Progress
**Branch**: `feature/002-jungian-archetypes`

## Integration (IO Map)

### Attachment Points

| File | Line/Method | Integration |
|------|-------------|-------------|
| `api/models/priors.py` | PriorHierarchy class | Add DISPOSITIONAL archetypes |
| `api/models/autobiographical.py` | DevelopmentArchetype enum | Migrate to JungianArchetype |
| `api/services/efe_engine.py` | `select_dominant_thought()` | Archetype-weighted EFE |
| `api/services/memory_basin_router.py` | `BASIN_MAPPING` | Archetype→Basin affinity |
| `api/services/narrative_extraction_service.py` | `extract_narrative()` | Motif→Archetype evidence |
| `api/services/consciousness/active_inference_analyzer.py` | `map_resonance_to_archetype()` | Replace with EFE-based |
| `api/services/arousal_system_service.py` | `_update_arousal()` | Allostatic load for resonance |

### Inlets

- Content strings from `ConsciousnessManager.run_cycle()`
- Tool invocation events from agent callbacks
- Basin activation signals from `MemoryBasinRouter`
- Arousal/precision state from `ArousalSystemService`

### Outlets

- `ConsciousnessManager.current_archetype` state
- `ShadowLog` entries for suppressed archetypes
- Archetype evidence persisted to Graphiti episodic memory
- Precision updates fed to `EFEEngine` calculations

---

## Phase 1: Archetype Prior Structure ✅

**Goal**: Extend the prior hierarchy with the 12 Jungian archetypes as Dispositional Priors.

- [x] **Task 1.1**: Create `JungianArchetype` enum in `api/models/autobiographical.py`
    - 12 primary archetypes (SAGE, WARRIOR, CREATOR, etc.)
    - 12 shadow archetypes (FOOL, VICTIM, DESTROYER, etc.)
    - Deprecate old `DevelopmentArchetype` with alias

- [x] **Task 1.2**: Create `ArchetypePrior` model in `api/models/priors.py`
    - Fields: archetype, dominant_attractor, subordinate_attractors
    - Fields: preferred_actions, avoided_actions, shadow
    - Fields: precision, activation_threshold
    - Include `ARCHETYPE_DEFINITIONS` constant with all 12 configured

- [x] **Task 1.3**: Extend `PriorHierarchy` in `api/models/priors.py`
    - Add `dispositional_archetypes: list[ArchetypePrior]`
    - Factory method to initialize from `ARCHETYPE_DEFINITIONS`
    - Integrate with existing BASAL/LEARNED hierarchy

- [x] **Task 1.4**: Write unit tests for archetype models (25 tests passing)
    - Test: `test_archetype_prior_creation`
    - Test: `test_prior_hierarchy_includes_archetypes`
    - Test: `test_archetype_shadow_mapping`
    - Target: `tests/unit/test_archetype_priors.py`

---

## Phase 2: EFE-Based Archetype Competition ✅

**Goal**: Implement archetype competition via Expected Free Energy minimization.

- [x] **Task 2.1**: Add archetype EFE calculation to `api/services/efe_engine.py`
    - New method: `calculate_archetype_efe(content, archetype_prior) -> float`
    - Use precision weighting from archetype prior
    - Factor in preferred/avoided action affordances

- [x] **Task 2.2**: Extend with `select_dominant_archetype()` method
    - Input: content + list of active archetypes
    - Calculate EFE for each archetype
    - Return dominant archetype (argmin EFE)
    - Return list of suppressed archetypes for shadow logging

- [x] **Task 2.3**: Create `ArchetypeShadowLog` class in `api/services/shadow_log_service.py`
    - Model: `ShadowEntry(archetype, efe_score, timestamp, context)`
    - Methods: `log_suppression()`, `get_recent(window)`, `check_resonance()`
    - In-memory storage with configurable window size

- [x] **Task 2.4**: Write unit tests for EFE competition (30 tests passing)
    - Test: `test_archetype_efe_calculation`
    - Test: `test_dominant_archetype_selection`
    - Test: `test_suppressed_archetypes_logged`
    - Test: `test_shadow_log_retrieval`
    - Target: `tests/unit/test_archetype_efe.py`

---

## Phase 3: Narrative → Archetype Evidence Pipeline ✅

**Goal**: Extract archetype evidence from narrative motifs and SVO patterns.

- [x] **Task 3.1**: Define archetype motif patterns in `api/models/autobiographical.py`
    - Constant: `ARCHETYPE_MOTIF_PATTERNS` dict
    - Maps narrative patterns to archetype + evidence weight
    - Example: "hero.*slay" → WARRIOR +0.3

- [x] **Task 3.2**: Extend `narrative_extraction_service.py` with archetype extraction
    - New method: `extract_archetype_evidence(content) -> list[ArchetypeEvidence]`
    - New method: `aggregate_archetype_evidence(evidence_list) -> dict[str, float]`
    - New method: `extract_relationships_with_archetypes()` for combined extraction
    - Return weighted evidence for each detected archetype

- [x] **Task 3.3**: Implement Bayesian precision update in `api/services/efe_engine.py`
    - New method: `update_archetype_precision_bayesian(archetype, evidence_weight, direction)`
    - Simple Bayesian update: posterior = prior * likelihood
    - Clamped to [0.0, 1.0]
    - (Completed in Phase 2)

- [ ] **Task 3.4**: Wire narrative extraction to archetype pipeline
    - In `MemoryBasinRouter.route_memory_with_resonance()`
    - After narrative extraction, call `extract_archetype_evidence()`
    - Feed evidence to EFE engine for precision updates
    - (Deferred to Phase 5 Integration)

- [x] **Task 3.5**: Write unit tests for narrative evidence pipeline (25 tests passing)
    - Test: `test_motif_pattern_extraction`
    - Test: `test_svo_to_archetype_evidence`
    - Test: `test_bayesian_precision_update` (Phase 2)
    - Test: `test_narrative_pipeline_integration`
    - Target: `tests/unit/test_archetype_narrative.py`

---

## Phase 4: Shadow Log & Resonance Protocol ✅

**Goal**: Implement shadow logging and resonance rebalancing under high allostatic load.

- [x] **Task 4.1**: Define resonance thresholds in `api/models/priors.py`
    - Constant: `RESONANCE_THRESHOLD = 0.75` (allostatic load threshold)
    - Constant: `RESONANCE_ACTIVATION_EFE = 0.4` (shadow candidate threshold)
    - Constant: `SHADOW_WINDOW_SIZE = 10` (recent suppressions to consider)
    - (Completed in Phase 2)

- [x] **Task 4.2**: Extend `ArousalSystemService` with allostatic load calculation
    - New method: `get_allostatic_load(state: SubcorticalState) -> float`
    - Components: NE tonic (uncertainty), DA tonic (goal deficit), NE phasic (errors), gain deficit
    - Return normalized load (0-1)

- [x] **Task 4.3**: Implement resonance protocol in `api/services/shadow_log_service.py`
    - Method: `check_resonance(allostatic_load) -> Optional[ShadowEntry]`
    - Method: `get_resonance_candidates(max_candidates) -> List[ShadowEntry]`
    - If load >= RESONANCE_THRESHOLD, return lowest-EFE candidate
    - (Completed in Phase 2)

- [ ] **Task 4.4**: Wire resonance to `ConsciousnessManager`
    - In DECIDE phase, check for resonance before action selection
    - If resonance triggered, temporarily boost suppressed archetype
    - Log resonance event for episodic memory
    - (Deferred to Phase 5 Integration)

- [x] **Task 4.5**: Write unit tests for resonance protocol (23 tests passing)
    - Test: `test_allostatic_load_calculation` (6 tests)
    - Test: `test_resonance_threshold_trigger` (5 tests)
    - Test: `test_shadow_candidate_selection` (4 tests)
    - Test: `test_resonance_archetype_boost` (3 tests)
    - Test: `test_integration_with_arousal_service` (2 tests)
    - Target: `tests/unit/test_archetype_resonance.py`

---

## Phase 5: Integration & Verification ✅

**Goal**: Wire all components together and verify end-to-end archetype flow.

- [x] **Task 5.1**: Update `ConsciousnessManager` with archetype state tracking
    - Add field: `current_archetype: ArchetypePrior | None`
    - Add field: `archetype_history: list[tuple[str, str, str]]`
    - New method: `update_archetype_state()` - runs EFE competition each cycle
    - New method: `get_archetype_context()` - returns state for context injection
    - Integrated into `_run_ooda_cycle()` before result return

- [ ] **Task 5.2**: Update `active_inference_analyzer.py` to use EFE-based classification
    - Replace heuristic `map_resonance_to_archetype()` with EFE call
    - Feed tool invocation patterns as evidence
    - Return dominant archetype from EFE engine
    - (Deferred - not critical for MVP)

- [ ] **Task 5.3**: Update basin router with archetype affinity weighting
    - In `_activate_basin()`, factor in current archetype affinity
    - Archetype with matching dominant_attractor boosts basin probability
    - Log archetype→basin alignment to memory
    - (Deferred - can be added incrementally)

- [x] **Task 5.4**: Integration tests written
    - Target: `tests/integration/test_archetype_integration.py` (14 tests passing)
    - Verify: archetype competition → shadow logging → resonance
    - Verify: narrative evidence → precision update flow

- [x] **Task 5.5**: Write end-to-end tests (14 tests passing)
    - Test: `TestArchetypeEFEIntegration` (3 tests)
    - Test: `TestNarrativeToArchetypeFlow` (2 tests)
    - Test: `TestSuppressionAndResonanceCycle` (3 tests)
    - Test: `TestArchetypeBasinAlignment` (3 tests)
    - Test: `TestConsciousnessManagerArchetypeState` (3 tests)

- [ ] **Task 5.6**: Update documentation
    - Update `docs/garden/content/silver-bullets/concepts/` with archetype pages
    - Link to Thoughtseeds framework reference
    - Document archetype→basin mappings
    - (Deferred - documentation task)

---

## Critical Files Summary

| File | Changes |
|------|---------|
| `api/models/autobiographical.py` | JungianArchetype enum, ARCHETYPE_MOTIF_PATTERNS |
| `api/models/priors.py` | ArchetypePrior, ARCHETYPE_DEFINITIONS, resonance constants |
| `api/services/efe_engine.py` | calculate_archetype_efe(), update_archetype_precision() |
| `api/services/shadow_log_service.py` | NEW - ShadowLog service |
| `api/services/narrative_extraction_service.py` | extract_archetype_evidence() |
| `api/services/arousal_system_service.py` | get_allostatic_load() |
| `api/services/consciousness_manager.py` | Archetype state tracking |
| `api/services/consciousness/active_inference_analyzer.py` | EFE-based classification |
| `api/services/memory_basin_router.py` | Archetype affinity weighting |
| `tests/unit/test_archetype_*.py` | NEW - Unit test files |
| `tests/integration/test_archetype_integration.py` | NEW - Integration tests |
| `scripts/test_archetype_integration.py` | NEW - Integration verification |

---

## Verification Checklist

Before marking track complete:

- [ ] All unit tests pass: `pytest tests/unit/test_archetype_*.py -v`
- [ ] All integration tests pass: `pytest tests/integration/test_archetype_integration.py -v`
- [ ] Coverage >80%: `pytest --cov=api/services --cov=api/models tests/`
- [ ] No orphan code (all new services have callers)
- [ ] IO Map verified (inlets/outlets documented)
- [ ] Documentation updated in Quartz garden

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| EFE calculation slow | Cache archetype EFE per basin; lazy evaluation |
| Too many shadow entries | Time-windowed cleanup; max buffer size |
| Resonance triggers too often | Tune RESONANCE_THRESHOLD empirically |
| Narrative evidence noisy | Use confidence thresholds; require multiple motifs |
| Backward compatibility | Alias old DevelopmentArchetype to new enum |
