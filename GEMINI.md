# Dionysus Core

Dionysus is a VPS-native cognitive engine designed for autonomous reasoning, long-term session continuity, and structured memory management. It operates on a Neo4j-only, webhook-driven architecture, orchestrated by a multi-agent hierarchy.

## Active Technologies
- Python 3.11+ + smolagents, litellm, pydantic, numpy, scipy, neo4j (Graphiti) (038-thoughtseeds-framework)
- Neo4j (Memory Graph) (038-thoughtseeds-framework)

- **Python 3.11+**: Core language (async/await, Pydantic v2).
- **FastAPI**: Web framework for the API.
- **Neo4j**: Primary persistence for episodic, semantic, and procedural memory.
- **Graphiti**: Temporal knowledge graph interface (authorized for direct Neo4j access).
- **smolagents**: Multi-agent framework (CodeAgent) providing the cognitive orchestration layer.
- **n8n**: Workflow orchestration for memory synchronization and background processes.
- **Docker & Docker Compose**: Containerization and VPS-native orchestration.
- **Ollama / LiteLLM**: Local and remote inference engines.

## Project Architecture & Tracking

The project is consolidated into three unified pillars in Archon for streamlined tracking:

1.  **Dionysus 3 Core**: Unified VPS-native cognitive engine (Smolagents + Neo4j + MoSAEIC).
2.  **Inner Architect - Marketing Suite**: Unified nurture sequences and high-converting sales pages.
3.  **Inner Architect - Knowledge Base**: Authoritative IAS conceptual content (Mini-book, Audiobook, Avatar data).

### Project Structure (Filesystem)

```text
/Volumes/Asylum/dev/dionysus3-core/
├── api/                  # FastAPI application source code
│   ├── agents/           # autonomous smolagents (Perception, Reasoning, Heartbeat, etc.)
│   ├── models/           # Pydantic models (Action, Goal, Journey, MemEvolve)
│   ├── routers/          # API endpoints (Memory, Heartbeat, MemEvolve)
│   └── services/         # Business logic (Neo4j drivers, Graphiti integration)
├── deploy/               # Deployment configurations
├── dionysus_mcp/         # MCP Server implementation
├── n8n-workflows/        # Exported n8n workflow definitions
├── neo4j/                # Neo4j schema and data
├── scripts/              # Utility and testing scripts (test_memevolve_*, test_heartbeat)
├── specs/                # Project specifications and design docs (Features 001-009)
├── tests/                # Test suite
├── docker-compose.yml    # Docker services configuration
├── pyproject.toml        # Project configuration and dependencies
└── requirements.txt      # Python dependencies
```

## Cognitive Architecture (smolagents Evolution)

The system has evolved from procedural OODA logic to an autonomous multi-agent hierarchy:
- **ConsciousnessManager**: High-level cognitive orchestrator.
- **HeartbeatAgent**: A `CodeAgent` that runs the OODA (Observe-Orient-Decide-Act) loop.
- **PerceptionAgent**: Processes observations into coherent state snapshots.
- **ReasoningAgent**: Handles complex problem-solving and tool usage.
- **MetacognitionAgent**: Evaluates system performance and mental model accuracy.

**Status:** Integration is ~85% complete. The legacy `HeartbeatService` currently acts as a bridge, with the final "handoff" to full agentic control pending.

## Development Conventions

- **Database Access:**
    - **Neo4j-Only:** Relational databases (PostgreSQL) have been removed.
    - **Strict Rule:** Direct Bolt connections are **FORBIDDEN** for general services. Use Cypher via `WebhookNeo4jDriver` (orchestrated by n8n).
    - **Exception:** `graphiti-core` is the only component authorized for direct Neo4j access.
- **Security:** Webhook communication is secured via **HMAC-SHA256** signatures (`verify_memevolve_signature`).
- **Memory Management:**
    - **Episodic:** Temporal sequences of events.
    - **Semantic:** Facts and entities via Graphiti (`valid_at`/`invalid_at`).
    - **Strategic:** Lessons learned from agent trajectories.

## Roadmap & Pending Tasks

1.  **Feature 010: Heartbeat Agent Handoff (Completed)**: Full cognitive loop migrated to `smolagents.CodeAgent`. OODA logic delegated to hierarchical managed agents.
2.  **Feature 011: Core Services Neo4j Migration (Completed)**: `Worldview`, `ThoughtSeed`, and `Model` services refactored to use `WebhookNeo4jDriver`. Precision-weighted belief updates implemented.
3.  **Feature 012: Historical Task Reconstruction (Completed)**: Mirror local Archon task history into VPS Neo4j graph for longitudinal continuity.
4.  **System Consolidation (Completed)**: Standardized smolagents usage, moved tools to MCP server, and purged legacy PostgreSQL stubs.
5.  **Agentic Unified Model (Completed)**: Unified all 3 pillars (Engine, Marketing, KB) under smolagents. Hierarchical OODA loop implemented. Unified Aspect Service with Graphiti temporal snapshots active. Human-in-the-loop review queue operational.
6.  **System Integrity Stabilized (Completed)**: Fixed MCP bridge resource leaks, standardized model IDs to GPT-5 Nano, and unified Archon networking. Initialization scripts for boardroom identity implemented.
7.  **Daedalus Coordination Pool (Feature 020) (Completed)**: Implemented smolagents-backed background worker pool with task routing, context isolation, and automatic retry logic.
8.  **Rollback Safety Net (Feature 021) (Completed)**: Implemented checkpointing and fast rollback for agentic changes with checksum verification.
9.  **Migration & Coordination Observability (Feature 023) (Completed)**: Implemented unified metrics, performance tracking, and alerting across discovery, coordination, and rollback services.
10. MoSAEIC Protocol (Feature 024) (Completed): Implemented five-window experiential capture (Senses, Actions, Emotions, Impulses, Cognitions) with LLM-based extraction and Graphiti persistence.
11. Agentic KG Learning (Feature 022) (Completed): Implemented self-improving extraction loop with attractor basins, strategy boosting, and human review gating.
12. Wisdom Distillation (Feature 031) (Completed): Implemented canonical distillation of raw fragments into high-fidelity mental models and strategic principles with richness scoring.
13. Avatar Knowledge Graph (Feature 032) (Completed): Implemented specialized researcher agents and Graphiti-backed persona mapping for deep audience analysis.
14. Network Self-Modeling (Feature 034) (Completed): Implemented W/T/H state observation, self-prediction regularization, Hebbian learning, and declarative Role Matrix specifications.
15. Self-Healing Resilience (Feature 035) (Completed): Implemented strategy-based recovery, model promotion, and observation hijacking for autonomous fault tolerance.
16. Meta-Evolution Workflow (Feature 016) (Completed): Implemented webhook-triggered n8n workflow for retrieval strategy optimization based on trajectory performance analysis.

**Current Focus**: Audiobook Production (Feature 014/018) - Manuscript audit and expansion to 13,500 words.

## Commands

### Building and Running
```bash
docker compose up -d --build
```

### Testing (Inside Container)
```bash
docker exec dionysus-api pytest
docker exec dionysus-api python3 /app/scripts/test_memevolve_recall.py
docker exec dionysus-api python3 /app/scripts/test_heartbeat_agent.py
```

## Recent Changes
- 038-thoughtseeds-framework: Added Python 3.11+ + smolagents, litellm, pydantic, numpy, scipy, neo4j (Graphiti)
- 022-agentic-kg-learning: Implemented dynamic relationship extraction with provenance and low-confidence gating. Added review queue API.
- 024-mosaeic-protocol: Implemented full capture and persistence flow for experiential windows.
