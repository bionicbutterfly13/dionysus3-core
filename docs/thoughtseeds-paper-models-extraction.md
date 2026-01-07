# Thoughtseeds Paper - Complete Model Extraction
**Source**: "From Neuronal Packets to Thoughtseeds: A Hierarchical Model of Embodied Cognition in the Global Workspace" (Kavi et al., 2025)

**Status**: Gap Analysis for Implementation
**Date**: 2026-01-03

## Executive Summary

This document extracts all mathematical models, architectural components, and concepts from the Thoughtseeds paper for systematic implementation in Dionysus3-core.

### Implementation Status

| Component | Paper Equations | Exists in Codebase | Implementation Gap |
|-----------|----------------|-------------------|-------------------|
| Neuronal Packet (NP) | Eq 1-3 | ❌ No | Complete implementation needed |
| Superordinate Ensemble (SE) | Eq 4 | ❌ No | Complete implementation needed |
| Neuronal Packet Domain (NPD) | Conceptual | ❌ No | Complete implementation needed |
| Knowledge Domain (KD) | Eq 5-7 | ❌ No | Complete implementation needed |
| ThoughtSeed | Eq 8-11 | ⚠️ Partial | Missing attractors, valence, arousal, FE |
| Markov Blanket | Conceptual | ✅ Yes | Comprehensive implementation exists |
| Active Pool | Eq 12 | ❌ No | Threshold mechanism needed |
| Dominant Selection | Eq 13-14 | ❌ No | Winner-take-all needed |
| Meta-cognition | Eq 15 | ❌ No | Higher-order influence needed |
| Agent-Level Models | Eq 16-17 | ❌ No | Goals, policies, affordances needed |

---

## I. NEURONAL PACKET (NP) - Fundamental Unit

### Equations 1-3

**State Representation (Eq 1):**
```
NP_i = {A_i^core, A_i^sub, α_i^core, α_i^sub, K_i, S_i}
```

Where:
- `A_i^core`: Core attractor - most probable/stable neural activity pattern
- `A_i^sub`: Subordinate attractors - less dominant patterns
- `α_i^core, α_i^sub ∈ [0,1]`: Activation levels
- `K_i`: Encapsulated knowledge structure
- `S_i ∈ {0, 1, 2}`: State (0=unmanifested, 1=manifested, 2=activated)

**Generative Model (Eq 2):**
```
P(s_i, a_i | μ_i, θ_i, KD_parent, K_i, S_i)
```

Where:
- `s_i`: Sensory states
- `a_i`: Active states
- `μ_i`: Internal model parameters
- `θ_i`: State of parent Knowledge Domain
- Predicts sensory inputs and actions given internal state

**Free Energy Minimization (Eq 3):**
```
F_i = D_KL[q(μ_i) || p(μ_i | s_i, a_i, θ_i, K_i, S_i)] - E_q[log p(s_i, a_i | μ_i, θ_i, KD_parent, K_i, S_i)]
```

Components:
- **Complexity**: KL divergence - minimize internal state complexity
- **Accuracy**: Negative log-likelihood - maximize prediction accuracy

### NP States and Free Energy Landscapes

1. **Unmanifested**: Shallow local minimum, high potential for change
2. **Manifested**: Deep local minimum (core attractor) + shallow local minima (subordinate attractors)
   - Energy barriers separate attractors
   - Binding energy = depth of core attractor
3. **Activated**: Transient heightened activity, core attractor deepens further

---

## II. SUPERORDINATE ENSEMBLE (SE)

### Equation 4

**State Representation:**
```
SE_j = {A_j, α_j, K_j, v_j, r_j}
```

Where:
- `A_j = {A_j^core, A_j^sub}`: Set of attractors
- `α_j`: Activation levels
- `K_j`: Encapsulated knowledge structure
- `v_j ∈ [-1, 1]`: Valence (unpleasantness ← 0 → pleasantness)
- `r_j ∈ [0, 1]`: Arousal

**Emergence Mechanism:**
- Coordinated activity of multiple NPs
- Vector rotations align knowledge representations
- Forms nested Markov blanket

---

## III. NEURONAL PACKET DOMAIN (NPD)

**Conceptual Structure** (no explicit equation):

- Functional unit comprised of interconnected SEs
- Specialized for specific cognitive processes/tasks
- Hierarchical organization via nested Markov blankets
- Shaped by evolutionary priors and Hebbian learning

**Examples:**
- Visual cortex NPDs: color, motion, form processing
- Auditory NPDs: pitch, rhythm, speech
- Motor NPDs: planning, execution, coordination

---

## IV. KNOWLEDGE DOMAIN (KD)

### Equations 5-7

