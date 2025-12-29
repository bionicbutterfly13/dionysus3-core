# Quickstart: Network Reification and Self-Modeling

**Feature**: 034-network-self-modeling
**Date**: 2025-12-29

## Overview

This guide covers implementing the four additive components of the network self-modeling feature:

1. **NetworkState** - Observable W/T/H values
2. **Self-Prediction** - Auxiliary regularization task
3. **Hebbian Learning** - KG relationship strengthening
4. **Role Matrix** - Declarative network specification

All components are **opt-in** and **non-breaking**.

---

## Prerequisites

- Python 3.11+
- Existing Dionysus API running
- Neo4j accessible via webhooks + Graphiti
- pytest for testing

---

## Implementation Order

```
Phase 1: NetworkState (P1 - Foundation)
   └── Models → Service → Router → Tests

Phase 2: Hebbian Learning (P2 - Independent)
   └── Model extension → Service → Tests

Phase 3: Self-Prediction (P2 - Depends on Phase 1)
   └── Callback → Service → Integration

Phase 4: Role Matrix (P3 - Depends on Phase 1)
   └── Neo4j schema → Service → API

Phase 5: Multi-Level Adaptation (P3 - Depends on Phase 3)
   └── Extend metaplasticity → Second-order states
```

---

## Phase 1: NetworkState

### Step 1.1: Create Model

```python
# api/models/network_state.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class SnapshotTrigger(str, Enum):
    CHANGE_EVENT = "CHANGE_EVENT"
    DAILY_CHECKPOINT = "DAILY_CHECKPOINT"
    MANUAL = "MANUAL"

class NetworkState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trigger: SnapshotTrigger
    connection_weights: dict[str, float]  # "source->target": weight
    thresholds: dict[str, float]          # node_id: threshold
    speed_factors: dict[str, float]       # node_id: speed
    delta_from_previous: Optional[float] = None
    checksum: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "perception-agent-001",
                "trigger": "CHANGE_EVENT",
                "connection_weights": {"input->hidden": 0.75},
                "thresholds": {"hidden": 0.5},
                "speed_factors": {"hidden": 0.1}
            }
        }
```

### Step 1.2: Create Service

```python
# api/services/network_state_service.py
import numpy as np
from typing import Optional
from datetime import datetime, timedelta

class NetworkStateService:
    DELTA_THRESHOLD = 0.05  # 5% change triggers snapshot

    def __init__(self, webhook_driver, graphiti_client):
        self.webhook = webhook_driver
        self.graphiti = graphiti_client

    async def get_current(self, agent_id: str) -> Optional[NetworkState]:
        """Get most recent network state for agent."""
        # Query via webhook
        pass

    async def should_snapshot(self, agent_id: str, new_state: dict) -> bool:
        """Check if state change exceeds threshold."""
        current = await self.get_current(agent_id)
        if not current:
            return True

        old_vec = self._state_to_vector(current)
        new_vec = self._state_to_vector(new_state)

        if np.linalg.norm(old_vec) == 0:
            return True

        delta = np.linalg.norm(new_vec - old_vec) / np.linalg.norm(old_vec)
        return delta > self.DELTA_THRESHOLD

    async def create_snapshot(
        self,
        agent_id: str,
        trigger: SnapshotTrigger,
        weights: dict,
        thresholds: dict,
        speed_factors: dict
    ) -> NetworkState:
        """Create and persist network state snapshot."""
        pass

    def _state_to_vector(self, state) -> np.ndarray:
        """Convert state to numpy vector for delta calculation."""
        values = (
            list(state.connection_weights.values()) +
            list(state.thresholds.values()) +
            list(state.speed_factors.values())
        )
        return np.array(values)
```

### Step 1.3: Create Router

```python
# api/routers/network_state.py
from fastapi import APIRouter, Depends, HTTPException
from api.services.network_state_service import NetworkStateService

router = APIRouter(prefix="/api/v1/network-state", tags=["Network State"])

@router.get("/{agent_id}")
async def get_current_network_state(
    agent_id: str,
    service: NetworkStateService = Depends()
):
    state = await service.get_current(agent_id)
    if not state:
        raise HTTPException(404, f"No network state for agent {agent_id}")
    return state

@router.post("/{agent_id}/snapshot")
async def create_manual_snapshot(
    agent_id: str,
    service: NetworkStateService = Depends()
):
    # Rate limit: 1 per minute
    return await service.create_snapshot(
        agent_id=agent_id,
        trigger=SnapshotTrigger.MANUAL,
        # ... extract current state from agent
    )
```

---

## Phase 2: Hebbian Learning

### Step 2.1: Model Extension

```python
# api/models/hebbian.py
from pydantic import BaseModel, Field
from datetime import datetime
import math

class HebbianConnection(BaseModel):
    relationship_id: str
    hebbian_weight: float = Field(ge=0.01, le=0.99, default=0.5)
    persistence_mu: float = Field(ge=0.0, le=1.0, default=0.9)
    last_activation: datetime = Field(default_factory=datetime.utcnow)
    activation_count: int = Field(ge=0, default=0)
    decay_rate: float = Field(gt=0, default=0.01)

    def apply_hebbian_update(self, v1: float, v2: float) -> float:
        """Apply Hebbian learning rule."""
        new_weight = v1 * v2 * (1 - self.hebbian_weight) + self.persistence_mu * self.hebbian_weight
        self.hebbian_weight = self._enforce_bounds(new_weight)
        self.activation_count += 1
        self.last_activation = datetime.utcnow()
        return self.hebbian_weight

    def apply_decay(self) -> float:
        """Apply exponential decay based on time since activation."""
        seconds_since = (datetime.utcnow() - self.last_activation).total_seconds()
        decayed = self.hebbian_weight * math.exp(-self.decay_rate * seconds_since / 86400)
        self.hebbian_weight = self._enforce_bounds(decayed)
        return self.hebbian_weight

    def _enforce_bounds(self, weight: float) -> float:
        """Keep weight in (0.01, 0.99) range using sigmoid squashing."""
        return max(0.01, min(0.99, weight))
```

