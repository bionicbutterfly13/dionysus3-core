# MemEvolve + Dionysus3 + Neo4j/Graphiti Integration Plan

## Objectives & Scope
- Connect MemEvolve (Flash-Searcher main codebase) to Dionysus3-core via n8n webhooks with HMAC.
- Persist agent memories (vector + graph) in PostgreSQL/pgvector and Neo4j/Graphiti with temporal validity.
- Enable entity/relationship extraction from trajectories, cross-agent knowledge reuse, and consciousness-level reflection.
- Allow MemEvolve’s AutoEvolver to optimize Dionysus retrieval strategies.

## Benefits & Scenarios
- Persistent graph memory: Day 1 agent learns “gov stats > Wikipedia”; Day 30 agent reuses that heuristic for GDP tasks.
- Entity relationship learning: (Elon Musk)-[CEO_OF]->(Tesla); future queries traverse graph instantly instead of web search.
- Cross-agent knowledge sharing: GAIA agent learns arXiv citation format; WebWalkerQA agent learns DOI extraction; xBench agent gets both.
- Consciousness reflection: Heartbeat sees 9/47 runs failed on date parsing; generates strategic memory “clarify timezone”.
- Mental model formation: 200 runs reveal unit-conversion failures; auto-creates “UnitTrackingPattern” with confidence tracking.
- Meta-evolution of retrieval: AutoEvolver improves retrieval 72%→84% over rounds (hybrid BM25 + semantic + session rerank).
- Temporal fact validity: OAuth 1.0a marked invalid when OAuth 2.0 appears; queries surface only current facts.
- Session continuity: Start on desktop, resume on mobile with full session context.

## Architecture (text)
MemEvolve agent + AutoEvolver → DionysusMemoryProvider (new) → n8n webhooks (HMAC) → Dionysus3 services (Graphiti, VectorSearch, Heartbeat, ModelService, Reconstruction) → PostgreSQL+pgvector and Neo4j/Graphiti. No direct DB/Neo4j access from MemEvolve.

## Files to Create (MemEvolve)
- `Flash-Searcher-main/EvolveLab/providers/dionysus_memory_provider.py` — BaseMemoryProvider implementation.
- `Flash-Searcher-main/EvolveLab/providers/dionysus_client.py` — HTTP client with HMAC signing/retries.
- `Flash-Searcher-main/EvolveLab/providers/entity_extractor.py` — trajectory → entities/edges payload for Graphiti.
- `Flash-Searcher-main/EvolveLab/dionysus_config.py` — config schema and defaults.

## Files to Modify (MemEvolve)
- `Flash-Searcher-main/EvolveLab/memory_types.py` — add DIONYSUS enum + PROVIDER_MAPPING entry.
- `Flash-Searcher-main/EvolveLab/config.py` — Dionysus config block.
- `Flash-Searcher-main/MemEvolve/config.py` — runner support, feature flags.

## Files to Create (Dionysus)
- `api/services/memevolve_adapter.py` — bridge for MemEvolve payloads.
- `api/routers/memevolve.py` — REST endpoints (ingest/recall/evolve).
- `api/models/memevolve.py` — Pydantic schemas.
- `n8n-workflows/memevolve-ingest.json` — trajectory ingest → Graphiti + vector.
- `n8n-workflows/memevolve-recall.json` — recall → vector + graph traversal.
- `n8n-workflows/memevolve-evolve.json` — evolution result ingestion/refresh.

## Files to Modify (Dionysus)
- `api/services/remote_sync.py` — HMAC helpers and request verification.
- `api/services/graphiti_service.py` — trajectory entity extraction/edge creation.
- `api/services/heartbeat_service.py` — include MemEvolve runs in OBSERVE/ORIENT/DECIDE/ACT.
- `api/main.py` — register memevolve router.

## Implementation Phases
1) Foundation (2–3d): HMAC client, provider skeleton, add DIONYSUS type, n8n health check, end-to-end ping.
2) Retrieval (3–4d): `provide_memory` for BEGIN/IN phases; vector+graph recall via n8n; session/context mapping.
3) Ingestion (4–5d): `take_in_memory`; EntityExtractor; n8n ingest → Graphiti + pgvector; session attribution.
4) Consciousness (3–4d): Heartbeat consumes trajectories; generates strategic memories + mental models.
5) Meta-evolution (4–5d): AutoEvolver reports winners; Dionysus updates retrieval strategies; validation loop both ways.
6) Hardening (2–3d): Rate limits, caching/batching, monitoring, audit logging, docs.

## Data Flows (text)
- Retrieval: MemEvolve MemoryRequest → `/recall` (HMAC) → n8n → VectorSearch + Graph traversal → MemoryResponse (typed strategic/operational/working/episodic/semantic).
- Ingestion: TrajectoryData → EntityExtractor → `/ingest` → n8n → Graphiti (nodes/edges with valid_at/invalid_at) + pgvector store → success summary.
- Consciousness: Heartbeat queries recent trajectories → pattern detection (failures like date parsing/unit conversion) → strategic memories and model revisions emitted back to graph/vector stores.

## Configuration (examples)
- MemEvolve: `DIONYSUS_WEBHOOK_BASE_URL`, `DIONYSUS_HMAC_SECRET`, `DIONYSUS_PROJECT_ID`, `DIONYSUS_TIMEOUT_SECONDS`, `DIONYSUS_RETRY_COUNT`, `DIONYSUS_ENTITY_EXTRACTION`, `DIONYSUS_SESSION_TRACKING`.
- Dionysus: `MEMEVOLVE_HMAC_SECRET`, `MEMEVOLVE_ENABLED`, `MEMEVOLVE_HEARTBEAT_INCLUDE`.

