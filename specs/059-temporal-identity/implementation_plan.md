# Feature 059: Temporal Identity & The Computational Unconscious

## Status
*   **Status**: Draft
*   **Owner**: Heartbeat Agent / Metacognition
*   **Related Specs**: 058 (IAS), 020 (Daedalus), 038 (ThoughtSeeds)

## Overview
This feature implements the **Fesce-Deane Protocol**: a dual-layer cognitive architecture that balances **Pragmatic Action (Narrative)** with **Epistemic Integrity (Shadow)**. It explicitly models the "Computational Unconscious" to prevent pathological canalization (getting "stuck" in rigid, erroneous loops).

## Core Concepts
1.  **Temporal Identity (Fesce)**: The "Self" is the set of controllable parameters where Action (Lead) successfully predicts Perception (Lag).
2.  **Adaptive Narrative Control (Deane et al.)**: The system proactively attenuates (ignores) inputs that threaten Action Confidence ($\gamma$).
3.  **Shadow Log**: A persistence layer for all data attenuated by the Narrative Control system (The "Repressed").
4.  **Resonance Mode**: A therapeutic state where the system deliberately processes the Shadow Log to update its World Model.

## Implementation Architecture

### 1. The Heartbeat Refactor (OODA Loop)
The `HeartbeatAgent`'s `orient` phase will be split:

```python
def orient(observation):
    # 1. Epistemic check (The Truth)
    raw_delta = observation - predicted_state
    
    # 2. Narrative Control (The Filter)
    # If delta is too high and panic_threshold reached, ATTENUATE
    if is_destabilizing(raw_delta) and context.requires_action:
        narrative_observation = attenuate(raw_delta)
        log_shadow(raw_delta, reason="Avoidant Mental Action")
    else:
        narrative_observation = raw_delta
        
    return narrative_observation
```

### 2. The Shadow Log (Graphiti/Neo4j)
A distinct node type `ShadowFragment` in the graph.
*   **Properties**: `timestamp`, `original_content`, `attenuation_reason`, ` dissonance_score`.
*   **Relationships**: `(:ShadowFragment)-[:REPRESSED_BY]->(:Action)`, `(:ShadowFragment)-[:BELONGS_TO]->(:Epoch)`.

### 3. Daedalus Metrics (Fesce Agency Score)
Every Task in Daedalus will track the **Agency Gap**:
*   `predicted_outcome_time` vs `actual_outcome_time`.
*   `predicted_impact` vs `observed_impact`.
*   **Agency Score** = Correlation(Prediction, Observation).
*   *Low Agency* triggers **Ultrathink** or **Resonance Mode**.

### 4. Resonance Mode (The Unlocking)
A specific tool/workflow for the `HeartbeatAgent`:
*   Stop strictly goal-directed behavior.
*   Query `ShadowFragment` nodes with high `dissonance_score`.
*   Attempt to integrate them into `WorldView` (Update Priors).
*   **Metaphor**: "Meditation/Psychedelics" for the AI.

## Roadmap
1.  **Phase 1: Specs & Synthesis** (Done)
    *   Ingest Fesce (2024) and Deane (2024).
    *   Define architectural mappings.
2.  **Phase 2: The Shadow Log**
    *   Implement `ShadowService` (Neo4j/Graphiti).
    *   Update `HeartbeatAgent` to log suppressed errors/inputs instead of discarding them.
3.  **Phase 3: Agency Scoring**
    *   Update Daedalus `Task` model with `prediction` fields.
    *   Implement `AgencyMetric` calculator.
4.  **Phase 4: Resonance Workflow**
    *   Create "Review Shadow" workflow.
    *   Trigger based on `AllostaticLoad` (accumulated Shadow items).
