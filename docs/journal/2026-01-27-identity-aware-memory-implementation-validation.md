---
title: "Identity-Aware Memory Continuity — Implementation Validation"
date: 2026-01-27
tags: [identity, memory, session-manager, reconstruction, consciousness-manager, validation]
---

# Validation: Architectural Elaboration — Identity-Aware Memory Continuity

This document checks the **validity and completeness** of the implementation described in "Architectural Elaboration: Identity-Aware Memory Continuity" against the current codebase.

---

## 1. Identity Anchoring: Double-Punch Protocol

### Claims checked

| Claim | Status | Evidence |
|-------|--------|---------|
| WebhookNeo4jDriver shim (Port 8000 gateway) acts as async bridge; CREATE can return `[]` | **Valid** | `api/services/session_manager.py` uses `get_neo4j_driver()` from `api/services/remote_sync.py`, which returns `WebhookNeo4jDriver()`. Driver is the webhook-backed Neo4j bridge. |
| `SessionManager.get_or_create_journey(device_id, participant_id)` | **Valid** | `api/services/session_manager.py` L130: `async def get_or_create_journey(self, device_id: UUID, participant_id: Optional[str] = None)`. |
| Step A – Guard Match: `_driver.execute_query(query_match, {"device_id": ...})` | **Valid** | L143–151: `query_match` MATCHes `(j:Journey {device_id: $device_id})`; `result = await self._driver.execute_query(query_match, {"device_id": str(device_id)})`. |
| Step B – Double-Punch CREATE: new `journey_id` (UUID), then CREATE | **Valid** | L155–172: `new_id = str(uuid4())`, `query_create` CREATEs `(j:Journey)` with `SET j.device_id, j.id, ...`, then `execute_query(query_create, {...})`. |
| Step C – Shim Protection Match: if CREATE returns `[]`, re-run MATCH | **Valid** | L175–177: `if not result: result = await self._driver.execute_query(query_match, {"device_id": str(device_id)})`. |
| Step D – Optimistic Persistence: if still empty, return constructed `JourneyWithStats` | **Valid** | L179–192: `if not result:` → `return JourneyWithStats(id=UUID(new_id), device_id=device_id, ..., is_new=True)`. |
| Labels `:Journey:AutobiographicalJourney` | **Invalid** | SessionManager CREATE uses only `CREATE (j:Journey)` and `SET j.*`. No `:AutobiographicalJourney` label is ever set. |

### Verdict (Section 1)

**Mostly valid.** The double-punch and shim-protection logic are implemented as described. The **only incorrect claim** is “labels :Journey:AutobiographicalJourney.” The writer uses a single label `:Journey`. The *reader* (`ConsolidatedMemoryStore.get_active_journey`) matches both `(j:AutobiographicalJourney OR j:Journey)` and maps a technical `:Journey` to an `AutobiographicalJourney` DTO when returning (L212–221 in `consolidated_memory_stores.py`), but the SessionManager never creates or syncs an `:AutobiographicalJourney` node.

---

## 2. Cognitive Coherence: Anchoring the MARK_I Event

### Claims checked

| Claim | Status | Evidence |
|-------|--------|---------|
| `DevelopmentEvent` has `device_id` and `journey_id` as first-class fields | **Valid** | `api/models/autobiographical.py` L182–183: `device_id: Optional[str]`, `journey_id: Optional[str]` on `DevelopmentEvent`. |
| `ConsolidatedMemoryStore.store_event(event: DevelopmentEvent)` | **Valid** | `api/agents/consolidated_memory_stores.py` L24–25: `async def store_event(self, event: DevelopmentEvent) -> bool`. |
| Cypher: `MERGE (j:Journey {id: $journey_id})` and `MERGE (e)-[:BELONGS_TO]->(j)` | **Valid** | L30–34: `FOREACH (_ IN CASE WHEN $journey_id IS NOT NULL ... MERGE (j:Journey {id: $journey_id}) MERGE (e)-[:BELONGS_TO]->(j))`. Alternative when `journey_id` is null: `MERGE (j2:Journey {device_id: $device_id})` and `(e)-[:BELONGS_TO]->(j2)`. |
| Event carries `journey_id` from SessionManager | **Valid** | Model and Cypher support it; callers are responsible for passing a `DevelopmentEvent` that includes `journey_id` from the session/journey resolution. |