## Security & Compliance
- HMAC-SHA256 with signed-at timestamp + nonce (5–10 min skew window); replay cache; key rotation runbook.
- IP allowlist for n8n/Dionysus; no direct Neo4j/Postgres access from MemEvolve.
- Rate limiting per `project_id`; structured audit logs with request_id/user-agent/project_id.
- PII handling: sanitize trajectories before ingest (strip emails/phones/PII entities); retention policies per memory type.

## Reliability & Performance
- Retry/backoff matrix: idempotent calls (recall) with limited retries; ingest uses queue + DLQ; circuit breakers around n8n/Neo4j/pgvector.
- Timeouts per hop (MemEvolve client, n8n, Dionysus services); fallback to local cache when recall is degraded.
- Batching/backpressure for ingestion; rate limits per project; size caps on trajectories and entity payloads.
- Feature flags + kill switches: enable/disable Dionysus provider, graph writes, and vector writes independently; canary per `project_id`.

## Observability
- Structured logs with request_id/project_id and HMAC decision (accept/reject); end-to-end traces MemEvolve → n8n → Dionysus.
- Metrics/SLOs: recall/ingest p95 latency, error rate, throughput, replay-reject count, cache-hit rate; alerts on SLO burn and replay storms.

## Testing & Rollout
- Contract tests for payload schemas; e2e tests against local n8n stub; chaos tests (n8n down, Neo4j slow, partial graph failures).
- Golden fixtures for recall/ingest; replay-protection tests (nonce/timestamp); load tests for batching paths.
- Staged rollout: canary project, monitor SLOs, then expand; runbooks for replay storms, key drift, Neo4j bloat, cache evictions.

## Data Model & Migration
- Graph schema: node labels (StrategicMemory, ProceduralMemory, WorkingMemory, EpisodicMemory, SemanticMemory, Source, Entity), edges with `valid_at`, `invalid_at`, `source`, `trace_id`, `project_id`.
- Versioning: schema version tagged on nodes/edges; migration plan v1→v2 with backfill jobs; change log for memory type mapping.
- Vector store fields: text, embedding, `memory_type`, `project_id`, `trace_id`, timestamps; TTL for working memory if required.

## Success Metrics
- Retrieval accuracy: 72% baseline → 85%+ target; freshness SLA (max staleness before bypass).
- Cross-agent knowledge reuse: 0% → 60%+.
- Entity relationship coverage: 0% → 80%+ facts with edges.
- Reflection cadence: ≥1/hour; availability SLO for recall/ingest.
- Meta-evolution gain: ≥5% per round.
- Session resumability: ≥95%; p95 latency targets for recall/ingest.

## Implementation Guidance (concrete steps)
- MemEvolve client (`dionysus_client.py`):
  - Add HMAC header = HMAC_SHA256(secret, method + path + body + timestamp + nonce); include `X-Signed-At`, `X-Nonce`, `X-Project-Id`, `X-Request-Id`.
  - Retries: idempotent GET/POST recall → 2 retries with exp backoff; ingest → single attempt to queue endpoint; circuit-break on 5xx streak.
  - Timeouts: connect 2s, read 10s recall, 20s ingest; surface structured errors to provider.
- Provider (`dionysus_memory_provider.py`):
  - BEGIN/IN phases: map MemoryRequest to recall payload (query/context/memory_types/session_id/project_id); fallback to cached memories when recall fails.
  - Ingest: redact PII via EntityExtractor; enforce payload size caps; queue ingest if primary call fails.
  - Flags: `DIONYSUS_ENABLED`, `DIONYSUS_GRAPH_WRITES_ENABLED`, `DIONYSUS_VECTOR_WRITES_ENABLED`, `DIONYSUS_CANARY_PROJECT`.
- n8n workflows:
  - `/recall`: verify HMAC/timestamp/nonce; route to VectorSearch + optional Graph traversal; cap results; tag request_id/project_id in logs.
  - `/ingest`: verify HMAC; enqueue to worker; worker does Graphiti upsert + pgvector insert; DLQ on failure.
  - `/evolve`: accept strategy updates; trigger cache/embedding refresh as needed.
- Dionysus services:
  - `remote_sync.py`: implement signature verification, replay cache (timestamp+nonce), IP allowlist, and structured logging.
  - `graphiti_service.py`: upsert nodes/edges with `valid_at/invalid_at/source/trace_id/project_id/schema_version`; batch writes.
  - `heartbeat_service.py`: include MemEvolve trajectories in OBSERVE; write strategic memories/model updates in ACT with version tags.
  - `main.py`: register memevolve router under `/webhook/memevolve/v1`; apply rate limits per project.
- Schema/migration:
  - Define node labels/edge types + required props; store `schema_version`.
  - Migration plan: v1→v2 backfill job; maintain change log; add TTL for WorkingMemory in pgvector.
- Testing:
  - Contract tests for payload schemas; e2e against local n8n stub; replay tests (expired timestamp, reused nonce); chaos tests (n8n 500/timeout).
  - Golden fixtures for recall/ingest; load tests for batching; SLO verification (p95 latency, error rate).
- Rollout:
  - Enable canary project only; monitor SLOs/replay rejects; gradually widen allowlist.
  - Runbooks: key rotation, replay storm response, Neo4j bloat cleanup, cache eviction tuning, rollback to local memory.

## Next Action
Start with Phase 1 (Foundation): add DIONYSUS type, scaffold provider/client/extractor, n8n health check, and run a signed ping from MemEvolve → n8n → Dionysus.
