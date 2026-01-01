# Implementation Plan: Consciousness Self-Evolution (Feature 049)

## Phase 1: Continuous Monitoring
- [ ] **Step 1**: Create `api/services/background_worker.py` (if not exists) or enhance it.
- [ ] **Step 2**: Implement `capture_system_moment()` – captures energy, active basins, and memory stats.
- [ ] **Step 3**: Configure APScheduler to run the monitor cycle every 5 minutes.

## Phase 2: Self-Reflection Loop
- [ ] **Step 4**: Create `api/services/meta_evolution_service.py`.
- [ ] **Step 5**: Implement `reflect_on_episodes()` – analyzes the last 24h of `CognitiveEpisodes`.
- [ ] **Step 6**: Implement `propose_strategy_shift()` – uses LLM to generate internal alignment updates.

## Phase 3: Integration & Persistence
- [ ] **Step 7**: Update `ConsciousnessManager` to accept "Evolutionary Updates" during the OODA "Orient" phase.
- [ ] **Step 8**: Ensure all background reflections are pushed through the `UnifiedIntegrationPipeline`.

## Phase 4: Verification
- [ ] **Step 9**: Create `tests/integration/test_evolution_loop.py`.
- [ ] **Step 10**: Verify that "System Moments" are appearing in Neo4j.

## Phase 5: Pruning & Precision
- [ ] **Step 11**: Connect the evolution loop to the "Mental Zoom" (Precision modulation) logic.
