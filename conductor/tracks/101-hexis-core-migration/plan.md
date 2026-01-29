# Plan: Feature 101 - Hexis Core Migration (No Sprawl)

**Objective**: Fold Hexis core cognition (memory API, identity/worldview/goals, consent/boundaries, ingestion, heartbeat patterns) into Dionysus3 Core without code sprawl, using `hexis_`-prefixed modules, and migrate memory storage to Neo4j/Graphiti incrementally.

## Context
Hexis was Postgres-centric. Dionysus is Neo4j/Graphiti + MemEvolve/Nemori. Tracks 042 and 103 already ported consent, boundaries, and subconscious state. This track completes the migration.

## Requirements
1. **No sprawl**: Hexis code lives inside Dionysus (`api/services/hexis_*`). No new entrypoints.
2. **Gateway compliance**: All Neo4j access must route through `GraphitiService`. No direct driver use.
3. **Personality constraints**: Consent, boundaries, identity/worldview/goal semantics must be enforced in heartbeat.
4. **TDD**: Red → Green → Refactor for each task.

## Integration (IO Map)
- **Inlets**:
  - `api/agents/heartbeat_agent.py` (decision gating)
  - `api/services/heartbeat_service.py` (hexis subconscious state)
  - `api/routers/session.py` (session reconstruction)
  - `api/routers/memevolve.py` (trajectory ingestion)
- **Outlets**:
  - `GraphitiService` (Neo4j temporal facts/entities)
  - `MemEvolveAdapter` (trajectory ingestion, extraction)
  - `GoalService` (goal CRUD)
  - `WorldviewIntegrationService` (worldview alignment)

## Phase 1: Audit & Mapping (COMPLETE)

### Existing Infrastructure
| Component | Status | Location |
|-----------|--------|----------|
| HexisService (consent/boundaries/subconscious) | ✅ Done | `api/services/hexis_service.py` |
| Hexis Ontology (drives/goals/worldview models) | ✅ Done | `api/models/hexis_ontology.py` |
| Hexis Router | ✅ Done | `api/routers/hexis.py` |
| GoalService | ✅ Done | `api/services/goal_service.py` |
| WorldviewIntegrationService | ✅ Done | `api/services/worldview_integration.py` |
| Heartbeat → Hexis subconscious | ✅ Done | `heartbeat_service.py:202-204, 625-636` |

### Gaps Identified
| Gap | Required Action |
|-----|-----------------|
| Hexis-style memory API facade | Create `hexis_memory.py` |
| Identity aggregation for prompts | Create `hexis_identity.py` |
| Reconstruction → identity hydration | Extend `reconstruction_service.py` |
| Ingestion adapter | Create `hexis_ingest.py` (optional - MemEvolve may suffice) |

- [x] Inventory Hexis modules to import (audit complete)
- [x] Map Hexis Postgres functions to Dionysus/Graphiti equivalents
- [x] Define dual-write boundaries (not needed - Graphiti-only)

## Phase 2: Hexis Core Services (No Sprawl)

### Tasks
- [x] Add `api/services/hexis_memory.py` - Facade over Graphiti/MemEvolve with `recall()` and `store()`
- [x] Add `api/services/hexis_identity.py` - Aggregates worldview/goals/identity for prompt context
- [x] Add tests for hexis_memory.py (8 tests)
- [x] Add tests for hexis_identity.py (9 tests)

### hexis_memory.py Design
```python
class HexisMemoryService:
    async def recall(query: str, agent_id: str, limit: int = 10) -> List[MemoryItem]
    async def store(content: str, agent_id: str, memory_type: MemoryType) -> str
    async def get_neighborhoods(agent_id: str) -> List[Neighborhood]
```

### hexis_identity.py Design
```python
class HexisIdentityService:
    async def get_identity_context(agent_id: str) -> IdentityContext
    async def get_active_goals(agent_id: str) -> List[Goal]
    async def get_worldview(agent_id: str) -> List[Worldview]
    async def get_prompt_context(agent_id: str) -> str  # Formatted for LLM
```

## Phase 3: Personality Constraints Enforcement

- [ ] Wire consent/boundary checks into heartbeat `decide()` (verify existing implementation)
- [ ] Ensure refusal pathways flow through existing Outbox and logging
- [ ] Add integration test for boundary violation → refusal flow

## Phase 4: Session Reconstruction + Hydration

- [ ] Extend `ReconstructionService` to hydrate identity/worldview/goals using HexisIdentityService
- [ ] Add tests for reconstruction invariants (consent gates, boundary enforcement)

## Phase 5: Cleanup + Cutover

- [ ] Remove any legacy pathways (if found)
- [ ] Update docs and operational runbooks
- [ ] Journal entry

## Branch
`feature/101-hexis-core-migration`
