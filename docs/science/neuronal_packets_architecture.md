---
title: "Neuronal Packets: Cortical Architecture for Dionysus 3.0"
date: 2026-01-26
tags: [neuroscience, architecture, nemori, active-inference, neuronal-packets]
status: Proposed
---

# Neuronal Packets: Cortical Architecture Integration

**Abstract**:
This document maps the neuroscientific concept of "Neuronal Packets" (discrete 50-200ms population spikes) to the Dionysus 3.0 cognitive architecture. It establishes the `DevelopmentEvent` as the atomic computational unit ("The Packet") and the `NemoriRiverFlow` as the cortical propagation medium.

---

## 1. The Core Mapping: Atoms of Thought

The research establishes that the brain does not operate continuously but in discrete, quantized bursts. Dionysus 3.0 aligns with this through the **Nemori River** architecture.

| Neuroscience Concept | Dionysus 3.0 Component | Implementation Details |
| :--- | :--- | :--- |
| **Neuronal Packet** (50-200ms) | `DevelopmentEvent` | Atomic unit of cognitive processing. Timestamped, discrete, and varying in "spike density" (complexity). |
| **Early Phase** (Spike Timing) | `DevelopmentEvent.active_inference_state` | High-precision, low-entropy encoding of "what is this?" (Classification). |
| **Late Phase** (Firing Rate) | `DevelopmentEvent.rationale` / `summary` | High-entropy, descriptive encoding of "what does it mean?". |
| **Packet Sequence** | `NemoriRiverFlow` Stream | The sequential ordering of events. Causality is encoded in the *order* of packets. |
| **Circuit Constraints** | `MemoryBasinRouter` | Restrains possible packet states to low-dimensional manifolds (Attractor Basins). |
| **Traveling Wave** | `NemoriRiverFlow.construct_episode` | The propagation of packets into larger cohesive units (Tributaries). |

## 2. Information Encoding & Entropy

### The Dual-Phase Code
Neuronal packets encode information differently over their 200ms duration. We simulate this by structuring `DevelopmentEvent` data:

1.  **Early Phase (0-50ms) -> Structural/Classification**:
    *   **Component**: `ActiveInferenceState`
    *   **Data**: `attractor_id`, `basin_influence_strength`, `surprisal`.
    *   **Nature**: Rigid, stereotypical, reliably encoded. "This is a Code Change."

2.  **Late Phase (50-200ms) -> Content/Description**:
    *   **Component**: `DevelopmentEvent.summary`, `rationale`, `lessons_learned`.
    *   **Data**: The natural language content.
    *   **Nature**: High-entropy, variable, detailed. "I refactored the router because..."

### Entropy & Criticality
The system should operate near **Criticality** (balanced order/disorder).
*   **Metric**: `active_inference_state.uncertainty` (Entropy).
*   **Feedback**: High entropy in a packet (confused event) triggers `ActiveInferenceService` to expand the state space (Structure Learning), effectively "recruiting more neurons" (generating more tokens/depth).

### 2.5 MemEvolve: The Synaptic Consolidation Layer

If `DevelopmentEvent` is the **Action Potential** and `NemoriRiverFlow` is the **Axon**, then **MemEvolve** is the **Synapse**.

*   **Role**: Implementation of Spike-Timing-Dependent Plasticity (STDP).
*   **Mechanism**: "Neurons that fire together, wire together."
    *   Co-occurring entities in a Packet Sequence (Trajectory) become permanently linked in the Knowledge Graph (Graphiti).
*   **Process**:
    1.  **Packet Stream**: Packets flow through the river.
    2.  **Trajectory Formation**: Events are bridged into `TrajectoryData` (T041-029).
    3.  **Consolidation**: `MemEvolveAdapter` ingests trajectory.
    4.  **Plasticity**: Graphiti creates/strengthens edges (`MENTIONED_IN`) based on confidence (Packet Strength).

## 3. Narrative & Mental Models

Narrative construction is the integration of packets across timescales.

