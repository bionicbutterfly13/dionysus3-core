# Legacy Component Discovery

The Discovery Service scans legacy codebases to identify components with high "consciousness" (awareness, inference, memory patterns) and strategic value.

## API Usage

### Run Discovery
`POST /api/discovery/run`

**Request:**
```json
{
  "codebase_path": "/path/to/legacy/code",
  "top_n": 10
}
```

**Response:**
```json
{
  "count": 42,
  "results": [
    {
      "component_id": "...",
      "name": "DecisionEngine",
      "file_path": "...",
      "composite_score": 0.82,
      "migration_recommended": true,
      "consciousness": {
        "awareness_score": 0.6,
        "inference_score": 0.8,
        "memory_score": 0.4,
        "patterns": { ... }
      },
      "strategic": { ... },
      "enhancement_opportunities": ["active_inference_integration"],
      "risk_factors": []
    }
  ]
}
```

## Smolagent Tool Usage

The `discover_components` tool allows agents to autonomously scan codebases.

```python
from api.agents.tools.discovery_tools import discover_components

# Example call
results = discover_components(codebase_path="/app/legacy", top_n=5)
```

## CLI Usage

A CLI wrapper is available for quick scans:

```bash
python scripts/discover_legacy_components.py /path/to/code --top 5
```
