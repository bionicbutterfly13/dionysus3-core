# Plan: Feature 102 – Subconscious Integration

**Objective**: Integrate Hexis-style subconscious observation flow and Letta-style session subconscious API into Dionysus3 Core using Graphiti/MemEvolve/MemoryBasinRouter only.

## Integration (IO Map)

- **Attachment points**: `api/routers/subconscious.py`, `api/services/subconscious_service.py`, `api/main.py` (router registration). Optional: maintenance/scheduler calling `SubconsciousService.run_subconscious_decider()`.
- **Inlets**: Session-start/sync/ingest HTTP bodies; internal calls to `get_subconscious_context` / `run_subconscious_decider` (recent memories, trajectories, basin context from Graphiti/MemEvolve).
- **Outlets**: GraphitiService (persist_fact, extract_with_context), MemoryBasinRouter (route_memory), MemEvolveAdapter (ingest_trajectory / ingest_message). Sync API returns JSON (guidance, memory_blocks). No Postgres, no Letta.

## Phases

### Phase 1: Models and SubconsciousService (Hexis-style) [925e313]

- [x] Add Pydantic models for subconscious observations (`SubconsciousObservations`, narrative/relationship/contradiction/emotional/consolidation item types). [925e313]
- [x] Add `api/services/subconscious_service.py`:
  - `get_subconscious_context(agent_id?: str)` – build context dict from Graphiti search + recent trajectory summaries (from MemEvolveAdapter or Graphiti); return structure compatible with Hexis-style prompt (recent_memories, goals, etc. as we have them). [925e313]
  - `run_subconscious_decider(context: dict)` – call LLM with subconscious prompt (from prompt file or inline), return parsed observation dict. [925e313]
  - `apply_subconscious_observations(observations: SubconsciousObservations)` – map each observation kind to MemoryBasinRouter.route_memory() or GraphitiService.persist_fact(); no Postgres. [925e313]
- [x] Add subconscious prompt asset (inline in service as `SUBCONSCIOUS_PROMPT`) – adapt Hexis prompt to our JSON schema and memory model. [925e313]
- [x] Unit tests for SubconsciousService (mocked Graphiti/MemEvolve/MemoryBasinRouter) – `tests/unit/test_subconscious_service.py` (13 tests, all passing). [925e313]

### Phase 2: Session Subconscious API (Letta-style) [925e313]

- [x] Add `POST /subconscious/session-start` – body: `session_id`, optional `project_id`, optional `cwd`; store session in memory or lightweight in-memory/store; return 200. [925e313]
- [x] Add `GET /subconscious/sync` (or POST with session_id) – query param `session_id`; build guidance + memory_blocks from Graphiti recall + optional short LLM pass; return `{ "guidance": "...", "memory_blocks": { ... } }`. [925e313]
- [x] Add `POST /subconscious/ingest` – body: `session_id`, `transcript` or `summary`; call MemEvolveAdapter.ingest_message(); return 200. [925e313]
- [x] Register router in `api/main.py`. [925e313]

### Phase 3: Router and Contract Tests [925e313]

- [x] Create `api/routers/subconscious.py` – mount session-start, sync, ingest; `POST /subconscious/run-decider` for maintenance trigger. [925e313]
- [x] Contract tests: `tests/contract/test_subconscious_api.py` – session-start, sync, ingest, run-decider return expected shapes and status codes. [925e313]
- [x] Update plan.md with completion checkmarks. [925e313]

## Dependencies

- GraphitiService, MemEvolveAdapter, MemoryBasinRouter, llm_service (chat_completion).
- Existing Hexis integration (042) for consent/boundaries only; no shared DB.

## Branch

`feature/102-subconscious-integration`
