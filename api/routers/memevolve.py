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
    MemoryRecallItem,
    IngestResponse,
    EvolutionResponse,
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


@router.get("/health", response_model=HealthCheckResponse)
async def health_check_get(
    adapter: MemEvolveAdapter = Depends(get_memevolve_adapter)
) -> HealthCheckResponse:
    """
    Health check endpoint (GET) for MemEvolve integration.

    Matches the EvolveLab client expectation.
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
    """
    result = await adapter.ingest_trajectory(request)
    return IngestResponse(
        ingest_id=result["ingest_id"],
        entities_extracted=result["entities_extracted"],
        memories_created=result["memories_created"],
    )


@router.post("/recall", response_model=MemoryRecallResponse)
async def recall_memories(
    request: MemoryRecallRequest,
    adapter: MemEvolveAdapter = Depends(get_memevolve_adapter)
) -> MemoryRecallResponse:
    """
    Recall memories for MemEvolve query.
    
    Performs semantic vector search via n8n webhook and returns
    relevant memories with similarity scores.
    
    Phase 2 implementation - fully functional.
    """
    result = await adapter.recall_memories(request)
    
    # Convert dict results to MemoryRecallItem models
    memory_items = [
        MemoryRecallItem(**mem) if isinstance(mem, dict) else mem
        for mem in result.get("memories", [])
    ]
    
    return MemoryRecallResponse(
        memories=memory_items,
        query=result["query"],
        result_count=result["result_count"],
        search_time_ms=result.get("search_time_ms")
    )


@router.post("/evolve", response_model=EvolutionResponse)
async def trigger_evolution(
    adapter: MemEvolveAdapter = Depends(get_memevolve_adapter)
) -> EvolutionResponse:
    """
    Trigger meta-evolution retrieval strategy optimization.
    
    Analyzes recent trajectory performance and generates a new
    optimized RetrievalStrategy node in Neo4j.
    """
    result = await adapter.trigger_evolution()
    
    if result.get("success", True):
        # n8n may return results in different formats
        records = result.get("records", [])
        new_strategy = records[0] if records else {}
        
        return EvolutionResponse(
            success=True,
            message="Meta-evolution cycle triggered successfully",
            optimization_basis=new_strategy.get("basis"),
            new_strategy_id=new_strategy.get("id")
        )
    else:
        return EvolutionResponse(
            success=False,
            message=f"Meta-evolution failed: {result.get('error', 'Unknown error')}"
        )
