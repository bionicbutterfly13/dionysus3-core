# Thoughtseed Framework & Dionysus Alignment

**Source:** *From Neuronal Packets to Thoughtseeds: A Hierarchical Model of Embodied Cognition* (Kavi et al., 2026) -> *Note: Year inferred or simulated*

## 1. The Hierarchy of Cognition
The paper defines a 4-level hierarchy. Here is how it maps to Dionysus:

| Concept | Definition (Paper) | Dionysus Equivalent (Current/Planned) |
| :--- | :--- | :--- |
| **Neuronal Packet (NP)** | Fundamental unit. Self-organizing ensemble. Encodes specific feature. Stable "Core Attractor". | **Graphiti Node**. A single semantic unit in the Graph. |
| **Superordinate Ensemble (SE)** | Coordinated NPs representing complex concepts. | **Graphiti Cluster** / Community. |
| **Knowledge Domain (KD)** | "Repository" of integrated knowledge. Context scaffolding. | **Memory Stores** (e.g., `Bio_Story`, `Tech_Stack`). Defined by `context_id`. |
| **Thoughtseed (TS)** | Higher-order construct with **agency**. Emerges from KDs. Competes for Global Workspace. | **MetacognitiveParticle**. The active object in OODA. |
| **Global Workspace (GW)** | The "stage" where the Dominant Thoughtseed broadcasts. | **ConsciousnessManager**. The OODA Loop. |

## 2. Relationships & Dynamics

### A. From Packet to Seed
- **Theory:** Thoughtseeds emerge from the dynamic interaction of KDs. They are "Transient Coalitions" of NPs.
- **Integration Point:** When `ReasoningAgent` (using tools) retrieves nodes (NPs) from Graphiti (KDs), it synthesizes them into a `structured_result`.
- **Transformation:** `ConsciousnessManager` wraps this result into a `MetacognitiveParticle` (Thoughtseed).
- **Gap:** We currently don't track *which* NPs (Graphiti Nodes) spawned the Thoughtseed.
    - *Fix:* Add `provenance_nodes: List[str]` to `MetacognitiveParticle`.

### B. Attractor Basins & Competition
- **Theory:** Thoughtseeds compete via **EFE Minimization** (Expected Free Energy).
- **Mechanism:** "Winner-take-all". The `Dominant Thoughtseed` enters consciousness.
- **Dionysus:**
    - `resonance_score` (in `MetacognitiveParticle`) represents the **Activation Level**.
    - `ParticleStore` represents the **Active Thoughtseed Pool**.
    - The `_sort_particles()` method implements the "Winner-take-all" ranking.
    - **Persistence:** High resonance (>0.8) implies the Thoughtseed has become a strong Attractor (Memory).

### C. Metacognition (The Tuner)
- **Theory:** Meta-cognition modulates **Attentional Precision** ($\pi$) and **Activation Threshold** ($\gamma$).
- **Dionysus:**
    - `MetaplasticityController` (`metaplasticity_svc`) calculates `current_precision`.
    - Ours is explicit: `precision` on the particle is set by `metaplasticity_svc`.

## 3. Mathematical Framework Integration

### Free Energy Formulation
$$F_{TS} = \text{Complexity} - \text{Accuracy}$$
- **Complexity:** The "cost" of the thought (Entropy).
- **Accuracy:** How well it predicts the sensory/context state.

**Codebase Application:**
- We currently use `confidence` as a proxy for Accuracy.
- We use `entropy` field in `MetacognitiveParticle`.
- *Future:* Implement `calculate_free_energy()` method on `MetacognitiveParticle`.

## 4. Connectivity & IO Map (Mandate Compliance)

**New Feature: Thoughtseed Provenance (F041)**

- **Component:** `ConsciousnessManager`
- **Input:** 
    - `ReasoningAgent` result (Content).
    - `Graphiti` Retrieval Trace (The NPs used).
- **Transformation:**
    - `MetacognitiveParticle` created.
    - `provenance_nodes` populated with Graphiti Node IDs.
- **Output:**
    - `ParticleStore` (Pool).
    - `Graphiti` (Persistence): The new Node (Thoughtseed) links back to its parent NPs (Edges: `DERIVED_FROM`).

## 5. Summary
The paper provides the **Physics** for our **Cognitive Architecture**.
- **Nodes** = Mass (NPs).
- **Particles** = Momentum (Thoughtseeds).
- **Resonance** = Gravity (Attractor Basins).
- **Precision** = Temperature (Metacognition).

We are 80% aligned. The missing 20% is **Provenance Tracking** (linking Seeds back to Packets).
