# Track 094 Inventory (Phase 0)

## Scope
Audit of memory/graph/active-inference components with emphasis on attractor basins, neural packets, worldview/identity models, and CGR3 usage.

## Attractor Basins (Observed)
- `api/services/memory_basin_router.py`: Memory-type routing (EPISODIC/SEMANTIC/PROCEDURAL/STRATEGIC) → `AttractorBasin` nodes; provides basin context for ingestion.
- `api/services/kg_learning_service.py`: Uses basin context for extraction; creates/strengthens `AttractorBasin`.
- `api/services/graphiti_service.py`: Accepts `basin_context` for extraction; writes `basin_id` on facts.
- `api/services/nemori_river_flow.py`: Basin-aligned prediction/calibration; uses basin context and router.
- `api/services/clauses_service.py`: Strengthens `MemoryCluster` nodes (label drift vs AttractorBasin).
- `api/services/execution_trace_service.py`: Links activated basins via `MemoryCluster` nodes.
- `api/agents/callbacks/basin_callback.py`: Activates basins using `MemoryCluster` label.
- `api/services/thoughtseed_integration.py`: Activates basins using `Basin` label (drift).
- `api/services/autobiographical_service.py`: Seeds/links `AttractorBasin` nodes.
- `api/agents/consolidated_memory_stores.py`: Links ingests to `AttractorBasin`.
- `api/models/cognitive.py`: `MemoryCluster` + `AttractorBasin` models (Pydantic).
- `api/models/metacognitive_particle.py`: `MetacognitiveAttractorBasin` training helpers.
- `api/schemas/metacognitive_kg_schema.json`: Defines `AttractorBasin` schema + relationships.

## Basin Naming/Schema Drift
- Labels used: `AttractorBasin`, `MemoryCluster`, `Basin`.
- Services inconsistent about which label to read/write (router vs clause/traces vs thoughtseeds).

## Neural Packets + ThoughtSeeds (Observed)
- `api/models/cognitive.py`: `NeuronalPacketModel` (boundary energy, cohesion, stability).
- `api/services/model_service.py`: `NeuronalPacket` class exists (synergistic boost) but not wired into selection flow.
- `api/services/thoughtseed_integration.py`: Stores a `neuronal_packet` JSON blob on `ThoughtSeed` nodes.
- `api/models/thought.py`: `ThoughtSeed` model.
- `api/models/markov_blanket.py` + `api/services/blanket_enforcement.py`: ThoughtSeed Markov blankets.
- `docs/thoughtseeds-implementation-plan.md` + `docs/neo4j-paper-schema.md`: Planned NeuronalPacket nodes and services.

## Mental Models (Observed)
- `api/models/mental_model.py`: Mental model entities + predictions + revisions.
- `api/routers/models.py`: Mental model API.
- `api/services/model_service.py`: CRUD + prediction + revision logic; references NeuronalPacket.
- `api/services/thoughtseed_integration.py`: Converts predictions → ThoughtSeeds.
- `api/services/worldview_integration.py`: Filters predictions + records prediction errors to Worldview.

## Worldview + Identity (Observed)
- `api/services/worldview_integration.py`: Operates on `Worldview` nodes in Neo4j; no `api/models/worldview.py` found.
- `docs/concepts/THE_GHOST_IN_THE_MACHINE.md`: References missing `api/models/worldview.py`.
- Identity signals appear in `api/services/heartbeat_service.py`, `api/services/context_packaging.py`, `api/models/priors.py`, and `api/services/fractal_reflection_tracer.py`.

## CGR3 / Context Graph (Observed)
- `api/services/context_discovery_service.py`: Imports `cgr3` (MACERReasoner + GraphitiContextGraph) and logs trajectories.
- `api/agents/tools/discovery_tools.py`: Exposes `macer_discover` (CGR3/ToG-3 reasoning).
- No `cgr3` package in repo (external dependency).

## Immediate Gaps
- Basin label mismatch (`AttractorBasin` vs `MemoryCluster` vs `Basin`) across services.
- Neural packet constructs exist but are not integrated into ThoughtSeed selection or basin routing.
- Worldview model referenced in docs but absent in code.
- CGR3 dependency appears external; migration planning needed.

## External Repos + Papers (Integration Deltas)
- **Nemori** (`/Volumes/Asylum/repos/nemori`, paper `2508.03341v3.pdf`)\
  Two-step alignment (boundary + representation) + Predict/Calibrate loop. Integration delta: map boundary detection to basin/episode segmentation, and use Predict/Calibrate to drive dissonance-triggered updates and semantic distillation into Graphiti/Neo4j-backed memory.
- **MemEvolve** (`/Volumes/Asylum/repos/MemEvolve`, paper `2512.18746v1.pdf`)\
  Dual-loop memory evolution (content + architecture) with evaluation harness. Integration delta: wire MemEvolve’s memory-provider interface to Dionysus memory pipeline and use evaluation scripts to score basin/graph variants.
- **AutoSchemaKG** (`/Volumes/Asylum/repos/AutoSchemaKG`)\
  Schema induction + triple extraction + Neo4j export. Integration delta: use schema induction to auto-extend Graphiti/TrustGraph ontology and generate graph schemas for new domains.
- **Graphiti** (`/Volumes/Asylum/repos/graphiti`)\
  Temporal KG with hybrid retrieval and custom entity schemas. Integration delta: align Graphiti service usage with basin-aware ingestion and ensure schema definitions mirror ThoughtSeed/NeuronalPacket nodes.
- **TrustGraph** (`/Volumes/Asylum/repos/trustgraph`)\
  Context graph factory with ontology-driven construction, context cores, and workflow tooling. Integration delta: plan migration of CGR3 discovery to TrustGraph graph factory + context cores.
- **Context Graph / CGR3 paper** (`/Volumes/Asylum/_Downloads/2406.11160v3.pdf`)\
  Contextual KG with temporal/provenance metadata + CGR3 retrieve-rank-reason loop. Integration delta: preserve CGR3 logic but move storage/ontology to TrustGraph or Graphiti-backed context graph.
- **TOBUGraph paper** (`/Volumes/Asylum/_Downloads/2412.05447v3.pdf`)\
  Graph-based retrieval from unstructured data, avoiding chunking. Integration delta: apply TOBUGraph-style traversal to basin-aware retrieval and reduce chunk dependence.
- **Decision Trace**\
  Identified as TOBUGraph lineage (no separate PDF). Integration delta: treat as retrieval + trace layer in CGR3 migration plan.

## Ingestion Rules + Gaps (Phase 0)
- **Rules documented**: `docs/ingestion-rules.md` summarizes Graphiti, MemEvolve adapter, and Nemori river flow ingestion expectations.\n- **Gaps logged**: Nemori rewrite mismatch, schema enforcement absent, basin label drift, missing payload validation, and fragmented production webhook policies.
