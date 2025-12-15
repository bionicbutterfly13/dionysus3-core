"""
Sync Router - Memory Synchronization API
Feature: 002-remote-persistence-safety
Tasks: T022, T023, T024, T026

REST API endpoints for memory synchronization with remote Neo4j.
Implements contracts/webhook-sync.yaml specification.
"""

import os
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from api.models.sync import MemoryType
from api.services.hmac_utils import validate_signature
from api.services.neo4j_client import Neo4jClient, Neo4jConnectionError
from api.services.remote_sync import RemoteSyncService, SyncConfig

router = APIRouter(tags=["sync"])

# =========================================================================
# Configuration
# =========================================================================

_webhook_token: Optional[str] = None
_sync_service: Optional[RemoteSyncService] = None


def set_webhook_token(token: str) -> None:
    """Set webhook token (for testing)."""
    global _webhook_token
    _webhook_token = token


def get_webhook_token() -> str:
    """Get webhook token from env or override."""
    return _webhook_token or os.getenv("MEMORY_WEBHOOK_TOKEN", "")


async def get_sync_service() -> RemoteSyncService:
    """Get or create sync service singleton."""
    global _sync_service
    if _sync_service is None:
        config = SyncConfig(
            webhook_url=os.getenv(
                "N8N_WEBHOOK_URL", "http://localhost:5678/webhook/memory/v1/ingest/message"
            ),
            webhook_token=get_webhook_token(),
        )
        # Neo4j is only accessible through n8n - no direct connection needed for sync
        # Neo4j client is optional, only used for recovery operations
        _sync_service = RemoteSyncService(neo4j_client=None, config=config)
    return _sync_service


# =========================================================================
# Request/Response Models
# =========================================================================


class MemorySyncPayload(BaseModel):
    """Payload for memory sync webhook."""

    memory_id: str
    content: str = Field(min_length=1, max_length=50000)
    memory_type: MemoryType
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    embedding: Optional[list[float]] = Field(
        default=None, min_length=768, max_length=768
    )
    session_id: str
    project_id: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    sync_version: int = Field(ge=1)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("memory_id", "session_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate UUID format."""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid UUID format")


class SyncResponse(BaseModel):
    """Response for successful sync."""

    success: bool
    memory_id: str
    remote_id: Optional[str] = None
    synced_at: str
    embedding_generated: bool = False


class SyncTriggerRequest(BaseModel):
    """Request to trigger sync."""

    memory_ids: Optional[list[str]] = None


class SyncTriggerResponse(BaseModel):
    """Response from sync trigger."""

    triggered: bool
    queue_size: int
    estimated_duration_seconds: int = 0


class SyncStatusResponse(BaseModel):
    """Response for sync status."""

    healthy: bool
    neo4j_connected: bool
    n8n_connected: bool = False
    ollama_connected: bool = False
    queue_size: int
    pending_count: int
    failed_count: int
    last_sync: Optional[str] = None
    last_error: Optional[str] = None


class RecoveryRequest(BaseModel):
    """Request for bootstrap recovery."""

    project_id: Optional[str] = None
    since: Optional[str] = None
    dry_run: bool = False


class RecoveryResponse(BaseModel):
    """Response from recovery."""

    success: bool
    recovered_count: int
    skipped_count: int = 0
    conflict_count: int = 0
    duration_ms: int
    dry_run: bool


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    message: Optional[str] = None
    details: Optional[dict[str, Any]] = None


# =========================================================================
# POST /sync/memory - Webhook endpoint (T022)
# =========================================================================


@router.post(
    "/sync/memory",
    response_model=SyncResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid payload"},
        401: {"model": ErrorResponse, "description": "Invalid signature"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def sync_memory(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
) -> SyncResponse:
    """
    Sync a memory to remote Neo4j.

    Requires HMAC-SHA256 signature for authentication.
    """
    # Get raw body for signature validation
    body = await request.body()

    # Validate HMAC signature
    token = get_webhook_token()
    if not x_webhook_signature:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Missing signature header. X-Webhook-Signature required."},
        )

    if not validate_signature(body, x_webhook_signature, token):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid signature"},
        )

    # Parse and validate payload
    try:
        import json

        payload_dict = json.loads(body)
        payload = MemorySyncPayload(**payload_dict)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid payload", "message": str(e)},
        )

    # Forward to n8n webhook for processing
    # This endpoint receives validated payloads and forwards to n8n
    # n8n handles all Neo4j operations - no direct Neo4j access from here
    try:
        sync_service = await get_sync_service()

        # Build memory data for sync
        memory_data = {
            "id": payload.memory_id,
            "content": payload.content,
            "memory_type": payload.memory_type.value,
            "importance": payload.importance,
            "source_project": payload.project_id,
            "session_id": payload.session_id,
            "tags": payload.tags,
            "sync_version": payload.sync_version,
            "created_at": payload.created_at or datetime.utcnow().isoformat(),
            "updated_at": payload.updated_at,
        }

        # Sync via n8n webhook (not direct Neo4j)
        result = await sync_service.sync_memory_on_create(memory_data)

        if result.get("synced"):
            return SyncResponse(
                success=True,
                memory_id=payload.memory_id,
                synced_at=datetime.utcnow().isoformat(),
                embedding_generated=payload.embedding is None,
            )
        elif result.get("queued"):
            return SyncResponse(
                success=True,
                memory_id=payload.memory_id,
                synced_at=datetime.utcnow().isoformat(),
                embedding_generated=False,
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "Sync failed", "message": result.get("error")},
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Sync service unavailable", "message": str(e)},
        )


