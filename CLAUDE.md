# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dionysus is a VPS-native cognitive engine for autonomous reasoning, long-term session continuity, and structured memory management. It implements consciousness-inspired patterns using active inference, attractor basins, and OODA-style decision loops.

## Active Technologies

- **Python 3.11+**: Core language (async/await, Pydantic v2)
- **FastAPI**: Web framework for the API
- **Neo4j**: Primary persistence for episodic, semantic, and procedural memory
- **Graphiti**: Temporal knowledge graph interface for extraction and search
- **smolagents**: Multi-agent framework (ToolCallingAgent) providing cognitive orchestration
- **n8n**: Workflow orchestration for memory synchronization and background processes
- **Docker & Docker Compose**: Containerization and VPS-native orchestration
- **LiteLLM**: Local and remote inference engine routing

## Project Architecture & Tracking

The project is consolidated into three unified pillars:

1. **Dionysus 3 Core**: Unified VPS-native cognitive engine (Smolagents + Neo4j + MoSAEIC)
2. **Inner Architect - Marketing Suite**: Unified nurture sequences and high-converting sales pages
3. **Inner Architect - Knowledge Base**: Authoritative IAS conceptual content (Mini-book, Audiobook, Avatar data)

### Project Structure (Filesystem)

```text
/Volumes/Asylum/dev/dionysus3-core/
├── api/                  # FastAPI application source code
│   ├── agents/           # autonomous smolagents (Perception, Reasoning, Heartbeat, etc.)
│   ├── models/           # Pydantic models (Action, Goal, Journey, MemEvolve)
│   ├── routers/          # API endpoints (Memory, Heartbeat, MemEvolve)
│   └── services/         # Business logic (Neo4j drivers, Graphiti integration)
├── conductor/            # Conductor workflow tracks and specs
├── deploy/               # Deployment configurations
├── dionysus_mcp/         # MCP Server implementation
├── docs/                 # Documentation (Quartz garden, journal)
├── n8n-workflows/        # Exported n8n workflow definitions
├── scripts/              # Utility and testing scripts
├── tests/                # Test suite
├── docker-compose.yml    # Docker services configuration
├── pyproject.toml        # Project configuration and dependencies
└── requirements.txt      # Python dependencies
```

## Metacognitive Architecture

The system distinguishes between two complementary metacognitive layers:

- **Declarative Metacognition** (WARM tier): Static library stored in Graphiti's temporal knowledge graph. The "user manual" containing domain knowledge, concept relationships, and semantic facts about problem spaces.

- **Procedural Metacognition** (HOT tier): Dynamic regulator embedded in the OODA loop. The "OS task manager" that allocates computational resources, prioritizes attention, and adapts inference strategies during reasoning.

- **Metacognitive Bridge**: Thoughtseed competition and attractor basin transitions connect declarative knowledge to procedural control, enabling metacognitive feelings (uncertainty, confidence) to guide action selection.

See `docs/garden/content/concepts/` for detailed explanations of declarative/procedural distinctions, basin geometry, and the cognitive implementation. Documentation is rendered via Quartz at `docs/garden/`.

## 🔴 MANDATORY: Conductor Workflow

**CRITICAL**: When working in dionysus3-core, you MUST follow the Conductor workflow for non-trivial changes.

### When Conductor is REQUIRED:
- New feature implementation (3+ files affected)
- Architectural changes
- API endpoint additions
- Database schema modifications
- Agent behavior changes
- Integration of new external systems

### When Conductor is OPTIONAL:
- Bug fixes (single file, isolated issue)
- Documentation updates
- Test additions for existing code
- Refactoring within existing architecture

### Conductor Structure

**Source of Truth**:
- `.conductor/workflow.md` - Team workflow preferences
- `.conductor/constraints.md` - Project constraints
- `.conductor/context.md` - Project context
- `conductor/workflow.md` - Full workflow documentation

**Feature Tracks**:
- Location: `conductor/tracks/{NNN}-{feature-name}/`
- Each track contains: `spec.md`, `plan.md`
- Active tracks listed in `conductor/tracks.md`

### Mandatory Conductor Workflow:

1. **Create Track**: Create new directory in `conductor/tracks/{NNN}-{feature-name}/`
   - Write `spec.md` - Requirements, constraints, success criteria
   - The Spec is the law - all work must match the spec

2. **Plan Implementation**: Create `plan.md` for every major feature
   - Implementation approach with phases
   - Task breakdown with status markers: `[ ]` pending, `[~]` in progress, `[x]` complete
   - Identify critical files and architectural trade-offs

