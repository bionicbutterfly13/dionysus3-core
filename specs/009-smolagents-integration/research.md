# Research: Smolagents Integration

**Feature**: 009-smolagents-integration | **Date**: 2025-12-25

## 1. CodeAgent Patterns for Cognitive Tool Composition

### Decision
Adopt the **Thought-Code-Observation cycle** for cognitive operations. CodeAgent generates Python code that composes multiple tools in a single execution, enabling 30% fewer steps than JSON-based tool calling.

### Rationale
- Maps directly to Dionysus OODA loop: Orient=Thought, Decide=Code, Act=Execute, Observe=Observation
- Code composition allows conditional logic: `if model.accuracy > 0.5: generate_prediction() else: flag_for_revision()`
- Error recovery through retry with revised reasoning

### Alternatives Considered
- **ToolCallingAgent (JSON)**: Safer but less expressive; rejected for primary path but retained as fallback
- **Custom code generation**: Higher effort; rejected in favor of proven smolagents pattern

### Code Pattern
```python
from smolagents import CodeAgent, Tool

class CognitiveTool(Tool):
    name = "resolve_prediction"
    description = "Resolves a mental model prediction against an observation"
    inputs = {
        "prediction_id": {"type": "string", "description": "UUID of prediction"},
        "observation": {"type": "string", "description": "What was observed"},
    }
    output_type = "string"

    def forward(self, prediction_id: str, observation: str) -> str:
        result = self.service.resolve_prediction(prediction_id, observation)
        return f"Prediction resolved. Model accuracy now {result.accuracy:.0%}."
```

---

## 2. Docker Sandbox Configuration

### Decision
Use **Docker sandbox on Hostinger VPS** with custom `DockerSandbox` class for fine-grained security control. Default timeout: 30 seconds. Step limit: 10.

### Rationale
- Self-hosted: No external API costs (Blaxel/E2B unnecessary)
- Security controls: Drop all capabilities, run as `nobody`, memory/CPU limits
- Hostinger VPS has Docker available

### Security Configuration
| Setting | Value | Rationale |
|---------|-------|-----------|
| `mem_limit` | 512MB | Sufficient for cognitive operations |
| `cpu_quota` | 50000 | 50% of one CPU core |
| `pids_limit` | 100 | Prevent fork bombs |
| `cap_drop` | ["ALL"] | Minimal privileges |
| `user` | nobody | Unprivileged execution |
| `network_mode` | none | Isolate from network (optional) |

### Code Pattern
```python
from smolagents import CodeAgent, LiteLLMModel

# Simple usage with built-in Docker executor
with CodeAgent(
    tools=cognitive_tools,
    model=LiteLLMModel(model_id="anthropic/claude-sonnet-4-20250514"),
    executor_type="docker",
    max_steps=10,  # Spec default
) as agent:
    result = agent.run(task)
```

---

## 3. MCP Tool Loading

### Decision
Use **stdio transport with StdioServerParameters** to spawn dionysus_mcp as subprocess. MCPClient with context manager for automatic cleanup.

### Rationale
- dionysus_mcp uses FastMCP with stdio transport (default)
- Subprocess spawning ensures clean lifecycle management
- Context manager pattern handles cleanup automatically

### Alternatives Considered
- **HTTP/SSE transport**: Requires modifying dionysus_mcp to add HTTP endpoint; deferred
- **Manual lifecycle**: More control but error-prone; use context manager instead

### Code Pattern
```python
from smolagents import MCPClient, CodeAgent
from mcp import StdioServerParameters
import os

server_params = StdioServerParameters(
    command="python",
    args=["-m", "dionysus_mcp.server"],
    env={"DATABASE_URL": os.environ.get("DATABASE_URL"), **os.environ},
)

with MCPClient(server_params, structured_output=True) as tools:
    # Validate required tools present
    tool_names = {t.name for t in tools}
    required = {"semantic_recall", "create_memory", "get_consciousness_state"}
    if not required.issubset(tool_names):
        raise RuntimeError(f"Missing tools: {required - tool_names}")

    agent = CodeAgent(tools=tools, model=model, add_base_tools=True)
    result = agent.run(task)
```

---

## 4. LiteLLM + Claude Configuration

