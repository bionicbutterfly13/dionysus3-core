"""
Heartbeat REST API Router
Feature: 004-heartbeat-system
Task: T026

REST endpoints for heartbeat system control and goal management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/heartbeat", tags=["heartbeat"])


# =============================================================================
# Request/Response Models
# =============================================================================


class TriggerHeartbeatResponse(BaseModel):
    """Response from triggering a heartbeat."""

    success: bool
    heartbeat_number: int
    energy_start: float
    energy_end: float
    actions_completed: int
    narrative: str


class HeartbeatStatusResponse(BaseModel):
    """Current heartbeat system status."""

    energy_current: float
    energy_max: float
    paused: bool
    pause_reason: Optional[str]
    heartbeat_count: int
    last_heartbeat_at: Optional[str]
    scheduler_state: str


class EnergyStatusResponse(BaseModel):
    """Current energy budget status."""

    current_energy: float
    max_energy: float
    base_regeneration: float
    action_costs: dict[str, float]
    affordable_actions: list[str]


class CreateGoalRequest(BaseModel):
    """Request to create a new goal."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: str = Field(default="queued", pattern="^(active|queued|backburner)$")
    source: str = Field(default="user_request", pattern="^(curiosity|user_request|identity|derived|external)$")


class GoalResponse(BaseModel):
    """Goal data response."""

    id: str
    title: str
    priority: str
    source: str
    blocked: bool = False
    last_touched: Optional[str]


class GoalListResponse(BaseModel):
    """List of goals response."""

    count: int
    goals: list[GoalResponse]


class UpdateGoalRequest(BaseModel):
    """Request to update a goal."""

    action: str = Field(pattern="^(promote|demote|complete|abandon|add_progress)$")
    note: Optional[str] = Field(None, max_length=2000)


class PauseHeartbeatRequest(BaseModel):
    """Request to pause heartbeat."""

    reason: str = Field(min_length=1, max_length=500)


# =============================================================================
# Heartbeat Control Endpoints
# =============================================================================


@router.get("/status", response_model=HeartbeatStatusResponse)
async def get_heartbeat_status():
    """
    Get current heartbeat system status.

    Shows energy state, pause status, heartbeat count, and scheduler info.
    """
    from api.services.energy_service import get_energy_service
    from api.services.heartbeat_scheduler import get_heartbeat_scheduler

    energy_service = get_energy_service()
    scheduler = get_heartbeat_scheduler()

    state = await energy_service.get_state()
    config = energy_service.get_config()
    scheduler_status = scheduler.get_status()

    return HeartbeatStatusResponse(
        energy_current=state.current_energy,
        energy_max=config.max_energy,
        paused=state.paused,
        pause_reason=state.pause_reason,
        heartbeat_count=state.heartbeat_count,
        last_heartbeat_at=state.last_heartbeat_at.isoformat() if state.last_heartbeat_at else None,
        scheduler_state=scheduler_status["state"],
    )


