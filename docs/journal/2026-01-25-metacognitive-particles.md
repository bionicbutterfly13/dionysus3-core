# 2026-01-25: Metacognitive Particles (The Atomic Thought)

## Overview
Implemented Feature 040, transforming "Thoughts" from loose text into **Metacognitive Particles**. This fulfills the "Ultrathink Depth" requirement and the "Connectivity Mandate".

## Why
To support Active Inference and Deep Cognition, thoughts must have physics (Mass/Resonance, Velocity/Precision). Text strings cannot have physics. Objects can.

## What
1.  **MetacognitiveParticle:** A Pydantic model with `precision`, `entropy`, and `resonance_score`.
2.  **ParticleStore:** A Working Memory service that manages these particles, enacting "Forgetfulness" (Decay) and "Consolidation" (Persistence).
3.  **Connectivity:**
    -   **Input:** `ConsciousnessManager` generates particles from OODA reasoning.
    -   **Output:** `ParticleStore` persists resonant particles (>0.8) to **Graphiti/Neo4j**.

## Key Decisions
- **Persistence Threshold:** Only thoughts with `resonance > 0.8` are saved to the Knowledge Graph. This prevents "Memory Flood" and mimics biological consolidation.
- **Context Linking:** Added `context_id` to link thoughts to their Journey/Session.

## Artifacts
- [Plan](file:///Volumes/Asylum/dev/dionysus3-core/conductor/tracks/040-metacognitive-particles/plan.md)
- [Code](file:///Volumes/Asylum/dev/dionysus3-core/api/models/metacognitive_particle.py)
