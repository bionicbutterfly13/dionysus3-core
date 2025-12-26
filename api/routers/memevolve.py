"""
MemEvolve Integration Router

API endpoints for MemEvolve-Dionysus integration.
Feature: 009-memevolve-integration
Phase: 1 - Foundation
"""

from fastapi import APIRouter, Depends

from api.models.memevolve import (
    HealthCheckResponse,
    MemoryIngestRequest,
    MemoryRecallRequest,
    MemoryRecallResponse,
    IngestResponse,
)
from api.services.hmac_utils import verify_memevolve_signature
from api.services.memevolve_adapter import get_memevolve_adapter, MemEvolveAdapter


router = APIRouter(
    prefix="/webhook/memevolve/v1",
    tags=["memevolve"],
    dependencies=[Depends(verify_memevolve_signature)]
)


@router.post("/health", response_model=HealthCheckResponse)
async def health_check(
    adapter: MemEvolveAdapter = Depends(get_memevolve_adapter)
) -> HealthCheckResponse:
    """
    Health check endpoint for MemEvolve integration.
    
    Verifies HMAC signature and returns service status.
    """
    result = await adapter.health_check()
    return HealthCheckResponse(
        status=result["status"],
        service=result["service"]
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_trajectory(
    request: MemoryIngestRequest,
    adapter: MemEvolveAdapter = Depends(get_memevolve_adapter)
) -> IngestResponse:
    """
    Ingest memory trajectory from MemEvolve.
    
    Receives trajectory data and processes it for storage.
    Note: Full implementation in Phase 2.
    """
    result = await adapter.ingest_trajectory(request.trajectory_data)
    return IngestResponse(
        success=result["success"],
        ingested_count=result["ingested_count"],
        message=result["message"]
    )


@router.post("/recall", response_model=MemoryRecallResponse)
async def recall_memories(
    request: MemoryRecallRequest,
    adapter: MemEvolveAdapter = Depends(get_memevolve_adapter)
) -> MemoryRecallResponse:
    """
    Recall memories for MemEvolve query.
    
    Performs semantic search and returns relevant memories.
    Note: Full implementation in Phase 2.
    """
    result = await adapter.recall_memories(
        query=request.query,
        context=request.context,
        max_results=request.max_results
    )
    return MemoryRecallResponse(
        memories=result["memories"],
        query=result["query"],
        result_count=result["result_count"]
    )
