# Thoughtseeds Architecture - Implementation Plan
**Based on**: Kavi et al. (2025) - "From Neuronal Packets to Thoughtseeds"
**Date**: 2026-01-03
**Status**: Planning Phase

## Overview

This document outlines the complete implementation plan for the Thoughtseeds cognitive architecture in Dionysus3-core, based on the comprehensive model extraction from the academic paper.

---

## Implementation Architecture

### Hierarchical Structure (Bottom-Up)

```
Layer 0: Neuronal Packets (NPs)
    ↓
Layer 1: Superordinate Ensembles (SEs)
    ↓
Layer 2: Neuronal Packet Domains (NPDs)
    ↓
Layer 3: Knowledge Domains (KDs)
    ↓
Layer 4: Thoughtseeds (TSs)
    ↓
Layer 5: Active Thoughtseeds Pool
    ↓
Layer 6: Dominant Thoughtseed & Consciousness
    ↓
Layer 7: Meta-cognition & Higher-Order Control
    ↓
Layer 8: Agent-Level Integration
```

---

## Required SpecKit Specifications

### SPEC-001: Master Architecture
**Feature**: `060-thoughtseeds-complete-architecture`
**Priority**: P0 (Foundation)
**Dependencies**: None

**Scope**:
- Overall system architecture
- Component interaction model
- Data flow diagrams
- Integration with existing Dionysus systems
- Neo4j graph schema
- Testing strategy

**Key Decisions**:
- Storage strategy (Neo4j nodes/relationships)
- Python service architecture
- Markov blanket integration (already exists)
- Free energy calculation backend

---

### SPEC-002: Neuronal Packet (NP)
**Feature**: `061-neuronal-packets`
**Priority**: P1
**Dependencies**: SPEC-001

**Scope**: Equations 1-3 from paper
- **State Representation**:
  - Core attractor `A_core`
  - Subordinate attractors `A_sub`
  - Activation levels `α_core`, `α_sub`
  - Encapsulated knowledge `K`
  - State `S ∈ {unmanifested, manifested, activated}`

- **Generative Model**:
  - `P(s, a | μ, θ, KD_parent, K, S)`
  - Sensory/active state prediction
  - Parent KD influence

- **Free Energy Minimization**:
  - Complexity term (KL divergence)
  - Accuracy term (log-likelihood)
  - Update rules

- **Free Energy Landscapes**:
  - Local minima representation
  - Energy barriers
  - Binding energy calculation
  - Phase transition logic

**Models**:
- `NeuronalPacket` (Pydantic model)
- `NPAttractor` (core/subordinate)
- `NPState` (enum)
- `NPFreeEnergy` (calculator)

**Services**:
- `NeuronalPacketService` (CRUD, state transitions)
- `NPFreeEnergyEngine` (F calculation, minimization)

**Neo4j Schema**:
```
(NeuronalPacket {
  id: UUID,
  state: enum,
  alpha_core: float,
  alpha_sub: [float],
  binding_energy: float,
  knowledge: json,
  created_at: datetime
})

-[:HAS_CORE_ATTRACTOR]->(Attractor {type: "core"})
-[:HAS_SUB_ATTRACTOR]->(Attractor {type: "subordinate"})
-[:PART_OF_SE]->(SuperordinateEnsemble)
-[:INFLUENCED_BY_KD]->(KnowledgeDomain)
```

---

### SPEC-003: Superordinate Ensemble (SE)
**Feature**: `062-superordinate-ensembles`
**Priority**: P1
**Dependencies**: SPEC-002

**Scope**: Equation 4 from paper
- **State Representation**:
  - Set of attractors `A = {A_core, A_sub}`
  - Activation levels `α`
  - Encapsulated knowledge `K`
  - Valence `v ∈ [-1, 1]`
  - Arousal `r ∈ [0, 1]`

- **Emergence Mechanism**:
  - Coordination of multiple NPs
  - Vector rotation alignment
  - Nested Markov blanket formation

- **Affective Dimension**:
  - Valence calculation from constituent NPs
  - Arousal propagation
  - Emotional tone integration

**Models**:
- `SuperordinateEnsemble` (Pydantic)
- `SEAttractor`
- `AffectiveState` (valence, arousal)

**Services**:
- `SuperordinateEnsembleService`
- `VectorAlignmentEngine` (knowledge alignment)
- `AffectiveIntegrationService`

