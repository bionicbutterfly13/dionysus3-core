# Quickstart: DAEDALUS Coordination Pool

**Feature**: 020-daedalus-coordination-pool

## Prerequisites

- Dionysus 3 API running (`docker compose up -d --build`)
- API accessible at `http://localhost:8000`

## Basic Usage

### 1. Initialize the Pool

```bash
# Initialize with default size (4 agents)
curl -X POST http://localhost:8000/api/coordination/pool/initialize

# Or specify a custom size (1-16)
curl -X POST http://localhost:8000/api/coordination/pool/initialize \
  -H "Content-Type: application/json" \
  -d '{"size": 8}'
```

Response:
```json
{
  "agent_ids": ["uuid1", "uuid2", "uuid3", "uuid4"],
  "pool_size": 4
}
```

### 2. Submit a Task

```bash
curl -X POST http://localhost:8000/api/coordination/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"action": "recall", "query": "recent memories"},
    "task_type": "research"
  }'
```

Response:
```json
{
  "task_id": "task-uuid",
  "status": "in_progress",
  "assigned_agent_id": "agent-uuid"
}
```

### 3. Check Task Status

```bash
curl http://localhost:8000/api/coordination/tasks/{task_id}
```

### 4. Complete a Task

```bash
# Success
curl -X POST http://localhost:8000/api/coordination/tasks/{task_id}/complete

# Failure
curl -X POST "http://localhost:8000/api/coordination/tasks/{task_id}/complete?success=false"
```

### 5. View Metrics

```bash
curl http://localhost:8000/api/coordination/metrics
```

Response:
```json
{
  "agents": 4,
  "tasks_total": 10,
  "tasks_in_progress": 2,
  "tasks_pending": 1,
  "tasks_completed": 6,
  "tasks_failed": 1,
  "queue_length": 1,
  "avg_task_duration": 1.23,
  "avg_assignment_latency_ms": 45.2,
  "utilization": 0.5
}
```

### 6. Check Agent Isolation

```bash
curl http://localhost:8000/api/coordination/isolation-report
```

## Using smolagent Tools

From within a smolagent, use the coordination tools:

```python
from api.agents.tools.coordination_tools import (
    spawn_coordination_agent,
    submit_coordination_task,
    complete_coordination_task,
    coordination_metrics,
)

# Spawn an agent
result = spawn_coordination_agent()
print(result["agent_id"])

# Submit a task
task = submit_coordination_task(
    payload={"action": "analyze", "target": "user_behavior"},
    task_type="research"
)
print(task["task_id"], task["status"])

# Complete when done
complete_coordination_task(task["task_id"], success=True)
```

## Task Types

| Type | Description | Requires Spec 019 |
|------|-------------|-------------------|
| `discovery` | Legacy component discovery | Yes |
| `migration` | Component migration jobs | Yes |
| `heartbeat` | System heartbeat cycles | No |
| `ingest` | Memory ingestion jobs | No |
| `research` | Analysis/research tasks | No |
| `general` | Unclassified tasks | No |

## Error Handling

### Queue Full (429)
```json
{"detail": "Task queue full (100 pending tasks)"}
```
Wait for tasks to complete or increase pool size.

### Pool Full (503)
```json
{"detail": "Agent pool at maximum capacity (16 agents)"}
```
Pool is at maximum size. Tasks will queue until agents free up.

### Agent Failure
If an agent crashes, the task is automatically retried on a different agent (up to 3 attempts).

```bash
# Manually report agent failure
curl -X POST http://localhost:8000/api/coordination/agents/{agent_id}/fail
```

## Graceful Degradation

When Spec 019 discovery service is unavailable:
- `discovery` and `migration` tasks remain queued
- `heartbeat`, `ingest`, `research`, and `general` tasks continue processing
- Check `/metrics` for queue depth to monitor backlog
