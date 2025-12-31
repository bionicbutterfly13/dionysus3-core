# Implementation Plan: Active Inference Planning (Feature 046)

## Phase 1: Policy Models
- [ ] **Step 1**: Create `api/models/policy.py`.
- [ ] **Step 2**: Define `ActionPolicy`, `SimulatedStep`, and `PolicyResult` Pydantic models.

## Phase 2: Action Planner Service
- [ ] **Step 3**: Create `api/services/action_planner_service.py`.
- [ ] **Step 4**: Implement LLM-based policy generation.
- [ ] **Step 5**: Implement path-based EFE calculation (summing uncertainty + divergence over steps).
- [ ] **Step 6**: Implement `select_best_policy`.

## Phase 3: Reasoning Tool
- [ ] **Step 7**: Create `api/agents/tools/planning_tools.py`.
- [ ] **Step 8**: Implement `active_planner` tool using `ActionPlannerService`.
- [ ] **Step 9**: Register tool in `ConsciousnessManager` for the `ReasoningAgent`.

## Phase 4: Verification
- [ ] **Step 10**: Create `tests/unit/test_action_planner.py`.
- [ ] **Step 11**: End-to-end OODA cycle test with planning enabled.

## Phase 5: Documentation
- [ ] **Step 12**: Update `spec.md` and tasks.
