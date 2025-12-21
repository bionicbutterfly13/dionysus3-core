# Remote Sync API Documentation

**Feature**: 002-remote-persistence-safety
**Version**: 1.0.0
**Last Updated**: 2025-12-15

## Overview

The Remote Sync API provides memory synchronization between local PostgreSQL and remote Neo4j via n8n webhooks. It includes:

- Memory sync operations (create, update, delete)
- Session and project tagging
- Destruction detection and safety mechanisms
- Bootstrap recovery from remote

## Architecture

```
Local App → RemoteSyncService → n8n Webhook → Neo4j
                                    ↓
                               Ollama (embeddings)
```

All Neo4j access goes through n8n webhooks. No direct database connections in production.

---

## REST API Endpoints

Note: In the core API, these routes are mounted without an `/api` prefix.
If you mount the sync router under `/api`, prepend `/api` in your requests.

### Sync Operations

#### POST /sync/trigger

Manually trigger sync queue processing.

**Request:**
```http
POST /sync/trigger
Authorization: Bearer <token>
```

**Response:**
```json
{
  "processed": 5,
  "succeeded": 4,
  "failed": 1,
  "requeued": 1,
  "queue_remaining": 2
}
```

#### GET /sync/status

Get current sync system status.

**Response:**
```json
{
  "queue_size": 3,
  "pending_count": 2,
  "failed_count": 1,
  "processing": false,
  "paused": false,
  "last_sync": "2025-12-15T10:30:00Z",
  "last_error": null,
  "destruction_detection": {
    "active": false,
    "delete_count_in_window": 2,
    "threshold": 10,
    "window_seconds": 60
  }
}
```

### Memory Operations

#### GET /api/memory/sessions/{session_id}

Get memories for a specific session.

**Parameters:**
- `session_id` (path): Session UUID
- `query` (query, optional): Keyword search within session
- `include_metadata` (query, optional): Include session start/end times

**Response:**
```json
{
  "session_id": "abc-123",
  "memories": [
    {
      "id": "mem-1",
      "content": "Discussed rate limiting",
      "memory_type": "semantic",
      "importance": 0.7,
      "created_at": "2025-12-15T09:00:00Z"
    }
  ],
  "count": 1
}
```

#### GET /api/memory/range

Get memories within a date range.

**Parameters:**
- `from_date` (query): ISO datetime start
- `to_date` (query): ISO datetime end
- `session_id` (query, optional): Filter by session

**Response:**
```json
{
  "from_date": "2025-12-14T00:00:00Z",
  "to_date": "2025-12-15T00:00:00Z",
  "memories": [...],
  "count": 15
}
```

#### GET /api/memory/search

Search memories with optional session attribution.

**Parameters:**
- `query` (query): Search string
- `include_session` (query, optional): Include session_id in results
- `limit` (query, optional): Max results (default 20)

**Response:**
```json
{
  "query": "rate limiting",
  "memories": [
    {
      "id": "mem-1",
      "content": "Implemented token bucket rate limiting",
      "session_id": "sess-123",
      "relevance_score": 0.92
    }
  ],
  "count": 3
}
```

#### GET /api/memory/projects

Get memories grouped by project.

**Response:**
```json
{
  "projects": {
    "dionysus-core": {
      "memory_count": 45,
      "last_updated": "2025-12-15T10:00:00Z"
    },
    "inner-architect": {
      "memory_count": 23,
      "last_updated": "2025-12-14T15:00:00Z"
    }
  }
}
```

#### GET /api/memory/projects/{project_id}

Get memories for a specific project.

**Parameters:**
- `project_id` (path): Project identifier
- `query` (query, optional): Keyword search
- `limit` (query, optional): Max results

### Recovery Operations

#### POST /recovery/bootstrap

Recover memories from remote Neo4j.

**Request:**
```json
{
  "project_id": "dionysus-core",
  "since": "2025-12-01T00:00:00Z",
  "dry_run": true
}
```

**Response:**
```json
{
  "success": true,
  "recovered_count": 127,
  "duration_ms": 1523,
  "dry_run": true,
  "memories": [...]  // Only included if dry_run=true
}
```

---

## MCP Tools

Available via the Dionysus MCP server for Dionysus self-management.

### sync_now

Immediately process pending sync queue.

```python
# MCP call
await sync_now(force=False, batch_size=10)
```

**Parameters:**
- `force` (bool): Override pause status
- `batch_size` (int): Max items to process

**Returns:** Sync results with counts

### get_sync_status

Get comprehensive sync system status.

```python
# MCP call
status = await get_sync_status()
```

**Returns:** Queue size, pause status, destruction detection, health

### pause_sync

Pause sync operations.

