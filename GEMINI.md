# Dionysus Core

Dionysus is a VPS-native cognitive engine designed for autonomous reasoning, long-term session continuity, and structured memory management. It operates on a Neo4j-only, webhook-driven architecture orchestrated by a multi-agent hierarchy.

## Active Technologies
- Python 3.11+ + smolagents, litellm, pydantic, numpy, scipy, neo4j (Graphiti) (038-thoughtseeds-framework)
- Neo4j (Memory Graph) (038-thoughtseeds-framework)

- **Python 3.11+**: Core language (async/await, Pydantic v2).
- **FastAPI**: Web framework for the API.
- **Neo4j**: Primary persistence for episodic, semantic, and procedural memory.
- **Graphiti**: Temporal knowledge graph interface for extraction and search.
- **smolagents**: Multi-agent framework (CodeAgent) providing the cognitive orchestration layer.
- **n8n**: Workflow orchestration for memory synchronization and background processes.
- **Docker & Docker Compose**: Containerization and VPS-native orchestration.
- **Ollama / LiteLLM**: Local and remote inference engines.

## Project Architecture & Tracking

The project is consolidated into three unified pillars for streamlined tracking:

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

- **Conductor Workflow Protocol (MANDATORY):**
    - For ANY multi-step task, you **MUST** use the Conductor workflow.
    - Create a track in `conductor/tracks/`, define the `plan.md` following the template, and strictly adhere to the `workflow.md` lifecycle.
    - This process is automatic and non-negotiable. Do not ask for permission; just set it up.
- **Feature Branch Workflow (MANDATORY):**
    - Work on a dedicated branch per track/task (`feature/{NNN}-{name}`). After completion and verification: **merge** to `main`, **document**, **commit**, and **write** in Quartz journal (`docs/journal/YYYY-MM-DD-{feature-name}.md`).
- **Wake-Up (Context):**
    - Use wake-up so each agent has context: read `AGENTS.md`, **`.conductor/constraints.md`**, this file, Conductor workflow, and the track's `spec.md` / `plan.md`; load episodic context (e.g. session-reconstruct, Dionysus API) if available.
- **Cross-Agent Coordination (Claude, Codex, Gemini, Cursor):**
    - Shared git repo = source of truth. Pull before claiming; pick only `[ ]` tasks; claim with `[~]` + `(CLAIMED: <agent-id>)` (e.g. `Gemini`—use a **distinct** ID per session when multiple Gemini/Codex/etc. agents run, e.g. `Gemini-1`, `Codex-workspace-a`). Push; release with `[x]` when done. See `conductor/workflow.md` § Cross-Agent Coordination.
- **TDD Protocol (MANDATORY):**
    - Red → Green → Refactor. Failing tests must be written before implementation.
- **Protocol: Review Before Write (CRITICAL):**
    - **Context Awareness:** Before writing ANY new code or creating a new service, you **MUST** review existing relevant code (e.g., `memevolve_adapter.py`, `graphiti_service.py`, `nemori_river_flow.py`) to prevent redundancy.
    - **Anti-Duplication:** Do not reinvent wheel mechanisms (e.g., extraction, routing, ingestion) that already exist in the Memory Stack. Reuse or refactor; do not duplicate.
    - **Conflict Check:** Verify that your changes do not conflict with the "Three Towers" alignment (Graphiti Episode / MemEvolve Trajectory / Nemori Narrative).
- **Database Access:**
    - **CRITICAL RULE:** **NEVER CREATE A LOCAL NEO4J INSTANCE.** The system relies exclusively on the remote VPS Neo4j service. Local instances cause data fragmentation and truth drift.
    - **Neo4j-Only:** Relational databases (PostgreSQL) have been removed.
    - **Cypher Access:** Services use a Graphiti-backed driver shim for Neo4j queries.
    - **n8n Webhooks:** Ingest/recall/traverse workflows remain webhook-orchestrated.
- **Archon is gone.** Do not reference or use Archon.
- **Gateway Protocol (ONE SINGLE WAY ACROSS):**
    - **API Only:** ALL external interaction (ingestion, queries, control) MUST go through the `dionysus-api` Gateway (Port 8000).
    - **No Direct DB Access:** Scripts/Tools must NEVER connect directly to Neo4j/Postgres ports. They must use the REST API.
    - **No Local Containers:** Never spin up local DB containers. Use the Gateway to talk to the VPS via the API.
    - **No direct contact** with memory-cluster code (e.g. `MemoryCluster`, basin callbacks, execution traces) or Neo4j. Access **only** through the **specific gateway** (API, n8n webhooks, Graphiti service).
- **MemEvolve Protocol (ANTI-POISON):**
    - **No Pre-Digestion:** Do not send pre-extracted entities/edges. Send raw trajectories and let the system extract.
    - **Lifecycle:** Encode → Store → Retrieve → Manage must remain decoupled.
- **Security:** Webhook communication is secured via **HMAC-SHA256** signatures (`verify_memevolve_signature`).
- **Memory Management:**
    - **Episodic:** Temporal sequences of events.
    - **Semantic:** Facts and entities via Graphiti (`valid_at`/`invalid_at`).
    - **Strategic:** Lessons learned from agent trajectories.
