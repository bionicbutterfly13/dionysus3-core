# Conductor Track 065: Adaptive MemEvolve Implementation

## Objective
Upgrade Dionysus to a **VPS-Native Generative Learning System** by implementing the "Express Highway" and "Structure Learning" protocols. This moves beyond RAG to **Active Inference**: the system minimizes Variational Free Energy (VFE) to optimize its own mental model.

## Core Constraint
**"Structure Learning" (Phase 4)** requires a unified **"Express Highway" (Phase 1)**. We cannot mathematically expand the state space if the data flow is fragmented.

## The 4 Phases Implementation Plan

### Phase 1: The Express Highway (Ingestion/Encoding)
**Current Status:** Fragmented (multiple paths).
**Goal:** Unified Linear Pipeline.
**Architecture:**
1.  **Input:** Raw Content + Metadata.
2.  **Episodic Encoder (Nemori):** Assigns Time/Episodic Context (`EventID`).
3.  **Context Encoder (Basin):** Assigns Gravity/Context (`BasinID`).
4.  **Structural Encoder (AutoSchema):** Assigns Structure/Ontology (`SchemaStructure`). This acts as the **Semantic Layout Engine**, mapping tokens to Hierarchical Concept Nodes.
5.  **Gateway (MemEvolve):** The *single* Write Point.
6.  **Driver (Graphiti):** The *single* DB Transaction.

### Phase 2: Retrieval (Exit Ramps)
**Current Status:** Functional but static tuning.
**Goal:** Context-Aware Strategy Switching.
**Architecture:**
-   Implement `RetrievalStrategy` nodes in Neo4j.
-   `MemEvolveAdapter` selects strategy (Vector vs. Graph vs. Hybrid) based on query context.

### Phase 3: Active Inference (Parameter Learning)
**Current Status:** Theoretical.
**Goal:** VFE-Based Parameter Optimization.
**Architecture:**
-   **Service:** `ActiveInferenceService` (Generative Model).
-   **Mechanism:**
    -   Predicts observation ($P(o|s)$).
    -   Calculates Surprisal (VFE).
    -   **Low Surprisal:** Updates $A$ (Likelihood) and $D$ (Prior) matrices (Habit Formation).

### Phase 4: Structure Learning (Meta-Evolution)
**Current Status:** New (Frontiers 2020 Protocol).
**Goal:** State-Space Discovery.
**Architecture:**
-   **Mechanism:**
    -   **High Surprisal:** Triggers `expand_state_space()` (Adds new Hidden State Factor).
    -   **Consolidation:** Uses **Bayesian Model Reduction** to prune unused states (Sleep Optimization).

## Success Criteria
1.  **Unified Ingest:** `KGLearningService` orchestrates the "Express Highway" (Nemori+AutoSchema -> Graphiti).
2.  **No Bypass:** `AutoSchemaKG` returns *concepts*, not *writes*.
3.  **VFE Metric:** Every ingestion logs a VFE score, driving the evolution loop.
4.  **Structure Learning:** The graph automatically creates new "Concept Basins" for novel inputs.