**State Representation (Eq 5):**
```
KD_k = {SE_1, SE_2, ..., SE_n}
```

Collection of Superordinate Ensembles representing a domain of knowledge

**Generative Model (Eq 6):**
```
P(a_k, s_k, μ_k, C_k, v_k, r_k | θ_k, TS_parent)
```

Where:
- `a_k`: Active states
- `s_k`: Sensory states
- `μ_k`: Internal state (constituent SEs)
- `C_k`: Content of consciousness (qualia)
- `v_k, r_k`: Valence, arousal
- `θ_k`: Model parameters
- `TS_parent`: Parent thoughtseed state

**Free Energy (Eq 7):**
```
F_k = D_KL[q(μ_k) || p(μ_k | a_k, s_k, C_k, v_k, r_k, θ_k, TS_parent)]
      - E_q[log p(a_k, s_k, C_k, v_k, r_k | μ_k, θ_k, TS_parent)]
```

Optional: Can add weighted difference for valence/arousal prediction errors

### KD Characteristics

- Hierarchical AND heterarchical structures
- Intrinsic affective dimension (v, r)
- Context-dependent binding process
- Integration across multiple sensory modalities
- Acts as knowledge repository for thoughtseeds

---

## V. THOUGHTSEED - Higher-Order Construct

### Equations 8-11

**State Representation (Eq 8):**
```
TS_m = {A_m^core, A_m^sub, α_m^core, α_m^sub, K_m, S_m, v_m, r_m}
```

Where:
- `A_m^core, A_m^sub`: Core and subordinate attractors
- `α_m^core, α_m^sub ∈ [0, 1]`: Activation levels
- `K_m`: Encapsulated knowledge structures (from KDs)
- `S_m ∈ {0, 1, 2, 3, 4}`: State
  - 0: unmanifested
  - 1: manifested-inactive
  - 2: manifested-active
  - 3: manifested-dominant
  - 4: dissipated
- `v_m ∈ [-1, 1]`: Valence
- `r_m ∈ [0, 1]`: Arousal

**Activation Level (Eq 9):**
```
α_m = weighted_combination(brain_state, A_m^core, A_m^sub)
```

Represents thoughtseed's "bid" for dominance

**Generative Model (Eq 10):**
```
P(TS_m^next, C_m | TS_m^current, KD_states, s_salience, A_affordances, θ_m, π_m, v_KD, r_KD)
```

Dual prediction:
1. **Own future state**: Next TS_m configuration
2. **Content of consciousness**: C_m - what enters global workspace

Where:
- `s_salience`: Sensory input salience
- `A_affordances`: Perceived affordances for action
- `π_m`: Policies guiding action selection

**Free Energy (Eq 11):**
```
F_m = Complexity + Accuracy
```

- **Complexity**: Tendency to acquire information from global broadcast
- **Accuracy**: Tendency to contribute information to workspace

---

## VI. ACTIVE THOUGHTSEEDS POOL

### Equation 12

**Pool Selection:**
```
A_pool(t) = {TS_m | α_m(t) ≥ τ_activation(consciousness_state, arousal)}
```

Where:
- `τ_activation`: Global activation threshold (dynamic)
- Influenced by consciousness state and arousal levels
- Acts as "gain" control for Global Workspace
- Pool fluctuates within brief intervals

---

## VII. DOMINANT THOUGHTSEED & CONSCIOUSNESS

### Equations 13-14

**Winner-Take-All Selection (Eq 13):**
```
TS_dominant = argmin_{TS_m ∈ A_pool} F_m
```

Thoughtseed minimizing free energy wins

**Alternative**: Cumulative EFE minimization or GFE for long-term planning

**Content of Consciousness (Eq 14):**
```
C_global = f(TS_dominant)
```

- Shaped by single dominant thoughtseed
- Reflects unitary nature of conscious experience
- Broadcast to Global Workspace

---

## VIII. META-COGNITION

### Equation 15

**Higher-Order Influence:**
```
γ_precision = g(μ_competing, π_HO, G_HO, θ_HO, ψ_HO, A_pool)
```

Where:
- `γ_precision`: Attentional precision modulation
- `μ_competing`: Internal states of competing lower-level thoughtseeds
- `π_HO`: Policies of higher-order thoughtseed
- `G_HO`: Goals of higher-order thoughtseed
- `θ_HO`: Model parameters
- `ψ_HO`: Prior beliefs

Higher-order thoughtseeds modulate attention and guide goal-directed behavior

---

## IX. AGENT-LEVEL MODELS

### Equations 16.1-16.4

**Global Goals (Eq 16.1):**
```
G_agent = f_goals({s_char}, τ_threshold, σ_stability)
```

