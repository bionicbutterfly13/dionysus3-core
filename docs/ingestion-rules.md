# Ingestion Rules + Gaps (Phase 0)

## Graphiti (Neo4j) Ingestion Rules
- **Primary service**: `api/services/graphiti_service.py`.
- **Episode ingestion**: `ingest_message` creates message episodes with entity extraction.
- **Relationship ingestion**: `ingest_extracted_relationships` expects approved relationships; uses `basin_id` for cross-referencing.
- **Contextual triplets**: `ingest_contextual_triplet` supports `context` metadata.
- **Required env**: `NEO4J_PASSWORD` and `OPENAI_API_KEY` are mandatory; `NEO4J_URI` optional.
- **Group IDs**: default `group_id="dionysus"` unless overridden.

## MemEvolve Adapter Rules
- **Adapter**: `api/services/memevolve_adapter.py`.
- **Ingest**: `ingest_trajectory` summarizes trajectories, runs Graphiti extraction, and persists `Trajectory` nodes.
- **Webhook**: optional n8n ingest via `MEMEVOLVE_WEBHOOK_INGEST_ENABLED`.
- **Output**: `ingest_id` and Graphiti ingestion counts.

## Nemori River Flow Rules
- **Service**: `api/services/nemori_river_flow.py`.
- **Boundary alignment**: LLM-driven boundary detection with surprisal thresholds.
- **Predict/Calibrate**: LLM-generated predictions and calibration with basin context.
- **Basin context**: `MemoryBasinRouter` provides attractor alignment for episodes.

## Known Gaps
- **Nemori rewrite mismatch**: current Nemori integration is prompt-based and does not use `/Volumes/Asylum/repos/nemori` implementation.
- **Schema enforcement**: `api/schemas/metacognitive_kg_schema.json` defines `graphiti_ingestion_format`, but `GraphitiService` does not enforce schema templates.
- **Basin label drift**: `AttractorBasin` vs `MemoryCluster` vs `Basin` across ingestion paths.
- **Payload validation**: ingestion payloads are not consistently validated or typed across services.
- **Production path**: n8n webhook ingestion is optional and lacks a consolidated policy document in core services.