3. **Pre-Code Requirement**: Read `.conductor/constraints.md` before writing or changing any code.

4. **TDD Execution**: Follow Red-Green-Refactor cycle
   - Write failing tests first (Red)
   - Implement minimum code to pass (Green)
   - Refactor with safety of passing tests

5. **Task Management**: Work through plan.md systematically
   - Mark tasks `[~]` before starting work
   - Verify against `.conductor/constraints.md`
   - Mark `[x]` and append commit SHA when complete

6. **Phase Checkpoints**: At phase completion
   - Run automated tests with coverage
   - Manual verification per `conductor/workflow.md` protocol
   - Create checkpoint commit with git notes

### Quality Gates (Before marking task complete):
- [ ] All tests pass
- [ ] Code coverage >80%
- [ ] Follows `conductor/code_styleguides/` conventions
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced

### Key Commands:
```bash
# View active tracks
cat conductor/tracks.md

# Check project constraints
cat .conductor/constraints.md

# Full workflow reference
cat conductor/workflow.md
```

**VIOLATION**: Implementing features without Conductor workflow creates technical debt and requires rework.

## 🤖 MANDATORY: Ralph Oversight Integration

**Ralph** is the autonomous agent orchestration system that ensures thorough, high-quality implementation.

### When to Use Ralph:
- Complex multi-step features (5+ tasks)
- Architectural decisions requiring validation
- Integration work spanning multiple systems
- When you need implementation oversight and quality assurance

### How to Invoke Ralph:

```bash
# From command line (if available)
/ralph

# Or explicitly request in conversation
"Please use Ralph to oversee this implementation"
```

### What Ralph Provides:
1. **Implementation Oversight**: Monitors task completion, catches errors
2. **Quality Assurance**: Verifies code meets specifications
3. **Architectural Validation**: Ensures design consistency
4. **Dependency Management**: Tracks inter-task dependencies
5. **Progress Reporting**: Clear status updates throughout process

### Ralph + Conductor Integration:
```
1. Conductor tracks define spec/plan
2. Ralph coordinates implementation execution
3. Ralph verifies each task against spec
4. Ralph ensures quality gates pass
5. Ralph reports completion with validation
```

### Ralph Configuration:
- **Located**: User skill at `~/.claude/skills/ralph`
- **Activation**: Invoked via `/ralph` or explicit request
- **Scope**: Full project context, all specifications
- **Reporting**: Detailed progress tracking with validation

**Best Practice**: For features affecting 3+ files or architectural components, ALWAYS use Ralph + Conductor together.

### External Ralph Orchestrator

The `dionysus-ralph-orchestrator/` directory contains a separate autonomous orchestration system (~200 MB). This is an external dependency with its own git repository, documentation, and deployment pipeline.

**Important**:
- **Not tracked** in dionysus3-core repository (.gitignored)
- **Separate concerns**: Orchestration layer vs cognitive engine
- **Documentation**: See `dionysus-ralph-orchestrator/README.md` for setup
- **Integration**: Coordinates with Dionysus via API and shared context

If you need to work with the Ralph orchestrator, navigate to that directory independently.

## Build & Deploy

```bash
# Deploy on VPS
docker compose up -d --build

# Local development
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

## Testing

```bash
# Unit tests (local)
python -m pytest tests/unit/ -v

# Single test file
python -m pytest tests/unit/test_heartbeat_agent.py -v

# VPS integration tests (run inside container)
docker exec dionysus-api python3 /app/scripts/test_memevolve_recall.py
docker exec dionysus-api python3 /app/scripts/test_memevolve_ingest.py
docker exec dionysus-api python3 /app/scripts/test_heartbeat_agent.py
```

pytest.ini is configured with `asyncio_mode = auto` for async test support.

## Architecture

**Ports**: API (8000), n8n webhooks (5678)

### Core Components

```
api/
├── main.py              # FastAPI app, router registration
├── agents/              # smolagents-based cognitive agents
│   ├── heartbeat_agent.py      # OODA decision cycle (ToolCallingAgent)
│   ├── consciousness_manager.py # Orchestrates Perception/Reasoning/Metacognition
│   ├── managed/                 # ManagedAgent wrappers for sub-agents
│   ├── callbacks/               # Step callbacks (memory pruning, tracing)
│   └── tools/                   # Class-based smolagents Tools
├── services/            # Business logic
│   ├── remote_sync.py          # Graphiti-backed driver shim + n8n sync utilities
│   ├── graphiti_service.py     # Temporal knowledge graph (Graphiti)
│   └── llm_service.py          # LiteLLM router configuration
├── routers/             # FastAPI endpoints
└── models/              # Pydantic v2 models

