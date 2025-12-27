"""
Smolagent tools for coordination pool interactions.
Feature: 020-daedalus-coordination-pool
"""

from smolagents import tool

from api.services.coordination_service import get_coordination_service


@tool
def spawn_coordination_agent() -> dict:
    """Spawn a coordination pool agent and return its identifiers."""
    service = get_coordination_service()
    agent_id = service.spawn_agent()
    agent = service.agents[agent_id]
    return {
        "agent_id": agent.agent_id,
        "context_window_id": agent.context_window_id,
        "status": agent.status.value,
    }


@tool
def submit_coordination_task(payload: dict, preferred_agent_id: str | None = None) -> dict:
    """Submit a task to the coordination pool."""
    service = get_coordination_service()
    task_id = service.submit_task(payload, preferred_agent_id)
    task = service.tasks[task_id]
    return {
        "task_id": task_id,
        "status": task.status.value,
        "assigned_agent_id": task.assigned_agent_id,
    }


@tool
def complete_coordination_task(task_id: str, success: bool = True) -> dict:
    """Complete a task and trigger queue drain."""
    service = get_coordination_service()
    service.complete_task(task_id, success=success)
    task = service.tasks.get(task_id)
    return {"task_id": task_id, "status": task.status.value if task else "unknown"}


@tool
def coordination_metrics() -> dict:
    """Return coordination metrics."""
    service = get_coordination_service()
    return service.metrics()

