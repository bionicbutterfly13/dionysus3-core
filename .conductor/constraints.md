# Technical Constraints & Standards

## Pre-Code Requirement (Mandatory)

- **Before writing or changing any code**, agents must:
  1. **Read this file** and follow all constraints below
  2. **Review all relevant code** in the codebase before writing
  3. **Check memory flow patterns** - When touching memory-related code, review:
     - `api/services/memevolve_adapter.py` - MemEvolve integration patterns
     - `api/services/nemori_river_flow.py` - Nemori predict-calibrate flow
     - `api/services/graphiti_service.py` - Graphiti KG operations
     - `api/services/memory_basin_router.py` - Basin routing patterns
  4. **Validate alignment** - Ensure new memory operations align with:
     - MemEvolve adapter patterns (trajectory ingestion, entity extraction)
     - Nemori river flow (episode construction, fact distillation)
     - AutoSchemaKG integration (5-level concept extraction)
  5. **Document inlet/outlet** - When modifying memory code, document:
     - **Inlets:** What memory data this code receives and from where
     - **Outlets:** Where memory data flows (Graphiti, MemEvolve, Nemori, consolidated store)
     - **Memory flow path:** Trace the complete path from agent → memory system → persistence

If unsure, stop and re-read.

## Testing Strategy

- **Unit Tests**: Required for all new Services and Agents.
- **Integration Tests**: Required for MCP tools and Neo4j interactions.
- **E2E Tests**: Critical for the OODA loop (Heartbeat).

## Security Requirements

- **Authentication**: Webhook signatures (HMAC-SHA256) for n8n communication.
- **Environment**: No hardcoded API keys. Use `.env`.
- **VPS**: SSH Tunnel required for Neo4j access (localhost:7687 -> VPS:7687).

## Performance Requirements

- **Inference**: Optimized for `gpt-5-nano` (or equivalent efficient models).
- **Graph**: Index critical paths (Entity IDs, Timestamps).
- **Startup**: API must be healthy within 30 seconds.

## Deployment Constraints

- **Docker**: All services must be containerized.
- **Migration**: Schema changes must be additive or explicitly migrated via scripts.
- **Rollback**: Feature 021 implements rollback safety nets.

## Integration & Depth Policy (No Orphan Code)

**Mandatory.** All feature work **and any code you touch** must satisfy this policy. Verify against it before marking tasks complete and when reviewing commits.

