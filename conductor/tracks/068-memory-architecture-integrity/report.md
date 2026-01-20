# Memory Architecture Integrity Audit Report

## Scope
- Nemori: `api/services/nemori_river_flow.py`
- MemEvolve: `api/services/memevolve_adapter.py`
- Graphiti: `api/services/graphiti_service.py`
- Consolidated store: `api/agents/consolidated_memory_stores.py`
- Webhook shim: `api/services/webhook_neo4j_driver.py`

## Correct Usage Observations
- GraphitiService is the only module importing `neo4j` in `api/`.
- WebhookNeo4jDriver proxies all Cypher to MemEvolveAdapter, which in turn calls GraphitiService.
- ConsolidatedMemoryStore uses WebhookNeo4jDriver, so Nemori River Flow writes ultimately route through Graphiti.
- MemEvolveAdapter ingests trajectories via GraphitiService and offers an `execute_cypher` proxy.

## Integrity Gaps / Risks
- Nemori predict-calibrate distills facts into the consolidated store but does not persist explicit Graphiti fact nodes or bi-temporal fact metadata (see Track 041 tasks T041-028/T041-029).
- Direct Graphiti usage remains widespread across services/routers/tools (bypassing MemEvolve pipeline benefits like trajectory tracking and audit logging).
- Dual-path behavior exists in MemEvolveAdapter (Graphiti direct + optional webhook), which complicates enforcing a single gateway policy.

## Other Agent Progress Signals
- Recent commits touching memory architecture: `aad42fa`, `b5ee7b2`, `d73344f`, `099359e`, `b71af22`.
- Track 057 (Memory Systems Integration) is marked Done; Track 041 Phase 7 Nemori + MemEvolve tasks remain open.
- Current worktree shows no uncommitted changes in Nemori/Graphiti/MemEvolve files, suggesting no in-flight edits right now.
- Untracked scripts `scripts/ingest_vigilant_sentinel*.py` indicate recent work on ingestion workflows.

## Recommended Processing Flow (System-Wide)
1. Classify incoming content via MemoryBasinRouter to set basin metadata (conceptual/strategic/etc).
2. Build a MemEvolve Trajectory with metadata (session_id, project_id, memory_type, basin_id).
3. Ingest via MemEvolveAdapter to trigger Graphiti extraction + storage.
4. Use Nemori predict-calibrate to distill semantic facts and attach basin/blanket metadata.
5. Persist distillates to Graphiti with bi-temporal fields for recall + evolution.

## Single-Entry Formalization Direction
- Define a MemoryGateway interface (write + recall) as the only allowed entrypoint.
- Route Nemori, tools, routers, and services through MemoryGateway.
- Enforce with lint rules / tests that forbid direct GraphitiService imports outside the gateway.
- Migrate direct Graphiti callers to MemEvolveAdapter or the new gateway, keeping Graphiti isolated.
