# Ralph Orchestrator Skill

**Version**: 1.1
**Status**: Active Development
**Integration**: Local execution via customized fork
**Repository**: [mikeyobrien/ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) (customized for Dionysus)

## Overview

Ralph is an autonomous iteration engine that loops until a task is complete. Rather than a one-shot execution, Ralph maintains state across multiple Claude invocations, handling:

- Iterative refinement with intelligent loop detection
- Budget protection via MAX_ITERATIONS and COST_THRESHOLD
- Git-based checkpointing and progress tracking
- Integration with Dionysus cognitive patterns

Ralph is designed for:
- Complex reasoning tasks requiring multi-step refinement
- Planning and design work (Meta-ToT decision integration)
- Code generation with iterative improvement
- Structured problem-solving with feedback loops

---

## Implementation: Customized Ralph-Orchestrator

Ralph is implemented as a **customized fork** of [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator), adapted for Dionysus patterns.

### Architecture

```
User Invocation (/ralph)
    ↓
Bash Skill Wrapper (ralph-orchestrator.sh)
    ↓
Ralph Orchestrator (Python)
    ↓
Claude Agent SDK
    ↓
Iterative Execution Loop
    ↓
Git Checkpointing + Metrics
```

### Local Installation

Ralph orchestrator is located at `ralph-orchestrator/` in dionysus3-core:

```bash
# Install dependencies (first time only)
cd ralph-orchestrator
uv sync

# Verify installation
uv run python -m ralph_orchestrator --help
curl http://localhost:3001/health
```

### Configuration

File: `docker-compose.yml` (Ralph service section)

```yaml
ralph:
  image: ralph-orchestrator:latest
  ports:
    - "3001:3001"
  environment:
    MAX_ITERATIONS: 10
    COST_THRESHOLD: 5.00
    TIMEOUT_SECONDS: 300
    LOG_LEVEL: INFO
  volumes:
    - ./data/ralph:/data
```

### Budget Protection

Ralph enforces cost/iteration limits to prevent runaway loops:

| Config | Default | Purpose |
|--------|---------|---------|
| `MAX_ITERATIONS` | 10 | Exit after N loop iterations |
| `COST_THRESHOLD` | $5.00 | Exit when cumulative cost exceeds threshold |
| `TIMEOUT_SECONDS` | 300 | Exit after 5 minutes of execution |

These are checked on every iteration. If any limit is exceeded, Ralph gracefully exits and reports the final state.

---

## Usage from Claude Desktop

### Basic Invocation

Use the `ralph_orchestrator` MCP tool to start an autonomous iteration loop:

```
use ralph_orchestrator tool to iterate on [task description]
```

### Tool Signature

```python
async def ralph_orchestrator(
    task: str,                          # Task description or problem statement
    context: Optional[dict] = None,     # Optional context data
    config: Optional[dict] = None,      # Optional config overrides
) -> dict
```

### Example Usage

**Planning Task**:
```
Use ralph_orchestrator to iterate on "Create a comprehensive 30-day marketing
strategy for a SaaS product launch targeting technical founders. Include
positioning, messaging, channel strategy, and metrics."
```

**Code Generation**:
```
Use ralph_orchestrator to iterate on "Implement a Python async HTTP client
with retry logic, timeout handling, and request batching. Include unit tests."
```

**Design Work**:
```
Use ralph_orchestrator to iterate on "Design the data model and API contracts
for a real-time collaboration system. Include schema diagrams and endpoint specs."
```

### Return Value

Ralph returns a dict with:

```python
{
    "success": bool,                    # Did Ralph complete successfully?
    "iterations": int,                  # Number of loops executed
    "cost_used": float,                 # Total API cost (USD)
    "final_state": dict,                # Final task state/output
    "completion_reason": str,           # Why Ralph stopped (completed|max_iters|cost_limit|timeout|error)
    "trace": list[dict]                 # Iteration history with decisions
}
```

---

## Usage from Agents

Ralph is callable from autonomous reasoning workflows (HeartbeatAgent, Meta-ToT).

### HeartbeatAgent Integration

The HeartbeatAgent can invoke Ralph during the DECIDE phase for complex planning:

