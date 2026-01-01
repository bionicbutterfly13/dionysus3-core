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

## 🔴 MANDATORY: SpecKit Best Practices

**CRITICAL**: When working in dionysus3-core, you MUST follow SpecKit workflow for non-trivial changes.

### When SpecKit is REQUIRED:
- New feature implementation (3+ files affected)
- Architectural changes
- API endpoint additions
- Database schema modifications
- Agent behavior changes
- Integration of new external systems

### When SpecKit is OPTIONAL:
- Bug fixes (single file, isolated issue)
- Documentation updates
- Test additions for existing code
- Refactoring within existing architecture

### Mandatory SpecKit Workflow:

1. **Specify First**: Use `/speckit.specify` to create feature specification
   - Generates: `specs/{NNN}-{feature-name}/spec.md`
   - Creates feature branch: `{NNN}-{feature-name}`
   - Captures requirements, constraints, success criteria

2. **Clarify Ambiguities**: Use `/speckit.clarify` if requirements unclear
   - Asks targeted questions
   - Updates spec.md with answers
   - Prevents implementation mistakes

3. **Plan Implementation**: Use `/speckit.plan` to generate design
   - Generates: `specs/{NNN}-{feature-name}/plan.md`
   - Identifies critical files
   - Considers architectural trade-offs

4. **Generate Tasks**: Use `/speckit.tasks` to create task breakdown
   - Generates: `specs/{NNN}-{feature-name}/tasks.md`
   - Dependency-ordered task list
   - Status tracking per task

5. **Implement**: Work through tasks.md systematically
   - Use TodoWrite to track progress
   - Mark tasks as in_progress/completed
   - Update plan.md if approach changes

6. **Analyze**: Use `/speckit.analyze` after task generation
   - Cross-artifact consistency check
   - Quality analysis
   - Identifies gaps/conflicts

### Verification Checklist:
- [ ] Spec created before implementation
- [ ] Plan reviewed and approved
- [ ] Tasks generated and ordered
- [ ] Implementation matches spec
- [ ] Tests cover acceptance criteria
- [ ] Documentation updated

**VIOLATION**: Implementing features without SpecKit workflow creates technical debt and requires rework.

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

### Ralph + SpecKit Integration:
```
1. SpecKit generates spec/plan/tasks
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

**Best Practice**: For features affecting 3+ files or architectural components, ALWAYS use Ralph + SpecKit together.

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

**CRITICAL**: Cypher access is Graphiti-backed (direct Neo4j). n8n webhooks are used for sync pipelines.

```python
# Correct - use Graphiti-backed driver shim
from api.services.remote_sync import get_neo4j_driver
driver = get_neo4j_driver()
result = await driver.execute_query(cypher, params)

# Graphiti service for temporal KG operations
from api.services.graphiti_service import get_graphiti_service
```

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

Feature specs live in `specs/{NNN}-{feature-name}/` with:
- `spec.md` - Requirements and design
- `plan.md` - Implementation approach
- `tasks.md` - Task breakdown with status

Active features:
- 038-thoughtseeds-framework: Active inference, Free Energy Engine
- 039-smolagents-v2-alignment: ManagedAgent pattern, execution traces
- 041-meta-tot-engine: MCTS-based reasoning with active inference
- 042-cognitive-tools-upgrade: D2-validated reasoning tools

## Environment Variables

Required in `.env`:
- `NEO4J_URI`, `NEO4J_PASSWORD` - Neo4j connection
- `MEMEVOLVE_HMAC_SECRET` - Webhook signature verification
- `ANTHROPIC_API_KEY` - For Graphiti extraction
- `OPENAI_API_KEY` - For smolagents orchestration
- `N8N_CYPHER_URL` - Webhook endpoint for Cypher queries