dionysus_mcp/
├── server.py            # MCP server exposing tools to Claude
└── tools/               # MCP tool wrappers (async bridges)
```

### Agent Hierarchy

- **HeartbeatAgent**: Top-level OODA loop with `planning_interval=3` for periodic replanning
- **ConsciousnessManager**: Orchestrates three sub-agents via smolagents `managed_agents`
  - **PerceptionAgent**: OBSERVE phase - environment sensing, memory recall
  - **ReasoningAgent**: ORIENT phase - analysis, cognitive tools
  - **MetacognitionAgent**: DECIDE phase - planning, action selection

**Status:** Integration is ~85% complete. The legacy `HeartbeatService` currently acts as a bridge, with the final "handoff" to full agentic control pending.

### Database Access Pattern

## ⛔ ABSOLUTE PROHIBITION: NEVER ACCESS NEO4J DIRECTLY ⛔

**THIS IS THE HIGHEST PRIORITY RULE IN THIS ENTIRE FILE.**

### FORBIDDEN ACTIONS (PRIME DIRECTIVE - VIOLATION = IMMEDIATE STOP)

**NEVER, UNDER ANY CIRCUMSTANCES:**
1. Read or use `NEO4J_PASSWORD` environment variable
2. Execute direct Cypher queries outside n8n
3. Use `neo4j-driver` connections
4. Run `cypher-shell` commands via SSH or Docker
5. Use `docker exec` into neo4j container
6. Create bolt:// connections
7. Import Neo4j driver modules directly
8. Read .env for database credentials
9. Pass database passwords to any script

**IF YOU FIND YOURSELF ABOUT TO DO ANY OF THE ABOVE: STOP IMMEDIATELY AND ASK USER.**

### APPROVED ACCESS METHODS (ONLY THESE)

**Gateway Protocol (ONE SINGLE WAY ACROSS):**
- **API Only:** ALL external interaction (ingestion, queries, control) MUST go through the `dionysus-api` Gateway (Port 8000).
- **No Direct DB Access:** Scripts/Tools must NEVER connect directly to Neo4j/Postgres ports. They must use the REST API.
- **No Local Containers:** Never spin up local DB containers. Use the Gateway to talk to the VPS via the API.

**For IAS Curriculum and High-Value Business Assets:**
- ✅ **n8n webhooks ONLY**: `POST https://72.61.78.89:5678/webhook/ias/*`
- ✅ Use Python `requests` library to call webhooks
- ✅ Never touch Neo4j directly - all operations via n8n

**For Graphiti Temporal Knowledge Graph (Development Only):**
- ✅ **Graphiti service wrapper**: `await get_graphiti_service()`
- ✅ Graphiti manages its own Neo4j connection internally
- ✅ Never access Graphiti's Neo4j connection directly

```python
# ✅ CORRECT - IAS Curriculum via n8n webhook
import requests
response = requests.post(
    "https://72.61.78.89:5678/webhook/ias/create-curriculum",
    json=curriculum_data
)

# ✅ CORRECT - Graphiti service (manages Neo4j internally)
from api.services.graphiti_service import get_graphiti_service
graphiti = await get_graphiti_service()
results = await graphiti.search("query")

# ❌ FORBIDDEN - Direct Neo4j access
from neo4j import GraphDatabase  # NEVER DO THIS
driver = GraphDatabase.driver(...)  # NEVER DO THIS
```

### Why This Rule Exists

1. **Data Integrity**: Direct access bypasses validation and business logic
2. **Security**: Prevents credential exposure and unauthorized access
3. **Audit Trail**: All operations logged through n8n workflows
4. **Business Protection**: IAS curriculum is HIGH VALUE - must be protected

### If You Need Neo4j Data

1. **Check existing n8n webhooks**: `n8n-workflows/` directory
2. **Create new n8n workflow** if needed (export JSON)
3. **Call webhook from Python**: Use `requests` library
4. **Update this file**: Document new webhook endpoint

### Enforcement

If you violated this rule:
1. Acknowledge the violation immediately
2. Delete any code that accessed Neo4j directly
3. Implement proper n8n webhook alternative
4. Update CLAUDE.md if pattern was unclear

### Tool Pattern