```python
# In consciousness_manager.py or decision pathway
from api.agents.tools.ralph_tools import ralph_orchestrator_tool

# During autonomous reasoning:
result = await ralph_orchestrator_tool(
    task="Refine marketing strategy based on engagement metrics",
    context={
        "current_metrics": {...},
        "constraints": {...},
        "goals": [...]
    }
)

if result["success"]:
    # Integrate Ralph's output into memory
    await memory_service.create_memory(
        content=result["final_state"],
        memory_type="strategic",
        importance=0.9
    )
```

### Meta-ToT Integration

Ralph works with Meta-ToT to refine candidate plans:

```python
# From Meta-ToT tool after selecting a branch
candidate_plan = meta_tot_result["selected_branch"]

# Use Ralph to refine the selected plan
refined = await ralph_orchestrator_tool(
    task=f"Refine this plan with detailed implementation steps: {candidate_plan}",
    context={
        "active_inference_state": {...},
        "consciousness_level": 0.75
    },
    config={"MAX_ITERATIONS": 5}  # Limit for tight integration
)
```

### Integration Pattern

Ralph is part of the Dionysus reasoning stack:

```
Perception (observe environment)
    ↓
Reasoning (research options)
    ↓
Meta-ToT (select best branch)  ← High-complexity decisions
    ↓
Ralph (refine selected plan)   ← Multi-step iteration
    ↓
Metacognition (review & learn)
    ↓
Action (execute plan)
```

---

## Configuration

### Environment Variables

Set in `.env` or `docker-compose.yml`:

```bash
# Iteration/budget limits
MAX_ITERATIONS=10              # Max loop count
COST_THRESHOLD=5.00            # Max USD spend
TIMEOUT_SECONDS=300            # Max execution time (5 min)

# Ralph service
RALPH_SERVICE_URL=http://localhost:3001
RALPH_API_KEY=<secret>         # For service auth

# Logging
LOG_LEVEL=INFO                 # DEBUG|INFO|WARNING|ERROR
RALPH_LOG_DIR=/data/logs
```

### Overriding at Runtime

Pass config dict to override defaults per call:

```python
result = await ralph_orchestrator_tool(
    task="...",
    config={
        "MAX_ITERATIONS": 5,           # Lower for quick iteration
        "COST_THRESHOLD": 2.00,        # Tighter budget
        "TIMEOUT_SECONDS": 120,        # 2 minute limit
    }
)
```

### Cost Calculation

Ralph tracks costs per Claude API call:

- Input tokens: $0.003 per 1M tokens (Claude Opus)
- Output tokens: $0.015 per 1M tokens (Claude Opus)
- Ralph adds 10% overhead for infrastructure

Example: 3 iterations with 500 input + 1000 output tokens each:
```
Per iteration: (500 * 0.000000003) + (1000 * 0.000000015) = ~0.018
3 iterations: 0.054 * 1.1 overhead = ~$0.06 total
```

---

## Integration Points

### MCP Tool Pattern

Ralph follows the same MCP tool pattern as Serena:

```python
# In dionysus_mcp/tools/ralph.py
from mcp.server.fastmcp import FastMCP

@app.tool()
async def ralph_orchestrator(
    task: str,
    context: Optional[dict] = None,
    config: Optional[dict] = None,
) -> dict:
    """
    Orchestrate autonomous iteration using Ralph.

    Ralph loops until completion, handling:
    - State tracking across iterations
    - Cost/iteration budgets
    - Intelligent exit detection
    - Integration with Meta-ToT for complex reasoning
    """
    from api.services.ralph_service import get_ralph_service

    service = get_ralph_service()
    result = await service.orchestrate(task, context, config)
    return result
```

### Router Integration

Ralph also has a FastAPI router for direct HTTP access:

```python
# In api/routers/ralph.py
from fastapi import APIRouter

router = APIRouter(prefix="/ralph", tags=["ralph"])

@router.post("/orchestrate")
async def orchestrate(request: OrchestrationRequest) -> OrchestrationResult:
    """Start a Ralph orchestration loop."""
    service = get_ralph_service()
    return await service.orchestrate(
        task=request.task,
        context=request.context,
        config=request.config
    )

@router.get("/status/{orchestration_id}")
async def get_status(orchestration_id: str) -> dict:
    """Poll status of an active orchestration."""
    service = get_ralph_service()
    return await service.get_status(orchestration_id)
```

