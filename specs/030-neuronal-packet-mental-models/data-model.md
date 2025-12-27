# Data Model: Neuronal Packet Mental Models

**Feature**: 030-neuronal-packet-mental-models

## Entities

### MemoryCluster (Augmentation) [P]
Properties added to existing `MemoryCluster` nodes.

| Field | Type | Description |
|-------|------|-------------|
| `boundary_energy` | `float` | Height of the energy barrier (default: 0.5) |
| `cohesion_ratio` | `float` | Ratio of internal to external connection strength |
| `stability` | `float` | Resistance to entropic erosion (inverse of variance) |

### NeuronalPacket (New) [P]
Group of related ThoughtSeeds acting as a synergistic whole.

| Field | Type | Description |
|-------|------|-------------|
| `packet_id` | `str` | Unique identifier |
| `seed_ids` | `list[str]` | IDs of constituent ThoughtSeeds |
| `state_vector` | `list[float]` | Aggregate vector representation |
| `cohesion_weight` | `float` | Strength of internal constraints |

### Trajectory (Augmentation)
New attribute for longitudinal analysis.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | `EPISODIC` or `STRUCTURAL` |

## Parallel Development Paths [P]
1.  **Schema Implementation**: Batch-updating Neo4j nodes with new float properties.
2.  **Logic Implementation**: Building the `NeuronalPacket` and `EFEEngine` Python libraries.
3.  **Metaplasticity Service**: Implementing the learning rate controller.