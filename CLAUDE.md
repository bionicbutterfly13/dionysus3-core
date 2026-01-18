# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dionysus is a VPS-native cognitive engine for autonomous reasoning, long-term session continuity, and structured memory management. It implements consciousness-inspired patterns using active inference, attractor basins, and OODA-style decision loops.

## Metacognitive Architecture

The system distinguishes between two complementary metacognitive layers:

- **Declarative Metacognition** (WARM tier): Static library stored in Graphiti's temporal knowledge graph. The "user manual" containing domain knowledge, concept relationships, and semantic facts about problem spaces.

- **Procedural Metacognition** (HOT tier): Dynamic regulator embedded in the OODA loop. The "OS task manager" that allocates computational resources, prioritizes attention, and adapts inference strategies during reasoning.

- **Metacognitive Bridge**: Thoughtseed competition and attractor basin transitions connect declarative knowledge to procedural control, enabling metacognitive feelings (uncertainty, confidence) to guide action selection.

See `docs/silver-bullets/` for detailed explanations of declarative/procedural distinctions, basin geometry, and the cognitive implementation.

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

3. **TDD Execution**: Follow Red-Green-Refactor cycle
   - Write failing tests first (Red)
   - Implement minimum code to pass (Green)
   - Refactor with safety of passing tests

4. **Task Management**: Work through plan.md systematically
   - Mark tasks `[~]` before starting work
   - Verify against `.conductor/constraints.md`
   - Mark `[x]` and append commit SHA when complete

5. **Phase Checkpoints**: At phase completion
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

## 📚 Documentation Maintenance - Silver Bullets Pattern

**Critical**: Documentation follows the "silver bullets" pattern - atomic concept pages with bidirectional links that mirror the graph structure of the codebase.

### When to Document

**ALWAYS document** when:
- Adding new cognitive concepts (attractor basins, thoughtseeds, precision weighting, etc.)
- Implementing new agent types or tools
- Creating new services or architectural patterns
- Adding to IAS curriculum content

### Documentation Pattern

**Silver Bullets Structure**:
- `docs/silver-bullets/` - Main documentation hub
- `docs/silver-bullets/00-INDEX.md` - Navigation index (always update)
- `docs/silver-bullets/concepts/` - Atomic concept pages (one per concept)
- `docs/IAS-INDEX.md` - IAS curriculum navigation hub

**Atomic Concept Template**: See `docs/DOCUMENTATION-AGENT-GUIDE.md`

### Parallel Documentation Agents

Agents can work in parallel on documentation:

**Agent Roles**:
1. **Concept Extractor**: Identify undocumented concepts from code
2. **Atomic Writer**: Create individual concept pages
3. **Link Weaver**: Ensure bidirectional links
4. **Index Curator**: Maintain navigation indexes
5. **Code Linker**: Add implementation references
6. **Visualization Builder**: Create interactive diagrams

**Workflow**:
```bash
# 1. Check backlog
cat docs/DOCUMENTATION_BACKLOG.md

# 2. Claim task
# Update backlog: (AVAILABLE) → (CLAIMED: AgentName, Branch: docs/concept-{name})

# 3. Create branch
git checkout -b docs/concept-{concept-name}

# 4. Write concept page following template
# See docs/DOCUMENTATION-AGENT-GUIDE.md for full template

# 5. Create PR
git add docs/silver-bullets/concepts/{concept-name}.md
git commit -m "docs: add {concept-name} atomic concept page

AUTHOR Mani Saint-Victor, MD"
```

**Branch Naming**:
- Concept pages: `docs/concept-{concept-name}`
- Link updates: `docs/links-{concept-name}`
- Index updates: `docs/index-update`
- Visualizations: `docs/viz-{topic}`

**Conflict Avoidance**:
- Only ONE agent per concept file at a time
- Link Weaver waits for Atomic Writer to merge
- Index Curator waits for batch completion

**Integration with Ralph**:
```bash
# Spawn parallel documentation team
/ralph spawn-docs-team --concepts "precision-weighting,basin-stability,selective-attention"
```

**Complete Guide**: `docs/DOCUMENTATION-AGENT-GUIDE.md`
**Backlog**: `docs/DOCUMENTATION_BACKLOG.md`

## Active Technologies
- Python 3.11+ + FastAPI, Pydantic v2, smolagents, NumPy (056-beautiful-loop-hyper)
- Graphiti temporal knowledge graph (via GraphitiService) (056-beautiful-loop-hyper)

## Recent Changes
- 056-beautiful-loop-hyper: Added Python 3.11+ + FastAPI, Pydantic v2, smolagents, NumPy
