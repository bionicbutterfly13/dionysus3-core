# Research: Remote Persistence Safety Framework

**Feature**: 002-remote-persistence-safety
**Date**: 2025-12-14
**Status**: Complete

## Research Topics

### 1. Neo4j Python Driver Best Practices

**Decision**: Use `neo4j` async driver with connection pooling

**Rationale**:
- Official `neo4j` package supports async operations via `AsyncGraphDatabase`
- Connection pooling handles remote VPS latency (pool_size=5-10 for single dev)
- Bolt protocol (7687) is efficient for frequent small writes
- Session-per-transaction pattern prevents connection leaks

**Alternatives Considered**:
- `py2neo`: Rejected - less maintained, no native async
- HTTP API: Rejected - higher latency, less efficient for frequent syncs
- GraphQL via n8n: Rejected - adds unnecessary hop for direct Neo4j access

**Code Pattern**:
```python
from neo4j import AsyncGraphDatabase

driver = AsyncGraphDatabase.driver(
    "bolt://72.61.78.89:7687",
    auth=("neo4j", os.getenv("NEO4J_PASSWORD")),
    max_connection_pool_size=10
)

async def sync_memory(memory: Memory):
    async with driver.session() as session:
        await session.run(
            "MERGE (m:Memory {id: $id}) SET m += $props",
            id=memory.id, props=memory.dict()
        )
```

---

### 2. n8n Webhook Integration

**Decision**: Use n8n webhook with HMAC signature validation

**Rationale**:
- n8n webhooks support custom headers for authentication
- HMAC-SHA256 signature prevents unauthorized sync triggers
- Webhook retry is built into n8n (configurable)
- Webhook URL: `http://72.61.78.89:5678/webhook/memory-sync`

**Alternatives Considered**:
- Basic Auth: Rejected - credentials in URL, less secure
- API Key header: Acceptable but HMAC is stronger
- OAuth: Rejected - overkill for single-dev use case

**Integration Pattern**:
```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

**n8n Workflow Design**:
1. Webhook Trigger (POST /webhook/memory-sync)
2. Validate payload schema
3. Check if embedding needed (missing vector)
4. If yes: Call Ollama API for embedding
5. Write to Neo4j with MERGE (idempotent)
6. Return success/failure response

---

### 3. Ollama Embedding Generation

**Decision**: Use Ollama API with `nomic-embed-text` model, fallback to skip embedding

**Rationale**:
- Ollama API is simple HTTP POST to `/api/embeddings`
- `nomic-embed-text` is fast and produces 768-dim vectors (matches existing schema)
- Fallback: If Ollama unavailable, sync without embedding (mark for later)
- Batch not needed for sync (one memory at a time)

**Alternatives Considered**:
- OpenAI embeddings: Rejected - external dependency, cost, latency
- Local embedding in dionysus-core: Rejected - adds complexity to sync flow
- Skip embeddings entirely: Rejected - breaks semantic search on recovery

**API Pattern**:
```python
async def get_embedding(text: str) -> list[float] | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "http://72.61.78.89:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text}
            )
            return response.json()["embedding"]
    except Exception:
        return None  # Mark for retry later
```

---

### 4. Cross-Session Identity

**Decision**: Generate session_id at Claude Code startup, persist to local file

**Rationale**:
- Session = one Claude Code conversation/context
- UUID4 for uniqueness, stored in `.claude-session-id` file
- Same session_id used for all memories until session ends
- Session end detected by: explicit command, timeout (30min idle), or process exit

**Alternatives Considered**:
- Timestamp-based: Rejected - not unique across rapid restarts
- Hash of first message: Rejected - not deterministic across retries
- Server-generated: Rejected - adds round-trip, breaks offline scenarios

**Implementation**:
```python
import uuid
from pathlib import Path

SESSION_FILE = Path.home() / ".claude-session-id"

def get_or_create_session_id() -> str:
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    session_id = str(uuid.uuid4())
    SESSION_FILE.write_text(session_id)
    return session_id

def end_session():
    SESSION_FILE.unlink(missing_ok=True)
```

---

### 5. LLM Destruction Detection

**Decision**: Monitor for rapid delete patterns, alert but don't block

**Rationale**:
- LLMs may accidentally run destructive commands (DROP TABLE, rm -rf, etc.)
- Detection heuristics:
  - >10 deletes in 60 seconds
  - Schema modification (ALTER/DROP)
  - Bulk update affecting >50% of memories
- Alert via log + optional webhook to n8n for notification
- Don't auto-block (false positives possible) - alert for human review

**Alternatives Considered**:
- Auto-rollback: Rejected - may block legitimate batch operations
- Read-only mode trigger: Rejected - breaks normal workflow
- Pre-commit hooks: Rejected - LLMs bypass hooks

**Implementation**:
```python
from collections import deque
from datetime import datetime, timedelta

delete_timestamps = deque(maxlen=100)

def record_delete():
    delete_timestamps.append(datetime.now())
    recent = [t for t in delete_timestamps if t > datetime.now() - timedelta(seconds=60)]
    if len(recent) > 10:
        alert_destruction_detected("Rapid delete pattern: {len(recent)} deletes in 60s")

def alert_destruction_detected(message: str):
    logger.warning(f"LLM DESTRUCTION ALERT: {message}")
    # Optionally trigger n8n alert workflow
```

---

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Neo4j auth | Use env var NEO4J_PASSWORD, same as existing .env pattern |
| Webhook security | HMAC-SHA256 signature using MEMORY_WEBHOOK_TOKEN from .env |
| Embedding model | nomic-embed-text (768 dims, matches schema) |
| Session boundary | UUID file + 30min timeout + explicit end |
| Destruction threshold | >10 deletes/60s triggers alert (configurable) |

## Dependencies Identified

| Dependency | Version | Purpose |
|------------|---------|---------|
| neo4j | ^5.0 | Async Neo4j driver |
| httpx | ^0.25 | Async HTTP for webhooks/Ollama |
| pydantic | ^2.0 | Already in project, sync models |

## Next Steps

1. Create data-model.md with SyncEvent, Neo4j schema
2. Create contracts/ with OpenAPI spec, Neo4j Cypher, n8n workflow JSON
3. Create quickstart.md for dev setup
