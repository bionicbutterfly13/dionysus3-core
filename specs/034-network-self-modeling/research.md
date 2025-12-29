# Research: Network Reification and Self-Modeling

**Feature**: 034-network-self-modeling
**Date**: 2025-12-29

## 1. Treur Network Dynamics Implementation

### Decision
Use discrete-time difference equations with configurable time step (Δt).

### Rationale
Treur's temporal-causal networks use the equation: `Y(t+Δt) = Y(t) + ηY[cY(...) - Y(t)]Δt`

For our Python implementation:
- Discrete updates align with agent processing cycles
- Speed factor (η) maps directly to our H states
- Combination functions (cY) are pluggable strategies

### Formula Implementation
```python
def update_state(current: float, target: float, speed: float, dt: float = 1.0) -> float:
    """Treur temporal-causal state update."""
    return current + speed * (target - current) * dt
```

### Alternatives Considered
- Continuous-time ODEs: Rejected - overcomplicated for discrete agent cycles
- Pure Hebbian without Treur dynamics: Rejected - loses speed factor control

---

## 2. Hebbian Learning Implementation

### Decision
Use standard Hebbian formula with persistence parameter (μ) and exponential decay.

### Rationale
The Treur Hebbian formula: `hebbμ(V1, V2, W) = V1·V2·(1-W) + μ·W`

Where:
- V1, V2: Co-activation values (0-1 normalized)
- W: Current weight
- μ: Persistence parameter (0-1), controls how much learned weight persists

### Formula Implementation
```python
def hebbian_update(v1: float, v2: float, w: float, mu: float = 0.9) -> float:
    """Hebbian weight update with persistence."""
    return v1 * v2 * (1 - w) + mu * w

def weight_decay(w: float, decay_rate: float, time_since_activation: float) -> float:
    """Exponential decay for inactive connections."""
    return w * math.exp(-decay_rate * time_since_activation)
```

### Boundary Enforcement
- Use sigmoid squashing to keep weights in (0.01, 0.99) range
- Prevents exact 0 (connection death) or 1 (saturation)

### Alternatives Considered
- Oja's rule: Rejected - designed for competitive learning, not association
- BCM rule: Rejected - requires sliding threshold, adds complexity

---

## 3. Neo4j Graph Patterns for Role Matrix

### Decision
Store role matrices as labeled nodes with typed relationships.

### Rationale
Role matrices map naturally to graph structure:
- **mb (base connectivity)**: `(:RoleNode)-[:CONNECTS {base: true}]->(:RoleNode)`
- **mcw (connection weights)**: Relationship property `weight: float`
- **mcfp (aggregation params)**: Node property `aggregation_params: dict`
- **ms (speed factors)**: Node property `speed_factor: float`

### Neo4j Schema (via Graphiti)
```cypher
// Role matrix nodes
CREATE (:RoleMatrix {id: $id, agent_id: $agent_id, version: $version})
CREATE (:RoleNode {id: $id, matrix_id: $matrix_id, role: $role,
                   speed_factor: $speed, aggregation_params: $params})

// Connectivity relationships
CREATE (a:RoleNode)-[:CONNECTS {weight: $w, base: true}]->(b:RoleNode)
```

### Alternatives Considered
- YAML file storage: Rejected - user specified Neo4j in clarification
- JSON blob in node: Rejected - loses graph query benefits

---

## 4. Snapshot Delta Calculation

### Decision
Use L2 norm of state vector differences with 5% threshold.

### Rationale
For a network state vector S = [w1, w2, ..., wn, t1, t2, ..., tm, h1, h2, ..., hk]:
- Calculate `delta = ||S_new - S_old|| / ||S_old||`
- Trigger snapshot if `delta > 0.05` (5%)

### Implementation
```python
import numpy as np

def should_snapshot(old_state: np.ndarray, new_state: np.ndarray, threshold: float = 0.05) -> bool:
    """Check if state change exceeds threshold."""
    if np.linalg.norm(old_state) == 0:
        return True  # Always snapshot from zero state
    delta = np.linalg.norm(new_state - old_state) / np.linalg.norm(old_state)
    return delta > threshold
```

### Daily Checkpoint
- Separate scheduled task triggers snapshot regardless of delta
- Ensures at least one snapshot per 24 hours per agent

### Alternatives Considered
- Per-element threshold: Rejected - doesn't capture overall state change
- Cosine similarity: Rejected - doesn't capture magnitude changes

---

## 5. smolagents Auxiliary Task Integration

### Decision
Use callback hooks in ToolCallingAgent for self-prediction injection.

### Rationale
The existing `AgentAuditCallback` pattern (from `api/agents/audit.py`) shows how to inject behavior:
- `on_step()` called after each agent step
- Can capture internal state and trigger self-prediction

### Implementation Pattern
```python
class SelfModelingCallback:
    """Auxiliary task callback for self-prediction."""

    def __init__(self, network_state_service, prediction_service):
        self.network_state_service = network_state_service
        self.prediction_service = prediction_service
        self.last_predicted_state = None

    def on_step(self, step: ActionStep):
        # Get current network state
        current_state = self.network_state_service.get_current(step.agent_id)

        # Compare to prediction if exists
        if self.last_predicted_state:
            error = self.prediction_service.calculate_error(
                self.last_predicted_state, current_state
            )
            self.prediction_service.record(error)

        # Generate next prediction
        self.last_predicted_state = self.prediction_service.predict_next(current_state)
```

### Opt-In Configuration
```python
# In agent initialization
if config.self_modeling_enabled:
    callbacks.append(SelfModelingCallback(network_state_svc, prediction_svc))
```

### Alternatives Considered
- Modify ToolCallingAgent base class: Rejected - violates non-breaking design
- Separate monitoring agent: Rejected - adds latency, complexity

---

## Summary

All research questions resolved. Key decisions:

| Area | Decision | Key Formula/Pattern |
|------|----------|---------------------|
| Network Dynamics | Discrete-time Treur equations | `Y += η(c - Y)Δt` |
| Hebbian Learning | Standard + persistence + decay | `hebbμ(V1,V2,W) = V1V2(1-W) + μW` |
| Role Matrix Storage | Neo4j labeled nodes + relationships | Graph schema with typed edges |
| Snapshot Triggers | L2 norm delta > 5% + daily | `||S_new - S_old|| / ||S_old||` |
| Agent Integration | Callback hooks (opt-in) | `SelfModelingCallback.on_step()` |

Ready for Phase 1: Design & Contracts.