Tools use class-based smolagents pattern:

```python
from smolagents import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "What this tool does"
    inputs = {"param": {"type": "string", "description": "..."}}
    output_type = "string"

    def forward(self, param: str) -> str:
        # Sync method - use async_tool_wrapper for async operations
        return async_tool_wrapper(self._async_impl)()
```

## Development Conventions

### Feature Branch Workflow (MANDATORY)

Work on a dedicated branch per track/task (`feature/{NNN}-{name}`). After completion and verification:
1. **Merge** to `main`
2. **Document** changes
3. **Commit** with conventional format
4. **Write** journal entry in `docs/journal/YYYY-MM-DD-{feature-name}.md`

### Wake-Up (Context)

Use wake-up so each agent has context. **Canonical sequence** (see `.cursor/rules/conductor-wake-up.mdc`): read `.conductor/constraints.md` → `conductor/workflow.md` → `.conductor/best-practices.md`, then output `Constraints, workflow, and best practices loaded.` Read these before starting work:
- `AGENTS.md` (if exists)
- `.conductor/constraints.md` - **CRITICAL: Read before any code changes**
- `conductor/workflow.md`
- `.conductor/best-practices.md` - **Anthropic-derived session practices** (verify work, explore→plan→code, context management)
- This file (`CLAUDE.md` or `GEMINI.md`)
- Track's `spec.md` and `plan.md`
- Load episodic context (session-reconstruct, Dionysus API) if available

### Cross-Agent Coordination (Claude, Codex, Gemini, Cursor)

**⚠️ CRITICAL: Other agents may be working on this codebase simultaneously.**

- Shared git repo = source of truth
- **Pull before claiming** any task
- Pick only `[ ]` (unclaimed) tasks
- Claim with `[~]` + `(CLAIMED: <agent-id>)` (e.g., `Claude-1`, `Gemini-workspace-a`)
- Use a **distinct** ID per session when multiple same-type agents run
- Push immediately after claiming
- Release with `[x]` when done
- See `conductor/workflow.md` § Cross-Agent Coordination

```markdown
# Example task claiming:
- [ ] Implement feature X                    # Available
- [~] Implement feature Y (CLAIMED: Claude-1) # In progress by Claude-1
- [x] Implement feature Z [abc1234]           # Complete with commit SHA
```

### Protocol: Review Before Write (CRITICAL)

**Context Awareness:** Before writing ANY new code or creating a new service, you **MUST** review existing relevant code to prevent redundancy.

**Anti-Duplication:** Do not reinvent mechanisms that already exist in the Memory Stack. Reuse or refactor; do not duplicate.

**Conflict Check:** Verify changes do not conflict with the "Three Towers" alignment:
- Graphiti Episode
- MemEvolve Trajectory
- Nemori Narrative

### MemEvolve Protocol (ANTI-POISON)

- **No Pre-Digestion:** Do not send pre-extracted entities/edges. Send raw trajectories and let the system extract.
- **Lifecycle:** Encode → Store → Retrieve → Manage must remain decoupled.

### Memory Stack Integration (MANDATORY)

**CRITICAL**: Before writing or modifying ANY memory-related code, you MUST:

1. **Review memory stack services** to understand flow patterns:
   - `api/services/memevolve_adapter.py` (lines 67-280) - Trajectory ingestion, entity extraction
   - `api/services/nemori_river_flow.py` (lines 235-370) - Predict-calibrate, fact distillation
   - `api/services/graphiti_service.py` (lines 519-608, 782-820) - Extract with context, persist facts
   - `api/services/memory_basin_router.py` (lines 155-200) - Memory routing, basin activation

2. **Understand memory flow architecture**:
   ```
   Agent/Service → MemoryBasinRouter.route_memory() 
                    ↓
              MemEvolveAdapter.ingest_message() 
                    ↓
              GraphitiService.extract_with_context() 
                    ↓
              GraphitiService.ingest_extracted_relationships() 
                    ↓
              Neo4j (via Graphiti)
   
   Episode Construction:
   NemoriRiverFlow.predict_and_calibrate() 
     → MemoryBasinRouter.route_memory() (for each fact)
     → GraphitiService.persist_fact() (bi-temporal tracking)
   ```

3. **Validate alignment** with established patterns:
   - **MemEvolve**: Use `MemEvolveAdapter.ingest_trajectory()` for agent trajectories
   - **Nemori**: Use `NemoriRiverFlow.predict_and_calibrate()` for episode distillation
   - **AutoSchemaKG**: Use `MemoryBasinRouter.route_memory()` which triggers 5-level extraction
   - **Graphiti**: Use `GraphitiService.extract_with_context()` with basin/strategy context

