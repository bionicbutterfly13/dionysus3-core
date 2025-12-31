"""
Agents REST API Router (Feature 039, T014)

REST endpoints for agent execution trace management.

TERMINOLOGY: "ExecutionTrace" = agent step logs (operational audit trail)
NOT state-space trajectories. See docs/TERMINOLOGY.md for disambiguation.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.services.execution_trace_service import (
    ExecutionTraceData,
    ExecutionStepData,
    get_execution_trace_service,
)
from api.agents.audit import get_all_token_summaries, get_aggregate_token_stats

router = APIRouter(prefix="/api/agents", tags=["agents"])


# =============================================================================
# Response Models
# =============================================================================


class TraceSummary(BaseModel):
    """Summary of an execution trace for list views."""

    id: str
    agent_name: str
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    step_count: int = 0
    planning_count: int = 0
    success: Optional[bool] = None


class TraceListResponse(BaseModel):
    """Response for listing execution traces."""

    traces: List[TraceSummary]
    count: int


class TraceReplayStep(BaseModel):
    """Formatted step for replay view."""

    step_number: int
    step_type: str
    timestamp: str
    description: str
    tool_name: Optional[str] = None
    error: Optional[str] = None


class TraceReplayResponse(BaseModel):
    """Formatted replay view of an execution trace."""

    trace_id: str
    agent_name: str
    started_at: str
    completed_at: Optional[str] = None
    success: Optional[bool] = None
    steps: List[TraceReplayStep]
    activated_basins: List[str]
    summary: str


class TokenUsageResponse(BaseModel):
    """Token usage statistics."""

    agents: List[dict]
    aggregate: dict


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(20, ge=1, le=100, description="Maximum traces to return"),
    success_only: bool = Query(False, description="Only return successful traces"),
):
    """
    List recent agent execution traces.

    Returns:
        List of trace summaries ordered by start time (newest first)
    """
    service = get_execution_trace_service()

    traces = await service.list_traces(
        agent_name=agent_name,
        limit=limit,
        success_only=success_only,
    )

    summaries = [
        TraceSummary(
            id=t.get("id", ""),
            agent_name=t.get("agent_name", "unknown"),
            run_id=t.get("run_id", ""),
            started_at=t.get("started_at", ""),
            completed_at=t.get("completed_at"),
            step_count=t.get("step_count", 0),
            planning_count=t.get("planning_count", 0),
            success=t.get("success"),
        )
        for t in traces
    ]

    return TraceListResponse(traces=summaries, count=len(summaries))


@router.get("/traces/{trace_id}", response_model=ExecutionTraceData)
async def get_trace(trace_id: str):
    """
    Get full details of an execution trace.

    Args:
        trace_id: The trace UUID

    Returns:
        Full execution trace with steps and activated basins
    """
    service = get_execution_trace_service()
    trace = await service.get_trace(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    return trace


@router.get("/traces/{trace_id}/replay", response_model=TraceReplayResponse)
async def get_trace_replay(trace_id: str):
    """
    Get a formatted replay view of an execution trace.

    This endpoint formats the trace for human-readable display,
    with step descriptions and a narrative summary.

    Args:
        trace_id: The trace UUID

    Returns:
        Formatted replay with step descriptions
    """
    service = get_execution_trace_service()
    trace = await service.get_trace(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    # Format steps for replay
    replay_steps = []
    for step in trace.steps:
        # Build description based on step type
        if step.step_type == "ActionStep":
            if step.tool_name:
                desc = f"Called {step.tool_name}"
                if step.observation_summary:
                    desc += f" → {step.observation_summary}"
            else:
                desc = step.observation_summary or "Action executed"
        elif step.step_type == "PlanningStep":
            plan_preview = (step.plan or "")[:100]
            desc = f"Planning: {plan_preview}..." if len(step.plan or "") > 100 else f"Planning: {step.plan}"
        else:
            desc = f"{step.step_type}: {step.observation_summary or 'No details'}"

        if step.error:
            desc += f" [ERROR: {step.error}]"

        replay_steps.append(
            TraceReplayStep(
                step_number=step.step_number,
                step_type=step.step_type,
                timestamp=step.timestamp,
                description=desc,
                tool_name=step.tool_name,
                error=step.error,
            )
        )

    # Build summary
    action_count = sum(1 for s in trace.steps if s.step_type == "ActionStep")
    planning_count = sum(1 for s in trace.steps if s.step_type == "PlanningStep")
    status = "✓ Succeeded" if trace.success else "✗ Failed" if trace.success is False else "? Unknown"

    summary = (
        f"{trace.agent_name} executed {action_count} actions and {planning_count} planning phases. "
        f"Status: {status}."
    )
    if trace.error_message:
        summary += f" Error: {trace.error_message}"
    if trace.activated_basins:
        basin_names = [b.get("basin_name", b.get("basin_id", "?")) for b in trace.activated_basins]
        summary += f" Activated basins: {', '.join(basin_names[:3])}"
        if len(basin_names) > 3:
            summary += f" (+{len(basin_names) - 3} more)"

    return TraceReplayResponse(
        trace_id=trace.id,
        agent_name=trace.agent_name,
        started_at=trace.started_at,
        completed_at=trace.completed_at,
        success=trace.success,
        steps=replay_steps,
        activated_basins=[b.get("basin_id", "") for b in trace.activated_basins],
        summary=summary,
    )


@router.get("/token-usage", response_model=TokenUsageResponse)
async def get_token_usage():
    """
    Get token usage statistics across all agents.

    Returns memory pruning effectiveness metrics.
    """
    agents = get_all_token_summaries()
    aggregate = get_aggregate_token_stats()

    return TokenUsageResponse(agents=agents, aggregate=aggregate)


__all__ = ["router"]
