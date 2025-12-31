# Feature 038: Tasks

## Phase 1: Foundation Models

### T038-001: Create Markov Blanket Model
- [ ] Create `api/models/markov_blanket.py`
- [ ] Implement `SensoryState`, `ActiveState` Pydantic models
- [ ] Implement `MarkovBlanket` with conditional independence properties
- [ ] Add nesting via `parent_blanket_id`
- [ ] Create unit tests in `tests/unit/test_markov_blanket.py`

### T038-002: Create Evolutionary Priors Model
- [ ] Create `api/models/evolutionary_prior.py`
- [ ] Implement `PriorType` enum (BASAL, LINEAGE_SPECIFIC, DISPOSITIONAL, LEARNED)
- [ ] Implement `EvolutionaryPrior` with probability distributions
- [ ] Add quasi-hierarchical influence flow logic
- [ ] Create unit tests

### T038-003: Create NPD Model
- [ ] Create `api/models/npd.py`
- [ ] Implement `NPDType` enum (SENSORY, ACTIVE, INTERNAL)
- [ ] Implement `NeuronalPacketDomain` with SE composition
- [ ] Add domain boundary validation
- [ ] Create unit tests

---

## Phase 2: Free Energy Extensions

### T038-004: Implement VFE Engine
- [ ] Create `api/services/vfe_engine.py`
- [ ] Implement surprise calculation: `-log P(o | θ)`
- [ ] Implement KL divergence: `KL(q(μ) || p(μ))`
- [ ] Implement `VFEResponse` model
- [ ] Add accuracy and complexity component methods
- [ ] Create unit tests with known values

### T038-005: Implement GFE Engine
- [ ] Create `api/services/gfe_engine.py`
- [ ] Implement future state projection
- [ ] Implement `GFE = VFE + E[EFE]` calculation
- [ ] Add time horizon parameter
- [ ] Create unit tests

### T038-006: Extend EFE Engine
- [ ] Add `epistemic_component()` method to efe_engine.py
- [ ] Add `pragmatic_component()` method
- [ ] Add per-level EFE calculation (NP, SE, NPD, Thoughtseed)
- [ ] Ensure backward compatibility
- [ ] Update existing tests

---

## Phase 3: Inner Screen & Consciousness

### T038-007: Create Inner Screen Model
- [ ] Create `api/models/inner_screen.py`
- [ ] Implement `PhenomenalProperties` (brightness, clarity, focus, stability)
- [ ] Implement `InnerScreenContent` with multimodal binding
- [ ] Implement `Spotlight` for attentional focus
- [ ] Create unit tests

### T038-008: Create Inner Screen Service
- [ ] Create `api/services/inner_screen_service.py`
- [ ] Implement `project_content()` for thoughtseed → screen
- [ ] Implement `bind_multimodal()` for content integration
- [ ] Implement `get_stream_of_thoughts()` for temporal history
- [ ] Create unit tests

### T038-009: Integrate Inner Screen with Consciousness Manager
- [ ] Modify `api/agents/consciousness_manager.py`
- [ ] Add inner screen initialization in constructor
- [ ] Add content projection after dominant thoughtseed selection
- [ ] Add phenomenal property updates based on flow state
- [ ] Create integration tests

---

## Phase 4: Affordances & Active Inference

### T038-010: Create Affordance Model
- [ ] Create `api/models/affordance.py`
- [ ] Implement `AffordanceType` enum (EPISTEMIC, PRAGMATIC)
- [ ] Implement `Affordance` with action space
- [ ] Implement `AffordanceSet` collection
- [ ] Create unit tests

### T038-011: Create Affordance Service
- [ ] Create `api/services/affordance_service.py`
- [ ] Implement `discover_epistemic()` - information gain opportunities
- [ ] Implement `discover_pragmatic()` - goal fulfillment opportunities
- [ ] Implement `evaluate_affordance()` using EFE
- [ ] Implement `select_optimal()` for policy selection
- [ ] Create unit tests

---

## Phase 5: Superordinate Ensembles & Attractor Geometry

### T038-012: Complete SE Implementation
- [ ] Create `api/services/ensemble_service.py`
- [ ] Implement `compose_se()` from NP collection
- [ ] Implement `integrate_states()` per Equation 4
- [ ] Implement `persist_part_of_relation()` to Neo4j
- [ ] Create integration tests with Neo4j

### T038-013: Create Attractor Basin Service
- [ ] Create `api/models/attractor_basin.py`
- [ ] Create `api/services/attractor_service.py`
- [ ] Implement basin depth calculation (binding energy)
- [ ] Implement energy barrier calculation
- [ ] Implement bifurcation detection
- [ ] Create unit tests

---

## Phase 6: Prior Service & Integration

### T038-014: Create Prior Service
- [ ] Create `api/services/prior_service.py`
- [ ] Implement phylogenetic prior loading
- [ ] Implement ontogenetic prior updates
- [ ] Implement prior-to-thoughtseed constraint propagation
- [ ] Create unit tests

### T038-015: Create Blanket Service
- [ ] Create `api/services/blanket_service.py`
- [ ] Implement blanket creation for new entities
- [ ] Implement blanket evolution tracking
- [ ] Implement conditional independence validation
- [ ] Create unit tests

---

## Phase 7: Neo4j Persistence

### T038-016: Persist New Models to Neo4j
- [ ] Add MarkovBlanket to Neo4j via n8n webhook
- [ ] Add EvolutionaryPrior to Neo4j
- [ ] Add NPD to Neo4j
- [ ] Add Affordance to Neo4j
- [ ] Add PART_OF, CONTAINS, INFLUENCES relationships
- [ ] Create persistence tests

### T038-017: Ingest Thoughtseeds Paper
- [ ] Extract key entities from paper (concepts, equations, authors)
- [ ] Create knowledge graph nodes via Graphiti
- [ ] Link concepts to implementation files
- [ ] Enable semantic search over paper content
- [ ] Verify ingestion via recall queries

---

## Phase 8: Testing & Documentation

### T038-018: Integration Tests
- [ ] Test full pipeline: NP → SE → NPD → Thoughtseed → InnerScreen
- [ ] Test VFE → EFE → GFE calculation chain
- [ ] Test affordance discovery → policy selection
- [ ] Test prior constraint propagation
- [ ] Benchmark performance (< 200ms for network)

### T038-019: Documentation
- [ ] Update CLAUDE.md with new architecture
- [ ] Add docstrings to all new models and services
- [ ] Create architecture diagram
- [ ] Document Neo4j schema extensions

---

## Dependencies

```
T038-001 → T038-003 (Blanket before NPD)
T038-002 → T038-014 (Prior model before service)
T038-004 → T038-005 (VFE before GFE)
T038-007 → T038-008 → T038-009 (Model → Service → Integration)
T038-010 → T038-011 (Affordance model before service)
T038-003 → T038-012 (NPD before SE completion)
All models → T038-016 (Persistence after models)
```

---

## Acceptance Criteria

1. All 8 major requirements (FR-038-001 through FR-038-008) implemented
2. Free energy calculations match paper equations (±5% tolerance)
3. Inner Screen projects dominant thoughtseed content
4. Markov blankets enforce conditional independence
5. Evolutionary priors constrain thoughtseed emergence
6. All tests pass with >80% coverage on new code
7. Performance benchmarks met (<200ms for full network)
8. Paper content indexed and searchable in Neo4j