### Service Layer

The Ralph service coordinates with other Dionysus services:

```python
# api/services/ralph_service.py
class RalphService:
    async def orchestrate(self, task: str, context: dict, config: dict):
        # 1. Initialize orchestration state
        # 2. Loop with Claude API
        # 3. Track cost/iterations
        # 4. Check exit conditions
        # 5. Integrate with memory services
        # 6. Return final state
```

---

## Example Workflows

### Workflow 1: Marketing Strategy Refinement

Task: Create a comprehensive GTM strategy with Ralph refinement.

```python
# Start with Ralph for iterative refinement
result = await ralph_orchestrator_tool(
    task="""
    Create a 90-day Go-To-Market strategy for a B2B analytics platform.
    Requirements:
    - Target personas and messaging
    - Channel prioritization with rationale
    - Launch timeline and milestones
    - Success metrics and KPIs
    - Risk mitigation strategies

    Iterate to ensure each section has clear next steps.
    """,
    context={
        "product_stage": "post-alpha",
        "budget": "$50k",
        "team_size": 3,
        "target_markets": ["healthcare", "fintech"],
    }
)

# Result contains refined strategy with implementation steps
strategy = result["final_state"]
```

### Workflow 2: Code Generation with Testing

Task: Implement a module with iterative refinement and testing.

```python
result = await ralph_orchestrator_tool(
    task="""
    Implement a Python module for managing user sessions.
    Requirements:
    - Session creation, validation, and cleanup
    - TTL-based expiration
    - Concurrent access safety
    - Integration with Redis for distributed state
    - Unit tests with 90%+ coverage
    - Type hints and docstrings

    Iterate until tests pass and code is production-ready.
    """,
    config={
        "MAX_ITERATIONS": 8,        # Code refinement often needs multiple passes
        "COST_THRESHOLD": 3.00,     # Tighter budget for focused task
    }
)

# Result contains working code with passing tests
code = result["final_state"]
```

### Workflow 3: Meta-ToT Plan Refinement

Task: Use Ralph to refine a Meta-ToT selected plan.

```python
# First, run Meta-ToT to select best branch
meta_tot_result = await meta_tot_run(
    task="Design an authentication system for a distributed app"
)

# Then refine the selected plan with Ralph
refinement = await ralph_orchestrator_tool(
    task=f"""
    Take this authentication design and produce an implementation plan:

    {meta_tot_result['selected_branch']['content']}

    Add:
    - Detailed API specs with examples
    - Security considerations
    - Deployment checklist
    - Fallback strategies for failure modes
    """,
    context={
        "selected_confidence": meta_tot_result["confidence"],
        "reasoning_trace": meta_tot_result["reasoning"],
    },
    config={"MAX_ITERATIONS": 5}
)
```

---

## Monitoring & Debugging

### Viewing Logs

Ralph logs go to `/data/ralph/logs/`:

```bash
# Watch Ralph logs in real-time
docker logs -f dionysus-ralph

# Or from inside container
tail -f /data/ralph/logs/orchestration.log
```

### Polling Status

Check live status of an orchestration:

```python
# After starting an orchestration
orchestration_id = result.get("orchestration_id")

# Poll status periodically
import asyncio
from api.services.ralph_service import get_ralph_service

service = get_ralph_service()
while True:
    status = await service.get_status(orchestration_id)
    print(f"Iteration: {status['iteration']}/{status['max_iterations']}")
    print(f"Cost so far: ${status['cost_used']:.2f}")

    if status["complete"]:
        break

    await asyncio.sleep(5)
```

### Exit Reasons

Ralph exits with one of these reasons:

| Reason | Meaning |
|--------|---------|
| `completed` | Task completed successfully (Claude indicated done) |
| `max_iters` | Hit MAX_ITERATIONS limit |
| `cost_limit` | Exceeded COST_THRESHOLD |
| `timeout` | Exceeded TIMEOUT_SECONDS |
| `error` | Unrecoverable error (check logs) |

---

## Comparison: Ralph vs Direct Claude Invocation

