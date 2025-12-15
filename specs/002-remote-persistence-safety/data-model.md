# Data Model: Remote Persistence Safety Framework

**Feature**: 002-remote-persistence-safety
**Date**: 2025-12-14
**Status**: Complete

## Overview

This document defines the data models for remote persistence, including local tracking entities and Neo4j graph schema.

## Local Entities (PostgreSQL)

### SyncEvent

Audit record for sync operations. Tracks every sync attempt for debugging and compliance.

```python
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

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

class SyncEvent(BaseModel):
    """Audit record for sync operations."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    direction: SyncDirection
    result: SyncResult
    record_count: int = Field(ge=0, description="Number of records synced")
    memory_ids: list[UUID] = Field(default_factory=list, description="IDs of memories involved")
    error_message: str | None = None
    duration_ms: int | None = Field(None, ge=0, description="Sync duration in milliseconds")
    retry_count: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-14T10:30:00Z",
                "direction": "local_to_remote",
                "result": "success",
                "record_count": 5,
                "memory_ids": ["memory-uuid-1", "memory-uuid-2"],
                "error_message": None,
                "duration_ms": 1250,
                "retry_count": 0
            }
        }
```

### SyncStatus

Per-memory sync tracking. Added to existing Memory model.

```python
class SyncStatus(str, Enum):
    """Sync state for individual memory records."""
    PENDING = "pending"      # Not yet synced
    SYNCED = "synced"        # Successfully synced to remote
    FAILED = "failed"        # Sync failed, needs retry
    QUEUED = "queued"        # In queue waiting for remote availability
    CONFLICT = "conflict"    # Local/remote conflict detected

class MemorySyncFields(BaseModel):
    """Fields to add to existing Memory model."""
    sync_status: SyncStatus = SyncStatus.PENDING
    synced_at: datetime | None = None
    sync_version: int = Field(default=1, ge=1, description="Monotonic version for conflict detection")
    remote_id: str | None = Field(None, description="Neo4j node ID if different from local")
```

### SyncQueue

Queue for pending sync operations when remote is unavailable.

```python
class SyncQueueItem(BaseModel):
    """Item in sync queue for retry."""
    id: UUID = Field(default_factory=uuid4)
    memory_id: UUID
    operation: str = Field(description="create, update, or delete")
    payload: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = Field(default=0, ge=0)
    next_retry_at: datetime | None = None
    last_error: str | None = None
```

## Remote Schema (Neo4j)

### Memory Node

Graph representation of memory with relationships to Session and Project.

```cypher
// Memory node schema
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE;

// Memory node properties
(:Memory {
    id: String,              // UUID from local system
    content: String,         // Memory text content
    memory_type: String,     // episodic, semantic, procedural, strategic
    importance: Float,       // 0.0 to 1.0
    embedding: List<Float>,  // 768-dim vector from nomic-embed-text
    created_at: DateTime,
    updated_at: DateTime,
    source_project: String,  // Project identifier
    session_id: String,      // Session UUID
    tags: List<String>,      // User-defined tags
    sync_version: Integer    // For conflict detection
})
```

### Session Node

Represents a bounded work session.

```cypher
// Session node schema
CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.id IS UNIQUE;

(:Session {
    id: String,              // UUID
    project_id: String,      // Parent project
    started_at: DateTime,
    ended_at: DateTime,      // Null if active
    summary: String,         // Auto-generated or manual
    memory_count: Integer    // Denormalized for quick stats
})
```

### Project Node

Namespace for grouping related memories.

```cypher
// Project node schema
CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE;

(:Project {
    id: String,              // e.g., "dionysus-core", "inner-architect-companion"
    name: String,
    description: String,
    created_at: DateTime
})
```

### Relationships

```cypher
// Memory belongs to Session
(m:Memory)-[:BELONGS_TO]->(s:Session)

// Session belongs to Project
(s:Session)-[:PART_OF]->(p:Project)

// Memory directly tagged with Project (for cross-project queries)
(m:Memory)-[:TAGGED_WITH]->(p:Project)

// Memory references another Memory (for linked thoughts)
(m1:Memory)-[:REFERENCES {context: String}]->(m2:Memory)

// Session follows another Session (for journey tracking)
(s1:Session)-[:FOLLOWED_BY]->(s2:Session)
```

### Indexes for Query Performance

