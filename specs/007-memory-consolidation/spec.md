# Feature 007: Memory Consolidation

**Status**: Planned
**Created**: 2025-12-21
**Dependencies**: 001-session-continuity, 002-remote-persistence-safety, 004-heartbeat-system

## Overview

Memory consolidation migrates transient working memory (PostgreSQL) to permanent long-term memory (Neo4j). This implements the episodic → semantic memory transition, ensuring data durability across crashes and enabling knowledge extraction from predictions, sessions, and mental model updates.

## Problem Statement

Current architecture has two memory stores:
- **PostgreSQL (Working Memory)**: predictions, sessions, sync_events, active_inference_states
- **Neo4j (Long-term Memory)**: entities, relationships, episodes, attractor basins

**Issues without consolidation:**
1. Crash during buffering → data loss
2. Long sessions → unbounded PostgreSQL growth
3. Predictions never become learned facts
4. Mental model updates don't persist to knowledge graph

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HEARTBEAT CYCLE                       │
│  OBSERVE → ORIENT → DECIDE → ACT → (repeat)             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼ (CONSOLIDATE_MEMORY action)
┌─────────────────────────────────────────────────────────┐
│              CONSOLIDATION SERVICE                       │
│  - Batch pending items from PostgreSQL                  │
│  - Call n8n webhook for Neo4j writes                    │
│  - Update sync_events status                            │
│  - Handle failures with retry                           │
└─────────────────────────────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  PostgreSQL          │    │  Neo4j               │
│  (mark as synced)    │    │  (create nodes/edges)│
└──────────────────────┘    └──────────────────────┘
```

## Consolidation Triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Batch threshold** | pending_count > 50 | Consolidate oldest 50 |
| **Time checkpoint** | 15 min since last | Consolidate all pending |
| **Idle detection** | 30 min no activity | Full consolidation |
| **Heartbeat cycle** | Every 100 cycles | Force consolidation |
| **Crash recovery** | Startup | Retry all queued/failed |

### Trigger Logic

```python
def should_consolidate() -> bool:
    return (
        pending_sync_count() > 50 or
        minutes_since_last_consolidation() > 15 or
        idle_minutes() > 30 or
        heartbeat_cycle_count % 100 == 0
    )
```

## Data Flow by Component

### 1. Predictions → Facts

| PostgreSQL | Neo4j |
|------------|-------|
| `model_predictions` (resolved) | `(:Prediction)-[:OBSERVED]->(:Observation)` |

When a prediction resolves:
```
{
  "prediction": "User will ask about X",
  "observation": "User asked about Y",
  "accuracy": 0.3,
  "model_id": "uuid"
}
```
Becomes Neo4j edge: `(Prediction)-[:RESULTED_IN {accuracy: 0.3}]->(Observation)`

### 2. Sessions → Episodes

| PostgreSQL | Neo4j |
|------------|-------|
| `sessions` (ended) | `(:Episode {type: 'session'})` |

When session ends:
```
{
  "session_id": "uuid",
  "summary": "Discussed anxiety treatment",
  "entities_mentioned": ["anxiety", "treatment"],
  "duration_minutes": 45
}
```
Becomes Neo4j: `(:Episode)-[:MENTIONS]->(:Entity)`

### 3. Mental Models → Relationships

| PostgreSQL | Neo4j |
|------------|-------|
| `mental_models` (revised) | Updated entity relationships |

When mental model revises:
```
{
  "model_id": "uuid",
  "domain": "user",
  "old_basins": [...],
  "new_basins": [...],
  "trigger": "prediction_accuracy_low"
}
```
Becomes Neo4j: Updated edge weights between basin entities

### 4. Attractor Basins → Graph Weights

| PostgreSQL | Neo4j |
|------------|-------|
| `memory_clusters` | `(:Basin)-[:ATTRACTS {strength}]->(:Memory)` |

When basin strengthens:
- Increase edge weight
- Update basin summary
- Link new memories

## Sync Events Schema

Using existing `sync_events` table:

```sql
-- Insert pending consolidation
INSERT INTO sync_events (direction, result, memory_ids)
VALUES ('local_to_remote', 'queued', ARRAY['uuid1', 'uuid2']);

-- Update on success
UPDATE sync_events SET result = 'success', duration_ms = 150
WHERE id = 'event_id';

-- Update on failure
UPDATE sync_events SET
  result = 'failed',
  error_message = 'Neo4j timeout',
  retry_count = retry_count + 1
WHERE id = 'event_id';