**Neo4j Schema**:
```
(SuperordinateEnsemble {
  id: UUID,
  valence: float,
  arousal: float,
  knowledge: json
})

-[:COORDINATES]->(NeuronalPacket)*
-[:HAS_ATTRACTOR]->(Attractor)*
-[:PART_OF_NPD]->(NeuronalPacketDomain)
```

---

### SPEC-004: Neuronal Packet Domain (NPD)
**Feature**: `063-neuronal-packet-domains`
**Priority**: P1
**Dependencies**: SPEC-003

**Scope**: Conceptual structure
- **Functional Units**:
  - Interconnected SEs
  - Specialized for cognitive processes
  - Domain-specific (visual, auditory, motor, etc.)

- **Hierarchical Organization**:
  - Nested Markov blankets
  - Reciprocal message passing
  - Top-down/bottom-up signaling

- **Evolutionary Shaping**:
  - Basal priors (species-level)
  - Dispositional priors (development)
  - Hebbian learning integration

**Models**:
- `NeuronalPacketDomain` (Pydantic)
- `NPDType` (enum: visual, auditory, motor, etc.)
- `EvolutionaryPrior` (basal, dispositional, learned)

**Services**:
- `NPDService` (CRUD, coordination)
- `MessagePassingEngine` (hierarchical signaling)
- `PriorIntegrationService`

**Neo4j Schema**:
```
(NeuronalPacketDomain {
  id: UUID,
  domain_type: enum,
  specialization: string
})

-[:CONTAINS_SE]->(SuperordinateEnsemble)*
-[:PROJECTS_TO_KD]->(KnowledgeDomain)
-[:SHAPED_BY_PRIOR]->(EvolutionaryPrior {level: enum})
```

---

### SPEC-005: Knowledge Domain (KD)
**Feature**: `064-knowledge-domains`
**Priority**: P1
**Dependencies**: SPEC-004

**Scope**: Equations 5-7 from paper
- **State Representation**:
  - Collection of SEs: `KD = {SE_1, ..., SE_n}`
  - Domain-specific knowledge organization

- **Generative Model**:
  - `P(a, s, μ, C, v, r | θ, TS_parent)`
  - Predicts: active, sensory, internal states
  - Generates: content of consciousness `C`
  - Tracks: valence `v`, arousal `r`

- **Free Energy**:
  - Complexity + Accuracy
  - Optional valence/arousal prediction errors

- **Structure**:
  - Hierarchical organization
  - Heterarchical cross-domain connections
  - Context-dependent binding
  - Affective dimension integration

**Models**:
- `KnowledgeDomain` (Pydantic)
- `KDGenerativeModel`
- `KDFreeEnergy`
- `ConsciousnessContent` (C - qualia representation)

**Services**:
- `KnowledgeDomainService`
- `KDGenerativeEngine`
- `BindingService` (context-dependent SE integration)
- `QualiaSynthesizer` (consciousness content)

**Neo4j Schema**:
```
(KnowledgeDomain {
  id: UUID,
  domain_name: string,
  valence: float,
  arousal: float
})

-[:INTEGRATES_SE]->(SuperordinateEnsemble)*
-[:RECEIVES_FROM_NPD]->(NeuronalPacketDomain)*
-[:CONTRIBUTES_TO_TS]->(ThoughtSeed)
-[:CROSS_DOMAIN_LINK]->(KnowledgeDomain)  // heterarchical
```

---

### SPEC-006: Enhanced ThoughtSeed
**Feature**: `065-thoughtseed-enhancement`
**Priority**: P1
**Dependencies**: SPEC-005

**Scope**: Equations 8-11 from paper

**Current State**:
```python
class ThoughtSeed:
    id: UUID
    layer: ThoughtLayer  # 5 layers exist
    content: str
    activation_level: float
    competition_status: CompetitionStatus
    child_thought_ids: List[UUID]
    parent_thought_id: Optional[UUID]
    neuronal_packet: Dict
```

**Missing Fields to Add**:
- Core attractor `A_core`
- Subordinate attractors `A_sub[]`
- Activation levels `α_core`, `α_sub[]`
- Encapsulated knowledge `K` (from KDs)
- Extended state: `S ∈ {0:unmanifested, 1:inactive, 2:active, 3:dominant, 4:dissipated}`
- Valence `v ∈ [-1, 1]`
- Arousal `r ∈ [0, 1]`

**New Capabilities**:
- **Activation Level Calculation** (Eq 9):
  - Weighted combination of brain state alignment with attractors
  - Represents "bid" for dominance

