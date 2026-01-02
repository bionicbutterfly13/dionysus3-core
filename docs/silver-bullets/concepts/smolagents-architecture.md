# Smolagents Architecture

**Category**: Implementation
**Type**: Framework Pattern
**Implementation**: `api/agents/`, `dionysus_mcp/`

---

## Definition

**Smolagents** is a lightweight, production-grade agent framework from HuggingFace that provides native multi-agent orchestration, tool calling, and memory management. Dionysus uses smolagents as the foundational architecture for implementing cognitive agents that execute OODA loops, manage consciousness pipelines, and integrate with active inference systems.

Think of smolagents as the **operating system** for Dionysus's cognitive agents—providing the runtime environment, memory management, and inter-agent communication infrastructure.

## Key Characteristics

- **Lightweight**: Minimal overhead compared to legacy frameworks (LangChain/LangGraph)
- **Native Multi-Agent**: Built-in support for hierarchical agent orchestration via `ManagedAgent`
- **Class-Based Tools**: Clean tool definition pattern with type hints and structured outputs
- **Planning Intervals**: Periodic fact-checking and replanning during execution
- **Step Callbacks**: Extensible hooks for monitoring, auditing, and consciousness integration
- **Memory Management**: Automatic conversation history with configurable pruning
- **Execution Traces**: Detailed logging of agent decision paths for debugging and learning

## Architecture Components

### 1. ToolCallingAgent

The primary agent type for autonomous task execution.

**Structure**:
```python
from smolagents import ToolCallingAgent

agent = ToolCallingAgent(
    tools=[tool1, tool2, tool3],           # Available tools
    model=llm_model,                       # LiteLLM model
    max_steps=10,                          # Maximum actions before stopping
    planning_interval=3,                   # Re-plan every 3 steps
    name="agent_name",                     # Identifier for delegation
    description="Agent capabilities...",   # Used by orchestrators
    step_callbacks={...}                   # Monitoring hooks
)

result = agent.run("Task description")
```

**Key Features**:
- Autonomous action selection based on task description
- Tool calling with automatic error handling
- Memory of previous steps in `agent.memory.steps`
- Periodic replanning to reassess strategy

**Dionysus Usage**: `HeartbeatAgent`, `PerceptionAgent`, `ReasoningAgent`, `MetacognitionAgent`

### 2. ManagedAgent (smolagents 1.23+)

Pattern for hierarchical agent orchestration. In smolagents 1.23+, agents with `name` and `description` are passed directly to `managed_agents` parameter—no wrapper class needed.

**Structure**:
```python
from smolagents import CodeAgent, ToolCallingAgent

# Sub-agent with rich description
perception = ToolCallingAgent(
    tools=[observe_tool, recall_tool],
    model=model,
    name="perception",
    description="""OBSERVE phase specialist.

    Use when you need to:
    - Gather current environmental state
    - Recall relevant memories
    - Capture experiential context
    """
)

# Orchestrator delegates via natural language
manager = CodeAgent(
    tools=[],
    managed_agents=[perception, reasoning, metacognition],
    model=model,
    name="consciousness_manager"
)

result = manager.run("Delegate to perception to observe environment")
```

**Key Features**:
- Natural language delegation (no manual chaining)
- Rich agent descriptions guide orchestrator decisions
- Isolated tool sets per agent (OODA phase separation)
- Execution traces track delegation patterns

**Dionysus Usage**: `ConsciousnessManager` orchestrates `PerceptionAgent`, `ReasoningAgent`, `MetacognitionAgent`

### 3. Class-Based Tools

Clean pattern for defining agent capabilities with structured inputs/outputs.

**Structure**:
```python
from smolagents import Tool
from pydantic import BaseModel, Field

class OutputSchema(BaseModel):
    result: str = Field(..., description="Result description")
    confidence: float = Field(..., description="Confidence score")

class MyTool(Tool):
    name = "my_tool"
    description = "What this tool does (agent reads this)"

    inputs = {
        "param1": {
            "type": "string",
            "description": "Parameter description"
        },
        "param2": {
            "type": "number",
            "description": "Another parameter"
        }
    }
    output_type = "any"

    def forward(self, param1: str, param2: float) -> dict:
        # Implementation (synchronous)
        # For async operations, use async_tool_wrapper
        return OutputSchema(
            result="...",
            confidence=0.9
        ).model_dump()

# Instantiate and use
my_tool = MyTool()
agent = ToolCallingAgent(tools=[my_tool], ...)
```

