"""
Agentic KG Learning Router
Feature: 022-agentic-kg-learning
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.models.kg_learning import ExtractionResult, RelationshipProposal
from api.services.kg_learning_service import get_kg_learning_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kg", tags=["kg_learning"])


class LearnRequest(BaseModel):
    content: str = Field(..., description="Raw text content to learn from")
    source_id: str = Field(..., description="Identifier for the content source")


@router.post("/learn", response_model=ExtractionResult)
async def learn_from_content(request: LearnRequest):
    """
    Perform agentic extraction and learning from raw content.
    Uses attractor basins and cognition strategies to guide extraction.
    """
    service = get_kg_learning_service()
    try:
        result = await service.extract_and_learn(request.content, request.source_id)
        return result
    except Exception as e:
        logger.error(f"kg_learning_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-queue", response_model=List[RelationshipProposal])


async def get_review_queue():


    """


    Retrieve relationships flagged for human review (low confidence).


    Queries Neo4j for 'pending_review' status.


    """


    service = get_kg_learning_service()


    cypher = "MATCH (r:RelationshipProposal {status: 'pending_review'}) RETURN r LIMIT 100"


    


    try:


        rows = await service._driver.execute_query(cypher)


        return [RelationshipProposal.model_validate(r["r"]) for r in rows]


    except Exception as e:


        logger.error(f"failed_to_fetch_review_queue: {e}")


        return []

