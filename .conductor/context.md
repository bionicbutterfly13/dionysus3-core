# Project Context: Dionysus 3.0 Core

## Project Overview
**Type**: Brownfield / Migration (Dionysus 2.0 -> 3.0)
**Primary Goal**: Establish a VPS-native cognitive engine for autonomous reasoning, long-term session continuity, and structured memory management using a Neo4j-only architecture.
**Target Users**: The Architect (Developer/User), The Analytical Empath (Avatar), Managed Agents.

## Architecture Overview
### Tech Stack
- **Languages**: Python 3.11+
- **Frameworks**: FastAPI (API), smolagents (Agent Orchestration), Graphiti (Graph RAG)
- **Database**: Neo4j (Graph Only - No Relational DB)
- **Infrastructure**: VPS (Docker Compose), n8n (Workflow Orchestration), Ollama/LiteLLM (Inference)

### Key Components
1.  **ConsciousnessManager**: High-level cognitive orchestrator.
2.  **HeartbeatAgent**: Runs the OODA loop (Observe-Orient-Decide-Act).
3.  **Memory Systems**:
    - **Episodic**: Time-series events (Neo4j).
    - **Semantic**: Knowledge graph (Graphiti).
    - **Procedural**: Action history and skills.
4.  **Coordination Pool**: Background worker pool for async tasks.
5.  **Serena MCP**: Metacognitive interface for creating/searching memories.

### Critical Dependencies
- **Neo4j**: Primary source of truth for all memory and state.
- **n8n**: Orchestrates complex memory ingestion and biological simulation workflows.
- **Graphiti**: Layer for temporal knowledge graph interactions.

## Project Guidelines
### Code Standards
- **Style**: Pythonic, localized imports to avoid circular dependencies.
- **Testing**: `pytest` for unit/integration.
- **Documentation**: Markdown-based specs in `specs/`.

### Architecture Principles
- **No SQL**: Strictly graph-based persistence.
- **Agentic First**: Logic resides in Agents/Tools, not just Services.
- **Ultrathink**: Architectural decisions prioritize depth, resonance, and system sovereignty.

## Current Focus
**Active Track**: Feature 058 - IAS Experience Dashboard
**Status**: Phase 4 (Final Polish)
**Goals**:
1.  **Voice UI**: Implemented `SpeechRecognition`/`Synthesis` in `story-chat.tsx`. Verified build.
2.  **Data Alignment**: `IAS MOSAEIC Source of Truth.md` is strictly aligned with the `CleanedFormat.csv`.
3.  **Deployment**: Preparing for final VPS deployment.
