# 2026-01-26: Thoughtseed Alignment (The Chain of Causality)

## Overview
Implemented Feature 041, aligning the codebase with the *Thoughtseed Framework* (Kavi et al., 2026). This feature introduces **Provenance Tracking**, linking current thoughts (Particles) to their origin Neuronal Packets (Graphiti Nodes).

## Why
To enable "Deep Cognition", the system must know *why* it thinks something. "Thoughts from thin air" are hallucinations. "Thoughts from Provenance" are deductions.

## What
1.  **Inlet (OODA):** `ConsciousnessManager` now extracts `provenance_ids` from `ReasoningAgent` results.
2.  **Transformation (Model):** `MetacognitiveParticle` carries a `provenance_ids` list.
3.  **Outlet (Graph):** `ParticleStore` persists this lineage to Graphiti/Neo4j, creating `DERIVED_FROM` edges.

## Connectivity Mandate (Verified)
- **Input:** `api/agents/consciousness_manager.py` (Line ~524)
- **Output:** `api/services/graphiti_service.py` (Node Payload)
- **Verification:** `tests/integration/test_provenance_flow.py` passed.

## Artifacts
- [Theory](file:///Volumes/Asylum/dev/dionysus3-core/docs/science/thoughtseed_framework.md)
- [Test](file:///Volumes/Asylum/dev/dionysus3-core/tests/integration/test_provenance_flow.py)
