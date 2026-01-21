"""
Coordination API router

Feature: 020-coordination-pool (formerly Daedalus)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from api.services.coordination_service import (
    get_coordination_service,
    PoolFullError,
    QueueFullError,
    TaskType,
)


router = APIRouter(prefix="/api/coordination", tags=["coordination"])


def get_service_with_trace(x_trace_id: Optional[str] = Header(None)):
    import uuid
    service = get_coordination_service()
    service.trace_id = x_trace_id or str(uuid.uuid4())
    return service


class InitializePoolRequest(BaseModel):
    size: int = Field(default=4, ge=1, le=16)


class SpawnAgentResponse(BaseModel):
    agent_id: str
    context_window_id: str
    status: str


class SubmitTaskRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    preferred_agent_id: Optional[str] = None
    task_type: TaskType = TaskType.GENERAL
    bootstrap_recall: bool = Field(default=True, description="Whether to perform bootstrap recall for this task")


class SubmitTaskResponse(BaseModel):
    task_id: str
    status: str
    assigned_agent_id: Optional[str]


class TaskDetailResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    assigned_agent_id: Optional[str]
    attempt_count: int
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    assignment_latency_ms: Optional[float]


class MetricsResponse(BaseModel):
    agents: int
    tasks_total: int
    tasks_pending: int
    tasks_in_progress: int
    tasks_completed: int
    tasks_failed: int
    queue_length: int
    avg_assignment_latency_ms: float
    utilization: float


class IsolationDetail(BaseModel):
    agent_id: str
    context_window_id: str
    tool_session_id: str
    memory_handle_id: str
    isolated: bool
    issues: List[str]


class IsolationReportResponse(BaseModel):
    timestamp: float
    total_agents: int
    breaches_detected: int
    details: List[IsolationDetail]


@router.post("/pool/initialize")
async def initialize_pool(request: InitializePoolRequest, service = Depends(get_service_with_trace)) -> Dict[str, Any]:
    spawned_ids = service.initialize_pool(request.size)
    return {"status": "initialized", "spawned_agents": len(spawned_ids), "agent_ids": spawned_ids}


@router.delete("/pool")
async def shutdown_pool(service = Depends(get_service_with_trace)) -> Dict[str, str]:
    service.shutdown_pool()
    return {"status": "shutdown_completed"}


@router.post("/agents", response_model=SpawnAgentResponse)
async def spawn_agent(service = Depends(get_service_with_trace)) -> SpawnAgentResponse:
    try:
        agent_id = service.spawn_agent()
        agent = service.agents[agent_id]
        return SpawnAgentResponse(
            agent_id=agent.agent_id,
            context_window_id=agent.context_window_id,
            status=agent.status.value,
        )
    except PoolFullError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/agents")
async def list_agents(service = Depends(get_service_with_trace)) -> List[Dict[str, Any]]:
    return service.agent_health_report()


@router.post("/agents/{agent_id}/fail")
async def fail_agent(agent_id: str, service = Depends(get_service_with_trace)) -> Dict[str, str]:
    if agent_id not in service.agents:
        raise HTTPException(status_code=404, detail="agent not found")
    service.handle_agent_failure(agent_id)
    return {"agent_id": agent_id, "status": service.agents[agent_id].status.value}


@router.get("/isolation-report", response_model=IsolationReportResponse)
async def get_isolation_report(service = Depends(get_service_with_trace)) -> IsolationReportResponse:
    report = service.generate_isolation_report()
    return IsolationReportResponse(**report)


@router.post("/tasks", response_model=SubmitTaskResponse)
async def submit_task(request: SubmitTaskRequest, service = Depends(get_service_with_trace)) -> SubmitTaskResponse:
    try:
        # Inject bootstrap_recall into payload so service/agents can see it
        request.payload["bootstrap_recall"] = request.bootstrap_recall
        task_id = service.submit_task(request.payload, request.preferred_agent_id, request.task_type)
        task = service.tasks[task_id]
        return SubmitTaskResponse(
            task_id=task_id,
            status=task.status.value,
            assigned_agent_id=task.assigned_agent_id,
        )
    except QueueFullError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str, service = Depends(get_service_with_trace)) -> TaskDetailResponse:
    task = service.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return TaskDetailResponse(
        task_id=task.task_id,
        task_type=task.task_type.value,
        status=task.status.value,
        assigned_agent_id=task.assigned_agent_id,
        attempt_count=task.attempt_count,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        assignment_latency_ms=task.assignment_latency_ms
    )


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, success: bool = True, service = Depends(get_service_with_trace)) -> Dict[str, str]:
    if task_id not in service.tasks:
        raise HTTPException(status_code=404, detail="task not found")
    service.complete_task(task_id, success=success)
    return {"task_id": task_id, "status": service.tasks[task_id].status.value}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(service = Depends(get_service_with_trace)) -> MetricsResponse:
    m = service.metrics()
    return MetricsResponse(**m)
