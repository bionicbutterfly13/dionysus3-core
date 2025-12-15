"""
Sync Models for Remote Persistence Safety Framework
Feature: 002-remote-persistence-safety
Tasks: T009, T010, T011

Pydantic models for sync tracking, audit records, and queue management.
Based on data-model.md specification.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# T010: SyncStatus Enum
# =============================================================================


class MemoryType(str, Enum):
    """Valid memory types per data model."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    STRATEGIC = "strategic"


class SyncStatus(str, Enum):
    """
    Sync state for individual memory records.

    States:
        PENDING: Not yet synced to remote
        SYNCED: Successfully synced to remote
        FAILED: Sync failed, needs retry
        QUEUED: In queue waiting for remote availability
        CONFLICT: Local/remote conflict detected
    """

    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    QUEUED = "queued"
    CONFLICT = "conflict"


class SyncDirection(str, Enum):
    """Direction of sync operation."""

    LOCAL_TO_REMOTE = "local_to_remote"
    REMOTE_TO_LOCAL = "remote_to_local"


class SyncResult(str, Enum):
    """Outcome of sync operation."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    QUEUED = "queued"


# =============================================================================
# T009: SyncEvent Model
# =============================================================================


class SyncEvent(BaseModel):
    """
    Audit record for sync operations.

    Tracks every sync attempt for debugging, compliance, and monitoring.
    """

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    direction: SyncDirection
    result: SyncResult
    record_count: int = Field(ge=0, description="Number of records synced")
    memory_ids: list[UUID] = Field(
        default_factory=list, description="IDs of memories involved"
    )
    error_message: str | None = None
    duration_ms: int | None = Field(None, ge=0, description="Sync duration in milliseconds")
    retry_count: int = Field(default=0, ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-14T10:30:00Z",
                "direction": "local_to_remote",
                "result": "success",
                "record_count": 5,
                "memory_ids": ["550e8400-e29b-41d4-a716-446655440001"],
                "error_message": None,
                "duration_ms": 1250,
                "retry_count": 0,
            }
        }
    }


# =============================================================================
# T011: SyncQueueItem Model
# =============================================================================


class SyncOperation(str, Enum):
    """Type of sync operation in queue."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncQueueItem(BaseModel):
    """
    Item in sync queue for retry.

    When remote services are unavailable, sync operations are queued
    for later retry with exponential backoff.
    """

    id: UUID = Field(default_factory=uuid4)
    memory_id: UUID
    operation: SyncOperation = Field(description="create, update, or delete")
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = Field(default=0, ge=0)
    next_retry_at: datetime | None = None
    last_error: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "memory_id": "550e8400-e29b-41d4-a716-446655440001",
                "operation": "create",
                "payload": {
                    "content": "Memory content to sync",
                    "memory_type": "episodic",
                },
                "created_at": "2025-12-14T10:30:00Z",
                "retry_count": 0,
                "next_retry_at": None,
                "last_error": None,
            }
        }
    }


# =============================================================================
# Memory Sync Fields (to be added to existing Memory model)
# =============================================================================


class MemorySyncFields(BaseModel):
    """
    Fields to add to existing Memory model for sync tracking.

    These fields track the sync state of each memory record.
    """

    sync_status: SyncStatus = SyncStatus.PENDING
    synced_at: datetime | None = None
    sync_version: int = Field(
        default=1, ge=1, description="Monotonic version for conflict detection"
    )
    remote_id: str | None = Field(None, description="Neo4j node ID if different from local")


# =============================================================================
# Webhook Payload Models (for n8n integration)
# =============================================================================


class MemorySyncPayload(BaseModel):
    """
    Payload for memory sync webhook.

    Matches the contract in webhook-sync.yaml.
    """

    memory_id: UUID
    content: str = Field(min_length=1, max_length=50000)
    memory_type: MemoryType = Field(description="episodic, semantic, procedural, or strategic")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    embedding: list[float] | None = Field(
        None,
        min_length=768,
        max_length=768,
        description="Pre-computed embedding. If missing, n8n generates via Ollama.",
    )
    session_id: UUID
    project_id: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    sync_version: int = Field(ge=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "memory_id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "Learned that FastAPI dependency injection works with Annotated types",
                "memory_type": "procedural",
                "importance": 0.8,
                "session_id": "660e8400-e29b-41d4-a716-446655440001",
                "project_id": "dionysus-core",
                "tags": ["fastapi", "python", "dependency-injection"],
                "sync_version": 1,
                "created_at": "2025-12-14T10:30:00Z",
                "updated_at": "2025-12-14T10:30:00Z",
            }
        }
    }


class SyncResponse(BaseModel):
    """Response from sync webhook."""

    success: bool
    memory_id: UUID
    remote_id: str | None = None
    synced_at: datetime
    embedding_generated: bool = False


class SyncStatusResponse(BaseModel):
    """Response from sync status endpoint."""

    healthy: bool
    neo4j_connected: bool
    n8n_connected: bool
    ollama_connected: bool
    queue_size: int
    pending_count: int
    failed_count: int
    last_sync: datetime | None = None
    last_error: str | None = None


class RecoveryResponse(BaseModel):
    """Response from bootstrap recovery endpoint."""

    success: bool
    recovered_count: int
    skipped_count: int = 0
    conflict_count: int = 0
    duration_ms: int
    dry_run: bool = False


class ConflictResponse(BaseModel):
    """Response when sync conflict is detected."""

    error: str = "conflict"
    memory_id: UUID
    local_version: int
    remote_version: int
    resolution: str = Field(description="local_wins, remote_wins, or manual_required")
