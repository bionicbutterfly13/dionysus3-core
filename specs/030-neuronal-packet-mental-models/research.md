# Research: Neuronal Packet Mental Models

## Technical Decisions

### 1. EFE Engine Calculation [P]
- **Decision**: Use `numpy` for high-performance vector distance calculations. EFE formula: `EFE(π) = Σ P(o|s,π) [ln P(o|s,π) - ln P(o|C)]`, simplified to `Entropy(Prediction) + CosineDistance(ThoughtSeed, Goal)`.
- **Rationale**: Cosine distance accurately represents goal divergence in our existing embedding space.
- **Parallel Path**: This can be developed and unit-tested independently of the OODA loop.

### 2. Metaplasticity Algorithm [P]
- **Decision**: Implement a sigmoid-based scaling function for learning rates: `η = η_base * (1 + sigmoid(surprise_level - threshold))`.
- **Rationale**: Prevents erratic learning rate spikes while allowing rapid adaptation to genuine architectural surprises.
- **Parallel Path**: The controller logic can be tested with simulated surprise data before OODA integration.

### 3. Synergistic Constraint Propagation
- **Decision**: When a `NeuronalPacket` is activated, iterate through its constituent `ThoughtSeeds` and apply a "Cohesion Boost" to their weights in Neo4j.
- **Rationale**: Implements the "Synergistic Wholes" principle where model components reinforce each other.

### 4. Neo4j Property Batching
- **Decision**: Update `boundary_energy` and `stability` properties in batches of 100 via n8n to minimize webhook overhead.
- **Rationale**: Maintains performance during high-frequency OODA cycles.

## Best Practices

### Parallel Development Strategy [P]
- **Path A**: Mathematical Engine (EFE + Metaplasticity logic)
- **Path B**: Neo4j Schema Augmentation (Migration scripts + n8n updates)
- **Path C**: smolagents Integration (ConsciousnessManager hooks)

### Traceability
- Every learning rate adjustment must be logged with the specific `prediction_error` that triggered it.