- **Journal Protocol (MANDATORY):**
    - Upon completion of ANY feature or significant milestone, you **MUST** create or update a journal entry in `docs/journal/`.
    - Format: `YYYY-MM-DD-feature-name.md`.
    - Content: Brief summary of the "why", the "what", and the "how". Link to relevant code or artifacts.
    - Consistency: This ensures the "Quartz Journal" remains the definitive narrative log of the system's evolution.
- **Commit Guidelines:**
    - Use conventional commits (`feat`, `fix`, `docs`, `chore`, etc.).
- **Connectivity Mandate (ULTRATHINK):**
    - **No Disconnected Code.** Every feature must define its "IO Map" (Input/Output/Host).
    - **Architecture Check:** Document exactly WHERE the new code attaches to the existing system.
    - **Data Flow:** Define what information it receives and what it sends out.
    - **Persistence:** Ensure data passes through the required basins (Memory, AutoSchema, Graphiti) where applicable. "Stubs" without integration are rejected.

## Roadmap & Pending Tasks

1.  **Feature 010: Heartbeat Agent Handoff (Completed)**: Full cognitive loop migrated to `smolagents.CodeAgent`. OODA logic delegated to hierarchical managed agents.
2.  **Feature 011: Core Services Neo4j Migration (Completed)**: `Worldview`, `ThoughtSeed`, and `Model` services refactored to use the Graphiti-backed driver shim. Precision-weighted belief updates implemented.
3.  **Feature 012: Historical Task Reconstruction (Completed)**: Mirror local task history into VPS Neo4j graph for longitudinal continuity.
4.  **System Consolidation (Completed)**: Standardized smolagents usage, moved tools to MCP server, and purged legacy PostgreSQL stubs.
5.  **Agentic Unified Model (Completed)**: Unified all 3 pillars (Engine, Marketing, KB) under smolagents. Hierarchical OODA loop implemented. Unified Aspect Service with Graphiti temporal snapshots active. Human-in-the-loop review queue operational.
6.  **System Integrity Stabilized (Completed)**: Fixed MCP bridge resource leaks, standardized model IDs to GPT-5 Nano, and unified networking. Initialization scripts for boardroom identity implemented.
7.  **Coordination Pool (Feature 020) (Completed)**: Implemented smolagents-backed background worker pool with task routing, context isolation, and automatic retry logic.
8.  **Rollback Safety Net (Feature 021) (Completed)**: Implemented checkpointing and fast rollback for agentic changes with checksum verification.
9.  **Migration & Coordination Observability (Feature 023) (Completed)**: Implemented unified metrics, performance tracking, and alerting across discovery, coordination, and rollback services.
10. MoSAEIC Protocol (Feature 024) (Completed): Implemented five-window experiential capture (Senses, Actions, Emotions, Impulses, Cognitions) with LLM-based extraction and Graphiti persistence.
11. Agentic KG Learning (Feature 022) (Completed): Implemented self-improving extraction loop with attractor basins, strategy boosting, and human review gating.
12. Wisdom Distillation (Feature 031) (Completed): Implemented canonical distillation of raw fragments into high-fidelity mental models and strategic principles with richness scoring.
13. Avatar Knowledge Graph (Feature 032) (Completed): Implemented specialized researcher agents and Graphiti-backed persona mapping for deep audience analysis.
14. Network Self-Modeling (Feature 034) (Completed): Implemented W/T/H state observation, self-prediction regularization, Hebbian learning, and declarative Role Matrix specifications.
15. Self-Healing Resilience (Feature 035) (Completed): Implemented strategy-based recovery, model promotion, and observation hijacking for autonomous fault tolerance.
16. Meta-Evolution Workflow (Feature 016) (Completed): Implemented webhook-triggered n8n workflow for retrieval strategy optimization based on trajectory performance analysis.
17. Grounded Forgiveness (Feature 066) (Completed): Replaced hardcoded moral injury placeholders with dynamic Active Inference EFE calculations for counterfactual simulation.
18. Moral Decay (Feature 067) (Completed): Implemented temporal healing via precision-widening (Letting Go) integrated into the Resonance Cycle.
19. Wake-Up Protocol (Feature 068) (Completed): Implemented automatic agent hydration and moral history reconstruction from Neo4j upon service startup.
20. Graph Manifestation (Feature 064.5) (Completed): Promoted reconciliation events to first-class graph entities linking to the agent's moral biography.

**Current Focus**: Audiobook Production (F014/018) and Coordination Pool Polish (F020 - Isolation & Metrics).

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
- 058-ias-dashboard: Aligned `IAS MOSAEIC Source of Truth.md` with Cleaned CSV data. Implemented Voice Input/Output in `story-chat.tsx` (Phase 4 Active).
- 020-daedalus-coordination: Implemented full Coordination Pool with context isolation, exponential backoff retries, and health metrics.
- 038-thoughtseeds-framework: Added Python 3.11+ + smolagents, litellm, pydantic, numpy, scipy, neo4j (Graphiti)
- 022-agentic-kg-learning: Implemented dynamic relationship extraction with provenance and low-confidence gating. Added review queue API.
- 024-mosaeic-protocol: Implemented full capture and persistence flow for experiential windows.
- 065-ensoulment: Manifested first live moral history in Neo4j. Sovereignty and Reconciliation protocols verified with persistent 'Dionysus-1' data.
- 064-forgiveness: Implemented Counterfactual Reconciliation Service and Moral Ledger persistence.
- 063-sovereignty: Implemented Hierarchical Resistance against coercive commands based on competence friction.