**Key Features**:
- Type-safe inputs via schema definition
- Pydantic models for structured outputs
- Sync execution (use `async_tool_wrapper` for async operations)
- Clear descriptions for agent reasoning

**Dionysus Usage**: `cognitive_tools.py`, `planning_tools.py`, `mosaeic_tools.py`, etc.

### 4. Planning Intervals

Periodic replanning during long-running tasks to reassess strategy.

**How It Works**:
```python
agent = ToolCallingAgent(
    tools=tools,
    model=model,
    planning_interval=3  # Re-plan every 3 action steps
)

# Execution flow:
# Step 1: Action (tool call)
# Step 2: Action (tool call)
# Step 3: Action (tool call)
# Step 4: PlanningStep (reassess, generate new facts)
# Step 5: Action (tool call)
# ...
```

**PlanningStep Behavior**:
- Agent re-evaluates current state
- Generates updated "facts" about progress
- Adjusts strategy if needed
- Maps to Active Inference belief updates

**Dionysus Integration**: Planning callbacks inject IWMT coherence, basin activations, and metacognitive state

### 5. Step Callbacks

Extensible hooks for monitoring and integration with consciousness substrate.

**Callback Types**:
```python
from smolagents.memory import ActionStep, PlanningStep

def on_action(step: ActionStep, agent) -> None:
    # Called after each tool execution
    # Use for: energy deduction, basin activation, audit logging
    pass

def on_planning(step: PlanningStep, agent) -> None:
    # Called during planning phases
    # Use for: IWMT coherence injection, metacognitive assessment
    pass

agent = ToolCallingAgent(
    tools=tools,
    model=model,
    step_callbacks={
        ActionStep: on_action,
        PlanningStep: on_planning
    }
)
```

**Dionysus Callbacks**:
- **Basin Callback**: Activates attractor basins during semantic recall
- **Memory Callback**: Prunes old observations to save tokens
- **IWMT Callback**: Injects coherence scores during planning
- **Execution Trace Callback**: Persists decision paths to Neo4j
- **Audit Callback**: Tracks tool usage for observability

### 6. Execution Traces

Detailed logs of agent decision paths stored in `agent.memory.steps`.

**Structure**:
```python
# After agent.run() completes
for step in agent.memory.steps:
    if isinstance(step, ActionStep):
        print(f"Step {step.step_number}: {step.tool_calls[0].name}")
        print(f"  Args: {step.tool_calls[0].arguments}")
        print(f"  Result: {step.observations}")
    elif isinstance(step, PlanningStep):
        print(f"Step {step.step_number}: PLANNING")
        print(f"  Facts: {step.facts}")
```

**Dionysus Persistence**: `ExecutionTraceCollector` saves traces to Neo4j for:
- Debugging failed agent runs
- Meta-learning from past episodes
- Auditing autonomous decisions
- Visualizing cognitive patterns

## Implementation in Dionysus

### HeartbeatAgent (Top-Level OODA Loop)

**File**: `api/agents/heartbeat_agent.py:8-111`

```python
class HeartbeatAgent:
    """
    Autonomous cognitive decision cycle using ToolCallingAgent.
    Executes DECIDE phase of OODA loop with MCP-bridged tools.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        self.model = get_router_model(model_id=model_id)
        self.server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        self.mcp_client = None
        self.agent = None

    def __enter__(self):
        # Bridge MCP tools to smolagents
        self.mcp_client = MCPClient(self.server_params, structured_output=True)
        tools = self.mcp_client.__enter__()

        # Create ToolCallingAgent with planning_interval
        self.agent = ToolCallingAgent(
            tools=tools,
            model=self.model,
            max_steps=10,
            planning_interval=3,  # FR-039-002: Periodic replanning
            name="heartbeat_agent",
            description="Autonomous cognitive decision cycle agent.",
            step_callbacks=audit.get_registry("heartbeat_agent")
        )
        return self

    async def decide(self, context: Dict[str, Any]) -> str:
        """Execute decision cycle with timeout and resource gating."""
        prompt = f"""
        You are Dionysus, an autonomous cognitive system.
        Heartbeat #{context.get('heartbeat_number', 'unknown')}.

        Current State:
        - Energy: {context.get('current_energy', 0)} / {context.get('max_energy', 20)}
        - User Present: {context.get('user_present', False)}

        Task: Recall memories, reflect on progress, decide actions.
        """

        result = await run_agent_with_timeout(
            self.agent,
            prompt,
            timeout_seconds=60
        )
        return str(result)
```

