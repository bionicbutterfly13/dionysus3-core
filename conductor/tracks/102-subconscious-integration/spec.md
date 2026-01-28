# Spec: Feature 102 – Subconscious Integration

**Objective**: Extract and integrate subconscious patterns from Hexis and Letta-Claude-Subconscious into Dionysus3 Core using our memory stack (Graphiti, MemEvolve, MemoryBasinRouter). No direct DB or external service dependencies; wrappers/adapters only.

## Context

- **Hexis** (Postgres): Maintenance tick runs a "subconscious decider" – gets context from DB, LLM produces observation JSON (narrative, relationship, contradiction, emotional, consolidation), then applies observations back to DB. We adopt the **observation taxonomy and flow**; we do not use Postgres.
- **Letta-Claude-Subconscious** (TypeScript/Letta): Session-start, before-prompt (sync memory to CLAUDE.md), after-response (send transcript to Letta). We adopt the **session lifecycle and memory-block concept**; we do not call Letta. Our API becomes the backend for a future Cursor/Claude plugin that syncs to our API instead of Letta.

## Requirements

1. **Subconscious maintenance (Hexis-style)**  
   - Build "subconscious context" from our memory (Graphiti/MemEvolve recall, recent trajectories, basin context).  
   - Run one LLM call with a subconscious observation prompt (JSON out).  
   - Apply observations: route narrative/relationship/contradiction/emotional/consolidation items through MemoryBasinRouter / GraphitiService (strategic facts, relationships, contradictions). No Postgres.

2. **Session subconscious API (Letta-style)**  
   - **Session start**: `POST /subconscious/session-start` – register session, optional project_id.  
   - **Sync (before prompt)**: `GET/POST /subconscious/sync` – return guidance/memory blocks for a session (e.g. guidance, user_preferences, project_context, pending_items) derived from our memory + optional short LLM summary.  
   - **Ingest (after response)**: `POST /subconscious/ingest` – accept transcript or session summary; store via MemEvolveAdapter / MemoryBasinRouter so it feeds future context.

3. **No orphan code**  
   - All endpoints and services must be reachable from API or scheduled/maintenance entry points. Document inlets/outlets.

4. **Gateway only**  
   - All persistence via GraphitiService / MemEvolveAdapter / MemoryBasinRouter. No new Neo4j driver, no Postgres, no Letta/Hexis direct calls.

## Success Criteria

- SubconsciousService: `get_subconscious_context()`, `run_subconscious_decider()`, `apply_subconscious_observations()` implemented against our memory stack.  
- Session API: session-start, sync, ingest implemented and wired to same memory stack.  
- Contract tests for subconscious router; unit tests for SubconsciousService.  
- Plan.md Integration (IO Map) updated with attachment points and data flow.
