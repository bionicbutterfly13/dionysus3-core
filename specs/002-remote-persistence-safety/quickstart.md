# Quickstart: Remote Persistence Safety Framework

**Feature**: 002-remote-persistence-safety
**Date**: 2025-12-14

Get the remote persistence system running for local development.

## Prerequisites

- Python 3.11+
- Access to VPS (72.61.78.89) with SSH key
- Docker running on VPS with neo4j, n8n, ollama services

## 1. Verify VPS Services

```bash
# Check all services are running
ssh root@72.61.78.89 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Expected output:
# NAMES    STATUS         PORTS
# neo4j    Up X hours     127.0.0.1:7474->7474/tcp, 127.0.0.1:7687->7687/tcp
# n8n      Up X hours     127.0.0.1:5678->5678/tcp
# ollama   Up X hours     127.0.0.1:11434->11434/tcp
```

## 2. Set Up SSH Tunnel (for local development)

Services are bound to localhost on VPS. Create SSH tunnels:

```bash
# Open tunnels to all services
ssh -L 7474:127.0.0.1:7474 \
    -L 7687:127.0.0.1:7687 \
    -L 5678:127.0.0.1:5678 \
    -L 11434:127.0.0.1:11434 \
    -N root@72.61.78.89
```

Or add to `~/.ssh/config`:

```
Host dionysus-tunnel
    HostName 72.61.78.89
    User root
    LocalForward 7474 127.0.0.1:7474
    LocalForward 7687 127.0.0.1:7687
    LocalForward 5678 127.0.0.1:5678
    LocalForward 11434 127.0.0.1:11434
```

Then: `ssh -N dionysus-tunnel`

## 3. Configure Environment Variables

Add to your local `.env` file:

```bash
# Remote Sync Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=DionysusMem2025!

N8N_WEBHOOK_URL=http://localhost:5678/webhook/memory-sync
MEMORY_WEBHOOK_TOKEN=09b845160bc4b24b78c103bf40dd5ac3c56229ed41e23a50e548ea01254483bc

OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

## 4. Initialize Neo4j Schema

Run the schema initialization:

```bash
# Via cypher-shell (if installed locally)
cat specs/002-remote-persistence-safety/contracts/neo4j-schema.cypher | \
  cypher-shell -u neo4j -p DionysusMem2025! -a bolt://localhost:7687

# Or via Neo4j Browser
# Open http://localhost:7474 and paste schema queries
```

## 5. Verify Connectivity

```python
# scripts/test_vps_connectivity.py
import asyncio
from neo4j import AsyncGraphDatabase
import httpx

async def test_neo4j():
    driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "DionysusMem2025!")
    )
    async with driver.session() as session:
        result = await session.run("RETURN 1 as n")
        record = await result.single()
        print(f"✓ Neo4j connected: {record['n']}")
    await driver.close()

async def test_n8n():
    async with httpx.AsyncClient() as client:
        # n8n health check
        response = await client.get("http://localhost:5678/healthz", timeout=5)
        print(f"✓ n8n health: {response.status_code}")

async def test_ollama():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        print(f"✓ Ollama models: {[m['name'] for m in models]}")

async def main():
    await test_neo4j()
    await test_n8n()
    await test_ollama()

if __name__ == "__main__":
    asyncio.run(main())
```

Run: `python scripts/test_vps_connectivity.py`

## 6. Load n8n Workflow

1. Open n8n at http://localhost:5678
2. Login with credentials from `.env` (N8N_BASIC_AUTH_USER/PASSWORD)
3. Import workflow from `specs/002-remote-persistence-safety/contracts/n8n-workflow.json`
4. Configure Neo4j credentials in n8n:
   - Go to Credentials
   - Create "Neo4j Dionysus" credential
   - Host: `neo4j`, Port: `7687`, User: `neo4j`, Password: (from .env)
5. Activate the workflow

## 7. Test Webhook

```bash
# Generate HMAC signature
export PAYLOAD='{"memory_id":"test-123","content":"Test memory","memory_type":"episodic","session_id":"sess-123","project_id":"dionysus-core","sync_version":1}'
export TOKEN="09b845160bc4b24b78c103bf40dd5ac3c56229ed41e23a50e548ea01254483bc"
export SIGNATURE="sha256=$(echo -n $PAYLOAD | openssl dgst -sha256 -hmac $TOKEN | cut -d' ' -f2)"

# Send test webhook
curl -X POST http://localhost:5678/webhook/memory-sync \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d "$PAYLOAD"

# Expected: {"success":true,"memory_id":"test-123","synced_at":"...","embedding_generated":true}
```

## 8. Verify in Neo4j

```cypher
// Check the test memory was created
MATCH (m:Memory {id: 'test-123'})
RETURN m.content, m.embedding IS NOT NULL as has_embedding;

// Clean up test data
MATCH (m:Memory {id: 'test-123'}) DETACH DELETE m;
```

## Development Workflow

### Running Tests

```bash
# Integration tests against VPS (requires tunnels)
pytest tests/integration/test_neo4j_sync.py -v

# Contract tests
pytest tests/contract/test_webhook_sync.py -v

# Unit tests (no VPS required)
pytest tests/unit/test_remote_sync.py -v
```

### Common Tasks

```bash
# Manual sync trigger
curl -X POST http://localhost:8000/api/sync/trigger \
  -H "Authorization: Bearer <token>"

# Check sync status
curl http://localhost:8000/api/sync/status

# Bootstrap recovery (use with caution!)
curl -X POST http://localhost:8000/api/recovery/bootstrap \
  -H "Authorization: Bearer <token>" \
  -d '{"dry_run": true}'
```

## Troubleshooting

### SSH Tunnel Drops

```bash
# Use autossh for persistent tunnels
autossh -M 0 -f -N dionysus-tunnel
```

### Neo4j Connection Refused

```bash
# Check Neo4j is running on VPS
ssh root@72.61.78.89 'docker logs neo4j --tail 20'

# Verify port binding
ssh root@72.61.78.89 'docker port neo4j'
```

### Ollama Model Missing

```bash
# Pull the embedding model
ssh root@72.61.78.89 'docker exec ollama ollama pull nomic-embed-text'
```

### n8n Workflow Not Triggering

1. Check workflow is active (green toggle)
2. Verify webhook URL matches exactly
3. Check n8n logs: `ssh root@72.61.78.89 'docker logs n8n --tail 50'`

### HMAC Signature Invalid

```python
# Debug signature generation
import hmac
import hashlib

payload = b'{"memory_id":"test",...}'
secret = "your-token"
signature = "sha256=" + hmac.new(
    secret.encode(), payload, hashlib.sha256
).hexdigest()
print(signature)
```

## File Locations

| File | Purpose |
|------|---------|
| `specs/002-remote-persistence-safety/contracts/webhook-sync.yaml` | OpenAPI spec |
| `specs/002-remote-persistence-safety/contracts/neo4j-schema.cypher` | Neo4j schema |
| `specs/002-remote-persistence-safety/contracts/n8n-workflow.json` | n8n workflow |
| `api/routers/sync.py` | Sync API endpoints (to be created) |
| `api/services/remote_sync.py` | RemoteSyncService (to be created) |
| `scripts/bootstrap_recovery.py` | Recovery script (to be created) |
