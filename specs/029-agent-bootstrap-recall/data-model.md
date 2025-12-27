# Data Model: Agent Bootstrap Recall

**Feature**: 029-agent-bootstrap-recall

## Entities

### BootstrapConfig (Pydantic Model)
Configuration for how recall is handled for a specific request.

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `bool` | Toggle for bootstrap recall (default: True) |
| `max_tokens` | `int` | Hard limit for injected context (default: 2000) |
| `project_id` | `str` | Mandatory scoping ID |
| `include_trajectories` | `bool` | Whether to fetch episodic history (default: True) |

### BootstrapResult (Pydantic Model)
The output of the recall process injected into the agent.

| Field | Type | Description |
|-------|------|-------------|
| `formatted_context` | `str` | Markdown formatted string for injection |
| `source_count` | `int` | Number of distinct memories found |
| `summarized` | `bool` | Whether LLM summarization was triggered |
| `latency_ms` | `float` | Total retrieval and formatting time |

## Relationships
- **ConsciousnessManager** (1) ── (1) **BootstrapRecallService**
- **BootstrapRecallService** (1) ── (*) **VectorSearchService**
- **BootstrapRecallService** (1) ── (*) **GraphitiService**