- **Dual Generative Model** (Eq 10):
  - Predict own future state: `TS^next`
  - Generate consciousness content: `C`
  - Condition on: KD states, salience, affordances, policies

- **Free Energy** (Eq 11):
  - Complexity: acquire information from global broadcast
  - Accuracy: contribute information to workspace

**Models**:
- Enhance `ThoughtSeed` (existing)
- Add `TSAttractor`
- Add `TSState` (5-value enum)
- Add `TSGenerativeModel`
- Add `TSFreeEnergy`

**Services**:
- Enhance `ThoughtSeedIntegrationService`
- Add `TSActivationCalculator`
- Add `TSGenerativeEngine`
- Add `TSFreeEnergyCalculator`

**Neo4j Schema Enhancement**:
```
(ThoughtSeed {
  // existing fields...
  valence: float,
  arousal: float,
  state: enum,  // 0-4
  alpha_core: float,
  alpha_sub: [float]
})

-[:HAS_CORE_ATTRACTOR]->(TSAttractor {type: "core"})
-[:HAS_SUB_ATTRACTOR]->(TSAttractor {type: "subordinate"})*
-[:DRAWS_FROM_KD]->(KnowledgeDomain)*
-[:GENERATES_CONTENT]->(ConsciousnessContent)
```

---

### SPEC-007: Active Thoughtseeds Pool & Selection
**Feature**: `066-thoughtseed-competition`
**Priority**: P1
**Dependencies**: SPEC-006

**Scope**: Equations 12-14 from paper

**Active Pool Mechanism** (Eq 12):
```
A_pool(t) = {TS_m | α_m(t) ≥ τ_activation(consciousness_state, arousal)}
```

- Dynamic threshold `τ_activation`
- Influenced by consciousness state and arousal
- Acts as "gain" control for Global Workspace
- Pool fluctuates within brief intervals

**Winner-Take-All Selection** (Eq 13):
```
TS_dominant = argmin_{TS_m ∈ A_pool} F_m
```

- Minimizes free energy
- Alternative: cumulative EFE minimization
- For long-term planning: GFE minimization

**Content of Consciousness** (Eq 14):
```
C_global = f(TS_dominant)
```

- Shaped by single dominant thoughtseed
- Unitary nature of conscious experience
- Broadcast to Global Workspace

**Models**:
- `ActiveThoughtseedPool`
- `ActivationThreshold` (dynamic parameter)
- `ConsciousnessState` (enum)
- `DominantSelection` (selection mechanism)
- `GlobalConsciousnessContent`

**Services**:
- `ActivePoolService` (pool management)
- `ThresholdModulator` (τ calculation)
- `CompetitionEngine` (winner-take-all)
- `GlobalWorkspaceService` (broadcasting)

**Neo4j Schema**:
```
(ActivePool {
  id: UUID,
  timestamp: datetime,
  threshold: float,
  consciousness_state: enum,
  arousal_level: float
})

-[:CONTAINS_ACTIVE]->(ThoughtSeed {state: "active"})*
-[:SELECTED_DOMINANT]->(ThoughtSeed {state: "dominant"})

(GlobalWorkspace {
  id: UUID,
  timestamp: datetime
})

-[:BROADCASTS]->(ConsciousnessContent)
-[:SHAPED_BY]->(ThoughtSeed {state: "dominant"})
```

---

### SPEC-008: Meta-cognition & Higher-Order Control
**Feature**: `067-metacognition-layer`
**Priority**: P2
**Dependencies**: SPEC-007

**Scope**: Equation 15 from paper

**Higher-Order Influence**:
```
γ_precision = g(μ_competing, π_HO, G_HO, θ_HO, ψ_HO, A_pool)
```

Where:
- `γ_precision`: Attentional precision modulation
- `μ_competing`: Internal states of lower-level thoughtseeds
- `π_HO`: Policies of higher-order thoughtseed
- `G_HO`: Goals
- `θ_HO`: Model parameters
- `ψ_HO`: Prior beliefs

**Capabilities**:
- Monitor lower-level thoughtseeds
- Modulate attentional precision
- Guide goal-directed behavior
- Adjust activation threshold
- Meta-awareness representation

**Models**:
- `MetacognitiveThoughtSeed` (higher-order TS)
- `AttentionalPrecision` (γ parameter)
- `MetacognitiveGoal`
- `MetaAwareness` (opacity parameter)