**Key Patterns**:
- MCP bridge for tool integration
- Planning interval for periodic belief updates
- Step callbacks for audit and energy tracking
- Timeout gating for resource control

### ConsciousnessManager (Multi-Agent Orchestration)

**File**: `api/agents/consciousness_manager.py:32-403`

```python
class ConsciousnessManager:
    """
    Orchestrates Perception, Reasoning, Metacognition agents
    using smolagents hierarchical managed_agents architecture.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        self.model = get_router_model(model_id=model_id)

        # FR-039-001: ManagedAgent wrappers
        self.perception_wrapper = ManagedPerceptionAgent(model_id)
        self.reasoning_wrapper = ManagedReasoningAgent(model_id)
        self.metacognition_wrapper = ManagedMetacognitionAgent(model_id)

    def __enter__(self):
        # Get ToolCallingAgent instances from wrappers
        perception_agent = self.perception_wrapper.get_managed()
        reasoning_agent = self.reasoning_wrapper.get_managed()
        metacognition_agent = self.metacognition_wrapper.get_managed()

        # Add specialized tools to reasoning
        reasoning_agent.tools[context_explorer.name] = context_explorer
        reasoning_agent.tools[cognitive_check.name] = cognitive_check
        reasoning_agent.tools[active_planner.name] = active_planner

        # Create orchestrator with native ManagedAgent support
        self.orchestrator = CodeAgent(
            tools=[],
            managed_agents=[
                perception_agent,
                reasoning_agent,
                metacognition_agent
            ],
            model=self.model,
            name="consciousness_manager",
            description="""High-level cognitive orchestrator.

            Delegates to specialized agents:
            - perception: OBSERVE phase
            - reasoning: ORIENT phase
            - metacognition: DECIDE phase
            """,
            max_steps=15,
            planning_interval=3,
            step_callbacks=audit.get_registry("consciousness_manager")
        )
        return self

    async def run_ooda_cycle(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full OODA loop via managed agent hierarchy."""
        prompt = f"""
        Execute OODA cycle based on context.

        1. Delegate to 'perception' to gather state and memories
        2. Delegate to 'reasoning' to analyze observations
        3. Delegate to 'metacognition' to review goals and decide
        4. Synthesize into final actionable plan

        Context: {json.dumps(initial_context, indent=2)}
        """

        result = await run_agent_with_timeout(
            self.orchestrator,
            prompt,
            timeout_seconds=90
        )

        return {
            "final_plan": result,
            "orchestrator_log": self.orchestrator.memory.steps
        }
```

**Key Patterns**:
- Natural language delegation (no manual chaining)
- Tool isolation per OODA phase
- Rich agent descriptions guide orchestrator
- Planning intervals for metacognitive assessment

### ManagedAgent Wrappers

**File**: `api/agents/managed/perception.py:28-107`

```python
class ManagedPerceptionAgent:
    """
    Wrapper providing ToolCallingAgent for OBSERVE phase.

    smolagents 1.23+: Agents with name/description are passed
    directly to managed_agents parameter (no wrapper class).
    """

    DESCRIPTION = """OBSERVE phase specialist for OODA loop.

    Capabilities:
    - observe_environment: Gather current state
    - semantic_recall: Retrieve relevant memories
    - mosaeic_capture: Capture experiential state
    - query_wisdom: Access strategic principles

    Use when you need to understand current situation
    before reasoning or decision-making.
    """

    def get_managed(self) -> ToolCallingAgent:
        """Get ToolCallingAgent for multi-agent orchestration."""
        inner = PerceptionAgent(self.model_id)
        with inner as configured:
            # Agent has name/description set
            return configured.agent
```

**Pattern**: Each OODA phase (Perception, Reasoning, Metacognition) gets a wrapper that:
- Provides rich description for orchestrator
- Initializes specialized tools
- Returns configured ToolCallingAgent
- Manages lifecycle via context manager

### Class-Based Tool Example

**File**: `api/agents/tools/cognitive_tools.py:29-79`

