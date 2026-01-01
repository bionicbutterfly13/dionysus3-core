"""
Maintenance and System Integrity REST API Router
Feature: 012-historical-reconstruction, 007-memory-consolidation

Endpoints for system cleanup, data migration, and memory consolidation.
"""

import json
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

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
    from api.services.maintenance_service import get_maintenance_service
    service = get_maintenance_service()
    
    items = await service.get_human_review_queue(limit=limit)
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

@router.delete("/review-queue/{item_id}")
async def resolve_review_item(item_id: str):
    """
    Mark a low-confidence item as resolved/reviewed.
    """
    from api.services.maintenance_service import get_maintenance_service
    service = get_maintenance_service()
    
    success = await service.resolve_review_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"success": True, "message": f"Item {item_id} resolved"}

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
    from api.services.meta_tot_decision import get_meta_tot_decision_service
    
    sync = RemoteSyncService()
    graphiti = await get_graphiti_service()
    
    results = {
        "n8n_neo4j_connectivity": await sync.check_health(),
        "graphiti_health": await graphiti.health_check(),
    }
    try:
        results["meta_tot_thresholds"] = await get_meta_tot_decision_service().get_thresholds_snapshot()
    except Exception as exc:
        results["meta_tot_thresholds"] = {"error": str(exc)}
    
    return results
