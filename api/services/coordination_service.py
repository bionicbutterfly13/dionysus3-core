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


@dataclass
class Agent:
    agent_id: str
    context_window_id: str
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


@dataclass
class Task:
    task_id: str
    payload: Dict
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class CoordinationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------
    def spawn_agent(self) -> str:
        agent_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        agent = Agent(agent_id=agent_id, context_window_id=context_id)
        self.agents[agent_id] = agent
        self.logger.info("agent_spawned", extra={"agent_id": agent_id, "context_id": context_id})
        return agent_id

    def list_agents(self) -> List[Agent]:
        return list(self.agents.values())

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------
    def submit_task(self, payload: Dict, preferred_agent_id: Optional[str] = None) -> str:
        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, payload=payload)
        self.tasks[task_id] = task
        assigned = self._assign_task(task, preferred_agent_id)
        if not assigned:
            self.queue.append(task_id)
            self.logger.info("task_queued", extra={"task_id": task_id})
        return task_id

    def _assign_task(self, task: Task, preferred_agent_id: Optional[str] = None) -> bool:
        agent = None
        if preferred_agent_id and preferred_agent_id in self.agents:
            cand = self.agents[preferred_agent_id]
            if cand.status == AgentStatus.IDLE:
                agent = cand
        if agent is None:
            for cand in self.agents.values():
                if cand.status == AgentStatus.IDLE:
                    agent = cand
                    break
        if agent is None:
            return False

        agent.current_task_id = task.task_id
        agent.status = AgentStatus.ANALYZING
        agent.performance["context_switches"] += 1

        task.assigned_agent_id = agent.agent_id
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = time.time()

        self.logger.info(
            "task_assigned",
            extra={"task_id": task.task_id, "agent_id": agent.agent_id},
        )
        return True

    def complete_task(self, task_id: str, success: bool = True) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        agent = self.agents.get(task.assigned_agent_id or "")
        now = time.time()
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = now
        if agent:
            agent.status = AgentStatus.IDLE
            agent.current_task_id = None
            agent.performance["tasks_completed" if success else "tasks_failed"] += 1
            if task.started_at:
                duration = now - task.started_at
                prev = agent.performance.get("average_task_time", 0.0)
                count = agent.performance["tasks_completed"] + agent.performance["tasks_failed"]
                agent.performance["average_task_time"] = (prev * (count - 1) + duration) / max(count, 1)

        # Drain queue if any
        if self.queue:
            next_task_id = self.queue.pop(0)
            next_task = self.tasks[next_task_id]
            self._assign_task(next_task)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def metrics(self) -> Dict:
        active_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]
        return {
            "agents": len(self.agents),
            "tasks_total": len(self.tasks),
            "tasks_in_progress": len(active_tasks),
            "queue_length": len(self.queue),
        }

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
            }
            for a in self.agents.values()
        ]


_coordination_service: Optional[CoordinationService] = None


def get_coordination_service() -> CoordinationService:
    global _coordination_service
    if _coordination_service is None:
        _coordination_service = CoordinationService()
    return _coordination_service