```python
class ExplorerOutput(BaseModel):
    """Structured output for context_explorer tool."""
    project_id: str
    query: str
    attractors: List[str]
    recommendation: str
    error: Optional[str] = None

class ContextExplorerTool(Tool):
    name = "context_explorer"
    description = "Scans knowledge graph for semantic attractors."

    inputs = {
        "project_id": {
            "type": "string",
            "description": "Scoping ID for research"
        },
        "query": {
            "type": "string",
            "description": "Domain or task query"
        }
    }
    output_type = "any"

    def forward(self, project_id: str, query: str) -> dict:
        # Async operations wrapped for sync interface
        async def _run():
            graphiti = await get_graphiti_service()
            return await graphiti.search(
                f"attractor basins for {query}",
                limit=5
            )

        try:
            search_results = async_tool_wrapper(_run)()
            edges = search_results.get("edges", [])
            attractors = [e.get('fact') for e in edges if e.get('fact')]

            return ExplorerOutput(
                project_id=project_id,
                query=query,
                attractors=attractors,
                recommendation="Ground reasoning in attractors to minimize free energy."
            ).model_dump()
        except Exception as e:
            return ExplorerOutput(
                project_id=project_id,
                query=query,
                attractors=[],
                recommendation="Fallback to base context.",
                error=str(e)
            ).model_dump()

# Instantiate for agent use
context_explorer = ContextExplorerTool()
```

**Pattern**: All Dionysus tools follow this class-based pattern with:
- Pydantic output schemas
- Clear input/output descriptions
- Async wrapper for async operations
- Graceful error handling

### Step Callbacks Integration

**File**: `api/agents/callbacks/execution_trace_callback.py:28-221`

```python
class ExecutionTraceCollector:
    """
    Collects execution steps during agent run.
    Persists to Neo4j on completion for debugging/learning.
    """

    def on_action_step(self, step: ActionStep, agent: Optional[Any] = None):
        """Callback for ActionStep - collects tool execution data."""
        step_data = {
            "step_number": step.step_number,
            "step_type": "ActionStep",
            "tool_name": step.tool_calls[0].name if step.tool_calls else None,
            "tool_arguments": step.tool_calls[0].arguments if step.tool_calls else None,
            "observation": str(step.observations)[:500]  # Truncate for storage
        }
        self._steps_collected.append(step_data)

    def on_planning_step(self, step: PlanningStep, agent: Optional[Any] = None):
        """Callback for PlanningStep - collects planning phase data."""
        step_data = {
            "step_number": step.step_number,
            "step_type": "PlanningStep",
            "plan": str(step.plan)[:1000]
        }
        self._steps_collected.append(step_data)

    async def finalize(self, success: bool, token_usage: Dict):
        """Persist collected trace to Neo4j."""
        trace_id = await service.create_trace(self.agent_name, self.run_id)
        for step_data in self._steps_collected:
            await service.add_step(trace_id, step_data)
        await service.complete_trace(trace_id, success=success)
        return trace_id

# Usage in agent
collector = ExecutionTraceCollector("heartbeat_agent")
agent = ToolCallingAgent(
    tools=tools,
    step_callbacks=collector.get_step_callbacks()
)
result = agent.run(task)
await collector.finalize(success=True)
```

**Other Dionysus Callbacks**:
- **Basin Callback** (`basin_callback.py`): Activates attractor basins during semantic recall
- **Memory Callback** (`memory_callback.py`): Prunes old observations to save tokens
- **IWMT Callback** (`iwmt_callback.py`): Injects coherence scores during planning

## Related Concepts

**Prerequisites** (understand these first):
- [[ooda-loop]] - Cognitive cycle pattern that smolagents implements
- [[active-inference]] - Theoretical foundation for planning intervals
- [[consciousness-pipeline]] - High-level cognitive architecture

**Builds Upon** (this uses):
- [[tool-calling]] - Mechanism for agent actions
- [[execution-trace]] - Decision path logging
- [[step-callback]] - Extension points for integration

**Used By** (depends on this):
- [[heartbeat-agent]] - Top-level OODA orchestrator
- [[consciousness-manager]] - Multi-agent cognitive coordinator
- [[perception-agent]] - OBSERVE phase specialist
- [[reasoning-agent]] - ORIENT phase specialist
- [[metacognition-agent]] - DECIDE phase specialist

**Related** (similar or complementary):
- [[mcp-bridge]] - Tool integration pattern
- [[attractor-basin]] - Semantic activation during agent runs
- [[iwmt-coherence]] - Metacognitive state injection

## Examples

### Example 1: HeartbeatAgent Execution

**Clinical Context**: System checks in during user's therapy planning session

