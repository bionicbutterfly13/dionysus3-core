# Feature 040: Metacognitive Particles

## Goal
Implement `MetacognitiveParticle` as the atomic unit of thought in the Dionysus System. Particles are discrete, trackable cognitive units that move through the OODA loop, carrying state, precision, and provenance.

## Context
Currently, thoughts are loose JSON dicts or text strings. Feature 040 formalizes them into a Pydantic model that the `ConsciousnessManager` can "hold", "inspect", and "store".

## Tasks
- [x] Initialize Feature Branch `feature/040-metacognitive-particles` [checkpoint: 1160aa4]
- [x] T001: Define `MetacognitiveParticle` Pydantic Model [checkpoint: 1160aa4]
    - Fields: `id`, `content`, `source_agent`, `timestamp`, `precision`, `entropy`, `resonance_score`.
- [x] T002: Implement `ParticleStore` (In-Memory + Graphiti persistence) [checkpoint: 1160aa4]
    - Ephemeral storage for the current "Working Memory" (OODA context).
- [ ] T003: Integrate Particles into `ReasoningAgent` input/output
- [x] T004: Verify Particle serialization/deserialization [checkpoint: 1160aa4]

## Verification
- Unit Test: `tests/unit/test_metacognitive_particles.py`
    - Test creation, validation, and JSON roundtrip.
