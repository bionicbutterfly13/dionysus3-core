# Spec: 099 – Memory Amnesia Fix

## Goal

Eliminate "brain dead / amnesic" agent behavior by wiring three pillars consistently:

1. **Bootstrap recall** – inject past context at session/cycle start.
2. **Reliable ingest** – persist agent output (decisions, narratives) through the memory stack after each cycle.
3. **Pre-prune memory flush** – before trimming in-memory steps, flush durable content to long-term memory via the gateway.

## Scope

- **In scope:** Heartbeat/OODA path (ConsciousnessManager, HeartbeatService), memory pruning callback, MemoryBasinRouter → MemEvolve → Graphiti flow.
- **Out of scope:** Refactoring ContextBuilder or basin callback off direct Neo4j (separate integrity work); changing MemEvolve/Graphiti internals.

## Success Criteria

- [ ] Bootstrap recall receives a non-empty `task` (or equivalent) so retrieval is query-driven.
- [ ] Every completed heartbeat narratives + key reasoning are routed through `route_memory` and ingested.
- [ ] When pruning old agent steps, we first `route_memory` the content we are about to drop, then prune. Failures in flush must not block pruning.

## Constraints

- Follow Memory Stack Integration Pattern (`.conductor/constraints.md`): all memory writes go through `MemoryBasinRouter.route_memory` or approved gateway.
- No new direct Neo4j access.

## References

- `api/services/bootstrap_recall_service.py` – bootstrap recall.
- `api/services/memory_basin_router.py` – `route_memory`.
- `api/services/heartbeat_service.py` – `_make_decision`, Phase 6 Record.
- `api/agents/callbacks/memory_callback.py` – pruning.
