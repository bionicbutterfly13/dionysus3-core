"""
Graphiti Router - REST API for knowledge graph operations.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from api.services.graphiti_service import get_graphiti_dependency, GraphitiService

router = APIRouter(prefix="/api/graphiti", tags=["graphiti"])


class IngestRequest(BaseModel):
    content: str = Field(..., description="Message content to ingest")
    source_description: str = Field(default="conversation", description="Source description")
    group_id: Optional[str] = Field(default=None, description="Group ID for partitioning")
    valid_at: Optional[datetime] = Field(default=None, description="When event occurred")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    group_ids: Optional[list[str]] = Field(default=None, description="Filter by groups")
    limit: int = Field(default=10, ge=1, le=100)
    use_cross_encoder: bool = Field(default=False, description="Use LLM reranking")


@router.post("/ingest")
async def ingest_message(
    request: IngestRequest,
    service: GraphitiService = Depends(get_graphiti_dependency)
):
    """Ingest a message and extract entities/relationships."""
    try:
        result = await service.ingest_message(
            content=request.content,
            source_description=request.source_description,
            group_id=request.group_id,
            valid_at=request.valid_at,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(
    request: SearchRequest,
    service: GraphitiService = Depends(get_graphiti_dependency)
):
    """Hybrid search across entities and relationships."""
    try:
        result = await service.search(
            query=request.query,
            group_ids=request.group_ids,
            limit=request.limit,
            use_cross_encoder=request.use_cross_encoder,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    service: GraphitiService = Depends(get_graphiti_dependency)
):
    """Check Graphiti and Neo4j connectivity."""
    try:
        return await service.health_check()
    except Exception as e:
        return {"healthy": False, "error": str(e)}


@router.get("/entity/{name}")
async def get_entity(
    name: str, 
    group_id: Optional[str] = None,
    service: GraphitiService = Depends(get_graphiti_dependency)
):
    """Get entity by name."""
    try:
        result = await service.get_entity(name, group_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Entity '{name}' not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
