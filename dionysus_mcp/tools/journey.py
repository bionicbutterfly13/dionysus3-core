"""
Journey MCP Tools
Feature: 001-session-continuity
Tasks: T018, T029, T038

MCP tools for journey management exposed to AGI for self-reference.
"""

import logging
from typing import Any, Optional
from uuid import UUID

from api.models.journey import (
    JourneyHistoryQuery,
    JourneyDocumentCreate,
)
from api.services.session_manager import SessionManager, get_session_manager

logger = logging.getLogger(__name__)


# =============================================================================
# Tool: get_or_create_journey (T018)
# =============================================================================

async def get_or_create_journey_tool(device_id: str) -> dict[str, Any]:
    """
    Get existing journey for device or create new one.
    
    Args:
        device_id: Device identifier (UUID) from ~/.dionysus/device_id
        
    Returns:
        Journey with is_new flag indicating if just created
    """
    manager = get_session_manager()
    
    try:
        device_uuid = UUID(device_id)
    except ValueError:
        return {"error": f"Invalid device_id format: {device_id}"}
    
    journey = await manager.get_or_create_journey(device_uuid)
    
    return {
        "journey_id": str(journey.id),
        "device_id": str(journey.device_id),
        "created_at": journey.created_at.isoformat(),
        "session_count": journey.session_count,
        "is_new": journey.is_new
    }


# =============================================================================
# Tool: query_journey_history (T029)
# =============================================================================

async def query_journey_history_tool(
    journey_id: str,
    query: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
    include_documents: bool = False
) -> dict[str, Any]:
    """
    Search journey sessions by keyword, time range, or metadata.
    
    Args:
        journey_id: Journey to search within
        query: Optional keyword search on session summaries
        from_date: Optional start of time range (ISO format)
        to_date: Optional end of time range (ISO format)
        limit: Maximum results (1-100)
        include_documents: Whether to include linked documents
        
    Returns:
        Matching sessions and optionally documents
    """
    from datetime import datetime
    
    manager = get_session_manager()
    
    try:
        journey_uuid = UUID(journey_id)
    except ValueError:
        return {"error": f"Invalid journey_id format: {journey_id}"}
    
    # Parse dates if provided
    parsed_from = None
    parsed_to = None
    
    if from_date:
        try:
            parsed_from = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            return {"error": f"Invalid from_date format: {from_date}"}
    
    if to_date:
        try:
            parsed_to = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            return {"error": f"Invalid to_date format: {to_date}"}
    
    history_query = JourneyHistoryQuery(
        journey_id=journey_uuid,
        query=query,
        from_date=parsed_from,
        to_date=parsed_to,
        limit=min(max(1, limit), 100),
        include_documents=include_documents
    )
    
    result = await manager.query_journey_history(history_query)
    
    return {
        "journey_id": str(result.journey_id),
        "sessions": [
            {
                "session_id": str(s.session_id),
                "created_at": s.created_at.isoformat(),
                "summary": s.summary,
                "has_diagnosis": s.has_diagnosis,
                "relevance_score": s.relevance_score
            }
            for s in result.sessions
        ],
        "documents": [
            {
                "document_id": str(d.document_id),
                "document_type": d.document_type,
                "title": d.title,
                "created_at": d.created_at.isoformat()
            }
            for d in result.documents
        ],
        "total_results": result.total_results
    }


# =============================================================================
# Tool: add_document_to_journey (T038)
# =============================================================================

async def add_document_to_journey_tool(
    journey_id: str,
    document_type: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Link a document or artifact to a journey.
    
    Args:
        journey_id: Journey to link document to
        document_type: Type of document (woop_plan, file_upload, artifact, note)
        title: Optional document title
        content: Optional document content or file path
        metadata: Optional additional metadata
        
    Returns:
        Created document record
    """
    manager = get_session_manager()
    
    try:
        journey_uuid = UUID(journey_id)
    except ValueError:
        return {"error": f"Invalid journey_id format: {journey_id}"}
    
    valid_types = {"woop_plan", "file_upload", "artifact", "note"}
    if document_type not in valid_types:
        return {"error": f"Invalid document_type: {document_type}. Must be one of: {valid_types}"}
    
    try:
        document = await manager.add_document_to_journey(
            JourneyDocumentCreate(
                journey_id=journey_uuid,
                document_type=document_type,
                title=title,
                content=content,
                metadata=metadata or {}
            )
        )
    except ValueError as e:
        return {"error": str(e)}
    
    return {
        "document_id": str(document.id),
        "journey_id": str(document.journey_id),
        "document_type": document.document_type,
        "created_at": document.created_at.isoformat()
    }


# =============================================================================
# Tool Registration Helper
# =============================================================================

def get_journey_tools() -> list[dict]:
    """
    Get tool definitions for MCP server registration.
    
    Returns:
        List of tool definitions with name, description, and function
    """
    return [
        {
            "name": "get_or_create_journey",
            "description": "Get existing journey for device or create new one. A journey tracks all conversations for a device across sessions.",
            "function": get_or_create_journey_tool,
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {
                        "type": "string",
                        "description": "Device identifier (UUID) from ~/.dionysus/device_id"
                    }
                },
                "required": ["device_id"]
            }
        },
        {
            "name": "query_journey_history",
            "description": "Search journey sessions by keyword, time range, or metadata. Use to answer questions like 'What did we discuss?' or 'Remember when we talked about X?'",
            "function": query_journey_history_tool,
            "parameters": {
                "type": "object",
                "properties": {
                    "journey_id": {
                        "type": "string",
                        "description": "Journey to search within"
                    },
                    "query": {
                        "type": "string",
                        "description": "Keyword search on session summaries"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start of time range filter (ISO format)"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End of time range filter (ISO format)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (1-100)",
                        "default": 10
                    },
                    "include_documents": {
                        "type": "boolean",
                        "description": "Include linked documents in results",
                        "default": False
                    }
                },
                "required": ["journey_id"]
            }
        },
        {
            "name": "add_document_to_journey",
            "description": "Link a document or artifact to a journey. Use for WOOP plans, file uploads, generated artifacts, notes.",
            "function": add_document_to_journey_tool,
            "parameters": {
                "type": "object",
                "properties": {
                    "journey_id": {
                        "type": "string",
                        "description": "Journey to link document to"
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["woop_plan", "file_upload", "artifact", "note"],
                        "description": "Type of document"
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Document content or file path"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata"
                    }
                },
                "required": ["journey_id", "document_type"]
            }
        }
    ]
