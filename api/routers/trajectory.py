"""
Trajectory Visualization REST API
Track: 062-document-ingestion-viz
Task: T062-021

Endpoints for viewing agent execution trajectories:
- GET /api/trajectory/{trace_id} - Get trace data
- GET /api/trajectory/{trace_id}/mermaid - Get Mermaid diagram
- GET /api/trajectory/{trace_id}/html - Get standalone HTML viewer
- GET /api/trajectory - List recent traces
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from api.services.trajectory_viz import (
    get_trajectory_viz_service,
    TrajectoryTrace,
)

logger = logging.getLogger("dionysus.routers.trajectory")

router = APIRouter(prefix="/api/trajectory", tags=["trajectory"])


class TraceResponse(BaseModel):
    """Response containing trace data."""
    trace_id: str
    session_id: str
    agent_name: str
    start_time: str
    end_time: Optional[str]
    ooda_cycles: int
    success: bool
    error_message: Optional[str]
    call_count: int
    basin_count: int


class TraceListResponse(BaseModel):
    """Response for trace list."""
    traces: list[TraceResponse]
    total: int


@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: str):
    """
    Get trajectory trace data.

    Returns metadata and statistics about the trace.
    """
    service = get_trajectory_viz_service()
    trace = await service.get_trace_from_execution(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return TraceResponse(
        trace_id=trace.trace_id,
        session_id=trace.session_id,
        agent_name=trace.agent_name,
        start_time=trace.start_time.isoformat(),
        end_time=trace.end_time.isoformat() if trace.end_time else None,
        ooda_cycles=trace.ooda_cycles,
        success=trace.success,
        error_message=trace.error_message,
        call_count=len(trace.calls),
        basin_count=len(trace.basin_transitions),
    )


@router.get("/{trace_id}/json")
async def get_trace_json(trace_id: str):
    """
    Get full trace data as JSON.

    Includes all calls and basin transitions.
    """
    service = get_trajectory_viz_service()
    trace = await service.get_trace_from_execution(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return service.generate_json(trace)


@router.get("/{trace_id}/mermaid", response_class=PlainTextResponse)
async def get_trace_mermaid(
    trace_id: str,
    diagram_type: str = Query("sequence", regex="^(sequence|ooda)$"),
):
    """
    Get Mermaid diagram for trace.

    Args:
        trace_id: The trace to visualize
        diagram_type: "sequence" for full sequence diagram, "ooda" for OODA loop

    Returns:
        Mermaid diagram source code
    """
    service = get_trajectory_viz_service()
    trace = await service.get_trace_from_execution(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    if diagram_type == "ooda":
        return service.generate_ooda_mermaid(trace)
    else:
        return service.generate_mermaid(trace)


@router.get("/{trace_id}/html", response_class=HTMLResponse)
async def get_trace_html(trace_id: str):
    """
    Get standalone HTML viewer for trace.

    Returns an HTML page with embedded Mermaid diagrams
    that can be viewed in any browser.
    """
    service = get_trajectory_viz_service()
    trace = await service.get_trace_from_execution(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return service.generate_html(trace)


@router.get("", response_model=TraceListResponse)
async def list_traces(
    limit: int = Query(20, ge=1, le=100),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
):
    """
    List recent execution traces.

    Args:
        limit: Maximum number of traces to return
        agent_name: Optional filter by agent name
    """
    try:
        from api.services.execution_trace_service import get_execution_trace_service

        service = get_execution_trace_service()
        traces = await service.list_traces(limit=limit, agent_name=agent_name)

        viz_service = get_trajectory_viz_service()
        results = []

        for t in traces:
            trace = await viz_service.get_trace_from_execution(t["trace_id"])
            if trace:
                results.append(TraceResponse(
                    trace_id=trace.trace_id,
                    session_id=trace.session_id,
                    agent_name=trace.agent_name,
                    start_time=trace.start_time.isoformat(),
                    end_time=trace.end_time.isoformat() if trace.end_time else None,
                    ooda_cycles=trace.ooda_cycles,
                    success=trace.success,
                    error_message=trace.error_message,
                    call_count=len(trace.calls),
                    basin_count=len(trace.basin_transitions),
                ))

        return TraceListResponse(traces=results, total=len(results))

    except Exception as e:
        logger.error(f"Failed to list traces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/sample", response_class=HTMLResponse)
async def get_demo_trace():
    """
    Get a demo trace visualization.

    Useful for testing the visualization without real trace data.
    """
    from datetime import datetime

    from api.services.trajectory_viz import (
        AgentCall,
        BasinTransition,
        OODAPhase,
        TrajectoryTrace,
    )

    # Create sample trace
    demo_trace = TrajectoryTrace(
        trace_id="demo-trace-001",
        session_id="demo-session",
        agent_name="heartbeat_agent",
        start_time=datetime.utcnow(),
        ooda_cycles=2,
        success=True,
    )

    # Add sample calls
    demo_trace.calls = [
        AgentCall("perception_agent", 1, "semantic_recall", {"query": "user context"}, "Found 3 memories", ooda_phase=OODAPhase.OBSERVE),
        AgentCall("reasoning_agent", 2, "analyze_context", {"depth": 2}, "Context analyzed", ooda_phase=OODAPhase.ORIENT),
        AgentCall("metacognition_agent", 3, "select_action", {"options": 3}, "Action selected", ooda_phase=OODAPhase.DECIDE),
        AgentCall("heartbeat_agent", 4, "execute_tool", {"tool": "respond"}, "Response generated", ooda_phase=OODAPhase.ACT),
        AgentCall("perception_agent", 5, "get_feedback", {}, "Positive feedback", ooda_phase=OODAPhase.OBSERVE),
        AgentCall("reasoning_agent", 6, "update_beliefs", {}, "Beliefs updated", ooda_phase=OODAPhase.ORIENT),
        AgentCall("metacognition_agent", 7, "plan_next", {}, "Next action planned", ooda_phase=OODAPhase.DECIDE),
        AgentCall("heartbeat_agent", 8, "complete", {}, "Task complete", ooda_phase=OODAPhase.ACT),
    ]

    # Add sample basin transitions
    demo_trace.basin_transitions = [
        BasinTransition(None, "conceptual-basin", "semantic_recall", 0.85, 1),
        BasinTransition("conceptual-basin", "procedural-basin", "action_selection", 0.72, 4),
    ]

    service = get_trajectory_viz_service()
    return service.generate_html(demo_trace)