| Aspect | Ralph | Direct Claude |
|--------|-------|---------------|
| **Iteration** | Automatic loops | Single shot |
| **Refinement** | Iterative improvement built-in | Manual re-prompting |
| **Budget Control** | Enforced limits | Manual tracking |
| **Exit Detection** | Intelligent (task done?) | Not applicable |
| **State Tracking** | Maintained across loops | Not applicable |
| **Best For** | Complex, multi-step tasks | Single analysis/generation |

**Use Ralph when**: Task requires refinement, multiple passes, or iterative improvement.
**Use direct Claude when**: Single analysis or generation is sufficient.

---

## Troubleshooting

### Ralph keeps looping without progress

**Cause**: Task is ambiguous or unfinished.
**Fix**: Clarify task definition with specific completion criteria.

```python
# Bad
task="Improve the code"

# Good
task="Improve the code by: 1) Reducing cyclomatic complexity below 5, " \
      "2) Adding type hints to all functions, 3) Reaching 90% test coverage"
```

### Cost threshold exceeded

**Cause**: Task is more complex than budget allows.
**Fix**: Increase COST_THRESHOLD or reduce MAX_ITERATIONS.

```python
config={
    "MAX_ITERATIONS": 5,      # Fewer iterations
    "COST_THRESHOLD": 10.00,  # Higher budget
}
```

### Timeout on complex tasks

**Cause**: Task takes longer than TIMEOUT_SECONDS.
**Fix**: Increase timeout or break task into smaller pieces.

```python
config={
    "TIMEOUT_SECONDS": 600,   # 10 minutes instead of 5
}
```

### Ralph service not responding

**Cause**: Container not running or port not mapped.
**Fix**: Restart the service.

```bash
docker compose restart ralph
docker logs ralph  # Check for errors
```

---

## Best Practices

### 1. Define Clear Success Criteria

Ralph needs to know when the task is done:

```python
task="""
Create a design document with:
- Current system architecture (2 diagrams)
- Three proposed improvements (pros/cons for each)
- Recommended solution with rationale
- Implementation roadmap (phases and timeline)

When all four sections are complete with actionable next steps, stop.
"""
```

### 2. Use Context for Constraints

Pass constraints and context to guide Ralph:

```python
result = await ralph_orchestrator_tool(
    task="Create a pricing model",
    context={
        "constraints": {
            "max_price_tier": "$299/month",
            "min_annual_plan": "$1999",
            "target_segment": "mid-market"
        },
        "market_research": {...},
        "competitor_pricing": {...}
    }
)
```

### 3. Set Appropriate Budgets

Match budget to task complexity:

```python
# Simple refinement: low budget
config={"MAX_ITERATIONS": 3, "COST_THRESHOLD": 1.00}

# Complex planning: medium budget
config={"MAX_ITERATIONS": 7, "COST_THRESHOLD": 3.00}

# Deep analysis: higher budget
config={"MAX_ITERATIONS": 10, "COST_THRESHOLD": 5.00}
```

### 4. Integrate with Memory

Save Ralph outputs to Dionysus memory for future reference:

```python
result = await ralph_orchestrator_tool(task="...")

if result["success"]:
    await memory_service.create_memory(
        content=json.dumps(result["final_state"]),
        memory_type="strategic",
        importance=0.8,
        metadata={
            "task": "marketing_strategy",
            "iterations": result["iterations"],
            "cost": result["cost_used"]
        }
    )
```

### 5. Use in Agent Workflows

Integrate Ralph into multi-agent workflows:

```python
# Consciousness Manager orchestration
perception_result = await perception_agent.run(...)
reasoning_result = await reasoning_agent.run(...)
plan = await meta_tot_engine.select_best_branch(...)
refined_plan = await ralph_orchestrator_tool(task=plan)  # Refine
action_result = await action_executor.execute(refined_plan)
```

---

## API Reference

### Ralph Orchestrator Tool

```python
async def ralph_orchestrator(
    task: str,
    context: Optional[dict] = None,
    config: Optional[dict] = None,
) -> dict
```

**Parameters:**
- `task` (str): Problem statement or task description
- `context` (dict, optional): Context data (constraints, metrics, research, etc.)
- `config` (dict, optional): Config overrides (MAX_ITERATIONS, COST_THRESHOLD, TIMEOUT_SECONDS)