### Verdict (Section 2)

**Valid and complete.** Model fields, `store_event`, and identity anchoring via `BELONGS_TO` to `Journey` (by `journey_id` or `device_id`) match the doc.

---

## 3. Context Isolation: Identity-Aware Scanning

### Claims checked

| Claim | Status | Evidence |
|-------|--------|---------|
| `ReconstructionService._scan_sessions(context)` uses `context.device_id` and `context.project_id` | **Valid** | `api/services/reconstruction_service.py` L396–408: `_scan_sessions` builds `payload["filters"]` with `"project_id": context.project_id`, `"device_id": context.device_id`, `"from_date": cutoff.isoformat()` and POSTs to `self.n8n_recall_url`. |
| “n8n Recall Webhook” / filters payload | **Valid** | L409–410: `async with httpx.AsyncClient(...)` then `await client.post(self.n8n_recall_url, json=payload)`. `n8n_recall_url` from config (e.g. `N8N_RECALL_URL`). |
| `ReconstructionContext` has `device_id` and `project_id` | **Valid** | L102–121: `ReconstructionContext` has `device_id: Optional[str] = None`, `project_id` derived in `__post_init__` from `project_path` (hash) if not set. |
| Session reconstruct request supplies `device_id` | **Valid** | `api/routers/session.py` L181–186: `ReconstructionContext(..., device_id=request.device_id, ...)`. |
| “device_id is propagated into semantic_recall_tool” / “GraphitiService.search(query, group_id, …)” so only that identity’s facts/episodes surface | **Invalid** | `_scan_episodic_memories` (L364–394) builds `query` from `context.project_name` and `context.cues`, then `results = await graphiti.search(query=query, limit=self.config.MAX_EPISODIC)`. It does **not** pass `group_ids` or `device_id`. `GraphitiService.search` accepts `group_ids` (L863–867), but reconstruction never uses it. Episodic scan is therefore **not** identity-scoped by device or group. |

### Verdict (Section 3)

**Partially valid.** Session-level identity isolation is implemented: n8n recall filters by `device_id` and `project_id`. **Episodic (Graphiti) scan is not identity-aware** in the current code; the doc’s claim that “Only ‘Facts’ and ‘Episodes’ created by the specific identity are surfaced” is not implemented for the Graphiti path.

---

## 4. Recognition: “Welcome Handshake”

### Claims checked

| Claim | Status | Evidence |
|-------|--------|----------|
| “ConsciousnessManager._build_ooda_prompt(context)” | **Invalid** | No method `_build_ooda_prompt` exists. OODA flow is `run_ooda_cycle` → `_run_ooda_cycle`. |
| “SessionManager looks for a BiographicalConstraintCell in the session’s active memory” | **Misleading** | The implementation does not “look for” an existing cell. It builds a **new** `BiographicalConstraintCell` from the active journey: `_fetch_biographical_context` uses `store.get_active_journey(device_id=device_id)` then constructs a `BiographicalConstraintCell` from that journey (L837–850 in `consciousness_manager.py`). |
| Prompt contains “Welcome back. Your biographical journey is active (ID: $JRNY_ID). Unified labels for :Journey and :AutobiographicalJourney are synchronized.” | **Invalid** | This exact text does not appear anywhere. Biography is injected as `biographical_constraints` = `biographical_cell.content`, which is the XML from `BiographicalConstraintCell` (journey, themes, markers, arcs) in `api/services/context_packaging.py` L161–181. |
| “Prompt now acknowledges the 149 specialized agents” / “Collaborative Roster” / “pytest-master, document-architect, memory-weaver” | **Invalid** | No code in `api/agents/` or `api/services/` injects a “Collaborative Roster” or 149-agent list into the OODA prompt. The 149-agent roster is defined in `.cursor/rules/conductor-wake-up.mdc` (“149 specialized agents at ~/.claude/agents/”) as rule text, not as prompt content built by ConsciousnessManager. |