- **No orphan code or stubs.** Do not add services, endpoints, or modules that are never invoked, that return hardcoded placeholders, or that have no callers in the live codebase. Every new piece of code must be reachable from an existing entry point (API, agent, callback, scheduled job, or other integrated component).
- **No disconnected features.** Every feature must have **explicit integration points**: where it attaches to the existing system, what it consumes, and what it produces. Code that "does something in isolation" but is never wired into the OODA loop, APIs, memory systems, or other core flows is rejected.
- **No garbage plug-and-play.** Do not wire in new code, add callers, or change integration points without understanding and documenting the flow. Every attachment must have clear **inlets** (what this code receives and from where) and **outlets** (what it produces and where it sends). Verify the piece fits the pipeline before and after your change.
- **Code you touch must have clear inlet/outlet.** When you **open or modify** any file—new or existing—apply the same standard. If that code **lacks** clear inlet/outlet documentation and you cannot see how it fits the pipeline:
  - **Figure out where it goes.** Trace callers and callees, routers, services, and data flow until you understand attachment points, inputs, and outputs.
  - **Document it.** Add or update module- or function-level comments (or the track's `plan.md` Integration / IO Map) with: **Inlets:** what this code receives and from where; **Outlets:** what it produces and where it sends.
  - **Ensure integrity.** Confirm the code actually fits the pipeline (is invoked, consumes real inputs, produces used outputs). If it does not—orphan, stub, or dead path—fix or remove it; do not leave it as undocumented, half-wired "plug and play."
  
- **Memory Stack Integration Pattern (Mandatory for Memory Code):**
  When working with memory-related code, you MUST understand and follow the memory flow patterns:
  
  **Memory Flow Architecture:**
  ```
  Agent/Service → MemoryBasinRouter → MemEvolveAdapter → GraphitiService → Neo4j
                    ↓
              NemoriRiverFlow (episode construction, fact distillation)
                    ↓
              ConsolidatedMemoryStore (event/episode persistence)
  ```
  
  **Key Memory Services & Their Roles:**
  - **MemEvolveAdapter**: Gateway for trajectory ingestion, entity extraction, webhook sync
    - **Inlets:** TrajectoryData from agents/routers, pre-extracted entities/edges
    - **Outlets:** GraphitiService (extract_with_context, ingest_extracted_relationships), n8n webhooks
  - **NemoriRiverFlow**: Episode construction, predict-calibrate, fact distillation
    - **Inlets:** DevelopmentEvent lists, basin context
    - **Outlets:** MemoryBasinRouter.route_memory(), GraphitiService.persist_fact(), ConsolidatedMemoryStore
  - **MemoryBasinRouter**: Classifies memory type, activates basins, routes through MemEvolve
    - **Inlets:** Raw content, optional memory_type
    - **Outlets:** MemEvolveAdapter.ingest_message(), GraphitiService.extract_with_context()
  - **GraphitiService**: Temporal KG operations (extract, ingest, persist facts)
    - **Inlets:** Content, basin_context, strategy_context
    - **Outlets:** Neo4j via Graphiti library, returns entities/relationships
  
  **When Adding Memory Operations:**
  1. **Check if content should flow through MemoryBasinRouter** - Use `route_memory()` for agent-generated content
  2. **Check if facts should be persisted** - Use `GraphitiService.persist_fact()` for distilled facts from Nemori
  3. **Check if trajectory should be ingested** - Use `MemEvolveAdapter.ingest_trajectory()` for agent trajectories
  4. **Validate alignment** - Ensure your code follows the established patterns in:
     - `memevolve_adapter.py` (lines 67-280) - Trajectory ingestion flow
     - `nemori_river_flow.py` (lines 235-370) - Predict-calibrate with basin routing
     - `graphiti_service.py` (lines 519-608, 782-820) - Extract and persist operations
     - `memory_basin_router.py` (lines 155-200) - Memory routing pattern
  
  **Memory Outlet Injection Points:**
  - After agent reasoning: Route through `MemoryBasinRouter.route_memory()`
  - After episode construction: Call `NemoriRiverFlow.predict_and_calibrate()` → routes facts
  - After fact distillation: Use `GraphitiService.persist_fact()` for bi-temporal tracking
  - After trajectory completion: Use `MemEvolveAdapter.ingest_trajectory()` for full persistence
- **Evaluate commits for depth and integration.** When completing a task or reviewing a PR, check that the change:
  - Implements real behavior (not TODOs or stub implementations).
  - Is integrated: called from routers, agents, services, or tests that exercise the full path.
  - Persists or reads data through approved paths (e.g. Graphiti, n8n webhooks, API) where applicable—not via one-off or local-only mechanisms.
  - Leaves touched code with clear inlet/outlet documentation where it was missing.
- **Document integration in the plan.** For every feature track, `plan.md` **must** include an **Integration (IO Map)** section that specifies:
  - **Attachment points:** Exact files, routers, or services where the feature plugs in (e.g. `api/routers/beautiful_loop.py`, `ConsciousnessManager.run_cycle`).
  - **Inputs:** What the feature receives and from where (e.g. context from `HeartbeatAgent`, precision profile from `HyperModelService`, webhook payload from n8n).
  - **Outputs:** What it produces and where it sends results (e.g. `UnifiedRealityModel` updates, EventBus events, API responses, Graphiti writes).

Create or update this section when the track is created; revise it if attachment points or data flow change during implementation.

## Memory Gateway (Markov Blanket) – Deterministic No-Bypass

**Mandatory.** The memory architecture must never be breached. All Neo4j access goes through a single boundary (the "Markov blanket"). No bypass.

- **Singleton gateway:** The only components that may touch Neo4j are:
  1. **GraphitiService** (singleton `_global_graphiti`) – temporal KG operations via the Graphiti library.
  2. **WebhookNeo4jDriver** (singleton) – compatibility shim that proxies to MemEvolveAdapter → GraphitiService.

  No other code may create or hold a Neo4j driver. All memory reads/writes cross this boundary only.

- **No direct driver use.** Forbidden everywhere:
  - `from neo4j import GraphDatabase`
  - `GraphDatabase.driver(...)`
  - Any new module that opens a bolt connection to Neo4j.

- **Deterministic enforcement:** Run `python scripts/verification/check_memory_gateway.py` before CI or as part of the test suite. It scans for the above violations and **exits 1** if any are found outside the allowlist. Fix violations; do not add new ones.

- **Allowlist (dev-only):** The following scripts may use direct Neo4j **only** for local verification (e.g. bolt connectivity, auth, memory-audit). They must be clearly marked DEV-ONLY and must not be used in production flows:
  - `scripts/verification/test_bolt_connection.py`
  - `scripts/verification/test_auth.py`
  - `scripts/verification/audit_memory_architecture.py`

  Any other script (e.g. ingestion, maintenance) must use the gateway (n8n webhooks, GraphitiService, or MemEvolveAdapter). Migrate or remove violators.

- **Adding new memory access:** Use `get_graphiti_service()` or `get_neo4j_driver()` (which returns the WebhookNeo4jDriver shim). Never introduce a new Neo4j driver or connection path.

## "Ultrathink" Protocols

- **Depth**: Code must reflect the "System Soul" (Analytical Empath).
- **Identity**: System must maintain "Voice" consistency.
