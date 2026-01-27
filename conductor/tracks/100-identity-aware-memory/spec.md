# Spec: 100 – Identity-Aware Memory Seeding

## Goal

Eliminate system amnesia by anchoring technical session journeys (`device_id`) to cognitive identity narratives (`AutobiographicalJourney`). This ensures the `ConsciousnessManager` always hydrates with the correct user context.

## 1. Identity Anchoring
Explicitly link `device_id` to a `participant_id` and an `AutobiographicalJourney`.

## 2. Recognition Logic
Implement a "Recognition Trigger" that hydrates the agent's identity from Neo4j upon session start.

## 3. Cross-Service Linkage
Ensure `ConsolidatedMemoryStore` and `SemanticRecall` filter by identity where appropriate.

## Scope
- `api/services/session_manager.py`
- `api/agents/consolidated_memory_stores.py`
- `api/agents/consciousness_manager.py`
- `dionysus_mcp/tools/recall.py`

## Success Criteria
- [ ] Identity is consistent across sessions for the same `device_id`.
- [ ] Recall only returns memories belonging to the current `device_id`/`participant_id`.
- [ ] The agent acknowledges user identity in the first response of a session.
