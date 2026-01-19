# Plan: Adaptive MemEvolve (Track 065)

## Phase 1: The Express Highway (Consolidation)

- [x] **Step 1: Refactor `KGLearningService` to orchestrate.**
    -   Create `ingest_unified(content, source_id)` method.
    -   It must sequentially call:
        -   `Nemori.analyze_event(content)` -> returns `EventContext`.
        -   `AutoSchema.infer_structure(content)` -> returns `Structure`.
        -   `AttractorBasin.classify(content)` -> returns `BasinID`.
    -   It must then package these into a `MemEvolveRequest`.

- [x] **Step 2: Update `MemEvolveAdapter` to handle rich context.**
    -   Ensure `ingest_trajectory` accepts `EventContext`, `Structure`, and `BasinID` in `metadata`.
    -   Pass these to `GraphitiService` to write as Properties/Labels on the created Node.

- [x] **Step 3: Disconnect Direct Writes (The "Transformer" Refactor).**
    -   **CRITICAL:** Refactor `AutoSchemaKG` from a "Consumer" (Direct Writer) to a **"Structural Encoder" (Pure Transformer)**.
    -   Remove `graphiti.ingest_contextual_triplet` calls from `infer_and_store`.
    -   Instead, `infer_schema` must return `InferredConcept` objects to the orchestrator.
    -   This ensures `KGLearningService` maintains atomic control over the write transaction.

## Phase 2: Retrieval Strategy

- [x] **Step 4: Implement `RetrievalStrategy` Node.**
    - [x] Define Schema for Strategy Node (top_k, alpha, expansion_depth) in `api/models/kg_learning.py`.
    - [x] Implement `ActiveInferenceService.expand_query` for latent query expansion.
    - [x] Update `MemEvolveAdapter.recall` to fetch the *Active Strategy* and expand queries.
    - [x] Verified via `scripts/verify_retrieval_strategy.py`.

## Phase 3: Meta-Evolution Loop (The "Active Inference" Upgrade)

- [x] **Step 1: Integrate Active Inference Service.**
    - [x] Utilize `ActiveInferenceService` for VFE calculation.
    - [x] Integrate `calculate_semantic_vfe` for scalar surprisal.

- [x] **Step 2: Implement VFE-Based Trigger.**
    - [x] Refactor `trigger_evolution` to calculate Avg VFE from recent trajectories.
    - [x] Trigger evolution when VFE > Threshold (High Surprisal).

- [x] **Step 3: Graphiti Strategy Injection (Parameter Learning).**
    - [x] Store new `RetrievalStrategy` nodes with updated parameters ($top\_k=15$) when triggered.
    - [x] Verified via `scripts/verify_meta_evolution.py`.

## Phase 4: Structure Learning (The "Frontiers 2020" Upgrade)

- [x] **Step 1: State Space Expansion (`expand_state_space`).**
    - [x] If VFE > 0.7 (Radical Surprisal), the Generative Model "hallucinates" a new hidden state.
    - [x] Create a new `Concept` node in Graphiti: `(c:Concept {status: 'experimental'})`.

- [x] **Step 2: Bayesian Model Reduction (`reduce_model`).**
    - [x] Periodically prune 'experimental' nodes that fail to gain evidence (low degree).
    - [x] Keep the graph lean and potent.

- [x] **Step 3: Verification.**
    - [x] Simulate "Radical Surprisal" (e.g., query about "Quantum Gravity in Marketing").
    - [x] Verify a new Concept is created.

## Phase 5: Verification

- [ ] **Step 6: State-Space Expansion (Discovery).**
    -   Ingest 1 Document.
    -   Verify Node in Neo4j has:
        -   `Time` (from Nemori)
        -   `Type` (from AutoSchema)
        -   `Basin` (from Context)
        -   `VFE Score` (from Active Inference)