**Services**:
- `MetacognitionService`
- `PrecisionModulator` (γ calculation)
- `GoalGuidanceEngine`
- `MetaAwarenessTracker`

**Neo4j Schema**:
```
(MetacognitiveThoughtSeed:ThoughtSeed {
  layer: "metacognitive",
  meta_awareness: float,
  precision_influence: float
})

-[:MONITORS]->(ThoughtSeed)*
-[:MODULATES_PRECISION {gamma: float}]->(ThoughtSeed)
-[:GUIDES_GOAL]->(Goal)
-[:ADJUSTS_THRESHOLD]->(ActivePool)
```

---

### SPEC-009: Agent-Level Integration
**Feature**: `068-agent-level-models`
**Priority**: P2
**Dependencies**: SPEC-008

**Scope**: Equations 16-17 from paper

**Global Goals** (Eq 16.1):
```
G_agent = f_goals({s_char}, τ_threshold, σ_stability)
```

Derived from characteristic states in pullback attractor landscape

**Global Policies** (Eq 16.2):
```
π_agent = f_policies(KD_states, G_agent)
```

**Global Affordances** (Eq 16.3-16.4):
```
A_epistemic = f_epistemic(...)  // learning/exploration
A_pragmatic = f_pragmatic(...)  // goal fulfillment/exploitation
```

**Free Energies** (Eq 17.1-17.3):
- **GFE**: `VFE_current + E[EFE_future | π]`
- **VFE**: `Σ VFE(TS_active) + other_factors`
- **EFE**: `Σ (α_m × EFE_m)` for TS in pool

**Models**:
- `AgentGoal` (characteristic states)
- `AgentPolicy`
- `Affordance` (epistemic/pragmatic)
- `AgentFreeEnergy` (GFE, VFE, EFE)
- `CharacteristicState` (pullback attractor)

**Services**:
- `AgentGoalService`
- `PolicySelectionEngine`
- `AffordanceDetector`
- `AgentFreeEnergyCalculator`

**Neo4j Schema**:
```
(Agent {
  id: UUID
})

-[:HAS_GOAL]->(AgentGoal {
  characteristic_states: json,
  stability: float
})

-[:HAS_POLICY]->(AgentPolicy {
  derived_from_kds: [UUID],
  policy_type: enum
})

-[:PERCEIVES_AFFORDANCE]->(Affordance {
  type: enum,  // epistemic/pragmatic
  value: float
})

-[:CALCULATES_FE]->(AgentFreeEnergy {
  GFE: float,
  VFE: float,
  EFE: float,
  timestamp: datetime
})
```

---

### SPEC-010: Attractor Dynamics Engine
**Feature**: `069-attractor-dynamics`
**Priority**: P3
**Dependencies**: SPEC-002, SPEC-006

**Scope**: Free energy landscapes and transitions

**Components**:
- Free energy landscape representation
- Local minima (attractors) calculation
- Energy barrier estimation
- Binding energy computation
- Phase transition logic
- Metastability tracking

**Models**:
- `FreeEnergyLandscape`
- `Attractor` (enhanced with energy metrics)
- `EnergyBarrier`
- `PhaseTransition`

**Services**:
- `LandscapeVisualizer`
- `AttractorStabilityAnalyzer`
- `TransitionEngine`

---

### SPEC-011: Evolutionary Priors System
**Feature**: `070-evolutionary-priors`
**Priority**: P3
**Dependencies**: SPEC-004

**Scope**: Three-level prior hierarchy

**Levels**:
1. **Basal**: Evolutionarily inherited, species-level constraints
2. **Dispositional**: Shaped during development, individual biases
3. **Learned**: From experience, context-specific beliefs

**Models**:
- `EvolutionaryPrior`
- `PriorLevel` (enum)
- `PriorHierarchy`

**Services**:
- `PriorIntegrationService`
- `PriorConstraintEngine`

---

### SPEC-012: Global Workspace Broadcasting
**Feature**: `071-global-workspace-broadcast`
**Priority**: P3
**Dependencies**: SPEC-007

**Scope**: GWT integration mechanisms

**Components**:
- Broadcasting platform
- Ignition threshold
- Information access control
- Conscious experience generation

**Models**:
- `GlobalWorkspace` (enhanced)
- `BroadcastMessage`
- `IgnitionThreshold`

