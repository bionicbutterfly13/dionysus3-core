"""
Avatar Research API Router

Endpoints for avatar knowledge graph research and analysis.
Feature: 019-avatar-knowledge-graph
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from api.agents.knowledge import AvatarResearcher, create_avatar_researcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/avatar", tags=["avatar"])


class AnalyzeContentRequest(BaseModel):
    """Request to analyze raw content for avatar insights."""
    content: str = Field(..., description="Raw text content to analyze")
    source: str = Field(default="api_input", description="Source identifier")


class AnalyzeDocumentRequest(BaseModel):
    """Request to analyze a document file."""
    file_path: str = Field(..., description="Path to document file")
    document_type: str = Field(default="copy_brief", description="Type: copy_brief, email, interview, review")


class ResearchQuestionRequest(BaseModel):
    """Request to answer a research question about the avatar."""
    question: str = Field(..., description="Natural language research question")


class ProfileRequest(BaseModel):
    """Request to generate avatar profile."""
    dimensions: str = Field(default="all", description="Dimensions to include (comma-separated or 'all')")


class QueryRequest(BaseModel):
    """Request to query the avatar knowledge graph."""
    query: str = Field(..., description="Natural language query")
    insight_types: Optional[str] = Field(None, description="Filter by insight types (comma-separated)")
    limit: int = Field(default=10, description="Maximum results")


@router.post("/analyze/content")
async def analyze_content(request: AnalyzeContentRequest):
    """
    Analyze raw content for avatar insights.

    Runs all sub-agents (PainAnalyst, ObjectionHandler, VoiceExtractor)
    in parallel to extract comprehensive insights.
    """
    try:
        researcher = await create_avatar_researcher()
        result = await researcher.analyze_content(request.content, request.source)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/document")
async def analyze_document(request: AnalyzeDocumentRequest):
    """
    Analyze a document file comprehensively.

    Uses bulk ingestion followed by specialized agent analysis.
    """
    try:
        researcher = await create_avatar_researcher()
        result = await researcher.analyze_document(request.file_path, request.document_type)
        return {"success": True, "data": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/ground-truth")
async def ingest_ground_truth(request: AnalyzeDocumentRequest):
    """
    Ingest a "Ground Truth" avatar document.

    This is a comprehensive ingestion that extracts all insights
    and builds the foundational avatar profile.
    """
    try:
        researcher = await create_avatar_researcher()
        result = await researcher.ingest_ground_truth(request.file_path)
        return {"success": True, "data": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    except Exception as e:
        logger.error(f"Ground truth ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research")
async def research_question(request: ResearchQuestionRequest):
    """
    Answer a research question about the avatar.

    Queries the knowledge graph and synthesizes findings.
    """
    try:
        researcher = await create_avatar_researcher()
        result = await researcher.research_question(request.question)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Research query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile")
async def generate_profile(request: ProfileRequest):
    """
    Generate a comprehensive avatar profile.

    Synthesizes all knowledge graph data into an actionable profile.
    """
    try:
        researcher = await create_avatar_researcher()
        result = await researcher.generate_avatar_profile(request.dimensions)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Profile generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_graph(request: QueryRequest):
    """
    Query the avatar knowledge graph directly.

    Semantic search with optional filtering by insight type.
    """
    from api.agents.knowledge.tools import async_query_avatar_graph

    try:
        result = await async_query_avatar_graph(
            query=request.query,
            insight_types=request.insight_types,
            limit=request.limit,
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def avatar_health():
    """Check avatar research system health."""
    return {
        "status": "healthy",
        "service": "avatar_research",
        "agents": ["pain_analyst", "objection_handler", "voice_extractor", "avatar_researcher"],
    }
