# Memory Amnesia Fix (Track 099) – Implemented

## Why

- Dionysus was "brain dead / amnesic": bootstrap recall had no task query, heartbeat output wasn't ingested, and pruning dropped step content without flushing to long-term memory.
- Align with the Clawdbot-style loop: **bootstrap recall** + **reliable ingest** + **pre-compaction flush**.

## What Changed

1. **Bootstrap recall task (T099-001)**  
   - In `HeartbeatService._make_decision`, we now set `initial_context["task"]` to  
     `"Heartbeat {N} decision. Active goals: {titles}."`  
   - Bootstrap recall uses this as the retrieval query instead of an empty string.

2. **Ingest after heartbeat (T099-002)**  
   - In Phase 6 Record, after `_record_heartbeat`, we call  
     `_route_heartbeat_memory(summary)`, which uses  
     `get_memory_basin_router().route_memory(narrative + reasoning, source_id="heartbeat:N")`.  
   - Exceptions are caught and logged; heartbeat never fails due to memory route failures.

3. **Pre-prune memory flush (T099-003)**  
   - In `memory_pruning_callback`, before pruning we collect the full observation text from steps we're about to prune, build a flush payload (capped by `AGENT_PRUNE_FLUSH_MAX_CHARS`), and schedule  
     `_flush_pruned_steps_to_memory` via `asyncio.run_coroutine_threadsafe` (fire-and-forget).  
   - Flush runs only when `asyncio.get_running_loop()` exists (e.g. real agent loop); sync tests skip it.  
   - Pruning then runs as before. Flush failures never block or break pruning.

4. **Tests (T099-004)**  
   - `tests/unit/test_memory_amnesia_fix.py`: task set for bootstrap, `_route_heartbeat_memory` called and error-safe, flush swallows router errors.  
   - All OODA heartbeat and memory-gateway unit tests still pass.

## Files Touched

- `api/services/heartbeat_service.py`: task wiring, `_route_heartbeat_memory`, Phase 6 hook.
- `api/agents/callbacks/memory_callback.py`: pre-prune flush, `_flush_pruned_steps_to_memory`, flush-only-when-loop.
- `conductor/tracks/099-memory-amnesia-fix/spec.md`, `plan.md`.
- `conductor/tracks.md`: 099 track added.
- `tests/unit/test_memory_amnesia_fix.py`: new.

## Notes

- Memory stack (MemoryBasinRouter → MemEvolve → Graphiti) unchanged; we only wire call sites.
- Pre-prune flush is best-effort. When there's no running event loop, we skip it to avoid hangs in tests.
