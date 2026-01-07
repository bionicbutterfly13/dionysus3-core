"""
DAEDALUS-style coordination pool (smolagents-backed placeholder).

Provides in-memory agent registry, task queue, assignments, and health stats.
Designed to be smolagents-friendly (agent ids/context ids tracked) and
instrumented for metrics/observability.
"""

from __future__ import annotations

import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    DEGRADED = "degraded"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    DISCOVERY = "discovery"
    MIGRATION = "migration"
    HEARTBEAT = "heartbeat"
    INGEST = "ingest"
    RESEARCH = "research"
    GENERAL = "general"


class PoolFullError(Exception):
    """Raised when the coordination pool has reached MAX_POOL_SIZE."""
    pass


class QueueFullError(Exception):
    """Raised when the task queue has reached MAX_QUEUE_DEPTH."""
    pass


DEFAULT_POOL_SIZE = 4
MAX_POOL_SIZE = 16
MAX_QUEUE_DEPTH = 100
MAX_RETRIES = 3
ASSIGNMENT_LATENCY_TARGET_MS = 500


@dataclass
class Agent:
    agent_id: str
    context_window_id: str
    tool_session_id: str
    memory_handle_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_task_id: Optional[str] = None
    performance: Dict = field(default_factory=lambda: {
        "tasks_completed": 0,
        "tasks_failed": 0,
        "average_task_time": 0.0,
        "context_switches": 0,
    }) 
    health: Dict = field(default_factory=lambda: {
        "memory_usage": 0.1,
        "cpu_usage": 0.1,
    })
    isolation: Dict = field(default_factory=lambda: {
        "shared_state_detected": False,
        "notes": [],
    })


@dataclass
class Task:
    task_id: str
    payload: Dict
    task_type: TaskType = TaskType.GENERAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    attempt_count: int = 0
    failed_agent_ids: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assignment_latency_ms: Optional[float] = None
    next_retry_at: Optional[float] = None


class CoordinationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []
        self.dead_letter_queue: List[str] = [] # Phase 3: DLQ
        self.delayed_retries: List[tuple[float, str]] = [] # Phase 3: (timestamp, task_id)
        self.last_context_snapshot: Dict[str, str] = {}  # agent_id -> context_window_id
        self._current_trace_id: Optional[str] = None

    @property
    def trace_id(self) -> str:
        return self._current_trace_id or "no-trace"

    @trace_id.setter
    def trace_id(self, value: str):
        self._current_trace_id = value

    def _log(self, level: int, event: str, **kwargs):
        extra = kwargs
        extra["trace_id"] = self.trace_id
        self.logger.log(level, event, extra=extra)

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------
    def initialize_pool(self, size: int = DEFAULT_POOL_SIZE) -> List[str]:
        """Initialize the pool with a specific number of agents."""
        if size > MAX_POOL_SIZE:
            self._log(logging.WARNING, f"Requested pool size {size} exceeds MAX_POOL_SIZE {MAX_POOL_SIZE}. Capping.")
            size = MAX_POOL_SIZE
        
        spawned_ids = []
        for _ in range(size):
            try:
                agent_id = self.spawn_agent()
                spawned_ids.append(agent_id)
            except PoolFullError:
                break
        
        self._log(logging.INFO, "pool_initialized", size=len(spawned_ids), requested=size)
        return spawned_ids

    def shutdown_pool(self) -> None:
        """Gracefully shut down the coordination pool."""
        self._log(logging.INFO, "pool_shutdown_initiated", agents=len(self.agents), queue=len(self.queue))
        self.agents.clear()
        self.tasks.clear()
        self.queue.clear()
        self.delayed_retries.clear()
        self.dead_letter_queue.clear()
        self.last_context_snapshot.clear()
        self._log(logging.INFO, "pool_shutdown_completed")

    def spawn_agent(self) -> str:
        if len(self.agents) >= MAX_POOL_SIZE:
            self._log(logging.ERROR, "pool_full_error", current_size=len(self.agents))
            raise PoolFullError(f"Coordination pool is full (MAX_POOL_SIZE={MAX_POOL_SIZE})")

        agent_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        tool_session_id = str(uuid.uuid4())
        memory_handle_id = str(uuid.uuid4())
        
        agent = Agent(
            agent_id=agent_id, 
            context_window_id=context_id,
            tool_session_id=tool_session_id,
            memory_handle_id=memory_handle_id
        )
        self.agents[agent_id] = agent
        self.last_context_snapshot[agent_id] = context_id
        self._log(logging.INFO, "agent_spawned", agent_id=agent_id, context_id=context_id)
        
        # Initial isolation check
        self._check_isolation(agent)
        
        return agent_id

    def list_agents(self) -> List[Agent]:
        return list(self.agents.values())

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------
    def _process_delayed_tasks(self) -> None:
        """Phase 3: Move ready tasks from delayed_retries to main queue."""
        if not self.delayed_retries:
            return
            
        now = time.time()
        # Filter tasks that are ready
        ready_tasks = [t for t in self.delayed_retries if t[0] <= now]
        # Keep tasks that are NOT ready
        self.delayed_retries = [t for t in self.delayed_retries if t[0] > now]
        
        for _, task_id in ready_tasks:
            task = self.tasks.get(task_id)
            if task:
                task.next_retry_at = None
            # Re-queue at the front for priority
            self.queue.insert(0, task_id)
            self._log(logging.INFO, "task_retry_ready", task_id=task_id)

    def submit_task(self, payload: Dict, preferred_agent_id: Optional[str] = None, task_type: TaskType | str = TaskType.GENERAL) -> str:
        self._process_delayed_tasks() # Check for retries first

        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL

        if len(self.queue) >= MAX_QUEUE_DEPTH:
            self._log(logging.ERROR, "queue_full_error", current_depth=len(self.queue))
            raise QueueFullError(f"Task queue is full (MAX_QUEUE_DEPTH={MAX_QUEUE_DEPTH})")

        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, payload=payload, task_type=task_type)
        self.tasks[task_id] = task
        
        assigned = self._assign_task(task, preferred_agent_id)
        if not assigned:
            self.queue.append(task_id)
            self._log(logging.INFO, "task_queued", task_id=task_id, task_type=task_type.value)
        
        return task_id

    def handle_agent_failure(self, agent_id: str) -> None:
        """Handle an agent failure by retrying its current task with backoff."""
        agent = self.agents.get(agent_id)
        if not agent:
            return

        agent.status = AgentStatus.DEGRADED
        
        if not agent.current_task_id:
            self._log(logging.WARNING, "agent_failure_detected_idle", agent_id=agent_id)
            return

        task_id = agent.current_task_id
        task = self.tasks[task_id]
        
        agent.status = AgentStatus.DEGRADED
        agent.performance["tasks_failed"] += 1
        agent.current_task_id = None
        
        task.attempt_count += 1
        task.failed_agent_ids.append(agent_id)
        task.status = TaskStatus.PENDING
        task.assigned_agent_id = None
        
        self._log(
            logging.WARNING,
            "agent_failure_detected",
            agent_id=agent_id,
            task_id=task_id,
            attempt_count=task.attempt_count
        )

        if task.attempt_count < MAX_RETRIES:
            assigned = self._reassign_task(task)
            if assigned:
                task.next_retry_at = None
                self._log(logging.INFO, "task_reassigned_after_failure", task_id=task_id)
                return

            # Phase 3: Exponential Backoff
            # 1st retry: 2s, 2nd: 4s, 3rd: 8s
            backoff_delay = 2 ** task.attempt_count
            task.next_retry_at = time.time() + backoff_delay

            self.delayed_retries = [t for t in self.delayed_retries if t[1] != task_id]
            self.delayed_retries.append((task.next_retry_at, task_id))
            self.delayed_retries.sort(key=lambda x: x[0]) # Keep sorted by timestamp

            self._log(logging.INFO, "task_scheduled_retry", task_id=task_id, delay_sec=backoff_delay)
        else:
            # Phase 3: Dead Letter Queue
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            self.dead_letter_queue.append(task_id)
            self._log(logging.ERROR, "task_moved_to_dlq", task_id=task_id, attempts=task.attempt_count)

    def replay_dead_letter_task(self, task_id: str) -> bool:
        """Phase 3: Manually replay a task from DLQ."""
        if task_id not in self.dead_letter_queue:
            return False
            
        task = self.tasks.get(task_id)
        if not task:
            return False
            
        # Reset task state
        task.status = TaskStatus.PENDING
        task.attempt_count = 0 # Reset attempts so it gets full retry budget again
        task.failed_agent_ids = [] # Optionally clear history or keep it
        task.next_retry_at = None
        task.completed_at = None
        
        self.dead_letter_queue.remove(task_id)
        
        # Try assign or queue
        assigned = self._assign_task(task)
        if not assigned:
            self.queue.insert(0, task_id) # Priority replay
            
        self._log(logging.INFO, "task_replayed_from_dlq", task_id=task_id)
        return True

    def _reassign_task(self, task: Task) -> bool:
        """Try to assign a task to an agent it hasn't failed on yet."""
        for agent in self.agents.values():
            if agent.status == AgentStatus.IDLE and agent.agent_id not in task.failed_agent_ids:
                return self._assign_task(task, preferred_agent_id=agent.agent_id)
        return False

    def _is_discovery_service_available(self) -> bool:
        """Check if Spec 019 discovery/migration service is available."""
        # This would usually call a health check on discovery_service.
        # For now, we'll try to get the service and check a property, 
        # or assume it's available unless we've detected failures.
        try:
            from api.services.discovery_service import get_discovery_service
            # If we can get it, assume it's up for this mockup
            return True
        except (ImportError, Exception) as e:
            self._log(logging.WARNING, "discovery_service_unavailable", error=str(e))
            return False

    def _should_process_task(self, task: Task) -> bool:
        """Determine if a task should be processed based on system state."""
        if task.task_type in [TaskType.DISCOVERY, TaskType.MIGRATION]:
            if not self._is_discovery_service_available():
                self._log(
                    logging.WARNING,
                    "skipping_discovery_task_service_unavailable", 
                    task_id=task.task_id, 
                    type=task.task_type.value
                )
                return False
        return True

    def _assign_task(self, task: Task, preferred_agent_id: Optional[str] = None) -> bool:
        if not self._should_process_task(task):
            return False

        agent = None
        
        # Preferred logic (T025a): task_type affinity
        if preferred_agent_id and preferred_agent_id in self.agents:
            cand = self.agents[preferred_agent_id]
            if cand.status == AgentStatus.IDLE:
                agent = cand
        
        if agent is None:
            # Find best IDLE agent based on affinity if possible
            best_cand = None
            min_latency = float('inf')
            
            for cand in self.agents.values():
                if cand.status == AgentStatus.IDLE and cand.agent_id not in task.failed_agent_ids:
                    # Very simple affinity: if they have average_task_time, they've done work.
                    # In a real system we'd track per-task-type metrics.
                    # For now, just pick any IDLE one, but prioritize the first found.
                    if best_cand is None:
                        best_cand = cand
            
            agent = best_cand

        if agent is None:
            return False

        agent.current_task_id = task.task_id
        agent.status = AgentStatus.ANALYZING
        agent.performance["context_switches"] += 1
        self._check_isolation(agent)

        task.assigned_agent_id = agent.agent_id
        task.status = TaskStatus.IN_PROGRESS
        if task.started_at is None:
            task.started_at = time.time()
            task.assignment_latency_ms = (task.started_at - task.created_at) * 1000

        self._log(
            logging.INFO,
            "task_assigned",
            task_id=task.task_id, 
            agent_id=agent.agent_id,
            latency_ms=task.assignment_latency_ms
        )
        return True

    def complete_task(self, task_id: str, success: bool = True, failure_reason: Optional[str] = None) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        
        if not success:
            self._log(
                logging.WARNING, 
                "task_completed_failure_reported", 
                task_id=task_id, 
                agent_id=task.assigned_agent_id,
                reason=failure_reason
            )

        agent = self.agents.get(task.assigned_agent_id or "")
        now = time.time()
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = now

        self._process_delayed_tasks()
        
        if agent:
            agent.status = AgentStatus.IDLE
            agent.current_task_id = None
            agent.performance["tasks_completed" if success else "tasks_failed"] += 1
            if failure_reason:
                 # Track specific failure reasons if needed in the future
                 pass

            if task.started_at:
                duration = now - task.started_at
                prev = agent.performance.get("average_task_time", 0.0)
                count = agent.performance["tasks_completed"] + agent.performance["tasks_failed"]
                agent.performance["average_task_time"] = (prev * (count - 1) + duration) / max(count, 1)

        # Drain queue if any
        if self.queue:
            next_task_id = self.queue.pop(0)
            next_task = self.tasks[next_task_id]
            # Try to re-assign
            self._assign_task(next_task)

    def _check_isolation(self, agent: Agent) -> None:
        """Detect unexpected context reuse across agents."""
        prior = self.last_context_snapshot.get(agent.agent_id)
        if prior and prior != agent.context_window_id:
            # Agent context changed; update snapshot
            self.last_context_snapshot[agent.agent_id] = agent.context_window_id

        # Detect if any other agent shares the same resources
        for other_id, other in self.agents.items():
            if other_id == agent.agent_id:
                continue
            
            collisions = []
            if other.context_window_id == agent.context_window_id:
                collisions.append("context_window_id")
            if other.tool_session_id == agent.tool_session_id:
                collisions.append("tool_session_id")
            if other.memory_handle_id == agent.memory_handle_id:
                collisions.append("memory_handle_id")
                
            if collisions:
                agent.isolation["shared_state_detected"] = True
                note = f"Collision with {other_id} on: {', '.join(collisions)}"
                if note not in agent.isolation["notes"]:
                    agent.isolation["notes"].append(note)
                
                self._log(
                    logging.WARNING,
                    "isolation_breach",
                    agent_id=agent.agent_id,
                    other_agent_id=other_id,
                    collisions=collisions,
                )

    def generate_isolation_report(self) -> Dict:
        """Generate a comprehensive report on agent isolation status."""
        report = {
            "timestamp": time.time(),
            "total_agents": len(self.agents),
            "breaches_detected": 0,
            "details": []
        }
        
        for agent in self.agents.values():
            # Run a fresh check
            self._check_isolation(agent)
            
            status = {
                "agent_id": agent.agent_id,
                "context_window_id": agent.context_window_id,
                "tool_session_id": agent.tool_session_id,
                "memory_handle_id": agent.memory_handle_id,
                "isolated": not agent.isolation["shared_state_detected"],
                "issues": agent.isolation["notes"]
            }
            
            if not status["isolated"]:
                report["breaches_detected"] += 1
                
            report["details"].append(status)
            
        return report

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def metrics(self) -> Dict:
        self._process_delayed_tasks()
        pending = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        in_progress = [t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]
        completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
        
        avg_latency = 0.0
        started_tasks = [t for t in self.tasks.values() if t.assignment_latency_ms is not None]
        if started_tasks:
            avg_latency = sum(t.assignment_latency_ms for t in started_tasks) / len(started_tasks)

        utilization = 0.0
        if self.agents:
            busy_agents = [a for a in self.agents.values() if a.status in [AgentStatus.ANALYZING, AgentStatus.EXECUTING]]
            utilization = len(busy_agents) / len(self.agents)

        return {
            "agents": len(self.agents),
            "tasks_total": len(self.tasks),
            "tasks_pending": len(pending),
            "tasks_in_progress": len(in_progress),
            "tasks_completed": len(completed),
            "tasks_failed": len(failed),
            "queue_length": len(self.queue),
            "avg_assignment_latency_ms": avg_latency,
            "utilization": utilization,
        }
    
    def get_pool_stats(self) -> Dict:
        """
        Get comprehensive pool statistics including isolation health.
        (Task T009 compliance)
        """
        stats = self.metrics()
        isolation = self.generate_isolation_report()
        stats["isolation_breaches"] = isolation["breaches_detected"]
        stats["pool_health_score"] = self._calculate_health_score(stats)
        return stats

    def _calculate_health_score(self, stats: Dict) -> float:
        """Calculate a 0.0-1.0 health score for the pool."""
        score = 1.0
        
        # Deduct for failures
        total = stats["tasks_total"]
        if total > 0:
            fail_rate = stats["tasks_failed"] / total
            score -= (fail_rate * 0.5) # Failures hurt health
            
        # Deduct for breaches
        if stats.get("isolation_breaches", 0) > 0:
            score -= 0.2 # Security risk
            
        # Deduct for queue overflow risk
        if stats["queue_length"] > MAX_QUEUE_DEPTH * 0.8:
            score -= 0.1
            
        return max(0.0, min(1.0, score))

    def agent_health_report(self) -> List[Dict]:
        return [
            {
                "agent": {
                    "agent_id": a.agent_id,
                    "context_window_id": a.context_window_id,
                    "status": a.status.value,
                },
                "health": a.health,
                "performance": a.performance,
                "isolation": a.isolation,
            }
            for a in self.agents.values()
        ]


_coordination_service: Optional[CoordinationService] = None


def get_coordination_service() -> CoordinationService:
    global _coordination_service
    if _coordination_service is None:
        _coordination_service = CoordinationService()
    return _coordination_service
