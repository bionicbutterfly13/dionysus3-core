# Coordination Pool (Spec 020) Quickstart

## API
- `POST /api/coordination/agents` → spawn an agent `{agent_id, context_window_id, status}`
- `GET /api/coordination/agents` → list agents with health/performance/isolation
- `POST /api/coordination/tasks` → submit task payload (optional `preferred_agent_id`)
- `POST /api/coordination/tasks/{task_id}/complete` → mark success/failure
- `GET /api/coordination/metrics` → `{agents, tasks_total, tasks_in_progress, queue_length, avg_task_duration}`

## Smolagent Tools
- `spawn_coordination_agent()`
- `submit_coordination_task(payload, preferred_agent_id=None)`
- `complete_coordination_task(task_id, success=True)`
- `coordination_metrics()`

## Notes
- Isolation guardrails detect context_window_id collisions and flag in health report.
- Metrics include average task duration; more detailed utilization can be added for Spec 023.
