# Feature 038: Thoughtseeds Framework Enhancement

## Overview

Implement missing components from the Thoughtseeds paper (Kavi, Zamora Lopez, Friedman 2024) to complete the neuronal packet architecture, active inference mechanisms, and conscious experience modeling in dionysus3-core.

## Source Reference

**Paper**: "Thoughtseeds: Evolutionary Priors, Nested Markov Blankets, and the Emergence of Embodied Cognition"
- Authors: Prakash Chandra Kavi, Gorka Zamora Lopez, Daniel Ari Friedman
- Institutions: Universitat Pompeu Fabra (Barcelona), Active Inference Institute (Davis, CA)
- Keywords: neuronal packets, evolution, embodied cognition, Markov Blanket, thoughtseed, inner screen

## Current Implementation Status

| Concept | Status | Completeness |
|---------|--------|--------------|
| Thoughtseeds | PARTIAL | 60% |
| Neuronal Packets | PARTIAL | 50% |
| Superordinate Ensembles | STUB | 5% |
| Neuronal Packet Domains | NOT IMPL | 0% |
| Knowledge Domains | PARTIAL | 40% |
| Inner Screen | NOT IMPL | 0% |
| Evolutionary Priors | NOT IMPL | 0% |
| Free Energy (EFE) | PARTIAL | 70% |
| Free Energy (VFE/GFE) | NOT IMPL | 0% |
| Meta-Cognition | PARTIAL | 65% |
| Markov Blankets | NOT IMPL | 0% |
| Active Inference | PARTIAL | 50% |
| Attractor Basins | PARTIAL | 45% |
| Metaplasticity | FULL | 95% |
| Fractal Structure | FULL | 100% |

---

## Requirements

### FR-038-001: Inner Screen Implementation

**Priority**: HIGH

Implement explicit Inner Screen as the locus of conscious experience where dominant thoughtseed content is projected.

**Components**:
1. `InnerScreen` model with phenomenal properties (brightness, clarity, focus)
2. Content binding mechanism for multi-modal integration
3. Attentional spotlight with adjustable precision
4. Dominant thoughtseed projection interface
5. Stream of thoughts serialization

**Mathematical Reference** (Paper Section 4):
- Content shaped by dominant thoughtseed within active pool
- Unitary nature: single coherent experience at any moment
- Equation 34: `C_IS(t) = content(θ_dominant)`

**Files to Create/Modify**:
- `api/models/inner_screen.py` (NEW)
- `api/services/inner_screen_service.py` (NEW)
- `api/agents/consciousness_manager.py` (MODIFY)

---

### FR-038-002: Neuronal Packet Domains (NPDs)

**Priority**: HIGH

Create explicit NPD taxonomy per the 4-layer Thoughtseeds hierarchy.

**Components**:
1. NPD model with domain type enum: SENSORY, ACTIVE, INTERNAL
2. Domain boundary enforcement via Markov blanket partitioning
3. Cross-domain coherence constraints
4. NPD-to-SE composition relationships

**Mathematical Reference** (Paper Equations 7-9):
- State representation: `S_NPD(t) = {S_SE1(t), S_SE2(t), ..., S_SEn(t)}`
- Generative model: `P(o, a | S_NPD, θ_NPD, θ_TS)`
- VFE minimization at NPD level

**Files to Create/Modify**:
- `api/models/npd.py` (NEW)
- `api/services/npd_service.py` (NEW)

---

### FR-038-003: VFE and GFE Calculations

**Priority**: HIGH

Extend free energy calculations beyond EFE to include Variational and Generalized Free Energy.

**Components**:
1. VFE calculation: `VFE = E_q[log q(μ) - log p(o, μ | θ)]`
2. GFE calculation: `GFE = VFE + E[EFE]` over time horizon
3. Information gain (epistemic value) component
4. Pragmatic value component
5. Per-level free energy (NP, SE, NPD, KD, Thoughtseed)

**Mathematical Reference** (Paper Equations 3, 6, 9, 13, 22, 23):
- Equation 3: NP VFE decomposition
- Equation 22: Thoughtseed VFE with characteristic states
- Equation 23: Thoughtseed GFE = VFE + E[EFE]
- Equation 24: EFE = epistemic + pragmatic components

**Files to Create/Modify**:
- `api/services/efe_engine.py` (MODIFY - extend)
- `api/services/vfe_engine.py` (NEW)
- `api/services/gfe_engine.py` (NEW)

---

### FR-038-004: Markov Blankets

**Priority**: HIGH

Implement nested Markov blanket structure for thoughtseeds and ensembles.

**Components**:
1. Blanket model: sensory states (s), active states (a)
2. Conditional independence enforcement: `P(μ | s, a, η) = P(μ | s, a)`
3. Nested blanket hierarchy (NP → SE → NPD → Thoughtseed)
4. Blanket evolution tracking over time
5. Blanket boundary energy calculation

**Mathematical Reference** (Paper Equations S.1, S.2):
- `μ ⊥⊥ η | (s, a)` - internal states independent of external given blanket
- Thoughtseed Network ⊆ Internal states (μ)

