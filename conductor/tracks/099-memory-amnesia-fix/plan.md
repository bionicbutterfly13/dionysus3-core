# Plan: 099 – Memory Amnesia Fix

## Phase 1: Bootstrap recall task wiring

- [x] **T099-001: Set `task` in OODA initial_context.**  
  - **Where:** `HeartbeatService._make_decision` when building `initial_context` for `ConsciousnessManager.run_ooda_cycle`.  
  - **What:** Add `task` (and `project_id` if missing) so bootstrap recall has a concrete query. Use e.g. `"Heartbeat {N} decision. Active goals: {titles}."` or similar.  
  - **Acceptance:** Bootstrap runs with non-empty query; recall results are relevant to the cycle.

## Phase 2: Ingest after heartbeat

- [x] **T099-002: Route heartbeat narrative + reasoning through MemoryBasinRouter.**  
  - **Where:** `HeartbeatService.heartbeat()`, Phase 6 Record, after `_generate_narrative` and `_record_heartbeat`.  
  - **What:** Call `get_memory_basin_router().route_memory(content=..., source_id="heartbeat")` with combined narrative + decision reasoning. Catch exceptions so memory failures do not fail the heartbeat.  
  - **Acceptance:** Each completed heartbeat results in a `route_memory` call; ingest flows through existing pipeline.

## Phase 3: Pre-prune memory flush

- [x] **T099-003: Flush step content to memory before pruning.**  
  - **Where:** `api/agents/callbacks/memory_callback.py` – `memory_pruning_callback`.  
  - **What:** Before pruning observations, collect full text from steps we are about to prune. Call `route_memory` with that content (fire-and-forget from sync callback, e.g. via `asyncio.run_coroutine_threadsafe` or equivalent). Then perform existing pruning. Ensure flush failures never block or break pruning.  
  - **Acceptance:** Pruning runs unchanged; durable content from pruned steps is passed to the memory stack when possible.

## Phase 4: Verification

- [x] **T099-004: Tests and sanity checks.**  
  - **What:** Unit test(s) or minimal integration checks that (a) `task` is set for bootstrap, (b) `route_memory` is invoked after heartbeat record, (c) flush logic runs before prune and does not break the callback.  
  - **Acceptance:** New/modified code paths covered; existing heartbeat and memory tests still pass.

## Notes

- Keep changes minimal and localized. No refactors of MemEvolve, Graphiti, or multi-tier lifecycle unless required for the above.