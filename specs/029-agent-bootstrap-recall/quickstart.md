# Quickstart: Agent Bootstrap Recall

## Initialization
The bootstrap recall is automatically triggered by the `ConsciousnessManager`. No manual setup is required if the feature is enabled in the configuration.

## Usage in Tasks
When submitting a task to the `CoordinationPool`, you can explicitly toggle bootstrap recall:

```json
{
  "payload": {
    "task": "Refactor Feature 020",
    "bootstrap_recall": true,
    "project_id": "dionysus-core"
  }
}
```

## Verification
1. **Logs**: Look for `bootstrap_recall_started` and `bootstrap_recall_completed` events in the service logs.
2. **Agent Context**: Check the `initial_context` or `orchestrator_log`. You should see:
   ```markdown
   ## Past Context
   Relevant memories from project: dionysus-core
   - [Memory 1] ...
   - [Memory 2] ...
   ```

## Development & Testing
Run unit tests to verify retrieval logic:
```bash
docker exec dionysus-api pytest tests/unit/test_bootstrap_recall.py
```
