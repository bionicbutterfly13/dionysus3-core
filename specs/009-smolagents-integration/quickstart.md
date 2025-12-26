# Quickstart: Smolagents Integration

**Feature**: 009-smolagents-integration | **Date**: 2025-12-25

## Prerequisites

- Python 3.11+
- Docker installed and running
- PostgreSQL database (local)
- ANTHROPIC_API_KEY environment variable set

## Installation

```bash
# Install smolagents with required extras
pip install 'smolagents[litellm,mcp,docker]'

# Verify installation
python -c "from smolagents import CodeAgent; print('smolagents OK')"
```

## Quick Test: Basic Agent

```python
from smolagents import CodeAgent, LiteLLMModel
import os

# Create model
model = LiteLLMModel(
    model_id="anthropic/claude-sonnet-4-20250514",
    temperature=0.2,
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

# Create agent
agent = CodeAgent(
    tools=[],
    model=model,
    add_base_tools=True,
    max_steps=10,
)

# Run simple task
result = agent.run("What is 2 + 2?")
print(result)
```

## Loading dionysus_mcp Tools

```python
from smolagents import CodeAgent, MCPClient, LiteLLMModel
from mcp import StdioServerParameters
import os

# Configure MCP connection
server_params = StdioServerParameters(
    command="python",
    args=["-m", "dionysus_mcp.server"],
    env={"DATABASE_URL": os.environ.get("DATABASE_URL"), **os.environ},
)

# Load tools from dionysus_mcp
with MCPClient(server_params, structured_output=True) as tools:
    print(f"Loaded {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}")

    # Create agent with dionysus tools
    agent = CodeAgent(
        tools=tools,
        model=LiteLLMModel(model_id="anthropic/claude-sonnet-4-20250514"),
        add_base_tools=True,
        max_steps=10,
    )

    # Run cognitive task
    result = agent.run("Recall memories about consciousness")
    print(result)
```

## Docker Sandbox Execution

```python
from smolagents import CodeAgent, LiteLLMModel

# Use Docker executor for sandboxed code
with CodeAgent(
    tools=[],
    model=LiteLLMModel(model_id="anthropic/claude-sonnet-4-20250514"),
    executor_type="docker",  # Enables Docker sandbox
    max_steps=10,
) as agent:
    result = agent.run("Calculate factorial of 10")
    print(result)
```

## Multi-Agent Hierarchy

```python
from smolagents import CodeAgent, ToolCallingAgent, ManagedAgent, LiteLLMModel

# Create layer agents
perception_agent = ToolCallingAgent(
    tools=[recall_tool],
    model=LiteLLMModel(model_id="anthropic/claude-3-haiku-20240307"),
    max_steps=3,
)

metacognition_agent = CodeAgent(
    tools=[reflect_tool, revise_model_tool],
    model=LiteLLMModel(model_id="anthropic/claude-sonnet-4-20250514"),
    max_steps=7,
)

# Wrap as managed agents
managed_perception = ManagedAgent(
    agent=perception_agent,
    name="perception",
    description="Fast pattern matching and memory retrieval."
)

managed_metacognition = ManagedAgent(
    agent=metacognition_agent,
    name="metacognition",
    description="Self-reflection and model revision."
)

# Create manager agent
consciousness = CodeAgent(
    tools=[remember_tool],
    model=LiteLLMModel(model_id="anthropic/claude-sonnet-4-20250514"),
    max_steps=10,
    managed_agents=[managed_perception, managed_metacognition],
)

# Manager delegates to subordinate agents
result = consciousness.run("""
    1. Use perception to find relevant memories about goals
    2. Use metacognition to reflect on progress
    3. Summarize findings
""")
```

## Integration with Heartbeat

```python
# In api/services/heartbeat_service.py

from smolagents import CodeAgent, MCPClient, LiteLLMModel
from mcp import StdioServerParameters

class HeartbeatService:
    def __init__(self):
        self.agent = None
        self._init_agent()

    def _init_agent(self):
        """Initialize cognitive agent for heartbeat decisions."""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "dionysus_mcp.server"],
            env=dict(os.environ),
        )

        self.mcp_client = MCPClient(server_params, structured_output=True)
        tools = self.mcp_client.get_tools()

        self.agent = CodeAgent(
            tools=tools,
            model=LiteLLMModel(
                model_id="anthropic/claude-sonnet-4-20250514",
                temperature=0.2,
            ),
            executor_type="docker",
            max_steps=10,
        )

    async def _make_decision(self, context: HeartbeatContext) -> list[ActionItem]:
        """Use agent for DECIDE phase instead of JSON prompting."""
        try:
            task = f"""
            Based on the following cognitive context, decide what actions to take:

            Energy: {context.energy}
            Active basins: {context.active_basins}
            Recent thoughts: {context.recent_thoughts}
            Pending predictions: {context.pending_predictions}

            Select appropriate cognitive actions within energy budget.
            Use the available tools to gather information and take action.
            """

            result = self.agent.run(task)
            return self._parse_agent_result(result)

        except Exception as e:
            # Fallback to legacy ActionHandler pattern
            logger.warning(f"Agent execution failed: {e}, using fallback")
            return self._make_default_decision(context)
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY=sk-ant-...
export DATABASE_URL=postgresql://user:pass@localhost:5432/dionysus

# Optional
export SMOLAGENTS_TIMEOUT=30          # Default timeout seconds
export SMOLAGENTS_MAX_STEPS=10        # Default max steps
export SMOLAGENTS_EXECUTOR=docker     # docker, local, or e2b
```

## Testing

```bash
# Run agent tests
pytest tests/integration/test_agent_execution.py -v

# Run with coverage
pytest tests/ --cov=api/services/agent_service -v

# Test Docker sandbox specifically
pytest tests/integration/test_sandbox_service.py -v
```

## Troubleshooting

### Docker executor fails to start
```bash
# Ensure Docker is running
docker info

# Check smolagents Docker image
docker images | grep agent-sandbox

# Rebuild if needed
pip install 'smolagents[docker]' --force-reinstall
```

### MCP connection fails
```bash
# Test dionysus_mcp directly
python -m dionysus_mcp.server

# Check DATABASE_URL is set
echo $DATABASE_URL
```

### Agent timeout
```python
# Increase timeout for complex tasks
agent = CodeAgent(
    ...,
    max_steps=20,  # More steps for complex reasoning
)
```

## Next Steps

1. Run database migrations: `python scripts/run_migrations.py`
2. Configure cognitive agents: `POST /api/agents`
3. Test heartbeat integration: `POST /api/heartbeat/trigger`
4. Monitor execution metrics: `GET /api/agents/metrics`
