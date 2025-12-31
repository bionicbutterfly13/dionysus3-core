# Research: Thoughtseeds Framework Enhancement

## Technical Decisions

### 1. Reciprocal Message Passing [P]
- **Decision**: Use an event-bus or observer pattern where each layer in the `PriorHierarchy` can emit "precision weights" to its neighbors.
- **Rationale**: Decouples the layers while allowing continuous updates. Pydantic models will store the state, and a controller will manage the passing.
- **Alternatives considered**: Direct method calls (too coupled), global state (hard to test).

### 2. Markov Blanket Structural Enforcement [P]
- **Decision**: Use Neo4j directionality and specific edge types (`[:SENSORY]`, `[:ACTIVE]`). Agents will be restricted to traversing only `[:SENSORY]` edges for input and creating `[:ACTIVE]` edges for output.
- **Rationale**: Native graph enforcement is more robust than application-level filtering.
- **Alternatives considered**: JSON metadata filtering (fragile).

### 3. Inner Screen Serialization [P]
- **Decision**: Implement as a singleton-like `Screen` object in the OODA loop context. Use a "Brightness" score (0-1) calculated via `1 - EFE`.
- **Rationale**: High brightness ThoughtSeeds dominate conscious attention. Logging to `EpisodicMemory` provides the required audit trail.
- **Alternatives considered**: Persistent DB node (too much overhead for transient attention).

## Best Practices

### Bayesian Inference in Python
- Use `scipy.stats` for entropy and probability distributions.
- Maintain "Precision" weights as float values in the [0, 1] range.

### Neo4j Graphiti Patterns
- Batch mutations using n8n webhooks.
- Preserve temporal validity using `valid_at` properties if applicable.