```cypher
// Vector index for semantic search
CREATE VECTOR INDEX memory_embedding IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
}};

// Text index for keyword search
CREATE FULLTEXT INDEX memory_content IF NOT EXISTS
FOR (n:Memory) ON EACH [n.content, n.tags];

// Composite index for filtered queries
CREATE INDEX memory_project_type IF NOT EXISTS
FOR (m:Memory) ON (m.source_project, m.memory_type);

// Date range queries
CREATE INDEX memory_created IF NOT EXISTS
FOR (m:Memory) ON (m.created_at);

CREATE INDEX session_dates IF NOT EXISTS
FOR (s:Session) ON (s.started_at, s.ended_at);
```

## SQL Migrations (PostgreSQL)

### Add sync tracking to memories table

```sql
-- Migration: Add sync tracking columns to memories
ALTER TABLE memories ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS sync_version INTEGER DEFAULT 1;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS remote_id VARCHAR(255);

-- Index for finding unsynced records
CREATE INDEX IF NOT EXISTS idx_memories_sync_status ON memories(sync_status);

-- Index for conflict detection
CREATE INDEX IF NOT EXISTS idx_memories_sync_version ON memories(id, sync_version);
```

### Create sync_events table

```sql
-- Migration: Create sync_events audit table
CREATE TABLE IF NOT EXISTS sync_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    direction VARCHAR(20) NOT NULL,
    result VARCHAR(20) NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    memory_ids UUID[] DEFAULT '{}',
    error_message TEXT,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0
);

-- Index for recent events
CREATE INDEX IF NOT EXISTS idx_sync_events_timestamp ON sync_events(timestamp DESC);

-- Index for failed syncs needing attention
CREATE INDEX IF NOT EXISTS idx_sync_events_failed ON sync_events(result) WHERE result = 'failed';
```

### Create sync_queue table

```sql
-- Migration: Create sync queue for offline operation
CREATE TABLE IF NOT EXISTS sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    operation VARCHAR(20) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT
);

-- Index for processing queue in order
CREATE INDEX IF NOT EXISTS idx_sync_queue_next_retry ON sync_queue(next_retry_at ASC NULLS FIRST);

-- Index for finding items by memory
CREATE INDEX IF NOT EXISTS idx_sync_queue_memory ON sync_queue(memory_id);
```

## Data Flow Diagrams

### Local to Remote Sync

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Memory Create  │────▶│ RemoteSyncService│────▶│  n8n Webhook    │
│   (PostgreSQL)  │     │   (queue item)   │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐              │
                        │  Update sync_    │◀─────────────┘
                        │  status='synced' │     ┌─────────────────┐
                        └──────────────────┘     │  Ollama Embed   │
                                                 └────────┬────────┘
                                                          │
                                                 ┌────────▼────────┐
                                                 │   Neo4j Write   │
                                                 │  (with vector)  │
                                                 └─────────────────┘
```

### Bootstrap Recovery

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Local DB Empty │────▶│ Bootstrap Script │────▶│  Neo4j Query    │
│   (detected)    │     │                  │     │  (all memories) │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐              │
                        │  Validate Data   │◀─────────────┘
                        │  (integrity check)│
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Bulk Insert to  │
                        │   PostgreSQL     │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Mark all as     │
                        │  sync_status=    │
                        │  'synced'        │
                        └──────────────────┘
```

## Conflict Resolution

### Last-Write-Wins Strategy

```python
def resolve_conflict(local: Memory, remote: dict) -> Memory:
    """
    Resolve conflict using last-write-wins with audit logging.

    Returns the winning version and logs the conflict.
    """
    local_version = local.sync_version
    remote_version = remote.get("sync_version", 0)

    if local_version > remote_version:
        # Local wins - push to remote
        winner = "local"
        result = local
    elif remote_version > local_version:
        # Remote wins - pull to local
        winner = "remote"
        result = Memory(**remote)
    else:
        # Same version - compare timestamps
        local_time = local.updated_at
        remote_time = datetime.fromisoformat(remote["updated_at"])
        winner = "local" if local_time >= remote_time else "remote"
        result = local if winner == "local" else Memory(**remote)

    # Log conflict for audit
    log_conflict(
        memory_id=local.id,
        local_version=local_version,
        remote_version=remote_version,
        winner=winner,
        local_content=local.content[:100],
        remote_content=remote.get("content", "")[:100]
    )

    return result
```

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| embedding | Length must be 768 | "Embedding dimension mismatch: expected 768, got {n}" |
| sync_version | Must be positive integer | "sync_version must be >= 1" |
| memory_type | Must be in enum | "Invalid memory_type: {value}" |
| importance | Must be 0.0 to 1.0 | "Importance must be between 0 and 1" |
| session_id | Must be valid UUID | "Invalid session_id format" |
