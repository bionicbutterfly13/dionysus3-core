# Spec: Feature 101 - Hexis Core Migration (No Sprawl)

## Objective

Fold remaining Hexis core cognition (memory API, identity/worldview/goals, consent/boundaries, ingestion, heartbeat patterns) into Dionysus3 Core without code sprawl. Migrate memory storage to Neo4j/Graphiti incrementally.

## Background

Hexis was originally Postgres-centric (schema + functions as the "brain"). Dionysus is Neo4j/Graphiti + MemEvolve/Nemori. Previous tracks (042, 103) have already ported:
- `hexis_service.py` - Consent, boundaries, subconscious state
- `hexis_ontology.py` - Full model ontology (drives, goals, worldview, etc.)
- `hexis.py` router - API endpoints

This track completes the migration by:
1. Adding memory API (recall/store patterns)
2. Adding identity service (worldview/goals retrieval and caching)
3. Adding ingestion adapter (Hexis-style → MemEvolve)
4. Wiring personality constraints into heartbeat

## Requirements

### Functional
1. **Memory API**: Hexis-style `recall()` and `store()` that route through Graphiti/MemEvolve
2. **Identity Service**: Retrieve and cache worldview, goals, identity from Graphiti facts
3. **Ingestion Adapter**: Map Hexis ingestion patterns to MemEvolve trajectory format
4. **Heartbeat Integration**: Enforce consent/boundary/identity checks in decide phase

### Non-Functional
1. **No sprawl**: All code in `api/services/hexis_*.py` or `api/models/hexis_*.py`
2. **Gateway compliance**: All Neo4j via GraphitiService (no direct driver)
3. **TDD**: Tests required for each new service

## Success Criteria

- [ ] `hexis_memory.py` service with `recall()` and `store()` methods
- [ ] `hexis_identity.py` service with worldview/goals/identity retrieval
- [ ] `hexis_ingest.py` adapter mapping to MemEvolve
- [ ] Heartbeat enforces hexis constraints before action execution
- [ ] All tests pass with 80%+ coverage
- [ ] No new entrypoints (all routes through existing routers)

## Out of Scope

- Postgres dual-write (deferred until proven necessary)
- New API endpoints (use existing hexis router)
- External Hexis app (fully deprecated)

## Dependencies

- Track 042 (Hexis Integration) - Done
- Track 103 (Hexis Boundary Enforcement) - Done
- GraphitiService singleton
- MemEvolveAdapter
- PriorConstraintService