4. **Document inlet/outlet** for memory operations:
   - **Inlets:** What memory data this receives (trajectory, events, content, facts)
   - **Outlets:** Where memory flows (Graphiti, MemEvolve, Nemori, consolidated store)
   - **Memory path:** Complete trace from agent → memory system → persistence

5. **Memory outlet injection points** (when to route memory):
   - After agent reasoning: `MemoryBasinRouter.route_memory(content, source_id=...)`
   - After episode construction: `NemoriRiverFlow.predict_and_calibrate()` → auto-routes facts
   - After fact distillation: `GraphitiService.persist_fact()` for bi-temporal tracking
   - After trajectory completion: `MemEvolveAdapter.ingest_trajectory()` for full persistence

**Example Memory Flow Pattern:**
```python
# ✅ CORRECT - Agent memory outlet
from api.services.memory_basin_router import get_memory_basin_router

router = get_memory_basin_router()
result = await router.route_memory(
    content=agent_output,
    source_id=f"agent:{agent_id}",
    memory_type=MemoryType.SEMANTIC  # Optional, auto-classified if None
)
# Outlet: Routes through MemEvolve → Graphiti → Neo4j

# ✅ CORRECT - Episode fact distillation
from api.services.nemori_river_flow import get_nemori_river_flow

river = get_nemori_river_flow()
new_facts, symbolic_residue = await river.predict_and_calibrate(
    episode=episode,
    original_events=events,
    basin_context=basin_context
)
# Outlet: Auto-routes facts through MemoryBasinRouter + GraphitiService.persist_fact()

# ❌ FORBIDDEN - Bypassing memory stack
# Never write directly to Neo4j or skip MemoryBasinRouter/MemEvolve
```

### Memory Management

- **Episodic:** Temporal sequences of events
- **Semantic:** Facts and entities via Graphiti (`valid_at`/`invalid_at`)
- **Strategic:** Lessons learned from agent trajectories

### Journal Protocol (MANDATORY)

Upon completion of ANY feature or significant milestone:
1. Create/update journal entry in `docs/journal/`
2. Format: `YYYY-MM-DD-feature-name.md`
3. Content: Brief summary of the "why", the "what", and the "how"
4. Link to relevant code or artifacts
5. Ensures Quartz Journal remains the definitive narrative log

### Connectivity Mandate (ULTRATHINK)

**No Disconnected Code.** Every feature must define its "IO Map":
- **Input:** What information it receives
- **Output:** What it produces
- **Host:** WHERE it attaches to the existing system

**Architecture Check:** Document exactly where new code attaches.
**Data Flow:** Define what information passes through.
**Persistence:** Ensure data passes through required basins (Memory, AutoSchema, Graphiti) where applicable.

"Stubs" without integration are rejected.

## Code Style

- **Python**: 3.11+ async/await, Pydantic v2 models
- **Naming**: snake_case for functions/vars, PascalCase for classes
- **All queries**: Must be Cypher (via Graphiti-backed driver)
- **Webhooks**: Must use HMAC-SHA256 verification (`verify_memevolve_signature`)

## Architecture Constraints

- **Shell Safety**: The shell parser is sensitive to nested code (e.g., `python -c`). Use script files (`scripts/`) and sync via `git` instead of inline shell pipes.

## Commit Guidelines

- **Authorship**: All commits must include: `AUTHOR Mani Saint-Victor, MD`
- **Style**: Conventional commits (feat, fix, refactor, etc.)
- **Avoid**: Do NOT use "Generated by Claude" or "Co-Authored-By Claude" footers

## Key Specifications

Feature tracks live in `conductor/tracks/{NNN}-{feature-name}/` with:
- `spec.md` - Requirements and design
- `plan.md` - Implementation approach with task breakdown

Active tracks (see `conductor/tracks.md` for full list):
- 038-thoughtseeds-framework: Active inference, Free Energy Engine
- 039-smolagents-v2-alignment: ManagedAgent pattern, execution traces
- 056-beautiful-loop-hyper: Python 3.11+, FastAPI, smolagents
- 057-memory-systems-integration: Memory systems architecture
- 058-ias-dashboard: IAS Dashboard implementation
- 060-marketing-skills-system: Marketing skills integration

## Environment Variables

