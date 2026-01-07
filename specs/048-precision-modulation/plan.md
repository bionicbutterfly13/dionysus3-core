# Implementation Plan: Precision Modulation (Feature 048)

## Phase 1: Precision Registry
- [ ] **Step 1**: Update `api/services/metaplasticity_service.py` to maintain a persistent `_precision_registry` (dictionary of agent_id -> float).
- [ ] **Step 2**: Implement `get_precision(agent_id)` and `set_precision(agent_id, value)`.

## Phase 2: Surprise Hook
- [ ] **Step 3**: Implement `update_precision_from_surprise(agent_id, surprise_score)` logic.
- [ ] **Step 4**: Modify `ConsciousnessManager._run_ooda_cycle` to call this update after calculating surprise.

## Phase 3: EFE Regularization
- [ ] **Step 5**: Update `EFEEngine.calculate_efe` or add a specific `calculate_precision_weighted_efe` method.
- [ ] **Step 6**: Refactor `ActionPlannerService` to use the precision-weighted EFE for lookahead evaluation.

## Phase 4: Metacognitive Tool
- [ ] **Step 7**: Implement `SetMentalFocusTool` in `api/agents/tools/cognitive_tools.py`.
- [ ] **Step 8**: Register tool in `ConsciousnessManager` for the `MetacognitionAgent`.

## Phase 5: Verification
- [ ] **Step 9**: Create `tests/unit/test_precision_modulation.py`.
- [ ] **Step 10**: Verify "Zoom Out" behavior on high-surprise events.
