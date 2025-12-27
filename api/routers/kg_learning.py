"""
Agentic Knowledge Graph Learning Loop Router
Feature: 022-agentic-kg-learning
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.models.kg_learning import ExtractionResult
from api.services.kg_learning_service import get_kg_learning_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kg-learning", tags=["kg_learning"])


class LearningExtractionRequest(BaseModel):
    content: str = Field(..., description="Raw text to extract knowledge from")
    source_id: str = Field(..., description="Source identifier")


@router.post("/extract", response_model=ExtractionResult)
async def extract_and_learn(request: LearningExtractionRequest):
    """
    Perform agentic knowledge extraction with learning loop.
    
    Uses basins and cognition strategies to guide extraction, 
    persists results to Graphiti, and updates basins/strategies.
    """
    service = get_kg_learning_service()
    try:
        result = await service.extract_and_learn(request.content, request.source_id)
        return result
    except Exception as e:
        logger.error(f"kg_learning_extraction_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/basins", response_model=List[Dict[str, Any]])
async def list_basins():
    """List active attractor basins."""
    from api.services.webhook_neo4j_driver import get_neo4j_driver
    driver = get_neo4j_driver()
    cypher = "MATCH (b:AttractorBasin) RETURN b ORDER BY b.strength DESC"
    rows = await driver.execute_query(cypher)
    return [r["b"] for r in rows]


@router.get("/strategies", response_model=List[Dict[str, Any]])
async def list_strategies():
    """List cognition strategies and priority boosts."""
    from api.services.webhook_neo4j_driver import get_neo4j_driver
    driver = get_neo4j_driver()
    cypher = "MATCH (s:CognitionStrategy) RETURN s ORDER BY s.priority_boost DESC"
    rows = await driver.execute_query(cypher)
    return [r["s"] for r in rows]