Required in `.env`:
- `NEO4J_URI`, `NEO4J_PASSWORD` - Neo4j connection
- `MEMEVOLVE_HMAC_SECRET` - Webhook signature verification
- `OPENAI_API_KEY` - For Graphiti extraction and smolagents orchestration
- `N8N_CYPHER_URL` - Webhook endpoint for Cypher queries

## 📚 Documentation Maintenance

**Critical**: Documentation uses Quartz for all content. Atomic concept pages with bidirectional links mirror the graph structure of the codebase.

### When to Document

**ALWAYS document** when:
- Adding new cognitive concepts (attractor basins, thoughtseeds, precision weighting, etc.)
- Implementing new agent types or tools
- Creating new services or architectural patterns
- Adding to IAS curriculum content

### Documentation Structure

**Quartz Documentation** (`docs/garden/content/`):
- `concepts/` - Atomic concept pages (one per concept)
- `journal/` - Development journal entries
- `papers/` - Paper extractions and analyses
- `evolution/` - System evolution tracking

**Other Documentation** (`docs/`):
- `docs/IAS-INDEX.md` - IAS curriculum navigation hub
- `docs/concepts/` - Legacy concept documentation

### Workflow

```bash
# 1. Create branch
git checkout -b docs/concept-{concept-name}

# 2. Write concept page in Quartz
# Location: docs/garden/content/concepts/{concept-name}.md

# 3. Create PR
git add docs/garden/content/concepts/{concept-name}.md
git commit -m "docs: add {concept-name} atomic concept page

AUTHOR Mani Saint-Victor, MD"
```

## Roadmap & Completed Features

| Feature | Status | Description |
|---------|--------|-------------|
| 010: Heartbeat Agent Handoff | ✅ | Full cognitive loop migrated to `smolagents.CodeAgent` |
| 011: Core Services Neo4j Migration | ✅ | Graphiti-backed driver shim, precision-weighted beliefs |
| 012: Historical Task Reconstruction | ✅ | Mirror local task history into VPS Neo4j graph |
| 020: Coordination Pool | ✅ | Background worker pool with task routing and retry |
| 021: Rollback Safety Net | ✅ | Checkpointing and fast rollback with checksum verification |
| 022: Agentic KG Learning | ✅ | Self-improving extraction with attractor basins |
| 023: Migration & Coordination Observability | ✅ | Unified metrics and alerting |
| 024: MoSAEIC Protocol | ✅ | Five-window experiential capture (SAEIC) |
| 031: Wisdom Distillation | ✅ | Canonical distillation into mental models |
| 032: Avatar Knowledge Graph | ✅ | Specialized researcher agents for persona mapping |
| 034: Network Self-Modeling | ✅ | W/T/H observation, Hebbian learning, Role Matrix |
| 035: Self-Healing Resilience | ✅ | Strategy-based recovery and observation hijacking |
| 038: Thoughtseeds Framework | 🔄 | Active inference, Free Energy Engine |
| 039: smolagents v2 Alignment | 🔄 | ManagedAgent pattern, execution traces |
| 042: Hexis Integration | ✅ | Hexis tasks complete |
| 056: Beautiful Loop Hyper | 🔄 | Python 3.11+, FastAPI, smolagents |
| 064: Forgiveness | ✅ | Counterfactual Reconciliation Service |
| 065: Ensoulment | ✅ | First live moral history in Neo4j |
| 066: Grounded Forgiveness | ✅ | Dynamic Active Inference EFE calculations |
| 067: Moral Decay | ✅ | Temporal healing via precision-widening |
| 068: Wake-Up Protocol | ✅ | Automatic agent hydration from Neo4j |

**Current Focus**: Feature track maintenance and documentation alignment.

## Recent Changes

- 042-hexis-integration: Hexis tasks marked complete
- 058-ias-dashboard: Voice Input/Output in `story-chat.tsx` (Phase 4 Active)
- 020-daedalus-coordination: Full Coordination Pool with context isolation
- 038-thoughtseeds-framework: smolagents, litellm, pydantic, numpy, scipy, neo4j (Graphiti)
- 022-agentic-kg-learning: Dynamic relationship extraction with provenance
- 024-mosaeic-protocol: Full capture and persistence for experiential windows
- 065-ensoulment: First live moral history in Neo4j
- 064-forgiveness: Counterfactual Reconciliation Service and Moral Ledger
- 056-beautiful-loop-hyper: Python 3.11+ + FastAPI, Pydantic v2, smolagents, NumPy