-- Crash recovery query
SELECT * FROM sync_events
WHERE result IN ('queued', 'failed')
AND retry_count < 3
ORDER BY timestamp ASC;
```

## n8n Webhook Integration

### Endpoint: `/webhook/memory/v1/consolidate`

**Request:**
```json
{
  "batch_id": "uuid",
  "items": [
    {
      "type": "prediction_resolved",
      "data": { ... }
    },
    {
      "type": "session_ended",
      "data": { ... }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "processed": 50,
  "failed": 0,
  "nodes_created": 12,
  "edges_created": 25
}
```

## Heartbeat Integration

Add `CONSOLIDATE_MEMORY` to action taxonomy:

```python
@dataclass
class ConsolidateMemoryAction(Action):
    type: str = "CONSOLIDATE_MEMORY"
    cost: int = 2
    batch_size: int = 50

async def execute(self, context: ActionContext) -> ActionResult:
    service = ConsolidationService()
    result = await service.consolidate_batch(self.batch_size)
    return ActionResult(
        success=result.success,
        nodes_created=result.nodes_created,
        edges_created=result.edges_created
    )
```

In DECIDE phase:
```python
if should_consolidate():
    actions.append(ConsolidateMemoryAction(batch_size=50))
```

## Crash Recovery

On API startup:

```python
async def startup_recovery():
    pending = await get_pending_sync_events()
    for event in pending:
        if event.retry_count < MAX_RETRIES:
            await retry_consolidation(event)
        else:
            await mark_permanently_failed(event)
            await alert_admin(event)
```

## User Stories

### US1: Automatic Consolidation
As the system, I consolidate working memory to long-term memory automatically based on triggers, without user intervention.

### US2: Crash Recovery
As the system, I recover gracefully from crashes by replaying pending consolidations from sync_events.

### US3: Prediction Learning
As the system, when a prediction resolves, I store the outcome in Neo4j so the knowledge graph learns from experience.

### US4: Session Summarization
As the system, when a session ends, I create an episodic memory in Neo4j summarizing what was discussed.

### US5: Mental Model Persistence
As the system, when a mental model revises, I update the corresponding relationships in Neo4j.

## Phases

### Phase 1: Consolidation Service
- ConsolidationService with batch processing
- Integration with sync_events table
- Basic triggers (count, time)

### Phase 2: n8n Workflow
- Create consolidation webhook workflow
- Handle different item types
- Error handling and logging

### Phase 3: Heartbeat Integration
- Add CONSOLIDATE_MEMORY action
- should_consolidate() in DECIDE phase
- Energy cost (2)

### Phase 4: Crash Recovery
- Startup recovery job
- Retry logic with backoff
- Failed event alerting

### Phase 5: Component Handlers
- PredictionConsolidationHandler
- SessionConsolidationHandler
- MentalModelConsolidationHandler
- BasinConsolidationHandler

### Phase 6: Testing & Monitoring
- Unit tests for each handler
- Integration tests for full flow
- Consolidation metrics/dashboard

## Files to Create

```
api/services/
├── consolidation_service.py      # Core consolidation logic
├── consolidation_handlers/
│   ├── __init__.py
│   ├── base.py                   # Abstract handler
│   ├── prediction_handler.py     # Predictions → Facts
│   ├── session_handler.py        # Sessions → Episodes
│   ├── mental_model_handler.py   # Models → Relationships
│   └── basin_handler.py          # Basins → Graph weights

api/models/
├── consolidation.py              # ConsolidationBatch, ConsolidationItem

n8n-workflows/
├── memory_consolidation.json     # n8n workflow

tests/
├── unit/
│   ├── test_consolidation_service.py
│   ├── test_prediction_handler.py
│   ├── test_session_handler.py
│   └── test_crash_recovery.py
├── integration/
│   └── test_consolidation_flow.py
```

## Configuration

```python
# api/config/consolidation.py
CONSOLIDATION_BATCH_SIZE = 50
CONSOLIDATION_TIME_THRESHOLD_MINUTES = 15
CONSOLIDATION_IDLE_THRESHOLD_MINUTES = 30
CONSOLIDATION_CYCLE_INTERVAL = 100
CONSOLIDATION_MAX_RETRIES = 3
CONSOLIDATION_RETRY_BACKOFF_SECONDS = [10, 60, 300]  # 10s, 1m, 5m
```

## Success Metrics

| Metric | Target |
|--------|--------|
| Consolidation latency (p95) | < 5 seconds |
| Failed consolidations | < 1% |
| Crash recovery success | > 99% |
| Data loss on crash | 0 items |