```python
# MCP call
await pause_sync(reason="Investigating anomaly")
```

**Parameters:**
- `reason` (str): Why sync is paused

### resume_sync

Resume sync operations.

```python
# MCP call
await resume_sync(process_queue=True)
```

**Parameters:**
- `process_queue` (bool): Process pending items immediately

### check_destruction

Check for destruction patterns (rapid deletion).

```python
# MCP call
result = await check_destruction()
# Returns: destruction_detected, delete_count, threshold, alert
```

### acknowledge_destruction_alert

Acknowledge a destruction detection alert.

```python
# MCP call
await acknowledge_destruction_alert()
```

### bootstrap_recovery

Recover memories from remote Neo4j.

```python
# MCP call
result = await bootstrap_recovery(
    project_id="dionysus-core",
    since="2025-12-01T00:00:00Z",
    dry_run=True
)
```

---

## Webhook Contract

### Memory Sync Webhook

**Endpoint:** `POST /webhook/memory/v1/ingest/message`

**Headers:**
```
Content-Type: application/json
X-Webhook-Signature: sha256=<hmac-signature>
```

**Payload:**
```json
{
  "memory_id": "uuid",
  "content": "Memory content text",
  "memory_type": "episodic|semantic|procedural|strategic",
  "importance": 0.5,
  "session_id": "uuid",
  "project_id": "project-name",
  "tags": ["tag1", "tag2"],
  "sync_version": 1,
  "created_at": "2025-12-15T10:00:00Z",
  "updated_at": "2025-12-15T10:00:00Z"
}
```

**Response (Success):**
```json
{
  "success": true,
  "memory_id": "uuid",
  "synced_at": "2025-12-15T10:00:01Z",
  "embedding_generated": true
}
```

### Session Summary Webhook

**Endpoint:** `POST /webhook/session/summary`

**Payload:**
```json
{
  "session_id": "uuid",
  "memories": [
    {"id": "mem-1", "content": "..."},
    {"id": "mem-2", "content": "..."}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "summary": "This session covered rate limiting and authentication."
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "SYNC_FAILED",
  "details": {}
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `SYNC_FAILED` | Webhook request failed |
| `INVALID_SIGNATURE` | HMAC signature validation failed |
| `INVALID_PAYLOAD` | Missing required fields |
| `NEO4J_ERROR` | Neo4j operation failed |
| `OLLAMA_ERROR` | Embedding generation failed |
| `SYNC_PAUSED` | Sync is paused (destruction detected) |

---

## Safety Features

### Destruction Detection

Monitors for rapid deletion patterns:

- **Threshold:** 10 deletes in 60 seconds (configurable)
- **Action:** Logs CRITICAL alert, optionally pauses sync
- **Recovery:** Call `acknowledge_destruction_alert()` after investigation

### Retry Logic

Failed sync operations use exponential backoff:

- Initial backoff: 1 second
- Multiplier: 2x
- Max backoff: 5 minutes
- Max retries: 5

### Queue Management

- Pending operations queued locally
- Processed in batches (default 10)
- Failed items requeued with backoff
- Dead letter after max retries

---

## Configuration

### Environment Variables

```bash
# Neo4j (via SSH tunnel for local dev)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>

# n8n Webhook
N8N_WEBHOOK_URL=http://localhost:5678/webhook/memory/v1/ingest/message
MEMORY_WEBHOOK_TOKEN=<hmac-secret>

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Sync Settings
SYNC_MAX_RETRIES=5
SYNC_INITIAL_BACKOFF=1.0
SYNC_MAX_BACKOFF=300.0
SYNC_BATCH_SIZE=10

# Destruction Detection
DESTRUCTION_THRESHOLD=10
DESTRUCTION_WINDOW_SECONDS=60
```

---

## Usage Examples

### Python SDK

```python
from api.services.remote_sync import RemoteSyncService

sync = RemoteSyncService()

# Sync a memory
result = await sync.sync_memory({
    "id": "mem-123",
    "content": "Learned about rate limiting",
    "type": "semantic",
    "importance": 0.7,
    "session_id": "sess-abc",
})

# Query by session
memories = await sync.query_by_session("sess-abc")

# Bootstrap recovery
recovered = await sync.bootstrap_recovery(
    project_id="dionysus-core",
    dry_run=False
)
```

### cURL

```bash
# Get sync status
curl http://localhost:8000/sync/status

# Trigger manual sync
curl -X POST http://localhost:8000/sync/trigger \
  -H "Authorization: Bearer <token>"

# Search memories
curl "http://localhost:8000/api/memory/search?query=rate+limiting&limit=10"

# Bootstrap recovery (dry run)
curl -X POST http://localhost:8000/recovery/bootstrap \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```
