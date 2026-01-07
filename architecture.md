# Dionysus Architecture

Dionysus is a VPS-native cognitive system designed for autonomous reasoning and temporal memory management.

## Core Pillars

### 1. VPS-Native Execution
All core services run containerized on a central VPS (72.61.78.89). This eliminates "session amnesia" by ensuring the cognitive engine and memory stay alive and unified across sessions.

### 2. Neo4j-Only Persistence
Dionysus has migrated entirely to a Neo4j-only architecture.
*   **n8n Webhooks:** Ingest/recall/traverse workflows are orchestrated via n8n webhooks.
*   **Graphiti-backed Driver:** Services run Cypher through a Graphiti-backed driver shim for Neo4j operations.
*   **Graphiti:** Provides temporal knowledge graph extraction and search.

### 3. Agentic Orchestration
Dionysus uses the `smolagents` multi-agent framework.
*   **ConsciousnessManager:** Coordinates specialized agents (Perception, Reasoning, Metacognition).
*   **Heartbeat System:** An OODA (Observe-Orient-Decide-Act) loop driven by an energy budget.

## Service Map
- **Dionysus API:** `port 8000` (FastAPI)
- **n8n:** `port 5678` (Workflow Orchestration)
- **Neo4j:** `port 7687` (Temporal Knowledge Graph)
- **Ollama:** `port 11434` (Local Embeddings & Inference)
- **Graphiti:** `port 8001` (Entity Extraction)
- **Archon:** `port 8181` (**Local-only** task management)

## Memory Layers (Neo4j)
- **Episodic Memory:** Temporal sequences of events and agent trajectories.
- **Semantic Memory:** Facts, entities, and conceptual relationships extracted by Graphiti.
- **Procedural Memory:** Skills and practiced behaviors.
- **Strategic Memory:** Long-term goals and mental models.

## Security
- **HMAC Authentication:** All webhook communication between the API and n8n is secured with HMAC-SHA256 signatures.
- **Service Isolation:** Databases are not exposed to the public internet; access is restricted to the internal Docker network.
