# Quickstart: Meta-ToT Engine Integration

## Prerequisites

- Run API server: `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
- Ensure Neo4j + n8n workflows are configured if you want trace persistence

## Example: Use Meta-ToT via Agent Tool

1. Run the consciousness manager with a task that includes a planning prompt.
2. The reasoning agent can call `meta_tot_decide` to see if Meta-ToT should run.
3. If recommended, call `meta_tot_run` with the task and context.

Example prompt fragment (agent input):
```
Assess whether Meta-ToT is needed for this planning task. If recommended, run Meta-ToT and summarize the selected path.
```

## Example: Use Meta-ToT via API

```
POST /api/meta-tot/run
{
  "task": "Create a 90-day marketing strategy for a new AI coaching product",
  "context": {"goal": "pipeline growth", "constraints": ["budget", "compliance"]}
}
```

Expected response includes:
- decision (mode + rationale)
- selected path
- branch metrics
- trace id (if persistence succeeded)
