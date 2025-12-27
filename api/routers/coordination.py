"""
Coordination API router

Feature: 020-daedalus-coordination-pool
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.services.coordination_service import (
    get_coordination_service,
    AgentStatus,
)


router = APIRouter(prefix="/api/coordination", tags=["coordination"])


class SpawnAgentResponse(BaseModel):
    agent_id: str
    context_window_id: str
    status: str


class SubmitTaskRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    preferred_agent_id: Optional[str] = None


class SubmitTaskResponse(BaseModel):
    task_id: str
    status: str
    assigned_agent_id: Optional[str]


class MetricsResponse(BaseModel):
    agents: int
    tasks_total: int
    tasks_in_progress: int
    queue_length: int
    avg_task_duration: float


@router.post("/agents", response_model=SpawnAgentResponse)
async def spawn_agent() -> SpawnAgentResponse:
    service = get_coordination_service()
    agent_id = service.spawn_agent()
    agent = service.agents[agent_id]
    return SpawnAgentResponse(
        agent_id=agent.agent_id,
        context_window_id=agent.context_window_id,
        status=agent.status.value,
    )


@router.get("/agents")
async def list_agents() -> List[Dict[str, Any]]:
    service = get_coordination_service()
    return service.agent_health_report()


@router.post("/tasks", response_model=SubmitTaskResponse)
async def submit_task(request: SubmitTaskRequest) -> SubmitTaskResponse:
    service = get_coordination_service()
    task_id = service.submit_task(request.payload, request.preferred_agent_id)
    task = service.tasks[task_id]
    return SubmitTaskResponse(
        task_id=task_id,
        status=task.status.value,
        assigned_agent_id=task.assigned_agent_id,
    )


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, success: bool = True) -> Dict[str, str]:
    service = get_coordination_service()
    if task_id not in service.tasks:
        raise HTTPException(status_code=404, detail="task not found")
    service.complete_task(task_id, success=success)
    return {"task_id": task_id, "status": service.tasks[task_id].status.value}


@router.get("/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    service = get_coordination_service()
    m = service.metrics()
    return MetricsResponse(**m)