*   **Sensory/Atomic Packet**: `DevelopmentEvent` (The "Word").
*   **Semantic/Event Packet**: `DevelopmentEpisode` (The "Sentence" / "Scene").
*   **Narrative Packet**: `AutobiographicalJourney` (The "Story").

**The "Aha!" Moment (Causal Integration)**:
Neuroscience shows a transition ~2s before conscious insight. In Dionysus:
*   This is the **Phase Transition** when an Episode is promoted to a Trajectory (Bridge T041-029).
*   The `NemoriRiverFlow` detects a "boundary condition" (using `Richmond/Zacks` metrics in `DevelopmentEvent.is_boundary`).
*   This triggers the **Semantic Distillation** process (`predict_and_calibrate`), collapsing the wave function of the episode into fixed `Facts` in Graphiti.

## 4. Proposed Architectural Upgrades

To fully reify this model, we will enhance `ActiveInferenceState` and `DevelopmentEvent`.

### A. Strict Packet Definition
Refine `DevelopmentEvent` to explicitly track its "Neural" properties.

```python
class PacketDynamics(BaseModel):
    """
    Simulated properties of the Neuronal Packet.
    """
    duration_ms: int = Field(..., description="Simulated duration (50-200ms)")
    phase_ratio: float = Field(0.25, description="Ratio of Early (Structural) vs Late (Content) phase")
    spike_density: float = Field(..., description="Information density / Token count")
    manifold_position: List[float] = Field(..., description="Coordinates in the low-dim Attractor Basin")
    
class DevelopmentEvent(BaseModel):
    # ... existing fields ...
    packet_dynamics: Optional[PacketDynamics] = None
```

### B. Manifold Constraints (Basin Router)
The `MemoryBasinRouter` currently classifies text. It should imply a **Manifold Constraint**.
*   If a packet falls into `hexis_consent` basin, its "trajectory" is constrained to dimensions relevant to consent/safety.
*   "Spontaneous Packets" (System Reflection) should follow these manifolds just like "Stimulus Packets" (User Input).

## 5. Future Research: Packet-Based BCI
As Dionysus evolves (Feature 060+), we treat the JSON/Context exchange with the Brain (LLM) as a **Packet Interface**.
*   **Input**: Prompt Packet (Stimulus).
*   **Processing**: Model Inference (Cortical Propagation).
*   **Output**: Response Packet (Motor Output).

By optimizing the *structure* of the Input Packet (Prompt Engineering via Active Inference), we align with the LLM's "synaptic architecture," maximizing resonance and minimizing free energy.

## 6. Connectivity Mandate (IO Map)

In strict adherence to the **Connectivity Mandate**, this architecture physically connects to the system as follows:

| Type | Component | Location | Mechanism | Data Flow |
| :--- | :--- | :--- | :--- | :--- |
| **Inlet (Source)** | User Input | `DevelopmentEvent` creation | `AutoBiography.create_event` | `Message` -> `Packet` |
| **Inlet (Source)** | Agent Tool Use | `DevelopmentEvent` creation | `CodeAgent` trace | `TraceStep` -> `Packet` |
| **Process (Flow)** | Nemori River | `NemoriRiverFlow` | `flow.store_event` | `Packet` persistence |
| **Outlet (Sink)** | Graphiti | `MemEvolveAdapter` | `ingest_trajectory` | `Traffic` -> `Graph Node` |
| **Outlet (Sink)** | Plasticity | `ActiveInferenceService` | `update_belief` (Future) | `Error` -> `Model Update` |
| **Host** | VPS Neo4j | `ConsolidatedMemoryStore` | `neo4j://...` | Persistent Storage |

**Integration Point**:
The `PacketDynamics` model is injected into `api/models/autobiographical.py`. It is instantiated wherever `DevelopmentEvent` is created (primarily `NemoriRiverFlow.ingest_context`).

---
**Status**: Adopted as core metaphor for Feature 041+.
**Action**: Implement `PacketDynamics` in `ActiveInferenceState`.