# =========================================================================
# POST /sync/trigger - Manual sync trigger (T023)
# =========================================================================


@router.post(
    "/sync/trigger",
    response_model=SyncTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def trigger_sync(
    request: SyncTriggerRequest = None,
    authorization: Optional[str] = Header(None),
) -> SyncTriggerResponse:
    """
    Manually trigger sync of pending memories.

    Forces immediate sync of all pending memories in the queue.
    """
    try:
        sync_service = await get_sync_service()

        # Process the queue
        results = await sync_service.process_queue()

        return SyncTriggerResponse(
            triggered=True,
            queue_size=sync_service.get_queue_size(),
            estimated_duration_seconds=sync_service.get_queue_size() * 2,  # ~2s per item
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Sync trigger failed", "message": str(e)},
        )


# =========================================================================
# GET /sync/status - Health status (T024)
# =========================================================================


@router.get(
    "/sync/status",
    response_model=SyncStatusResponse,
)
async def get_sync_status() -> SyncStatusResponse:
    """
    Get sync health status.

    Returns current sync state, queue size, and service health.
    """
    try:
        sync_service = await get_sync_service()
        status_info = sync_service.get_sync_status()
        health = await sync_service.check_health()

        return SyncStatusResponse(
            healthy=health.get("healthy", False),
            neo4j_connected=health.get("neo4j_connected", False),
            n8n_connected=health.get("n8n_reachable", False),
            ollama_connected=health.get("ollama_reachable", False),
            queue_size=status_info.get("queue_size", 0),
            pending_count=status_info.get("pending_count", 0),
            failed_count=status_info.get("failed_count", 0),
            last_sync=status_info.get("last_sync"),
            last_error=status_info.get("last_error"),
        )

    except Exception as e:
        # Return unhealthy status on error
        return SyncStatusResponse(
            healthy=False,
            neo4j_connected=False,
            queue_size=0,
            pending_count=0,
            failed_count=0,
            last_error=str(e),
        )


# =========================================================================
# POST /recovery/bootstrap - Bootstrap recovery (T026)
# =========================================================================


@router.post(
    "/recovery/bootstrap",
    response_model=RecoveryResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Neo4j unavailable"},
    },
)
async def bootstrap_recovery(
    request: RecoveryRequest = RecoveryRequest(),
    authorization: Optional[str] = Header(None),
) -> RecoveryResponse:
    """
    Trigger bootstrap recovery from Neo4j.

    Restores local database from remote Neo4j backup.
    WARNING: This will merge remote data into local database.
    """
    try:
        sync_service = await get_sync_service()

        result = await sync_service.bootstrap_recovery_with_stats(
            project_id=request.project_id,
            since=request.since,
            dry_run=request.dry_run,
        )

        return RecoveryResponse(
            success=True,
            recovered_count=result.get("recovered_count", 0),
            skipped_count=0,  # TODO: Track skipped in T027
            conflict_count=0,  # TODO: Track conflicts in T028
            duration_ms=result.get("duration_ms", 0),
            dry_run=request.dry_run,
        )

    except Neo4jConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Neo4j unavailable", "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Recovery failed", "message": str(e)},
        )
