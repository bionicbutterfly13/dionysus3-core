"""
Maintenance and System Integrity REST API Router
Feature: 012-historical-reconstruction, 007-memory-consolidation

Endpoints for system cleanup, data migration, and memory consolidation.
"""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

class ReconstructionResponse(BaseModel):
    status: str
    fetched: int
    mirrored: int

class ConsolidationResponse(BaseModel):
    status: str
    processed: int
    consolidated: int

class HumanReviewItem(BaseModel):
    id: str
    reason: str
    payload: Any
    confidence: float
    created_at: str

@router.get("/review-queue", response_model=list[HumanReviewItem])
async def get_review_queue(limit: int = 20):
    """
    Fetch low-confidence items requiring human oversight.
    """
    from api.services.aspect_service import get_aspect_service
    service = get_aspect_service()
    
    items = await service.get_human_review_items(limit=limit)
    return [
        HumanReviewItem(
            id=str(i["id"]),
            reason=i["reason"],
            payload=json.loads(i["payload"]) if isinstance(i["payload"], str) else i["payload"],
            confidence=float(i.get("confidence", 0.0)),
            created_at=i["created_at"].isoformat()
        )
        for i in items
    ]

@router.post("/reconstruct-tasks", response_model=ReconstructionResponse)
async def reconstruct_tasks(limit: int = 1000):
    """
    Fetch all historical tasks from local Archon and mirror them in Neo4j.
    Use this to bring Dionysus 3.0 into integrity with Archon history.
    """
    from api.services.reconstruction_service import get_reconstruction_service
    service = get_reconstruction_service()
    
    result = await service.reconstruct_task_history(limit=limit)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return ReconstructionResponse(
        status=result["status"],
        fetched=result.get("fetched", 0),
        mirrored=result.get("mirrored", 0)
    )

@router.post("/consolidate-memory", response_model=ConsolidationResponse)
async def consolidate_memory(limit: int = 50):
    """
    Manually trigger episodic-to-semantic memory consolidation.
    Extracts knowledge graph facts from important transient memories.
    """
    from api.services.consolidation_service import get_consolidation_service
    service = get_consolidation_service()
    
    result = await service.consolidate_episodic_to_semantic(limit=limit)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return ConsolidationResponse(
        status=result["status"],
        processed=result.get("processed", 0),
        consolidated=result.get("consolidated", 0)
    )

@router.get("/integrity-check")
async def integrity_check():
    """
    Run a comprehensive integrity check on core services and Neo4j connectivity.
    """
    from api.services.remote_sync import RemoteSyncService
    from api.services.graphiti_service import get_graphiti_service
    from api.services.archon_integration import get_archon_service
    
    sync = RemoteSyncService()
    graphiti = await get_graphiti_service()
    archon = get_archon_service()
    
    results = {
        "n8n_neo4j_connectivity": await sync.check_health(),
        "graphiti_health": await graphiti.health_check(),
        "archon_connectivity": await archon.check_health(),
    }
    
    return results
