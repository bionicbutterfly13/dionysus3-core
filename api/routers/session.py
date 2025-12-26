"""
Session Router
Feature: Session Continuity via Attractor-Based Memory Reconstruction

Provides endpoints for session context reconstruction at startup.
Any Claude Code user can call /api/session/reconstruct to get
coherent context for injection at session start.

Reference: 
- /Volumes/Asylum/repos/Context-Engineering/60_protocols/shells/memory.reconstruction.attractor.shell.md
- /Volumes/Asylum/skills-library/personal/memory-reconstruction/SKILL.md
"""

import os
import httpx
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from api.models.journey import SessionEvent
from api.services.reconstruction_service import (
    ReconstructionService,
    ReconstructionContext,
    get_reconstruction_service,
)


router = APIRouter(prefix="/api/session", tags=["session"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ReconstructRequest(BaseModel):
    """Request model for session reconstruction."""

    project_path: str = Field(
        ...,
        description="Absolute path to the project directory",
        example="/Volumes/Asylum/dev/dionysus3-core"
    )
    project_name: Optional[str] = Field(
        None,
        description="Project name (derived from path if not provided)",
        example="dionysus3-core"
    )
    device_id: Optional[str] = Field(
        None,
        description="Device identifier for journey tracking"
    )
    session_id: Optional[str] = Field(
        None,
        description="Current session identifier"
    )
    cues: list[str] = Field(
        default_factory=list,
        description="Explicit retrieval cues (keywords, topics)",
        example=["mental models", "heartbeat"]
    )
    prefetched_tasks: Optional[list[dict]] = Field(
        None,
        description="Pre-fetched tasks from Archon (bypasses VPS→Archon call)",
        example=[{"id": "abc", "title": "Task 1", "status": "todo"}]
    )


class ReconstructResponse(BaseModel):
    """Response model for session reconstruction."""

    success: bool = True
    project_summary: str
    recent_sessions: list[dict] = Field(default_factory=list)
    active_tasks: list[dict] = Field(default_factory=list)
    key_entities: list[dict] = Field(default_factory=list)
    recent_decisions: list[dict] = Field(default_factory=list)
    episodic_memories: list[dict] = Field(
        default_factory=list,
        description="Episodic memories from Neo4j retrieved by attractor resonance"
    )
    
    coherence_score: float = Field(
        ...,
        description="Overall coherence of reconstructed context (0-1)"
    )
    fragment_count: int = Field(
        ...,
        description="Number of memory fragments processed"
    )
    reconstruction_time_ms: float = Field(
        ...,
        description="Time taken to reconstruct in milliseconds"
    )
    
    gap_fills: list[dict] = Field(
        default_factory=list,
        description="Gaps that were filled by reasoning"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings during reconstruction"
    )
    
    compact_context: str = Field(
        ...,
        description="Compact markdown context for injection"
    )


class QuickContextResponse(BaseModel):
    """Lightweight response for quick context fetch."""
    
    success: bool = True
    project_name: str
    active_task_count: int
    recent_session_count: int
    compact_context: str
    reconstruction_time_ms: float


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/reconstruct",
    response_model=ReconstructResponse,
    summary="Reconstruct session context",
    description="""
    Reconstruct coherent session context using attractor-based memory dynamics.
    
    This endpoint implements the 10-step memory reconstruction protocol:
    1. SCAN - Gather fragments from sessions, tasks, entities
    2. ACTIVATE - Calculate resonance with current context
    3. EXCITE - Amplify high-resonance fragments
    4. EVOLVE - Field dynamics to surface top patterns
    5. EXTRACT - Pull coherent patterns by type
    6. IDENTIFY_GAPS - Find missing pieces
    7. FILL_GAPS - Use reasoning to fill
    8. VALIDATE - Check coherence
    9. ADAPT - Update fragment strengths
    10. CONSOLIDATE - Return compact context
    
    The response includes a `compact_context` field containing markdown
    suitable for injection into a Claude session via hooks.
    
    **Usage with Claude Code Hooks:**
    
    Add to `~/.claude/hooks.json`:
    ```json
    {
      "PreToolUse": [{
        "matcher": "Task",
        "hooks": [{
          "type": "command", 
          "command": "curl -s -X POST http://localhost:8000/api/session/reconstruct -H 'Content-Type: application/json' -d '{\"project_path\": \"$PWD\"}'"
        }]
      }]
    }
    ```
    """,
)
async def reconstruct_session(request: ReconstructRequest) -> ReconstructResponse:
    """
    Reconstruct session context for a project.
    
    Uses attractor-based resonance to surface relevant:
    - Recent session summaries
    - Active tasks from Archon
    - Key entities from Graphiti
    - Recent decisions and commitments
    """
    # Derive project name if not provided
    project_name = request.project_name
    if not project_name:
        project_name = os.path.basename(request.project_path.rstrip("/"))
    
    # Build reconstruction context
    context = ReconstructionContext(
        project_path=request.project_path,
        project_name=project_name,
        device_id=request.device_id,
        session_id=request.session_id,
        cues=request.cues,
    )
    
    # Get reconstruction service
    service = get_reconstruction_service()

    try:
        # Run reconstruction pipeline
        result = await service.reconstruct(
            context,
            prefetched_tasks=request.prefetched_tasks,
        )
        
        return ReconstructResponse(
            success=True,
            project_summary=result.project_summary,
            recent_sessions=result.recent_sessions,
            active_tasks=result.active_tasks,
            key_entities=result.key_entities,
            recent_decisions=result.recent_decisions,
            episodic_memories=result.episodic_memories,
            coherence_score=result.coherence_score,
            fragment_count=result.fragment_count,
            reconstruction_time_ms=result.reconstruction_time_ms,
            gap_fills=result.gap_fills,
            warnings=result.warnings,
            compact_context=result.to_compact_context(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reconstruction failed: {str(e)}"
        )


@router.get(
    "/context",
    response_model=QuickContextResponse,
    summary="Quick context fetch",
    description="""
    Lightweight endpoint for quick context retrieval.
    
    Uses query parameters instead of POST body for easier
    integration with simple curl commands or hooks.
    """,
)
async def get_quick_context(
    project_path: str = Query(
        ...,
        description="Absolute path to project directory"
    ),
    project_name: Optional[str] = Query(
        None,
        description="Project name (derived from path if not provided)"
    ),
    cues: Optional[str] = Query(
        None,
        description="Comma-separated retrieval cues"
    ),
) -> QuickContextResponse:
    """
    Quick context fetch for lightweight integration.
    """
    # Derive project name if not provided
    if not project_name:
        project_name = os.path.basename(project_path.rstrip("/"))
    
    # Parse cues
    cue_list = []
    if cues:
        cue_list = [c.strip() for c in cues.split(",") if c.strip()]
    
    # Build context
    context = ReconstructionContext(
        project_path=project_path,
        project_name=project_name,
        cues=cue_list,
    )
    
    # Get service and reconstruct
    service = get_reconstruction_service()
    
    try:
        result = await service.reconstruct(context)
        
        return QuickContextResponse(
            success=True,
            project_name=project_name,
            active_task_count=len(result.active_tasks),
            recent_session_count=len(result.recent_sessions),
            compact_context=result.to_compact_context(),
            reconstruction_time_ms=result.reconstruction_time_ms,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Context fetch failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Session service health check",
    description="Check health of session reconstruction dependencies.",
)
async def session_health() -> dict:
    """
    Health check for session reconstruction service.
    
    Checks:
    - Archon connectivity
    - n8n webhook connectivity
    - Graphiti (if enabled)
    """
    import httpx
    
    health = {
        "healthy": True,
        "archon": {"status": "unknown"},
        "n8n": {"status": "unknown"},
        "graphiti": {"status": "disabled"},
    }
    
    service = get_reconstruction_service()
    
    # Check Archon
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service.archon_url}/health")
            if response.status_code == 200:
                health["archon"] = {"status": "healthy"}
            else:
                health["archon"] = {"status": "unhealthy", "code": response.status_code}
                health["healthy"] = False
    except Exception as e:
        health["archon"] = {"status": "unreachable", "error": str(e)}
        health["healthy"] = False
    
    # Check n8n
    try:
        # Just check if the base n8n is reachable
        base_url = service.n8n_recall_url.rsplit("/webhook", 1)[0]
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/healthz")
            if response.status_code == 200:
                health["n8n"] = {"status": "healthy"}
            else:
                health["n8n"] = {"status": "unhealthy", "code": response.status_code}
    except Exception as e:
        health["n8n"] = {"status": "unreachable", "error": str(e)}
    
    # Check Graphiti if enabled
    if service.graphiti_enabled:
        try:
            from api.services.graphiti_service import get_graphiti_service
            graphiti = await get_graphiti_service()
            graphiti_health = await graphiti.health_check()
            health["graphiti"] = graphiti_health
            if not graphiti_health.get("healthy"):
                health["healthy"] = False
        except Exception as e:
            health["graphiti"] = {"status": "error", "error": str(e)}
    
    return health


@router.post(
    "/event",
    summary="Log a session event",
    description="""
    Log a granular session event (e.g., decision, commitment, task completion).
    Forwards the event to the n8n ingestion webhook for processing and storage.
    """,
    status_code=202,
)
async def log_session_event(
    event: SessionEvent,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Log a session event to n8n.
    """
    # Get service to access config URLs
    service = get_reconstruction_service()
    
    # Construct n8n webhook URL
    # Assuming standard n8n pattern: base_url + /webhook/session-event
    # We'll use the recall URL to derive the base if needed, or a configured env var
    n8n_base = service.n8n_recall_url.rsplit("/webhook", 1)[0]
    webhook_url = os.getenv("N8N_EVENT_URL", f"{n8n_base}/webhook/session-event")

    async def forward_event(payload: dict, url: str):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            # We log error but don't crash since this is background
            print(f"Failed to forward session event to n8n: {e}")

    # Forward in background to avoid blocking
    background_tasks.add_task(forward_event, event.dict(), webhook_url)

    return {"status": "accepted", "event_id": str(event.id)}