**Returns:**
```python
{
    "success": bool,
    "orchestration_id": str,
    "iterations": int,
    "cost_used": float,
    "final_state": dict,
    "completion_reason": str,
    "trace": list[dict]
}
```

### Ralph Service Endpoints

**POST /ralph/orchestrate**
```bash
curl -X POST http://localhost:3001/ralph/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "task": "...",
    "context": {...},
    "config": {...}
  }'
```

**GET /ralph/status/{orchestration_id}**
```bash
curl http://localhost:3001/ralph/status/uuid-here
```

---

## Architecture Decisions

### Why VPS-Native?

Ralph runs as a Docker service on the VPS for:
- **Persistence**: State survives across Claude sessions
- **Monitoring**: Logs and metrics centralized
- **Integration**: Direct Neo4j access via Graphiti
- **Cost Control**: Enforced limits prevent runaway spending
- **Autonomy**: Agents can invoke without Claude intermediary

### Usage

**Command**: `/ralph [OPTIONS] [PROMPT_TEXT]`

**Examples**:
```bash
# Use PROMPT.md in current directory
/ralph

# Inline prompt
/ralph "Implement user authentication with JWT"

# Custom file with iteration limit
/ralph -f my-task.md -i 100

# Verbose mode
/ralph -v "Debug the API endpoint"

# Dry run (test without execution)
/ralph -d "Refactor the memory system"
```

**Options**:
- `-f, --file FILE` - Prompt file (default: PROMPT.md)
- `-i, --iterations N` - Max iterations (default: 50)
- `-c, --cost AMOUNT` - Max cost in USD (default: $10)
- `-v, --verbose` - Verbose output
- `-d, --dry-run` - Test mode without execution
- `-h, --help` - Show help

### Configuration

Dionysus-specific configuration at `ralph-orchestrator/ralph-dionysus.yml`:

```yaml
agent: auto  # Claude, Q Chat, Gemini, or auto-detect
max_iterations: 50
max_runtime: 7200  # 2 hours
max_cost: 10.0  # $10 USD
checkpoint_interval: 10  # Git checkpoint every 10 iterations
context_window: 200000
context_threshold: 0.8  # Summarize at 80% of context
```

### Why Orchestrator?

ralph-orchestrator (Mikey O'Brien) was selected over other approaches because:
- **Production-Ready**: Used in real automation projects
- **Multi-Agent**: Coordinates multiple specialized agents
- **Cost-Aware**: Built-in budget tracking and limits
- **Observable**: Comprehensive logging and tracing
- **Active Development**: Regular updates and improvements

---

## Integration with Prompt Refinement Framework

Ralph works best with the **Prompt Refinement Framework** (see `docs/PROMPT_REFINEMENT_FRAMEWORK.md`):

1. **User provides prompt** → Claude analyzes for clarity
2. **Clarifying questions** → Fill gaps in requirements
3. **Refined task definition** → Create structured PROMPT.md
4. **Ralph execution** → Iterative completion with checkpointing
5. **Verification** → Confirm success criteria met

### Example Workflow

```bash
# User: "add authentication"
# Claude: [Asks clarifying questions via AskUserQuestion]
#   - Method: JWT, session, OAuth?
#   - Scope: Login only or full registration?
#   - Integration: Existing DB or separate service?
# User: [Answers questions]
# Claude: [Creates refined PROMPT.md]
# Claude: /ralph -f PROMPT.md -i 100

# Ralph iterates until:
# - All requirements implemented
# - Tests passing
# - Git commits created
# - Success criteria verified
```

## References

- **Repository**: [mikeyobrien/ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)
- **Local Path**: `ralph-orchestrator/` (customized fork)
- **Skill Wrapper**: `skills_library/personal/ralph/ralph-orchestrator.sh`
- **Configuration**: `ralph-orchestrator/ralph-dionysus.yml`
- **Prompt Framework**: `docs/PROMPT_REFINEMENT_FRAMEWORK.md`
- **Related**: Meta-ToT Engine, HeartbeatAgent, Consciousness Manager

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-01-01 | Customized ralph-orchestrator fork for Dionysus patterns |
| 1.0 | 2025-01-01 | Initial production release with VPS-native ralph-orchestrator |

---

**Last Updated**: 2025-01-01
**Author**: Mani Saint-Victor, MD
**License**: Apache 2.0
