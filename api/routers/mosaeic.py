"""
MOSAEIC Protocol API Router
Feature: 024-mosaeic-protocol
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.models.mosaeic import MOSAEICCapture
from api.services.mosaeic_service import get_mosaeic_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mosaeic", tags=["mosaeic"])


class MosaeicCaptureRequest(BaseModel):
    text: str = Field(..., description="The narrative or experience text to analyze")
    source_id: str = Field(default="user_input", description="Identifier for the source")


@router.post("/capture", response_model=MOSAEICCapture)
async def capture_experience(request: MosaeicCaptureRequest):
    """
    Perform a five-window MOSAEIC capture from raw text.
    
    Extracts Senses, Actions, Emotions, Impulses, and Cognitions,
    persists them to Graphiti, and returns the structured capture.
    """
    service = get_mosaeic_service()
    try:
        # 1. Extract the structured capture
        capture = await service.extract_capture(request.text, request.source_id)
        
        # 2. Persist to Neo4j/Graphiti
        await service.persist_capture(capture)
        
        return capture
    except Exception as e:
        logger.error(f"mosaeic_capture_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def mosaeic_health():
    """Check MOSAEIC service health."""
    return {"status": "healthy", "service": "mosaeic_protocol"}
