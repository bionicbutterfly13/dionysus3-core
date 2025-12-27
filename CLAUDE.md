# Dionysus Development Guide

VPS-native cognitive system with Neo4j-only persistence.

## Architecture
- **API:** FastAPI on VPS (port 8000)
- **Memory:** Neo4j via n8n webhooks (port 5678)
- **Orchestration:** smolagents multi-agent framework
- **Extraction:** Graphiti (direct Neo4j access exception)
- **Local:** Archon task management (port 8181)

## Environment Setup
- Deploy using `docker compose up -d --build` on VPS.
- Core configuration in `.env` (copied into image).
- Webhook communication secured via HMAC-SHA256.

## VPS Test Commands
Execute inside the API container:
- `docker exec dionysus-api python3 /app/scripts/test_memevolve_recall.py`
- `docker exec dionysus-api python3 /app/scripts/test_memevolve_ingest.py`
- `docker exec dionysus-api python3 /app/scripts/test_heartbeat_agent.py`

## Code Style
- **Python:** 3.11+ async/await, Pydantic v2 models.
- **Database:** All queries must be Cypher (via WebhookNeo4jDriver).
- **Naming:** snake_case for functions/vars, PascalCase for classes.

## Architecture Constraints
- **Neo4j-Only**: ALL database access must go through n8n webhooks. Direct Bolt connections are forbidden.
  - **EXCEPTION: Graphiti** - The `graphiti-core` library is approved for direct Neo4j access as a trusted infrastructure component.
- **HMAC Verification**: All webhook endpoints must use `verify_memevolve_signature` dependency.
- **Shell Safety**: The shell parser is sensitive to nested code (e.g., `python -c`). Use script files (`scripts/`) and sync via `git` instead of inline shell pipes.
- **Archon-First**: Archon remains local. Dionysus receives tasks via prefetched payloads in hooks.