### Step 2.2: Service

```python
# api/services/hebbian_service.py

class HebbianService:
    def __init__(self, graphiti_client):
        self.graphiti = graphiti_client

    async def record_coactivation(
        self,
        relationship_id: str,
        source_activation: float,
        target_activation: float
    ) -> HebbianConnection:
        """Record co-activation and update Hebbian weight."""
        conn = await self._get_or_create(relationship_id)
        conn.apply_hebbian_update(source_activation, target_activation)
        await self._persist(conn)
        return conn

    async def apply_decay_batch(self, relationship_ids: list[str]) -> int:
        """Apply decay to batch of relationships."""
        updated = 0
        for rid in relationship_ids:
            conn = await self._get_or_create(rid)
            old_weight = conn.hebbian_weight
            conn.apply_decay()
            if abs(conn.hebbian_weight - old_weight) > 0.001:
                await self._persist(conn)
                updated += 1
        return updated
```

---

## Phase 3: Self-Prediction

### Step 3.1: Callback

```python
# api/agents/self_modeling_callback.py
from smolagents import ActionStep

class SelfModelingCallback:
    """Opt-in callback for self-prediction auxiliary task."""

    def __init__(
        self,
        network_state_service: NetworkStateService,
        prediction_service: PredictionService,
        enabled: bool = False
    ):
        self.network_svc = network_state_service
        self.prediction_svc = prediction_service
        self.enabled = enabled
        self.last_prediction = None

    async def on_step(self, step: ActionStep):
        if not self.enabled:
            return

        # Get current network state
        current = await self.network_svc.get_current(step.agent_id)

        # Resolve previous prediction
        if self.last_prediction:
            await self.prediction_svc.resolve(
                self.last_prediction.id,
                current
            )

        # Generate next prediction
        self.last_prediction = await self.prediction_svc.predict(
            agent_id=step.agent_id,
            current_state=current
        )
```

### Step 3.2: Integration

```python
# In agent initialization (e.g., consciousness_manager.py)

def create_agent(config: AgentConfig):
    callbacks = [AgentAuditCallback(...)]  # Existing

    # Opt-in self-modeling
    if config.self_modeling_enabled:
        callbacks.append(SelfModelingCallback(
            network_state_service=network_state_svc,
            prediction_service=prediction_svc,
            enabled=True
        ))

    return ToolCallingAgent(..., callbacks=callbacks)
```

---

## Phase 4: Role Matrix

### Step 4.1: Neo4j Schema Setup

```cypher
// Run via Graphiti or n8n workflow

// Constraints
CREATE CONSTRAINT role_matrix_id IF NOT EXISTS
FOR (m:RoleMatrixSpec) REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT role_node_id IF NOT EXISTS
FOR (n:RoleNode) REQUIRE n.id IS UNIQUE;

// Indexes
CREATE INDEX role_matrix_agent IF NOT EXISTS
FOR (m:RoleMatrixSpec) ON (m.agent_id);

CREATE INDEX role_node_matrix IF NOT EXISTS
FOR (n:RoleNode) ON (n.matrix_id);
```

### Step 4.2: Service

```python
# api/services/role_matrix_service.py

class RoleMatrixService:
    async def create_from_state(self, agent_id: str) -> RoleMatrix:
        """Export current network state as role matrix."""
        state = await self.network_svc.get_current(agent_id)
        # Transform state to role matrix graph structure
        pass

    async def instantiate_agent(self, matrix_id: str) -> NetworkState:
        """Create agent network state from role matrix spec."""
        matrix = await self.get(matrix_id)
        # Transform role matrix to network state
        pass

    async def validate(self, matrix: RoleMatrixInput) -> list[str]:
        """Validate role matrix for internal consistency."""
        violations = []
        # Check for cycles in inhibitory connections
        # Check all nodes referenced in connections exist
        # Check weight bounds
        return violations
```

---

## Configuration

```python
# config.py or .env

# Feature flags (all default to False)
NETWORK_STATE_ENABLED=true
SELF_MODELING_ENABLED=false
HEBBIAN_LEARNING_ENABLED=false
ROLE_MATRIX_ENABLED=false

# Tuning parameters
NETWORK_STATE_DELTA_THRESHOLD=0.05
HEBBIAN_PERSISTENCE_MU=0.9
HEBBIAN_DECAY_RATE=0.01
SELF_PREDICTION_ERROR_THRESHOLD=0.3
```

---

## Testing Checklist

### Unit Tests
- [ ] NetworkState serialization/deserialization
- [ ] Delta calculation (5% threshold)
- [ ] Hebbian weight update formula
- [ ] Hebbian decay calculation
- [ ] Weight boundary enforcement
- [ ] Role matrix validation rules

### Integration Tests
- [ ] NetworkState persistence to Neo4j
- [ ] Hebbian weight updates persist correctly
- [ ] Role matrix round-trip (export → import)
- [ ] Self-prediction callback integration

### Contract Tests
- [ ] GET /network-state/{agent_id} returns 200
- [ ] GET /network-state/{agent_id} returns 404 for unknown agent
- [ ] POST /network-state/{agent_id}/snapshot rate limiting
- [ ] PUT /role-matrix/{agent_id} validation errors

### Regression Tests
- [ ] All existing tests pass (SC-009)
- [ ] Agents without features enabled behave identically (SC-010)
