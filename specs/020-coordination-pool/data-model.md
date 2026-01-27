# Data Model: Coordination Pool

**Feature**: 020-coordination-pool
**Date**: 2025-12-27

## Entities

### AgentStatus (Enum)

States for coordination pool agents.

| Value | Description |
|-------|-------------|
| `IDLE` | Agent available for task assignment |
| `ANALYZING` | Agent received task, preparing execution |
| `EXECUTING` | Agent actively processing task |
| `DEGRADED` | Agent unhealthy, should not receive new tasks |

### TaskStatus (Enum)

States for queued/assigned tasks.

| Value | Description |
|-------|-------------|
| `PENDING` | Task queued, awaiting agent assignment |
| `IN_PROGRESS` | Task assigned and being executed |
| `COMPLETED` | Task finished successfully |
| `FAILED` | Task failed after max retries (3 attempts) |
| `CANCELLED` | Task cancelled by operator |

### TaskType (Enum) - NEW

Classification for graceful degradation routing.

| Value | Description |
|-------|-------------|
| `DISCOVERY` | Spec 019 discovery jobs (requires discovery service) |
| `MIGRATION` | Spec 019 migration jobs (requires discovery service) |
| `HEARTBEAT` | System heartbeat jobs |
| `INGEST` | Memory ingest jobs |
| `RESEARCH` | Research/analysis jobs |
| `GENERAL` | Unclassified jobs |

### Agent (Dataclass)

Represents a smolagent instance in the pool.

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | `str` | Unique identifier (UUID) |
| `context_window_id` | `str` | Isolated context window ID (UUID) |
| `tool_session_id` | `str` | Isolated tool session ID (UUID) |
| `memory_handle_id` | `str` | Isolated memory handle ID (UUID) |
| `status` | `AgentStatus` | Current state (default: IDLE) |
| `current_task_id` | `Optional[str]` | Currently assigned task |
| `performance` | `Dict` | Performance metrics (see below) |
| `health` | `Dict` | Health metrics (see below) |
| `isolation` | `Dict` | Isolation status (see below) |

**Performance Dict**:
```python
{
    "tasks_completed": int,
    "tasks_failed": int,
    "average_task_time": float,  # seconds
    "context_switches": int,
}
```

**Health Dict**:
```python
{
    "memory_usage": float,  # 0.0-1.0
    "cpu_usage": float,     # 0.0-1.0
}
```

**Isolation Dict**:
```python
{
    "shared_state_detected": bool,
    "notes": List[str],
}
```

### Task (Dataclass)

Represents a unit of work in the coordination pool.

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Unique identifier (UUID) |
| `task_type` | `TaskType` | Classification for routing (NEW) |
| `payload` | `Dict` | Task-specific data |
| `status` | `TaskStatus` | Current state (default: PENDING) |
| `assigned_agent_id` | `Optional[str]` | Agent processing this task |
| `attempt_count` | `int` | Number of execution attempts (NEW) |
| `failed_agent_ids` | `List[str]` | Agents that failed this task (NEW) |
| `created_at` | `float` | Unix timestamp of creation |
| `started_at` | `Optional[float]` | Unix timestamp of first execution start |
| `completed_at` | `Optional[float]` | Unix timestamp of completion |

## Relationships

```
CoordinationService 1──* Agent     (pool membership)
CoordinationService 1──* Task      (task registry)
Agent 0..1──0..1 Task              (current assignment)
Task *──* Agent                    (failed_agent_ids history)
```

## State Transitions

### Agent Lifecycle

```
[spawn] → IDLE
IDLE → ANALYZING (task assigned)
ANALYZING → EXECUTING (execution started)
EXECUTING → IDLE (task completed/failed)
* → DEGRADED (health check failed)
DEGRADED → IDLE (health restored)
```

### Task Lifecycle

```
[submit] → PENDING (if no agent free)
[submit] → IN_PROGRESS (if agent available)
PENDING → IN_PROGRESS (agent became free)
IN_PROGRESS → COMPLETED (success)
IN_PROGRESS → PENDING (agent failed, retry available)
IN_PROGRESS → FAILED (agent failed, no retries left)
* → CANCELLED (operator cancellation)
```

## Validation Rules

1. **Pool Size**: `1 ≤ len(agents) ≤ 16`
2. **Queue Depth**: `len(queue) ≤ 100` (reject with 429 if exceeded)
3. **Retry Limit**: `attempt_count ≤ 3` (fail permanently after 3)
4. **Isolation**: No two agents may share `context_window_id`, `tool_session_id`, or `memory_handle_id`
5. **Assignment**: Only `IDLE` agents can receive new tasks
6. **Degradation**: `DISCOVERY`/`MIGRATION` tasks require discovery service availability

## Constants

```python
DEFAULT_POOL_SIZE = 4
MAX_POOL_SIZE = 16
MAX_QUEUE_DEPTH = 100
MAX_RETRIES = 3
ASSIGNMENT_LATENCY_TARGET_MS = 500
```