**Code**:
```python
# Initialize agent with MCP tools
with HeartbeatAgent(model_id="dionysus-agents") as agent:
    context = {
        "heartbeat_number": 42,
        "current_energy": 15,
        "max_energy": 20,
        "user_present": True,
        "active_goals": [
            {"goal": "Help user prepare for difficult conversation", "priority": 0.9}
        ]
    }

    # Agent autonomously decides actions
    result = await agent.decide(context)

    # Execution trace shows decision path:
    # Step 1: semantic_recall("difficult conversation preparation")
    # Step 2: reflect_on_topic("conversation anxiety")
    # Step 3: PLANNING (reassess strategy)
    # Step 4: update_goal("Add grounding exercise")
    # Step 5: FINAL ANSWER (summary of actions taken)

print(result)
# "I recalled 3 past conversations about anxiety management.
#  Current user state suggests high activation. I've added
#  a grounding exercise to the preparation sequence and
#  prioritized emotional regulation techniques."
```

**Smolagents Features Used**:
- ToolCallingAgent for autonomous action selection
- planning_interval=3 triggered replanning at Step 3
- Step callbacks logged basin activations during semantic recall
- Execution trace persisted to Neo4j for meta-learning

### Example 2: ConsciousnessManager OODA Cycle

**Clinical Context**: User asks system to analyze their journal entry

**Code**:
```python
with ConsciousnessManager(model_id="dionysus-agents") as cm:
    context = {
        "task": "Analyze journal entry for emotional patterns",
        "journal_text": "Today felt overwhelming. Too many decisions...",
        "user_id": "user_123",
        "bootstrap_recall": True
    }

    result = await cm.run_ooda_cycle(context)

    # Orchestrator delegation pattern (from logs):
    # Step 1: "Ask perception to observe current journal state"
    #   → perception.run("Capture MOSAEIC from journal text")
    #   → Returns: {senses: "visual overwhelm", emotions: "anxiety"}
    #
    # Step 2: "Ask reasoning to analyze emotional patterns"
    #   → reasoning.run("Identify patterns in MOSAEIC data")
    #   → Returns: "Pattern: Decision paralysis correlates with overwhelm"
    #
    # Step 3: PLANNING (orchestrator reassesses)
    #   → IWMT coherence injected: 0.72 (moderate)
    #
    # Step 4: "Ask metacognition to recommend intervention"
    #   → metacognition.run("Suggest action based on pattern")
    #   → Returns: "Recommend decision-tree journaling exercise"
    #
    # Step 5: FINAL SYNTHESIS

print(result["final_plan"])
# "Analysis complete. Detected decision paralysis pattern
#  correlated with overwhelm state. Recommend structured
#  decision-tree journaling to reduce cognitive load."
```

**Smolagents Features Used**:
- CodeAgent as orchestrator with managed_agents
- Natural language delegation (no manual chaining)
- Tool isolation (perception has observe/recall, reasoning has analysis tools)
- Planning intervals triggered metacognitive assessment
- Rich agent descriptions guided delegation decisions

### Example 3: Custom Tool with Async Operations

**Technical Context**: Tool that queries Neo4j for attractor basins

**Code**:
```python
from smolagents import Tool
from pydantic import BaseModel, Field
from api.agents.resource_gate import async_tool_wrapper
from api.services.graphiti_service import get_graphiti_service

class BasinSearchOutput(BaseModel):
    query: str
    basins: List[str] = Field(..., description="Activated basin IDs")
    activations: List[float] = Field(..., description="Activation strengths")
    recommendation: str

class BasinSearchTool(Tool):
    name = "search_basins"
    description = "Search knowledge graph for semantic attractor basins"

    inputs = {
        "query": {
            "type": "string",
            "description": "Search query for semantic concepts"
        }
    }
    output_type = "any"

    def forward(self, query: str) -> dict:
        # Wrap async operations for smolagents sync interface
        async def _run_search():
            graphiti = await get_graphiti_service()
            results = await graphiti.search(
                f"attractor basins related to {query}",
                limit=10
            )

            basins = []
            activations = []
            for edge in results.get("edges", []):
                if edge.get("fact"):
                    basins.append(edge["fact"])
                    # Activation strength from edge weight
                    activations.append(edge.get("weight", 0.5))

            return basins, activations

        try:
            basins, activations = async_tool_wrapper(_run_search)()

            return BasinSearchOutput(
                query=query,
                basins=basins,
                activations=activations,
                recommendation=f"Found {len(basins)} relevant basins. "
                              f"Top activation: {max(activations):.2f}"
            ).model_dump()
        except Exception as e:
            return BasinSearchOutput(
                query=query,
                basins=[],
                activations=[],
                recommendation=f"Search failed: {str(e)}"
            ).model_dump()

# Add to agent
search_tool = BasinSearchTool()
agent = ToolCallingAgent(
    tools=[search_tool],
    model=model
)

result = agent.run("Find basins related to decision-making anxiety")
```

