# Plan: Feature 069 Hexis Subconscious Integration

## Goal
Integrate cognitive concepts from Hexis (Drives, Neighborhoods) and Claude-Subconscious (Guidance) into Dionysus using the native Graphiti/Smolagents stack.

## Integration (IO Map) -> MANDATORY
**Service:** `DreamService` (`api/services/dream_service.py`)
- **Inlets:** 
    - `GraphitiService`: Reading node embeddings for clustering.
    - `HeartbeatAgent`: Reading recent activity logs to update drive states.
- **Outlets:**
    - `GraphitiService`: Writing `Neighborhood` nodes and `Drive` updates.
    - `ConsciousnessManager`: Providing "Guidance" blocks for the next session.

**Service:** `GuidanceInjector` (Future / API Endpoint)
- **Inlets:** `DreamService` (Subconscious State).
- **Outlets:** `gemini/active_context.md` (User Context).

## Tasks

### Phase 1: Ontology & Maintenance (The Dream)
- [~] Define Hexis-style Ontology Models (`hexis_ontology.py`)
    - Models: Neighborhood, Drive, DriveState, SubconsciousState.
- [~] Create `DreamService` Shell
    - Structure: `run_maintenance_cycle`, `_decay_drives`, `_supervise_clustering`.
- [ ] **TEST:** Write failing unit tests for `DreamService` logic (`tests/unit/test_dream_service.py`).
- [ ] Implement `DreamService` Logic
    - Drive decay mechanics.
    - Clustering stub (or basic implementation).
- [ ] Verify `DreamService` with Unit Tests.

### Phase 2: The Guidance Loop
- [ ] Add `generate_guidance()` to `ConsciousnessManager` (or `DreamService`).
- [ ] Create `fetch_guidance.py` client script.
- [ ] **TEST:** Integration test for Guidance generation.

### Phase 3: Integration Verification
- [ ] Manual verification of "Dream" cycle (Unit Test Output).
- [ ] Manual verification of "Guidance" output.