@router.post("/trigger", response_model=TriggerHeartbeatResponse)
async def trigger_heartbeat():
    """
    Manually trigger a heartbeat cycle.

    Use this to run an immediate heartbeat outside the normal hourly schedule.
    """
    from api.services.heartbeat_service import get_heartbeat_service, HeartbeatPausedError

    service = get_heartbeat_service()

    try:
        summary = await service.trigger_manual_heartbeat()
        return TriggerHeartbeatResponse(
            success=True,
            heartbeat_number=summary.heartbeat_number,
            energy_start=summary.energy_start,
            energy_end=summary.energy_end,
            actions_completed=summary.actions_completed,
            narrative=summary.narrative,
        )
    except HeartbeatPausedError as e:
        raise HTTPException(status_code=409, detail=f"Heartbeat paused: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_heartbeat(request: PauseHeartbeatRequest):
    """
    Pause the heartbeat system.

    Heartbeats will not run while paused.
    """
    from api.services.energy_service import get_energy_service

    service = get_energy_service()
    await service.pause(request.reason)

    return {"success": True, "paused": True, "reason": request.reason}


@router.post("/resume")
async def resume_heartbeat():
    """
    Resume the heartbeat system after a pause.
    """
    from api.services.energy_service import get_energy_service

    service = get_energy_service()
    await service.resume()

    return {"success": True, "paused": False}


@router.get("/energy", response_model=EnergyStatusResponse)
async def get_energy_status():
    """
    Get current energy budget and action costs.
    """
    from api.services.energy_service import get_energy_service

    service = get_energy_service()
    state = await service.get_state()
    config = service.get_config()
    costs = service.get_all_costs()

    return EnergyStatusResponse(
        current_energy=state.current_energy,
        max_energy=config.max_energy,
        base_regeneration=config.base_regeneration,
        action_costs=costs,
        affordable_actions=[
            action for action, cost in costs.items()
            if cost <= state.current_energy
        ],
    )


@router.get("/history")
async def get_heartbeat_history(limit: int = 10):
    """
    Get recent heartbeat history.

    Args:
        limit: Maximum heartbeats to return (default: 10)
    """
    from api.services.heartbeat_service import get_heartbeat_service

    service = get_heartbeat_service()
    heartbeats = await service.get_recent_heartbeats(limit=limit)

    return {
        "count": len(heartbeats),
        "heartbeats": heartbeats,
    }


# =============================================================================
# Goal Management Endpoints
# =============================================================================


@router.post("/goals", response_model=dict)
async def create_goal(request: CreateGoalRequest):
    """
    Create a new goal.

    Goals guide what Dionysus works on during heartbeat cycles.
    """
    from api.models.goal import GoalCreate, GoalPriority, GoalSource
    from api.services.goal_service import get_goal_service

    service = get_goal_service()

    goal_data = GoalCreate(
        title=request.title,
        description=request.description,
        priority=GoalPriority(request.priority),
        source=GoalSource(request.source),
    )

    goal = await service.create_goal(goal_data)

    return {
        "success": True,
        "goal": GoalResponse(
            id=str(goal.id),
            title=goal.title,
            priority=goal.priority.value,
            source=goal.source.value,
            blocked=goal.blocked_by is not None,
            last_touched=goal.last_touched.isoformat() if goal.last_touched else None,
        ).model_dump(),
    }


@router.get("/goals", response_model=GoalListResponse)
async def list_goals(
    priority: Optional[str] = None,
    include_completed: bool = False,
    limit: int = 20
):
    """
    List goals, optionally filtered by priority.

    Args:
        priority: Filter to specific priority (active, queued, backburner)
        include_completed: Include completed/abandoned goals
        limit: Maximum goals to return
    """
    from api.models.goal import GoalPriority
    from api.services.goal_service import get_goal_service

    service = get_goal_service()

    priority_filter = GoalPriority(priority) if priority else None
    goals = await service.list_goals(
        priority=priority_filter,
        include_completed=include_completed,
        limit=limit,
    )

    return GoalListResponse(
        count=len(goals),
        goals=[
            GoalResponse(
                id=str(g.id),
                title=g.title,
                priority=g.priority.value,
                source=g.source.value,
                blocked=g.blocked_by is not None,
                last_touched=g.last_touched.isoformat() if g.last_touched else None,
            )
            for g in goals
        ],
    )


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: UUID):
    """
    Get a specific goal by ID.
    """
    from api.services.goal_service import get_goal_service

    service = get_goal_service()
    goal = await service.get_goal(goal_id)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return {
        "id": str(goal.id),
        "title": goal.title,
        "description": goal.description,
        "priority": goal.priority.value,
        "source": goal.source.value,
        "progress": [
            {
                "timestamp": p.timestamp.isoformat(),
                "content": p.content,
                "heartbeat_number": p.heartbeat_number,
            }
            for p in goal.progress
        ],
        "blocked_by": goal.blocked_by.model_dump() if goal.blocked_by else None,
        "emotional_valence": goal.emotional_valence,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "last_touched": goal.last_touched.isoformat() if goal.last_touched else None,
        "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
        "abandoned_at": goal.abandoned_at.isoformat() if goal.abandoned_at else None,
        "abandonment_reason": goal.abandonment_reason,
    }


@router.put("/goals/{goal_id}")
async def update_goal(goal_id: UUID, request: UpdateGoalRequest):
    """
    Update a goal's status.

    Actions:
    - promote: Move to active priority
    - demote: Move to backburner
    - complete: Mark as completed
    - abandon: Mark as abandoned (requires note)
    - add_progress: Add a progress note (requires note)
    """
    from api.services.goal_service import get_goal_service

    service = get_goal_service()

    try:
        if request.action == "promote":
            goal = await service.promote_goal(goal_id)
        elif request.action == "demote":
            goal = await service.demote_goal(goal_id, "backburner")
        elif request.action == "complete":
            goal = await service.complete_goal(goal_id)
        elif request.action == "abandon":
            if not request.note:
                raise HTTPException(status_code=400, detail="Note required for abandon")
            goal = await service.abandon_goal(goal_id, request.note)
        elif request.action == "add_progress":
            if not request.note:
                raise HTTPException(status_code=400, detail="Note required for add_progress")
            goal = await service.add_progress(goal_id, request.note)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

        return {
            "success": True,
            "goal": GoalResponse(
                id=str(goal.id),
                title=goal.title,
                priority=goal.priority.value,
                source=goal.source.value,
                blocked=goal.blocked_by is not None,
                last_touched=goal.last_touched.isoformat() if goal.last_touched else None,
            ).model_dump(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: UUID):
    """
    Delete a goal.

    Use with caution - prefer abandon for tracking purposes.
    """
    from api.services.goal_service import get_goal_service

    service = get_goal_service()
    success = await service.delete_goal(goal_id)

    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")

    return {"success": True, "deleted": str(goal_id)}


@router.get("/goals/review")
async def review_goals():
    """
    Get a review/assessment of all goals.

    Returns analysis of active, queued, blocked, and stale goals.
    """
    from api.services.goal_service import get_goal_service

    service = get_goal_service()
    assessment = await service.review_goals()

    return {
        "active_count": len(assessment.active_goals),
        "queued_count": len(assessment.queued_goals),
        "backburner_count": len(assessment.backburner_goals),
        "blocked_count": len(assessment.blocked_goals),
        "stale_count": len(assessment.stale_goals),
        "promotion_candidates": [
            {"id": str(g.id), "title": g.title}
            for g in assessment.promotion_candidates
        ],
        "needs_brainstorm": assessment.needs_brainstorm,
        "issues": assessment.issues,
    }