**Files to Create/Modify**:
- `api/models/markov_blanket.py` (NEW)
- `api/services/blanket_service.py` (NEW)

---

### FR-038-005: Evolutionary Priors Hierarchy

**Priority**: MEDIUM

Create explicit prior hierarchy with phylogenetic and ontogenetic components.

**Components**:
1. Prior types: Basal (B), Lineage-Specific (L), Dispositional (D), Learned (λ)
2. Phylogenetic priors (B + L): slow-changing, species-wide
3. Ontogenetic priors (D + λ): individual, dynamic
4. Quasi-hierarchical influence flow
5. Prior-to-thoughtseed constraint propagation

**Mathematical Reference** (Paper Section 9.1):
- Basal: `P(B) = {P(B_i)}` - fundamental needs
- Lineage: `P(L | B)` - conditioned on basal
- Dispositional: `P(D | B, L)` - individual predispositions
- Learned: `P(λ | experiences)` - dynamic updates

**Files to Create/Modify**:
- `api/models/evolutionary_prior.py` (NEW)
- `api/services/prior_service.py` (NEW)

---

### FR-038-006: Superordinate Ensembles

**Priority**: MEDIUM

Complete SE implementation per existing spec FR-030-002.

**Components**:
1. SE model with constituent NP references
2. PART_OF relationship persistence to Neo4j
3. Recursive ensemble composition
4. Cross-level constraint enforcement
5. SE state integration function

**Mathematical Reference** (Paper Equation 4):
- `S_SE(t) = f_integrate({S_NP1(t), S_NP2(t), ..., S_NPm(t)})`

**Files to Create/Modify**:
- `api/models/cognitive.py` (MODIFY)
- `api/services/ensemble_service.py` (NEW)

---

### FR-038-007: Affordances Model

**Priority**: MEDIUM

Implement Gibson-inspired affordance model for active inference.

**Components**:
1. Epistemic affordances: information gain opportunities
2. Pragmatic affordances: goal fulfillment opportunities
3. Action possibility space derived from Umwelt
4. Affordance-to-policy mapping
5. EFE-based affordance evaluation

**Mathematical Reference** (Paper Equations 20, 24):
- `A_epistemic = f_e(KD states, sensory input, goals)`
- `A_pragmatic = f_p(KD states, sensory input, goals)`
- `EFE = E_epistemic + E_pragmatic`

**Files to Create/Modify**:
- `api/models/affordance.py` (NEW)
- `api/services/affordance_service.py` (NEW)

---

### FR-038-008: Attractor Basin Geometry

**Priority**: LOW

Add explicit attractor basin geometry calculations for energy landscape analysis.

**Components**:
1. Basin depth calculation (binding energy)
2. Basin width/volume estimation
3. Energy barrier between attractors
4. Bifurcation point detection
5. Heteroclinic connection mapping
6. Basin switching dynamics

**Mathematical Reference** (Paper Figure 3):
- Core attractor: deep local minimum
- Subordinate attractors: shallower local minima
- Energy barriers separate attractor states

**Files to Create/Modify**:
- `api/services/attractor_service.py` (NEW)
- `api/models/attractor_basin.py` (NEW)

---

## Non-Functional Requirements

### NFR-038-001: Neo4j Integration

All new models must persist to Neo4j via n8n webhooks (no direct Bolt connections except Graphiti).

### NFR-038-002: Performance

Free energy calculations must complete within 50ms for single thoughtseed, 200ms for full network.

### NFR-038-003: Compatibility

Must integrate with existing:
- ThoughtSeed model (thought.py)
- EFE Engine (efe_engine.py)
- Consciousness Manager (consciousness_manager.py)
- Metaplasticity Service (metaplasticity_service.py)

---

## Integration Points

1. **ThoughtSeed ↔ Inner Screen**: Dominant thoughtseed projects content to inner screen
2. **NP ↔ SE ↔ NPD**: Hierarchical composition with nested Markov blankets
3. **EFE ↔ VFE ↔ GFE**: Unified free energy calculation pipeline
4. **Priors ↔ Thoughtseeds**: Evolutionary priors constrain thoughtseed emergence
5. **Affordances ↔ Active Inference**: Affordances drive policy selection

---

## Testing Strategy

1. Unit tests for each new model
2. Integration tests for hierarchical composition
3. Free energy calculation accuracy tests against paper equations
4. Performance benchmarks for network-wide calculations
5. Neo4j persistence verification

---

## References

1. Kavi, P.C., Zamora Lopez, G., Friedman, D.A. (2024). Thoughtseeds: Evolutionary Priors, Nested Markov Blankets, and the Emergence of Embodied Cognition.
2. Friston, K.J. (2010). The free-energy principle: A unified approach to biological systems.
3. Ramstead, M.J.D. et al. (2023). The inner screen model of consciousness.
4. Parr, T., Friston, K.J. (2019). Generalised free energy and active inference.
