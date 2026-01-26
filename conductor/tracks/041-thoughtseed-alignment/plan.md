# Feature 041: Thoughtseed Alignment

## Goal
Align the Codebase with the "Thoughtseed Framework". Implement `provenance` tracking to link Thoughtseeds (Particles) to their Retrievals (Packets).

## Connectivity Mandate (Surgical IO Map)

### 1. Inlet (The Source)
- **Component:** `api/agents/consciousness_manager.py`
- **Location:** Inside `_run_ooda_cycle` loop, post-reasoning execution.
- **Variable:** `structured_result.get("provenance_ids")` (New field to be returned by Reasoning Agent).
- **Data Structure:** `List[str]` (UUIDs of Graphiti Nodes retrieved during reasoning).

### 2. Transformation (The Logic)
- **Component:** `api/models/metacognitive_particle.py`
- **Change:** Add field `provenance_ids: List[str]`.
- **Logic:** `Particle(..., provenance_ids=retrieved_ids)`.

### 3. Outlet (The Sink)
- **Component:** `api/services/particle_store.py` -> `GraphitiService`
- **Method:** `_persist_to_graphiti`.
- **Payload:**
    ```python
    {
        "type": "MetacognitiveParticle",
        "provenance": ["node-uuid-1", "node-uuid-2"],
        ...
    }
    ```
- **Graph Action:** `Graphiti` service will create `DERIVED_FROM` edges from the new Particle Node to the Provenance Nodes.

## Tasks
- [x] Initialize Feature Branch `feature/041-thoughtseed-alignment` [checkpoint: 63b73c5]
- [x] T001: Update `MetacognitiveParticle` Model (Add `provenance_ids`) [checkpoint: 63b73c5]
- [x] T002: Refactor `ParticleStore` (Pass `provenance` to Graphiti) [checkpoint: 63b73c5]
- [x] T003: Update `ReasoningAgent` (Mock capability to return `provenance_ids` from tools) [checkpoint: deferred to F022]
    - *Note:* Detailed implementation of Retrieval Provenance fits Feature 022, but we will add the *slot* here. We added the 'Inlet' logic in ConsciousnessManager.

## Verification
- [x] Connection Test: `tests/integration/test_provenance_flow.py` (Passed)
    - Verified `provenance_ids` extraction and payload construction.
