# Plan: Feature 101 - Hexis Core Migration (No Sprawl)

**Objective**: Fold Hexis core cognition (memory API, identity/worldview/goals, consent/boundaries, ingestion, heartbeat patterns) into Dionysus3 Core without code sprawl, using `hexis_`-prefixed modules, and migrate memory storage to Neo4j/Graphiti incrementally.

## Context
Hexis is Postgres-centric (schema + functions as the “brain”). Dionysus is Neo4j/Graphiti + MemEvolve/Nemori. We will **import Hexis logic into Dionysus** (no separate app) and **phase the DB migration** to avoid regressions.

## Requirements
1. **No sprawl**: Hexis code lives inside Dionysus (`api/services/hexis_*`, `api/agents/hexis_*` where needed). No new entrypoints.
2. **Gateway compliance**: All Neo4j access must route through `GraphitiService` or WebhookNeo4jDriver. No direct driver use.
3. **Incremental DB migration**: Start dual-write (Postgres for legacy, Neo4j for temporal KG). Cut over reads only after parity tests.
4. **Personality constraints**: Consent, boundaries, identity/worldview/goal semantics must be enforced in the heartbeat decide phase.
5. **TDD**: Red → Green → Refactor for each task. Tests required for new services and adapters.

## Integration (IO Map)
- **Host**: `dionysus-api`
- **Inlets**:
  - `api/agents/heartbeat_agent.py` (decision gating)
  - `api/routers/session.py` (session reconstruction)
  - `api/routers/memevolve.py` (trajectory ingestion)
- **Outlets**:
  - `GraphitiService` (Neo4j temporal facts/entities)
  - `MemEvolveAdapter` (trajectory ingestion, extraction)
  - `NemoriRiverFlow` (episode construction, fact distillation)
  - Optional: Postgres bridge during migration only
- **Data Flow**:
  - User/Agent → Heartbeat/Decision → Hexis constraints → MemoryBasinRouter → MemEvolve → Graphiti → Neo4j
  - Session start → ReconstructionService → Hexis identity/worldview/goals → prompt context

## Implementation Steps

### Phase 1: Audit & Mapping
- [ ] Inventory Hexis modules to import (memory API, consent, state/heartbeat, ingestion)
- [ ] Map Hexis Postgres functions to Dionysus/Graphiti equivalents or adapters
- [ ] Define dual-write boundaries and migration gates

### Phase 2: Hexis Core Services (No Sprawl)
- [ ] Add `api/services/hexis_memory.py` (Hexis-style API over Graphiti/MemEvolve)
- [ ] Add `api/services/hexis_identity.py` (worldview/goals/identity/consent)
- [ ] Add `api/services/hexis_ingest.py` (Hexis ingestion pipeline mapped to MemEvolve)

### Phase 3: Personality Constraints Enforcement
- [ ] Wire consent/boundary checks into heartbeat `decide()`
- [ ] Ensure refusal/termination pathways flow through existing Outbox and logging

### Phase 4: Session Reconstruction + Hydration
- [ ] Extend `ReconstructionService` to hydrate identity/worldview/goals using Hexis logic
- [ ] Add tests for reconstruction invariants (consent gates, boundary enforcement)

### Phase 5: Incremental DB Migration
- [ ] Implement dual-write adapter (Hexis memory → Graphiti facts + episodic)
- [ ] Add parity tests comparing Hexis-style recall vs Graphiti hybrid search
- [ ] Gate read-cutover behind config flag

### Phase 6: Cleanup + Cutover
- [ ] Remove legacy pathways once parity proven
- [ ] Update docs and operational runbooks

## Branch
`feature/101-hexis-core-migration`
