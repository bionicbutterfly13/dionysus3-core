# Feature 038: Implementation Plan

## Phase 1: Foundation Models (Week 1)

### 1.1 Markov Blanket Model
```
api/models/markov_blanket.py
├── MarkovBlanket (Pydantic model)
│   ├── sensory_states: List[SensoryState]
│   ├── active_states: List[ActiveState]
│   ├── internal_states: List[UUID]  # references to internal entities
│   ├── external_states: List[UUID]  # references to external entities
│   ├── blanket_id: UUID
│   └── parent_blanket_id: Optional[UUID]  # for nesting
└── BlanketHierarchy (composite structure)
```

### 1.2 Evolutionary Priors Model
```
api/models/evolutionary_prior.py
├── PriorType (Enum): BASAL, LINEAGE_SPECIFIC, DISPOSITIONAL, LEARNED
├── EvolutionaryPrior (Pydantic model)
│   ├── prior_id: UUID
│   ├── prior_type: PriorType
│   ├── probability_distribution: Dict[str, float]
│   ├── stability: float  # 0-1, higher = more stable
│   └── parent_prior_id: Optional[UUID]  # for hierarchy
└── PriorHierarchy (composite structure)
```

### 1.3 NPD Model
```
api/models/npd.py
├── NPDType (Enum): SENSORY, ACTIVE, INTERNAL
├── NeuronalPacketDomain (Pydantic model)
│   ├── npd_id: UUID
│   ├── domain_type: NPDType
│   ├── constituent_ses: List[UUID]
│   ├── markov_blanket: MarkovBlanket
│   └── coherence_constraints: Dict[str, float]
```

---

## Phase 2: Free Energy Extensions (Week 2)

### 2.1 VFE Engine
```
api/services/vfe_engine.py
├── VFEEngine
│   ├── calculate_vfe(entity, observations, parameters)
│   │   ├── surprise = -log P(o | θ)
│   │   ├── kl_divergence = KL(q(μ) || p(μ))
│   │   └── return VFEResponse(vfe=surprise+kl, components)
│   ├── calculate_accuracy(predictions, observations)
│   └── calculate_complexity(posterior, prior)
```

### 2.2 GFE Engine
```
api/services/gfe_engine.py
├── GFEEngine
│   ├── calculate_gfe(entity, time_horizon, policy)
│   │   ├── vfe = vfe_engine.calculate_vfe(entity)
│   │   ├── expected_efe = E[efe_engine.calculate_efe(future_states)]
│   │   └── return GFEResponse(gfe=vfe+expected_efe)
│   └── project_future_states(entity, policy, steps)
```

### 2.3 EFE Engine Extensions
```
api/services/efe_engine.py (MODIFY)
├── Add epistemic_component(entity) -> float
├── Add pragmatic_component(entity, goals) -> float
├── Decompose EFE = epistemic + pragmatic
└── Add per-level EFE (NP, SE, NPD, Thoughtseed)
```

---

## Phase 3: Inner Screen & Consciousness (Week 3)

### 3.1 Inner Screen Model
```
api/models/inner_screen.py
├── PhenomenalProperties
│   ├── brightness: float  # 0-1
│   ├── clarity: float     # 0-1
│   ├── focus_width: float # attention breadth
│   └── stability: float   # temporal persistence
├── InnerScreenContent
│   ├── dominant_thoughtseed_id: UUID
│   ├── bound_content: Dict[str, Any]  # multi-modal
│   ├── phenomenal_props: PhenomenalProperties
│   └── timestamp: datetime
└── InnerScreen
    ├── current_content: InnerScreenContent
    ├── content_history: List[InnerScreenContent]
    └── attentional_spotlight: Spotlight
```

### 3.2 Inner Screen Service
```
api/services/inner_screen_service.py
├── InnerScreenService
│   ├── project_content(thoughtseed: ThoughtSeed) -> InnerScreenContent
│   ├── bind_multimodal(sources: List[ContentSource]) -> BoundContent
│   ├── update_spotlight(precision: float, focus: UUID)
│   ├── get_stream_of_thoughts(window: int) -> List[InnerScreenContent]
│   └── integrate_with_consciousness_manager()
```

---

## Phase 4: Affordances & Active Inference (Week 4)

### 4.1 Affordance Model
```
api/models/affordance.py
├── AffordanceType (Enum): EPISTEMIC, PRAGMATIC
├── Affordance
│   ├── affordance_id: UUID
│   ├── affordance_type: AffordanceType
│   ├── action_space: List[Action]
│   ├── information_gain: float  # for epistemic
│   ├── goal_alignment: float    # for pragmatic
│   └── source_entity_id: UUID
└── AffordanceSet (collection per context)
```

### 4.2 Affordance Service
```
api/services/affordance_service.py
├── AffordanceService
│   ├── discover_epistemic(kd_states, sensory) -> List[Affordance]
│   ├── discover_pragmatic(kd_states, goals) -> List[Affordance]
│   ├── evaluate_affordance(affordance, policy) -> float  # EFE
│   ├── select_optimal(affordances) -> Affordance
│   └── map_to_policy(affordance) -> Policy
```

---

## Phase 5: Superordinate Ensembles & Attractor Geometry (Week 5)

### 5.1 Complete SE Implementation
```
api/services/ensemble_service.py
├── EnsembleService
│   ├── compose_se(nps: List[NeuronalPacket]) -> SuperordinateEnsemble
│   ├── integrate_states(se: SE) -> StateVector
│   ├── persist_part_of_relation(np_id, se_id) -> Neo4jResult
│   └── enforce_constraints(se: SE) -> ValidationResult
```

### 5.2 Attractor Basin Service
```
api/services/attractor_service.py
├── AttractorService
│   ├── calculate_basin_depth(attractor) -> float
│   ├── calculate_basin_width(attractor) -> float
│   ├── calculate_energy_barrier(a1, a2) -> float
│   ├── detect_bifurcation(landscape, perturbation) -> bool
│   ├── find_heteroclinic_connections(attractors) -> List[Connection]
│   └── visualize_landscape(attractors) -> LandscapeMap
```

---

## Integration Sequence

```
1. MarkovBlanket + EvolutionaryPrior → Foundation
2. NPD + SE extensions → Hierarchical structure
3. VFE + GFE → Complete free energy pipeline
4. InnerScreen → Consciousness locus
5. Affordances → Active inference completion
6. AttractorBasin → Energy landscape analysis
7. Integration tests → Validate full pipeline
8. Neo4j persistence → Store all new entities
```

---

## Dependency Graph

```
                    ┌─────────────────┐
                    │ MarkovBlanket   │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │    NP     │    │    SE     │    │   NPD     │
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  ┌─────────────────┐
                  │  ThoughtSeed    │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐   ┌────────────┐   ┌────────────┐
   │ VFE/GFE    │   │ InnerScreen│   │ Affordance │
   └────────────┘   └────────────┘   └────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
               ┌───────────────────┐
               │ ConsciousnessManager │
               └───────────────────┘
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Free energy calculations too slow | Pre-compute per-entity, cache results |
| Markov blanket nesting complexity | Limit depth to 4 levels (NP→SE→NPD→TS) |
| Neo4j write bottleneck | Batch writes via n8n webhook queuing |
| Breaking existing EFE engine | Extend, don't replace; add new methods |
