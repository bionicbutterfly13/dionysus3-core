# Implementation Plan: Meta-Cognitive Learning (Feature 043)

## Phase 1: Models & Schema
- [ ] **Step 1**: Create `api/models/meta_cognition.py` with `CognitiveEpisode` and `UsagePattern` models.
- [ ] **Step 2**: Create `scripts/setup_meta_cognition_schema.py` to ensure Neo4j indices for episode vectors exist (if not handled by Graphiti).

## Phase 2: Service Layer
- [ ] **Step 3**: Create `api/services/meta_cognitive_service.py`.
    - Implement `record_episode`.
    - Implement `retrieve_similar_episodes`.
    - Implement `synthesize_strategy`.

## Phase 3: Integration
- [ ] **Step 4**: Modify `api/agents/consciousness_manager.py`.
    - Inject `MetaCognitiveLearner` into the `__init__`.
    - Update `_run_ooda_cycle` to query learner at start.
    - Update `_run_ooda_cycle` to save episode at end.

## Phase 4: Testing
- [ ] **Step 5**: Create `tests/unit/test_meta_cognition.py`.
- [ ] **Step 6**: Run tests and verify behavior.

## Phase 5: Cleanup
- [ ] **Step 7**: Merge branch.
