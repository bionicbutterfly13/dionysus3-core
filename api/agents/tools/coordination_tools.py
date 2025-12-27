"""
Smolagent tools for coordination pool interactions.
Feature: 020-daedalus-coordination-pool
"""

from smolagents import tool

from api.services.coordination_service import get_coordination_service


@tool
def initialize_coordination_pool(size: int = 4) -> dict:
    """Initialize the coordination pool with a specific number of agents."""
    service = get_coordination_service()
    spawned_ids = service.initialize_pool(size)
    return {"status": "initialized", "spawned_agents": len(spawned_ids), "agent_ids": spawned_ids}


@tool
def shutdown_coordination_pool() -> dict:
    """Gracefully shut down the coordination pool."""
    service = get_coordination_service()
    service.shutdown_pool()
    return {"status": "shutdown_completed"}


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
def submit_coordination_task(payload: dict, preferred_agent_id: str | None = None, task_type: str = "general") -> dict:
    """Submit a task to the coordination pool with an optional type."""
    from api.services.coordination_service import TaskType
    service = get_coordination_service()
    try:
        tt = TaskType(task_type)
    except ValueError:
        tt = TaskType.GENERAL
        
    task_id = service.submit_task(payload, preferred_agent_id, tt)
    task = service.tasks[task_id]
    return {
        "task_id": task_id,
        "status": task.status.value,
        "assigned_agent_id": task.assigned_agent_id,
    }


@tool
def fail_coordination_agent(agent_id: str) -> dict:
    """Trigger failure handling for an agent."""
    service = get_coordination_service()
    service.handle_agent_failure(agent_id)
    agent = service.agents.get(agent_id)
    return {"agent_id": agent_id, "status": agent.status.value if agent else "unknown"}


@tool
def complete_coordination_task(task_id: str, success: bool = True) -> dict:
    """Complete a task and trigger queue drain."""
    service = get_coordination_service()
    service.complete_task(task_id, success=success)
    task = service.tasks.get(task_id)
    return {"task_id": task_id, "status": task.status.value if task else "unknown"}


@tool
def coordination_isolation_report() -> dict:
    """Generate a report on agent isolation status."""
    service = get_coordination_service()
    return service.generate_isolation_report()


@tool
def coordination_metrics() -> dict:
    """Return coordination metrics."""
    service = get_coordination_service()
    return service.metrics()