### Decision
Use **LiteLLMModel with `anthropic/` prefix** for Claude models. Primary: claude-sonnet-4-20250514. Temperature: 0.2-0.3 for deterministic agent behavior.

### Rationale
- LiteLLM provides unified interface across providers
- Low temperature (0.2) for consistent code generation
- Rate limiting via `requests_per_minute` prevents API throttling

### Model Selection
| Use Case | Model | Temperature | Rationale |
|----------|-------|-------------|-----------|
| Primary agent | claude-sonnet-4-20250514 | 0.2 | Balanced capability/cost |
| Complex reasoning | claude-opus-4-5-20251101 | 0.1 | Maximum precision |
| Perception layer | claude-3-haiku | 0.3 | Fast/cheap for simple tasks |

### Code Pattern
```python
from smolagents import LiteLLMModel

model = LiteLLMModel(
    model_id="anthropic/claude-sonnet-4-20250514",
    temperature=0.2,
    max_tokens=4096,
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    requests_per_minute=60,
)
```

### Error Handling
```python
from smolagents import LiteLLMRouterModel

# Automatic failover between models
router_model = LiteLLMRouterModel(
    model_id="claude-agent",
    model_list=[
        {"model_name": "claude-agent", "litellm_params": {"model": "anthropic/claude-sonnet-4-20250514"}},
        {"model_name": "claude-agent", "litellm_params": {"model": "anthropic/claude-opus-4-5-20251101"}},
    ],
    client_kwargs={"routing_strategy": "simple-shuffle"},
)
```

---

## 5. Multi-Agent Orchestration

### Decision
Use **hierarchical ManagedAgent pattern** with consciousness layer as manager orchestrating 4 cognitive layer agents. Each layer has specialized tools, model configuration, and step limits.

### Rationale
- Maps directly to ThoughtSeed 5-layer hierarchy (perceptual→conceptual→abstract→metacognitive→consciousness)
- ManagedAgent wrapper converts agents into callable tools for manager
- Independent step limits per layer prevent runaway execution
- Different model tiers optimize cost/capability tradeoff

### Layer Configuration
| Layer | Agent Type | Model Tier | Max Steps | Tools |
|-------|------------|------------|-----------|-------|
| perceptual | ToolCallingAgent | Haiku (cheap) | 3 | recall |
| conceptual | CodeAgent | Sonnet | 5 | recall, synthesize |
| abstract | CodeAgent | Sonnet | 7 | recall, synthesize, reflect |
| metacognitive | CodeAgent | Sonnet | 7 | reflect, revise_model, recall |
| consciousness | CodeAgent (manager) | Sonnet | 10 | remember + managed agents |

### Code Pattern
```python
from smolagents import CodeAgent, ToolCallingAgent, ManagedAgent

# Create layer agents
perceptual_agent = ToolCallingAgent(tools=[recall_tool], model=haiku_model, max_steps=3)
metacognitive_agent = CodeAgent(tools=[reflect_tool, revise_model_tool], model=sonnet_model, max_steps=7)

# Wrap as managed agents
managed_perception = ManagedAgent(
    agent=perceptual_agent,
    name="perception",
    description="Fast pattern matching and memory retrieval."
)
managed_metacognition = ManagedAgent(
    agent=metacognitive_agent,
    name="metacognition",
    description="Self-reflection and model revision."
)

# Manager orchestrates all layers
consciousness_agent = CodeAgent(
    tools=[remember_tool],
    model=sonnet_model,
    max_steps=10,
    managed_agents=[managed_perception, managed_metacognition, ...],
)
```

---

## Summary: All Research Topics Resolved

| Topic | Decision | Key Pattern |
|-------|----------|-------------|
| CodeAgent patterns | Thought-Code-Observation cycle | Tool composition via Python code |
| Docker sandbox | Custom DockerSandbox with security limits | 30s timeout, 10 steps, drop all caps |
| MCP tool loading | MCPClient with stdio transport | Context manager, subprocess spawn |
| LiteLLM + Claude | LiteLLMModel with anthropic/ prefix | Low temperature, rate limiting |
| Multi-agent | ManagedAgent hierarchical pattern | 5 layers matching ThoughtSeed |

**No NEEDS CLARIFICATION items remain.** Proceeding to Phase 1 design.