Where:
- `s_char`: Characteristic states in pullback attractor landscape
- Revisited frequently (above threshold `τ_threshold`)
- Demonstrate stability/persistence (`σ_stability`)

**Global Policies (Eq 16.2):**
```
π_agent = f_policies(KD_states, G_agent)
```

Derived from KD states and global goals

**Global Affordances (Eq 16.3-16.4):**
```
A_epistemic = f_epistemic(...)
A_pragmatic = f_pragmatic(...)
```

- **Epistemic**: Opportunities for learning/exploration
- **Pragmatic**: Opportunities for goal fulfillment/exploitation

### Equations 17.1-17.3

**Generalized Free Energy (GFE) (Eq 17.1):**
```
GFE = VFE_current + E[EFE_future | π_current]
```

Current surprise + expected future surprise under current policy

**Variational Free Energy (VFE) (Eq 17.2):**
```
VFE_agent = Σ VFE(TS_active) + other_factors
```

Sum of active thoughtseed VFEs

**Expected Free Energy (EFE) (Eq 17.3):**
```
EFE_agent = Σ_{TS_m ∈ A_pool} (α_m × EFE_m)
```

Weighted sum by activation levels, evaluates epistemic + pragmatic values

---

## X. SUPPORTING CONCEPTS

### A. Markov Blanket Structure

**Four-Way Partition:**
- `η` (external): States outside system boundary
- `s` (sensory): Input surface
- `a` (active): Output surface
- `μ` (internal): System's "self"

**Properties:**
- Blanket `b = s ∪ a` separates internal from external
- Conditional independence: `μ ⊥ η | b`
- Nested structure across hierarchical levels
- Reciprocal message passing: top-down predictions, bottom-up errors

**Implementation Status**: ✅ Comprehensive implementation exists in `api/models/markov_blanket.py`

### B. Attractor Dynamics

**Free Energy Landscape:**
- Local minima = attractor states
- Depth of minimum = stability/binding energy
- Energy barriers separate attractors
- Phase transitions between states

**Types:**
- **Core attractor**: Deepest minimum, most stable
- **Subordinate attractors**: Shallower minima, flexible responses

### C. Evolutionary Priors Hierarchy

**Three Levels:**
1. **Basal**: Evolutionarily inherited, species-level
2. **Dispositional**: Shaped during development, individual-level
3. **Learned**: From individual experience, context-specific

Influence NPD formation and KD organization

### D. Global Workspace Theory Integration

**Components:**
- **Broadcasting platform**: Global workspace for consciousness
- **Sources**: KDs provide specialized knowledge
- **Processors**: Thoughtseeds integrate knowledge
- **Selection**: Winner-take-all dynamic for conscious access
- **Ignition**: Threshold for neural assembly activation

---

## XI. IMPLEMENTATION PRIORITY

### Phase 1: Foundation (P1)
1. **Neuronal Packet** (NP) - Equations 1-3
2. **Superordinate Ensemble** (SE) - Equation 4
3. **Enhanced ThoughtSeed** - Equations 8-11 (add missing fields)

### Phase 2: Knowledge Architecture (P1)
4. **Knowledge Domain** (KD) - Equations 5-7
5. **Neuronal Packet Domain** (NPD) - Conceptual structure

### Phase 3: Competition & Selection (P1)
6. **Active Thoughtseeds Pool** - Equation 12
7. **Dominant Selection** - Equations 13-14
8. **Free Energy Calculations** - VFE, EFE implementations

### Phase 4: Meta-Cognition (P2)
9. **Meta-cognition** - Equation 15
10. **Higher-Order Thoughtseeds** - Attentional modulation

### Phase 5: Agent-Level Integration (P2)
11. **Agent-Level Models** - Equations 16-17
12. **Affordances** - Epistemic/pragmatic calculation
13. **Global Goals & Policies**

### Phase 6: Advanced Dynamics (P3)
14. **Attractor Landscapes** - Energy barriers, transitions
15. **Evolutionary Priors** - Basal, dispositional, learned
16. **Global Workspace** - Broadcasting mechanism

---

## XII. REFERENCES

All citations from paper available in APA format. Key references:

- **Friston, K. J. (2010)** - Free Energy Principle
- **Dehaene & Changeux (2011)** - Global Workspace Theory
- **Yufik & Friston (2016)** - Neuronal Packet Hypothesis
- **Ramstead et al. (2021)** - Neural representation under FEP
- **Palacios et al. (2020)** - Markov blankets and hierarchical self-organization

Complete bibliography: See paper sections 11 (References) and acknowledgments.

---

**Next Steps**: Create individual SpecKit specifications for each component with dependency ordering.
