# Dionysus Core

Dionysus is a VPS-native cognitive engine designed for autonomous reasoning, long-term session continuity, and structured memory management.

## System Architecture

Dionysus has migrated to a Neo4j-only, webhook-driven architecture to ensure high performance and seamless cross-session continuity.

- **Dionysus API:** FastAPI server managing agent lifecycles and cognitive state.
- **Neo4j:** Primary persistence for episodic, semantic, and procedural memory.
- **n8n:** Workflow orchestration for memory synchronization and background cognitive processes.
- **Ollama:** Local inference engine for embeddings and lightweight LLM tasks.
- **smolagents:** Multi-agent framework providing the cognitive orchestration layer.

## Core Features

- **Session Continuity:** Context is automatically reconstructed at the start of every Claude session using attractor-based resonance.
- **Cognitive Heartbeat:** An OODA-style loop (Observe-Orient-Decide-Act) driven by an internal energy budget.
- **Meta-ToT Reasoning:** Active-inference-based multi-branch planning with thresholded activation and traceable decision paths.
- **Temporal Memory:** Uses Graphiti to manage facts and entities with temporal validity (`valid_at`/`invalid_at`).
- **Secure Webhooks:** All database operations are secured via HMAC-SHA256 signatures.

## Tech Stack

- **Python 3.11+**
- **FastAPI**
- **Neo4j** (via n8n webhooks & Graphiti)
- **smolagents**
- **litellm**
- **Docker & Docker Compose**

## Setup & Deployment

Dionysus is designed to run on a VPS.

### 1. Prerequisites
- Docker and Docker Compose installed on VPS.
- n8n and Neo4j instances running.

### 2. Configuration
Copy `.env.example` to `.env` and configure the following:
- `NEO4J_URI`: `bolt://neo4j:7687` (internal Docker link)
- `NEO4J_PASSWORD`: Your Neo4j password
- `MEMEVOLVE_HMAC_SECRET`: Shared secret for webhooks
- `ANTHROPIC_API_KEY`: For Graphiti extraction
- `OPENAI_API_KEY`: For smolagents orchestration

### 3. Deploy
```bash
docker compose up -d --build
```

## Testing

Run the VPS-validated test suite:
```bash
docker exec dionysus-api python3 /app/scripts/test_memevolve_recall.py
docker exec dionysus-api python3 /app/scripts/test_memevolve_ingest.py
docker exec dionysus-api python3 /app/scripts/test_heartbeat_agent.py
```

## Integration with Archon

Archon remains a **local-only** task management service. Dionysus connects to Archon via prefetched task payloads in hooks to maintain context without exposing Archon to the public internet.
