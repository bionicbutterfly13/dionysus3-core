# Research: DAEDALUS Coordination Pool

**Feature**: 020-daedalus-coordination-pool
**Date**: 2025-12-27

## 1. smolagents Pool Patterns

### Decision
Use the existing in-memory agent registry pattern with enhanced isolation tracking. Each agent gets unique UUIDs for `context_window_id`, `tool_session_id`, and `memory_handle_id`.

### Rationale
- The current `coordination_service.py` already implements this pattern correctly
- smolagents `CodeAgent` instances are stateful but don't share context if instantiated separately
- The isolation check (`_check_isolation`) already detects collision between agent resource IDs
- No MCP session sharing needed - each agent can bridge its own tools

### Alternatives Considered
- **Shared ToolCollection with agent-specific namespacing**: Rejected - adds complexity without benefit for our workload
- **Multiprocessing with separate Python interpreters**: Rejected - overkill for background jobs; adds IPC overhead

---

## 2. Bounded Queue with Backpressure

### Decision
Implement queue depth check in `submit_task()` with HTTP 429 rejection when queue exceeds 100 pending tasks.

### Rationale
- Simple list-based queue (`self.queue`) is sufficient for 100-task limit
- Rejection at submission time is cleaner than async backpressure
- FastAPI's `HTTPException(429)` provides standard backpressure signaling
- No async queue library needed - synchronous check is fast enough for ≤500ms latency target

### Alternatives Considered
- **asyncio.Queue with maxsize**: Rejected - requires refactoring to async submission model; current sync pattern is simpler
- **Redis-backed queue**: Rejected - over-engineering for in-memory workload; adds external dependency

### Implementation Pattern
```python
MAX_QUEUE_DEPTH = 100

def submit_task(self, payload: Dict, preferred_agent_id: Optional[str] = None) -> str:
    if len(self.queue) >= MAX_QUEUE_DEPTH:
        raise QueueFullError("Task queue full")
    # ... existing logic
```

Router converts `QueueFullError` to HTTP 429.

---

## 3. Retry with Agent Failover

### Decision
Track `attempt_count` per task. On agent crash detection, reassign to a different agent up to 3 total attempts.

### Rationale
- Task dataclass already tracks `assigned_agent_id` - extend with `attempt_count` and `failed_agent_ids`
- Crash detection via explicit `fail_agent()` method or health check timeout
- Failover routing excludes previously failed agents when possible
- After 3 attempts, task transitions to `FAILED` status permanently

### Alternatives Considered
- **Exponential backoff**: Rejected - not needed for agent failover (agents don't throttle)
- **Dead letter queue**: Rejected - spec says fail after 3 attempts, no DLQ requirement

### Implementation Pattern
```python
@dataclass
class Task:
    # ... existing fields
    attempt_count: int = 0
    failed_agent_ids: List[str] = field(default_factory=list)

MAX_RETRIES = 3

def handle_agent_failure(self, agent_id: str) -> None:
    task = self._get_task_for_agent(agent_id)
    if task:
        task.attempt_count += 1
        task.failed_agent_ids.append(agent_id)
        if task.attempt_count >= MAX_RETRIES:
            task.status = TaskStatus.FAILED
        else:
            self._reassign_task(task, exclude_agents=task.failed_agent_ids)
```

---

## 4. Graceful Degradation for Spec 019

### Decision
Add `task_type` field to Task. When Spec 019 discovery service is unavailable, queue `discovery`/`migration` tasks but continue processing `heartbeat`, `ingest`, `research` tasks.

### Rationale
- Task type differentiation enables selective queueing
- Health check for Spec 019 service can be polled or event-driven
- Degraded state is logged but doesn't block other work
- When service recovers, queued discovery tasks resume automatically

### Alternatives Considered
- **Circuit breaker pattern**: Considered but deferred - simple availability check sufficient for V1
- **Task priority levels**: Deferred - out of scope for this feature

### Implementation Pattern
```python
class TaskType(str, Enum):
    DISCOVERY = "discovery"
    MIGRATION = "migration"
    HEARTBEAT = "heartbeat"
    INGEST = "ingest"
    RESEARCH = "research"
    GENERAL = "general"

def _should_process_task(self, task: Task) -> bool:
    if task.task_type in (TaskType.DISCOVERY, TaskType.MIGRATION):
        return self._is_discovery_service_available()
    return True
```

---

## 5. Pool Size Enforcement

### Decision
Add `MIN_POOL_SIZE`, `DEFAULT_POOL_SIZE`, `MAX_POOL_SIZE` constants. Enforce in `spawn_agent()` and add `initialize_pool(size: int)` method.

### Rationale
- Spec defines default=4, max=16
- `spawn_agent()` should reject if pool at max capacity
- Pool initialization on startup ensures minimum agents ready

### Implementation Pattern
```python
DEFAULT_POOL_SIZE = 4
MAX_POOL_SIZE = 16

def spawn_agent(self) -> str:
    if len(self.agents) >= MAX_POOL_SIZE:
        raise PoolFullError("Agent pool at maximum capacity")
    # ... existing logic

def initialize_pool(self, size: int = DEFAULT_POOL_SIZE) -> List[str]:
    size = min(size, MAX_POOL_SIZE)
    return [self.spawn_agent() for _ in range(size)]
```

---

## Summary

All research items resolved. No external dependencies required beyond existing stack.

| Topic | Decision | Complexity |
|-------|----------|------------|
| Agent pool isolation | Existing pattern sufficient | Low |
| Bounded queue | List + 429 rejection | Low |
| Retry/failover | Task attempt tracking | Medium |
| Graceful degradation | Task type + availability check | Medium |
| Pool size limits | Constants + enforcement | Low |