### Verdict (Section 4)

**Partially valid, with important gaps.** Biography **is** used: `_fetch_biographical_context` loads the active journey by `device_id`, builds a `BiographicalConstraintCell`, and injects `initial_context["biographical_constraints"]`. So the “limbic” idea (identity-aware context) is implemented. The doc, however, invents a method name (`_build_ooda_prompt`), a specific “Welcome back…” sentence, and a “Collaborative Roster” / 149-agent prompt block that **do not exist** in the codebase.

---

## 5. Edge Cases and Extra Claims

| Claim | Status | Evidence |
|-------|--------|----------|
| Race conditions: one MATCH, one MERGE; SessionManager always returns a valid object | **Consistent** | Match-then-create and optimistic persistence support this. No explicit distributed locking; behavior is as described for single-shim usage. |
| “MATCH (e:DevelopmentEvent {device_id: $id}) ORDER BY e.timestamp” for reconstruction if :HAS_EPISODE is missing | **Not verified** | This Cypher is not present in `reconstruction_service.py` or `consolidated_memory_stores.py` in the reviewed paths. May exist elsewhere or be aspirational. |
| “Mock protection for GraphitiConfig in tests” | **Not verified** | Not re-checked in this pass; left as-is. |

---

## 6. Bug Found During Validation

**context_packaging.py** (L716–718): `fetch_biographical_context` imports and calls `ConsolidatedMemoryStores()` (plural). The module actually defines `ConsolidatedMemoryStore` (singular) and `get_consolidated_memory_store()`. This will raise `ImportError` when `fetch_biographical_context` is exercised. It should use `get_consolidated_memory_store()` or `ConsolidatedMemoryStore()`.

---

## Summary

| Section | Verdict | Correct |
|---------|---------|---------|
| 1. Identity Anchoring (Double-Punch) | Mostly valid | Guard match, CREATE, shim re-MATCH, optimistic return all match. |
| 1. Labels | Invalid | Doc says `:Journey:AutobiographicalJourney`; only `:Journey` is created. |
| 2. Cognitive Coherence (MARK_I) | Valid | `DevelopmentEvent` fields and `store_event` + `BELONGS_TO` anchoring match. |
| 3. Context Isolation – Sessions | Valid | `device_id`/`project_id` in reconstruction context and n8n filters are correct. |
| 3. Context Isolation – Graphiti | Invalid | Episodic scan does not pass `device_id`/`group_ids` to Graphiti; not identity-scoped. |
| 4. Recognition – Biography | Partially valid | Journey → BiographicalConstraintCell injection exists; “Welcome back” / “Collaborative Roster” do not. |
| 4. Recognition – Method name | Invalid | No `_build_ooda_prompt`; OODA entrypoint is `_run_ooda_cycle`. |
| 4. Recognition – 149 agents in prompt | Invalid | Roster lives in conductor-wake-up rule, not in ConsciousnessManager prompt. |

**Recommendations**

1. **Doc:** Fix the label claim to “`:Journey` only at create time; reader treats `:Journey` and `:AutobiographicalJourney` for compatibility.”
2. **Doc:** Replace “_build_ooda_prompt” with “_run_ooda_cycle and _fetch_biographical_context,” and drop or soften the “Welcome back…” and “Collaborative Roster” lines unless they are implemented.
3. **Code:** If identity-scoped episodic recall is required, extend `_scan_episodic_memories` (or the recall path) to pass `group_ids`/device-derived scope into `GraphitiService.search`.
4. **Code:** In `context_packaging.fetch_biographical_context`, replace `ConsolidatedMemoryStores` with `get_consolidated_memory_store()` (or `ConsolidatedMemoryStore()` and fix the import).
