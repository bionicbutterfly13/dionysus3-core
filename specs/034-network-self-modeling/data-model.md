# Data Model: Network Reification and Self-Modeling

**Feature**: 034-network-self-modeling
**Date**: 2025-12-29

## Entity Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  NetworkState   │────▶│  SelfModelState │────▶│   TimingState   │
│  (snapshot)     │     │  (1st order)    │     │   (2nd order)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│ PredictionRecord│     │HebbianConnection│
│ (self-modeling) │     │ (KG extension)  │
└─────────────────┘     └─────────────────┘

┌─────────────────┐
│   RoleMatrix    │ ◀── Neo4j graph structure
│ (declarative)   │
└─────────────────┘
```

---

## NetworkState

Complete snapshot of an agent's reified network state.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique snapshot identifier | Primary key |
| agent_id | str | Agent this state belongs to | Required, indexed |
| timestamp | datetime | When snapshot was taken | Required, indexed |
| trigger | SnapshotTrigger | Why snapshot was created | Enum: CHANGE_EVENT, DAILY_CHECKPOINT, MANUAL |
| connection_weights | dict[str, float] | W values keyed by "source_id->target_id" | Values in (0.01, 0.99) |
| thresholds | dict[str, float] | T values keyed by node_id | Values in (0.0, 1.0) |
| speed_factors | dict[str, float] | H values keyed by node_id | Values > 0 |
| delta_from_previous | float | L2 norm change from last snapshot | >= 0, null if first |
| checksum | str | SHA256 of serialized state | For integrity verification |

### State Transitions
- Created on: significant change (>5% delta), daily checkpoint, or manual request
- Immutable after creation (snapshots are append-only)
- Pruned after 30 days (retention policy)

---

## SelfModelState

First-order self-model representing observable network characteristics.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique identifier | Primary key |
| agent_id | str | Agent this model belongs to | Required |
| network_state_id | UUID | Associated NetworkState snapshot | Foreign key |
| w_states | dict[str, float] | Self-model of connection weights | Mirrors NetworkState.connection_weights |
| t_states | dict[str, float] | Self-model of thresholds | Mirrors NetworkState.thresholds |
| observation_confidence | float | Confidence in self-observation | (0.0, 1.0) |
| created_at | datetime | When self-model was updated | Required |

### Relationships
- One SelfModelState per NetworkState snapshot
- References parent NetworkState via network_state_id

---

## TimingState

Second-order self-model controlling adaptation speed.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique identifier | Primary key |
| agent_id | str | Agent this controls | Required |
| self_model_state_id | UUID | Associated first-order state | Foreign key |
| h_states | dict[str, float] | Speed factors for each W/T state | Values > 0 |
| adaptation_mode | AdaptationMode | Current adaptation behavior | Enum: ACCELERATING, STABLE, DECELERATING, STRESSED |
| stress_level | float | Current stress indicator | (0.0, 1.0), affects adaptation |
| updated_at | datetime | Last timing update | Required |

### Relationships
- One TimingState per SelfModelState
- Controls learning rate of first-order states

---

## PredictionRecord

Self-prediction attempt for regularization.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique identifier | Primary key |
| agent_id | str | Agent that made prediction | Required, indexed |
| predicted_at | datetime | When prediction was made | Required |
| predicted_state | dict | Predicted next NetworkState values | JSON blob |
| actual_state_id | UUID | Actual NetworkState that occurred | Foreign key, nullable until resolved |
| prediction_error | float | L2 norm error between predicted and actual | >= 0, null until resolved |
| resolved_at | datetime | When actual state was observed | Nullable |

### State Transitions
1. PENDING: Created with prediction, actual_state_id null
2. RESOLVED: actual_state_id set, prediction_error calculated

---

## HebbianConnection

Extension to knowledge graph relationships with Hebbian weight.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| relationship_id | str | Existing KG relationship ID | Required |
| hebbian_weight | float | Learned association strength | (0.01, 0.99) |
| persistence_mu | float | Persistence parameter μ | (0.0, 1.0), default 0.9 |
| last_activation | datetime | Last co-activation time | Required |
| activation_count | int | Total co-activations | >= 0 |
| decay_rate | float | Exponential decay rate | > 0, default 0.01 |

### Notes
- Added as optional properties to existing Neo4j relationships
- Relationships without hebbian_weight behave as before (non-breaking)

---

## RoleMatrix (Neo4j Graph Structure)

Declarative network topology specification stored in Neo4j.

### Node: RoleMatrixSpec
| Property | Type | Description |
|----------|------|-------------|
| id | str | Unique matrix identifier |
| agent_id | str | Agent this matrix defines |
| version | int | Schema version for migrations |
| created_at | datetime | Creation timestamp |
| is_active | bool | Whether this is the active spec |

### Node: RoleNode
| Property | Type | Description |
|----------|------|-------------|
| id | str | Unique node identifier |
| matrix_id | str | Parent RoleMatrixSpec |
| role | str | Node role name |
| speed_factor | float | H value for this node |
| threshold | float | T value for this node |
| aggregation_type | str | Combination function type |
| aggregation_params | dict | Combination function parameters |

### Relationship: CONNECTS
| Property | Type | Description |
|----------|------|-------------|
| weight | float | Connection weight (W) |
| is_base | bool | Part of base connectivity (mb) |
| is_inhibitory | bool | Negative/inhibitory connection |

### Cypher Patterns
```cypher
// Create role matrix
MATCH (m:RoleMatrixSpec {id: $matrix_id})
CREATE (n:RoleNode {id: $node_id, matrix_id: $matrix_id, role: $role, ...})
CREATE (m)-[:DEFINES]->(n)

// Create connection
MATCH (a:RoleNode {id: $from_id}), (b:RoleNode {id: $to_id})
CREATE (a)-[:CONNECTS {weight: $w, is_base: true}]->(b)

// Export agent state as role matrix
MATCH (m:RoleMatrixSpec {agent_id: $agent_id, is_active: true})-[:DEFINES]->(n:RoleNode)
OPTIONAL MATCH (n)-[c:CONNECTS]->(target:RoleNode)
RETURN m, collect(n), collect(c)
```

---

## Validation Rules

### NetworkState
- `connection_weights` keys must be valid "source->target" format
- All weight values must be in (0.01, 0.99) range
- `delta_from_previous` required except for first snapshot

### PredictionRecord
- `prediction_error` must be calculated within 1 hour of `predicted_at`
- Unresolved predictions older than 1 hour marked as EXPIRED

### HebbianConnection
- `hebbian_weight` updates must not exceed 10% change per activation
- Decay cannot reduce weight below 0.01 (soft floor)

### RoleMatrix
- All RoleNodes must have valid `matrix_id` reference
- CONNECTS relationships must be between nodes in same matrix
- No cycles in inhibitory connections (prevents oscillation)

---

## Index Requirements

### PostgreSQL (if used for non-Neo4j entities)
```sql
CREATE INDEX idx_network_state_agent_time ON network_state(agent_id, timestamp DESC);
CREATE INDEX idx_prediction_agent_pending ON prediction_record(agent_id) WHERE actual_state_id IS NULL;
```

### Neo4j
```cypher
CREATE INDEX role_matrix_agent FOR (m:RoleMatrixSpec) ON (m.agent_id);
CREATE INDEX role_node_matrix FOR (n:RoleNode) ON (n.matrix_id);
CREATE INDEX hebbian_last_activation FOR ()-[r:CONNECTS]-() ON (r.last_activation);
```