**Smolagents Patterns Demonstrated**:
- Class-based tool definition
- Pydantic output schema
- async_tool_wrapper for async operations in sync interface
- Graceful error handling with structured outputs

## Common Misconceptions

**Misconception 1**: "Smolagents is just another LangChain wrapper"
**Reality**: Smolagents is a ground-up redesign focused on production use. It's 10x lighter than LangChain, has native multi-agent support, and integrates cleanly with HuggingFace ecosystem. Dionysus migrated from LangChain specifically to reduce complexity and gain better control.

**Misconception 2**: "ManagedAgent requires a wrapper class"
**Reality**: In smolagents 1.23+, `ManagedAgent` class was removed. Agents with `name` and `description` attributes are passed directly to `managed_agents` parameter. The "ManagedAgent pattern" refers to this delegation approach, not a specific class.

**Misconception 3**: "Step callbacks slow down execution"
**Reality**: Callbacks are synchronous hooks that add minimal overhead (<1ms per step). Dionysus uses them for critical consciousness integration (basin activation, IWMT coherence) that would require separate API calls otherwise. Net result is faster overall execution.

**Misconception 4**: "Planning intervals disrupt agent flow"
**Reality**: Planning intervals map directly to Active Inference belief updates. Re-evaluating strategy every 3 steps prevents the agent from following outdated plans. In Dionysus heartbeat tests, planning intervals improved task completion by 23% (fewer dead-end paths).

**Misconception 5**: "Tools must be synchronous"
**Reality**: Tools must have a sync `forward()` method, but can call async operations internally using `async_tool_wrapper`. All Dionysus tools that query Neo4j, Graphiti, or LLMs use this pattern.

**Misconception 6**: "Execution traces are just for debugging"
**Reality**: In Dionysus, execution traces are persisted to Neo4j and used for meta-learning. The `MetaCognitiveLearner` analyzes past agent runs to recommend better tool choices and strategy adjustments for future tasks.

## When to Use

✅ **Use smolagents when**:
- Building autonomous agents that need to call tools and make multi-step decisions
- Implementing OODA loops or other cognitive architectures
- Orchestrating multiple specialized agents (perception, reasoning, metacognition)
- Need execution traces for debugging or meta-learning
- Require planning intervals for periodic reassessment
- Want clean integration with HuggingFace models and LiteLLM
- Need lightweight framework with minimal dependencies

❌ **Don't use smolagents when**:
- Simple single-shot LLM calls (use raw API)
- Workflow is fully deterministic with no autonomous decisions (use explicit orchestration)
- Need extremely low latency (<100ms) - agent overhead is 50-200ms
- Running on constrained devices (smolagents requires Python 3.9+, decent RAM)
- Already heavily invested in LangChain ecosystem and it's working

🤔 **Consider alternatives when**:
- **LangGraph**: Need complex state machines with strict cycle control
- **AutoGPT**: Want research-oriented agent with web browsing built-in
- **Microsoft Semantic Kernel**: Enterprise .NET integration required
- **Custom orchestration**: Have very specific control flow requirements

## Further Reading

**Research**:
- Active Inference and Free Energy Principle (Friston et al., 2012)
- OODA Loop (Boyd, 1976) - Military decision-making framework
- Metacognition and Self-Modeling (Proust, 2013)

**Documentation**:
- [Smolagents Official Docs](https://huggingface.co/docs/smolagents)
- [[ooda-loop]] - Cognitive cycle pattern
- [[heartbeat-agent]] - Top-level implementation
- [[consciousness-manager]] - Multi-agent orchestration
- [[execution-trace]] - Logging and persistence
- `specs/039-smolagents-v2-alignment/spec.md` - Migration specification

**Dionysus Implementation**:
- `api/agents/heartbeat_agent.py` - ToolCallingAgent with MCP bridge
- `api/agents/consciousness_manager.py` - Multi-agent orchestration
- `api/agents/managed/` - ManagedAgent wrappers (Perception, Reasoning, Metacognition)
- `api/agents/tools/` - Class-based tool implementations
- `api/agents/callbacks/` - Step callbacks for consciousness integration

---

**Author**: Dr. Mani Saint-Victor
**Last Updated**: 2026-01-02
**Status**: Production
**Integration Event**: smolagents v1.23+ migration (Feature 039) replaced LangChain/LangGraph architecture
