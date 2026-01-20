# Architecture Audit: The Amnesiac Core

**Date:** 2026-01-19
**Context:** Feature 059 (Temporal Identity) & Feature 040 (Metacognition)
**Focus:** Technical Autopsy of Cognitive Systems

## Executive Summary
The cognitive architecture has "High Schema Fidelity" (the Pydantic models are theoretically sound and aligned with Tomasello/Fesce) but "Low Runtime Fidelity" (the services are often ephemeral, disconnected, or brittle).

## 1. What's Good? (The Solid Foundation)
*   **The Biological Agency Schema (`api/models/biological_agency.py`)**:
    *   **Verdict**: Excellent. The specific Pydantic models for `PerceptionState`, `ExecutiveState`, and `MetacognitiveState` map perfectly to the Evolutionary Tiers (Tomasello). It is a rigorous implementation of the theoretical specs.
*   **The Belief State Math (`api/models/belief_state.py`)**:
    *   **Verdict**: Robust. The implementation of Gaussian entropy, precision matrices, and uncertainty reduction is mathematically consistent. It correctly treats beliefs as distributions, not just values.
*   **Embedding Service Logic (`api/services/embedding.py`)**:
    *   **Verdict**: Solid. The logic for switching between OpenAI and Ollama, handling dimensionality checks (768 vs 1536), and health checks is well-implemented.

## 2. What's Broken? (Critical Failures)
*   **Belief System Schizophrenia**:
    *   **Issue**: `ActiveInferenceService` (Lines 100-115) defines its local `BeliefState` (qs, qπ) which is **totally incompatible** with the main `api/models/belief_state.py` (mean, precision).
    *   **Impact**: The "Brain" (Active Inference) and the "Soul" (Worldview/Beliefs) speak different languages. They cannot exchange data without complex data-lossy translation layers which currently do not exist.
*   **Julia Dependency Brittleness**:
    *   **Issue**: `ActiveInferenceService` relies entirely on a lazy-loaded Julia runtime (`_initialize_julia`).
    *   **Impact**: If the Julia environment isn't perfect (common in Docker/CI), the service hard-crashes. There is no Python-native fallback for the VFE/EFE calculations, making the "core cognitive loop" extremely fragile.

## 3. What Works But Shouldn't? (Brittle Luck)
*   **The "Bias" Filter (Silent Failure)**:
    *   **Code**: `WorldviewIntegrationService.filter_prediction_by_worldview`
    *   **Issue**: If the embedding service fails (e.g., OLLAMA down, API key missing), the `_calculate_alignment` method catches the exception and returns `0.5`.
    *   **Result**: The complex "Bayesian Prior" logic silently degrades into a coin flip. The system thinks it's strictly applying worldview constraints, but it's actually just letting everything through with a generic weight. It "works" (doesn't crash), but it defeats the purpose.

## 4. What Doesn't But Pretends To? (Mockware)
*   **Biological Identity (The Amnesiac)**:
    *   **Code**: `BiologicalAgencyService`
    *   **Issue**: The service uses an in-memory dictionary `self._agents = {}` to store `BiologicalAgentState`.
    *   **Reality**: It is **Ephemeral**. Every time the API restarts (deployment, crash, reload), the "Identity" dies and resets to `Tier 1: Goal-Directed`.
    *   **The Pretend**: It *looks* like a persistent, evolving agent, but it has no Long-Term Memory (no Graphiti/Neo4j persistence implemented for this state). It is a "Philosophy Zombie" that is born and dies with the process.

## Recommendations for Feature 059 Alignment
1.  **Persist Identity**: Move `BiologicalAgentState` storage from in-memory dict to Graphiti/Neo4j immediately.
2.  **Unify Beliefs**: Refactor `ActiveInferenceService` to import and use `api/models/belief_state.py`.
3.  **Harden Bias**: Change `_calculate_alignment` to raise an alert or default to "High Uncertainty" (0.1) rather than "Neutral" (0.5), or enforce Embedding Service health.

---

## 5. Protocol 060 (Unified Memory Pyramid) Implementation
*   **Status**: Completed & Verified.
*   **Architecture Change**:
    *   **Graphiti Refactor**: `ingest_extracted_relationships` now uses direct Cypher to link Entities to the source ID (Trajectory) without creating redundant Episode nodes ("The Fourth Tower" resolved).
    *   **Nemori Integration**: `NemoriRiverFlow` updated to ingest `Trajectory` streams directly, promoting them to `DevelopmentEpisode` nodes linked via `[:SUMMARIZES]`.
    *   **Verification**: `tests/integration/verify_protocol_060.py` confirms 1:1 linking and 0 redundancy.

## User Notes
<!-- Add your permanent notes here. The system will respect this section. -->

