# Graphiti Service - VPS Deployment

Temporal knowledge graph for entity extraction, deployed on VPS alongside Neo4j and n8n.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS (72.61.78.89)                        │
│                                                             │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   n8n   │───▶│  Graphiti   │───▶│       Neo4j         │  │
│  │  :5678  │    │    :8001    │    │  :7687 (internal)   │  │
│  └─────────┘    └─────────────┘    └─────────────────────┘  │
│                                                             │
│  Docker Network: dionysus_default                           │
└─────────────────────────────────────────────────────────────┘
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/api/graphiti/health` | Neo4j connectivity check |
| POST | `/api/graphiti/ingest` | Ingest text, extract entities |
| POST | `/api/graphiti/search` | Hybrid search |
| GET | `/api/graphiti/entity/{name}` | Get entity by name |

## Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Orchestration (uses dionysus_default network) |
| `main.py` | FastAPI application |
| `graphiti_service.py` | Core Graphiti wrapper |
| `graphiti_router.py` | REST API endpoints |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment template |
| `.env` | Actual credentials (NOT in git) |

## Environment Variables

```bash
NEO4J_URI=bolt://neo4j:7687      # Docker internal DNS
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secret>
OPENAI_API_KEY=<secret>
GRAPHITI_GROUP_ID=dionysus       # Partition key
```

## Deployment Commands

```bash
# SSH to VPS
ssh mani@72.61.78.89

# Navigate to graphiti
cd ~/graphiti

# Build and start
docker compose up -d --build

# Check logs
docker logs graphiti --tail 50

# Restart
docker compose restart

# Stop
docker compose down
```

## Usage Examples

### Ingest text
```bash
curl -X POST "http://72.61.78.89:8001/api/graphiti/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Dr. Mani is building Dionysus, an AI consciousness system.",
    "source_description": "conversation"
  }'
```

### Search
```bash
curl -X POST "http://72.61.78.89:8001/api/graphiti/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Dionysus AI"}'
```

## Deployed

- **Date**: 2025-12-21
- **graphiti-core version**: 0.24.3
- **Container name**: graphiti
- **Port**: 8001 (external), 8001 (internal)
