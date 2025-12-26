# Data Model: Smolagents Integration

**Feature**: 009-smolagents-integration | **Date**: 2025-12-25

## Entities

### CognitiveAgent

Represents a smolagent configured for a specific cognitive function.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique agent identifier |
| `name` | string | Yes | Agent name (e.g., "perception", "metacognition") |
| `layer` | enum | Yes | Cognitive layer: `perceptual`, `conceptual`, `abstract`, `metacognitive`, `consciousness` |
| `agent_type` | enum | Yes | `code_agent` or `tool_calling_agent` |
| `model_id` | string | Yes | LiteLLM model ID (e.g., "anthropic/claude-sonnet-4-20250514") |
| `temperature` | float | No | Model temperature (default: 0.2) |
| `max_steps` | int | No | Maximum execution steps (default: 10) |
| `tools` | list[string] | Yes | Tool names available to this agent |
| `description` | string | Yes | Description for manager delegation decisions |
| `is_manager` | bool | No | Whether this agent manages other agents (default: false) |
| `managed_agent_ids` | list[UUID] | No | IDs of agents this manager controls |
| `created_at` | datetime | Yes | Creation timestamp |
| `updated_at` | datetime | Yes | Last update timestamp |

**Constraints**:
- `name` must be unique per layer
- `consciousness` layer agents must have `is_manager=true`
- `max_steps` range: 1-50 (spec default: 10)

**State Transitions**: None (agents are configuration, not stateful)

---

### AgentExecution

A record of agent code execution for audit and debugging.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique execution identifier |
| `agent_id` | UUID | Yes | FK to CognitiveAgent |
| `heartbeat_id` | UUID | No | FK to heartbeat cycle that triggered this execution |
| `task` | string | Yes | Input task/prompt given to agent |
| `status` | enum | Yes | `running`, `completed`, `failed`, `timeout` |
| `steps` | list[ExecutionStep] | Yes | Ordered list of execution steps |
| `final_answer` | string | No | Agent's final output (null if failed) |
| `error` | string | No | Error message if failed |
| `duration_ms` | int | No | Total execution time in milliseconds |
| `tokens_used` | int | No | Total tokens consumed |
| `started_at` | datetime | Yes | Execution start time |
| `completed_at` | datetime | No | Execution end time |

**Constraints**:
- `status` must be `completed` or `failed` if `completed_at` is set
- `duration_ms` = `completed_at - started_at`

---

### ExecutionStep

A single step within an agent execution (embedded in AgentExecution).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step_number` | int | Yes | 1-based step index |
| `step_type` | enum | Yes | `thought`, `code`, `tool_call`, `observation`, `error` |
| `content` | string | Yes | Step content (thought text, generated code, tool output) |
| `tool_name` | string | No | Tool invoked (if step_type=tool_call) |
| `tool_input` | dict | No | Tool input arguments |
| `tool_output` | string | No | Tool output result |
| `duration_ms` | int | No | Step execution time |
| `timestamp` | datetime | Yes | When step occurred |

---

### SandboxConfiguration

Settings defining the execution environment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Configuration identifier |
| `name` | string | Yes | Configuration name (e.g., "production", "development") |
| `executor_type` | enum | Yes | `docker`, `local`, `e2b` |
| `timeout_seconds` | int | Yes | Execution timeout (spec default: 30) |
| `step_limit` | int | Yes | Max steps per agent (spec default: 10) |
| `memory_limit_mb` | int | No | Container memory limit (default: 512) |
| `cpu_quota` | int | No | CPU quota (default: 50000 = 50%) |
| `allowed_imports` | list[string] | Yes | Whitelisted Python modules |
| `network_enabled` | bool | No | Allow network access (default: false) |
| `is_default` | bool | No | Use as default configuration |
| `created_at` | datetime | Yes | Creation timestamp |

**Constraints**:
- Only one configuration can have `is_default=true`
- `timeout_seconds` range: 5-120
- `step_limit` range: 1-50

**Default allowed_imports**:
```python
["json", "datetime", "math", "re", "collections", "itertools", "statistics", "time"]
```

---

### CognitiveTool

A dionysus cognitive capability wrapped as a smolagents Tool.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name (e.g., "semantic_recall", "revise_model") |
| `description` | string | Yes | Tool description for LLM |
| `inputs` | dict | Yes | Input schema (smolagents format) |
| `output_type` | string | Yes | Return type: `string`, `dict`, `list` |
| `source` | enum | Yes | `mcp` (from dionysus_mcp) or `handler` (converted ActionHandler) |
| `handler_class` | string | No | Original ActionHandler class name (if source=handler) |
| `mcp_tool_name` | string | No | Original MCP tool name (if source=mcp) |
| `energy_cost` | int | No | Energy cost for heartbeat budgeting |

**Constraints**:
- `name` must be unique
- Either `handler_class` or `mcp_tool_name` must be set based on `source`

---

## Relationships

```
CognitiveAgent 1──N AgentExecution
     │
     └── N──N CognitiveAgent (manager → managed)

