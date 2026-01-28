"""
Subconscious API – session-start, sync, ingest, run-decider (Hexis + Letta-style).

Feature: 102-subconscious-integration
Inlets: POST/GET from clients (Cursor/Claude plugin, maintenance job).
Outlets: SubconsciousService -> MemoryBasinRouter, GraphitiService, MemEvolveAdapter.
"""

from fastapi import APIRouter, Depends

from api.models.subconscious import IngestRequest, SessionStartRequest, SyncResponse
from api.services.subconscious_service import get_subconscious_service, SubconsciousService

router = APIRouter(prefix="/subconscious", tags=["subconscious"])


def _service() -> SubconsciousService:
    return get_subconscious_service()


@router.post("/session-start")
async def session_start(
    body: SessionStartRequest,
    service: SubconsciousService = Depends(_service),
):
    """Register a session for sync/ingest (Letta-style)."""
    service.session_start(
        session_id=body.session_id,
        project_id=body.project_id,
        cwd=body.cwd,
    )
    return {"status": "ok", "session_id": body.session_id}


@router.get("/sync", response_model=SyncResponse)
@router.post("/sync", response_model=SyncResponse)
async def sync(
    session_id: str,
    service: SubconsciousService = Depends(_service),
):
    """Return guidance and memory_blocks for session (before-prompt sync)."""
    return await service.sync(session_id=session_id)


@router.post("/ingest")
async def ingest(
    body: IngestRequest,
    service: SubconsciousService = Depends(_service),
):
    """Ingest transcript or summary for session (after-response)."""
    result = await service.ingest(body)
    return result


@router.post("/run-decider")
async def run_decider(
    agent_id: str | None = None,
    service: SubconsciousService = Depends(_service),
):
    """Run subconscious decider (maintenance tick): context -> LLM -> apply observations."""
    result = await service.run_subconscious_decider(agent_id=agent_id)
    return result