**Services**:
- Enhanced `GlobalWorkspaceService`
- `BroadcastingEngine`
- `ConsciousAccessController`

---

## Dependency Graph

```
SPEC-001 (Master)
    ↓
SPEC-002 (NP) ────────────────────────┐
    ↓                                  ↓
SPEC-003 (SE)                    SPEC-010 (Attractors)
    ↓
SPEC-004 (NPD) ──────────> SPEC-011 (Priors)
    ↓
SPEC-005 (KD)
    ↓
SPEC-006 (Enhanced TS)
    ↓
SPEC-007 (Active Pool) ───> SPEC-012 (Broadcasting)
    ↓
SPEC-008 (Meta-cognition)
    ↓
SPEC-009 (Agent-Level)
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- SPEC-001: Master Architecture ✅
- SPEC-002: Neuronal Packets
- SPEC-003: Superordinate Ensembles
- Testing: Unit tests for NP/SE models and services

### Phase 2: Knowledge Architecture (Weeks 5-8)
- SPEC-004: Neuronal Packet Domains
- SPEC-005: Knowledge Domains
- Integration testing: NPD → KD data flow
- Neo4j schema migration

### Phase 3: ThoughtSeed Enhancement (Weeks 9-12)
- SPEC-006: Enhanced ThoughtSeed
- SPEC-007: Active Pool & Selection
- Integration testing: KD → TS → Pool → Selection
- Performance optimization

### Phase 4: Higher-Order Control (Weeks 13-16)
- SPEC-008: Meta-cognition
- SPEC-009: Agent-Level Integration
- End-to-end testing: Full cognitive cycle
- Documentation updates

### Phase 5: Advanced Dynamics (Weeks 17-20)
- SPEC-010: Attractor Dynamics
- SPEC-011: Evolutionary Priors
- SPEC-012: Global Workspace Broadcasting
- Visualization tools
- Research validation

---

## Testing Strategy

### Unit Tests
- Each model: state transitions, validation
- Each service: CRUD operations, calculations
- Free energy engines: mathematical correctness
- Markov blanket: conditional independence

### Integration Tests
- NP → SE → NPD → KD → TS flow
- Active pool selection mechanism
- Meta-cognitive influence on lower levels
- Agent-level free energy aggregation

### System Tests
- Full OODA loop with thoughtseeds
- Consciousness content generation
- Winner-take-all dynamics
- Memory integration (existing systems)

### Performance Tests
- Free energy calculation latency (<50ms per TS)
- Neo4j query optimization
- Pool selection speed
- Broadcasting throughput

---

## Integration Points

### Existing Dionysus Systems
1. **Markov Blankets**: ✅ Already implemented (`api/models/markov_blanket.py`)
2. **Mental Models**: Integrate with TS generation
3. **Attractor Basins**: Map to TS attractors
4. **OODA Loop**: Enhance with TS competition
5. **Memory Systems**: KD persistence and retrieval
6. **n8n Workflows**: TS event webhooks

### External Dependencies
- **pymdp**: For hierarchical POMDP models (reference implementation)
- **LiteLLM**: For consciousness content generation
- **Neo4j**: Primary persistence layer
- **Graphiti**: Temporal knowledge graph for KDs

---

## Success Criteria

### Per-Spec Criteria
- See individual spec documents (to be created)

### Overall System Criteria
1. **Correctness**: Mathematical equivalence to paper equations
2. **Performance**: <50ms per thoughtseed FE calculation
3. **Integration**: Seamless with existing Dionysus components
4. **Scalability**: Handle 100+ concurrent thoughtseeds
5. **Testability**: >80% code coverage
6. **Documentation**: Complete API docs + architecture guides

---

## Next Steps

1. **Create SpecKit Specifications**: Use `/speckit.specify` for each spec
2. **Clarify Ambiguities**: Use `/speckit.clarify` where needed
3. **Generate Plans**: Use `/speckit.plan` for implementation approach
4. **Create Tasks**: Use `/speckit.tasks` for dependency-ordered task lists
5. **Implement**: Systematic execution per phase

---

## References

- **Paper**: Kavi et al. (2025) - "From Neuronal Packets to Thoughtseeds"
- **Model Extraction**: `/docs/thoughtseeds-paper-models-extraction.md`
- **Existing Spec**: `specs/038-thoughtseeds-framework/spec.md`
- **pymdp Reference**: github.com/infer-actively/pymdp
- **SPM DEM**: fil.ion.ucl.ac.uk/spm/