SandboxConfiguration 1──N AgentExecution

CognitiveTool N──N CognitiveAgent (agent has tools)
```

---

## Database Schema (PostgreSQL)

```sql
-- Cognitive agents configuration
CREATE TABLE cognitive_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    layer VARCHAR(50) NOT NULL CHECK (layer IN ('perceptual', 'conceptual', 'abstract', 'metacognitive', 'consciousness')),
    agent_type VARCHAR(50) NOT NULL CHECK (agent_type IN ('code_agent', 'tool_calling_agent')),
    model_id VARCHAR(200) NOT NULL,
    temperature FLOAT DEFAULT 0.2,
    max_steps INT DEFAULT 10 CHECK (max_steps BETWEEN 1 AND 50),
    tools TEXT[] NOT NULL DEFAULT '{}',
    description TEXT NOT NULL,
    is_manager BOOLEAN DEFAULT FALSE,
    managed_agent_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, layer)
);

-- Agent execution audit log
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES cognitive_agents(id),
    heartbeat_id UUID,
    task TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'timeout')),
    steps JSONB NOT NULL DEFAULT '[]',
    final_answer TEXT,
    error TEXT,
    duration_ms INT,
    tokens_used INT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_agent_executions_agent ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_heartbeat ON agent_executions(heartbeat_id);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);

-- Sandbox configurations
CREATE TABLE sandbox_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    executor_type VARCHAR(20) NOT NULL CHECK (executor_type IN ('docker', 'local', 'e2b')),
    timeout_seconds INT NOT NULL DEFAULT 30 CHECK (timeout_seconds BETWEEN 5 AND 120),
    step_limit INT NOT NULL DEFAULT 10 CHECK (step_limit BETWEEN 1 AND 50),
    memory_limit_mb INT DEFAULT 512,
    cpu_quota INT DEFAULT 50000,
    allowed_imports TEXT[] NOT NULL DEFAULT ARRAY['json', 'datetime', 'math', 're', 'collections', 'itertools', 'statistics', 'time'],
    network_enabled BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure only one default configuration
CREATE UNIQUE INDEX idx_sandbox_default ON sandbox_configurations(is_default) WHERE is_default = TRUE;

-- Cognitive tools registry
CREATE TABLE cognitive_tools (
    name VARCHAR(100) PRIMARY KEY,
    description TEXT NOT NULL,
    inputs JSONB NOT NULL,
    output_type VARCHAR(20) NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('mcp', 'handler')),
    handler_class VARCHAR(200),
    mcp_tool_name VARCHAR(200),
    energy_cost INT DEFAULT 1
);
```

---

## Migration Notes

- **New tables**: All tables are new; no migration from existing schema
- **Reversible**: DROP TABLE statements for rollback
- **Dependencies**: Requires existing `heartbeats` table for FK (optional)
