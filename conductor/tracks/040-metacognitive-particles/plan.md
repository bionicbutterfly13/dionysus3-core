# Feature 040: Metacognitive Particles

## Goal
Implement `MetacognitiveParticle` as the atomic unit of thought in the Dionysus System. Particles are discrete, trackable cognitive units that move through the OODA loop, carrying state, precision, and provenance.

## Connectivity Mandate (IO Map)
- **Host Component:** `ConsciousnessManager` (`_run_ooda_cycle`)
- **Input Source:** OODA Loop Reasoning (`structured_result`) + Metaplasticity (`current_precision`).
- **Data Flow:** 
    1. `ReasoningAgent` generates text/JSON.
    2. `ConsciousnessManager` wraps it in `MetacognitiveParticle`.
    3. `ParticleStore` receives the particle.
- **Output Destination:** 
    - **Ephemeral:** `ParticleStore` (In-Memory List).
    - **Persistent:** `GraphitiService` (Neo4j) **IF** `resonance_score > 0.8` (Attractor Basin).
    
## Context
Currently, thoughts are loose JSON dicts or text strings. Feature 040 formalizes them into a Pydantic model that the `ConsciousnessManager` can "hold", "inspect", and "store".

## Tasks
- [x] Initialize Feature Branch `feature/040-metacognitive-particles` [checkpoint: 1160aa4]
- [x] T001: Define `MetacognitiveParticle` Pydantic Model [checkpoint: 1160aa4]
    - Fields: `id`, `content`, `source_agent`, `timestamp`, `precision`, `entropy`, `resonance_score`.
    - **Refactor:** Add `context_id` and `to_graphiti_node()` method (Depth) [checkpoint: pending]
- [x] T002: Implement `ParticleStore` (In-Memory + Graphiti persistence) [checkpoint: pending]
    - **Refactor:** Inject `GraphitiService`.
    - **Logic:** Implement `_persist_to_graphiti` for high-resonance particles.
- [x] T003: Integrate Particles into `ReasoningAgent` input/output [checkpoint: pending]
    - **Integration Point:** `api/agents/consciousness_manager.py` (Line ~460).
    - Logic: Instantiate Particle, push to Store.
- [x] T004: Verify Particle serialization/deserialization [checkpoint: 1160aa4]

## Verification
- Unit Test: `tests/unit/test_metacognitive_particles.py`
- Integration Test: `tests/integration/test_particle_flow.py` (Verify Graphiti persistence) [checkpoint: pending]
