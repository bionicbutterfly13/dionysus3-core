# Task Queue - 057-complete-placeholder-implementations

**Specification**: spec.md (6 user stories, 12 functional requirements)
**Strategy**: TDD methodology - tests before implementation, one task per iteration

---

## Current Task

> **T021: Un-skip test_service_creation, make it pass**
>
> Un-skip test_service_creation in tests/unit/test_epistemic_field_service.py.
> Verify EpistemicFieldService can be instantiated and singleton works.
>
> **Acceptance**: Test passes, service can be created
> **Time**: 10 min
> **Type**: Test+Code

---

## Backlog

### Phase 2: P2 - Validation (US3, US4)

#### US3: EpistemicFieldService Tests (FR-005, FR-006)
- [ ] T019: Read Beautiful Loop spec (056) to understand epistemic depth theory (Research, 10 min)
- [ ] T020: Create api/services/epistemic_field_service.py stub (Code, 5 min)
- [ ] T021: Un-skip test_service_creation, make it pass (Test+Code, 10 min)
- [ ] T022: Un-skip test_get_epistemic_state, implement minimal service (Test+Code, 15 min)
- [ ] T023: Un-skip test_track_sharing_depth (Test+Code, 15 min)
- [ ] T024: Un-skip test_depth_increases_with_more_layers (Test+Code, 10 min)
- [ ] T025: Un-skip test_bidirectional_sharing_counted (Test+Code, 15 min)
- [ ] T026: Un-skip test_depth_score_computed (Test+Code, 10 min)
- [ ] T027: Un-skip test_depth_score_in_range (Test+Code, 10 min)
- [ ] T028: Un-skip test_depth_score_weighted_average (Test+Code, 15 min)
- [ ] T029: Un-skip test_bound_processes_are_aware (Test+Code, 10 min)
- [ ] T030: Un-skip test_unbound_processes_are_transparent (Test+Code, 10 min)
- [ ] T031: Un-skip test_classify_process (Test+Code, 10 min)
- [ ] T032: Un-skip test_focused_vs_diffuse_differentiation (Test+Code, 15 min)
- [ ] T033: Un-skip test_effect_size_threshold (Test+Code, 15 min)
- [ ] T034: Un-skip all 5 luminosity factor tests (Test+Code, 20 min total)
- [ ] T035: Run coverage report, verify >90% coverage (Verify, 5 min)
- [ ] T036: Add edge case tests for negative/invalid luminosity factors (Test+Code, 15 min)

#### US4: Beautiful Loop OODA Tests (FR-007, FR-008)
- [ ] T037: Read OODA agent hierarchy to understand integration points (Research, 10 min)
- [ ] T038: Un-skip test_perception_uses_current_phi (Test+Code, 15 min)
- [ ] T039: Un-skip test_observation_weighted_by_modality_precision (Test+Code, 15 min)
- [ ] T040: Un-skip test_reasoning_respects_layer_precision (Test+Code, 15 min)
- [ ] T041: Un-skip test_inference_candidates_generated (Test+Code, 15 min)
- [ ] T042: Un-skip test_binding_selection_in_decide (Test+Code, 15 min)
- [ ] T043: Un-skip test_bound_inferences_become_actions (Test+Code, 15 min)
- [ ] T044: Un-skip test_action_generates_prediction_errors (Test+Code, 15 min)
- [ ] T045: Un-skip test_errors_feed_back_to_hyper_model (Test+Code, 15 min)
- [ ] T046: Un-skip test_complete_cycle_execution (Test+Code, 20 min)
- [ ] T047: Un-skip test_cycle_runs_once_per_ooda_iteration (Test+Code, 15 min)
- [ ] T048: Un-skip test_state_persists_across_cycles (Test+Code, 15 min)
- [ ] T049: Un-skip test_phi_reaches_all_layers (Test+Code, 15 min)
- [ ] T050: Un-skip test_layers_acknowledge_precision_update (Test+Code, 15 min)
- [ ] T051: Un-skip test_precision_profile_consistency (Test+Code, 15 min)
- [ ] T052: Un-skip test_no_mid_cycle_updates (Test+Code, 15 min)
- [ ] T053: Un-skip test_overhead_under_10_percent (Test+Code, 20 min)
- [ ] T054: Un-skip test_no_blocking_operations (Test+Code, 15 min)
- [ ] T055: Un-skip all 4 event broadcast tests (Test+Code, 20 min)
- [ ] T056: Run coverage report, verify >90% coverage (Verify, 5 min)
- [ ] T057: Measure overhead, verify <10% of baseline (Verify, 10 min)

### Phase 3: P3 - Operational (US5, US6)

#### US5: GHL Email Sync (FR-009)
- [ ] T058: Read GHL API docs for workflow/email endpoints (Research, 10 min)
- [ ] T059: Write test for fetch_all_emails() success case (Test, 10 min)
- [ ] T060: Implement fetch_all_emails() with GHL API call (Code, 15 min)
- [ ] T061: Write test for GHL API error handling (Test, 10 min)
- [ ] T062: Implement error handling with descriptive exceptions (Code, 10 min)
- [ ] T063: Write test for pagination if >100 emails (Test, 10 min)
- [ ] T064: Implement pagination with exponential backoff (Code, 15 min)
- [ ] T065: Manual test with real API (8 emails in 30s) (Verify, 10 min)

#### US6: Metacognition Storage (FR-010)
- [ ] T066: Read Graphiti service API for add_entity/add_relationship (Research, 10 min)
- [ ] T067: Read multi-tier service API for store_hot (Research, 5 min)
- [ ] T068: Replace mock in store_semantic() with real Graphiti calls (Code, 15 min)
- [ ] T069: Replace mock in store_episodic() with real HOT tier calls (Code, 15 min)
- [ ] T070: Replace mock in store_procedural() with real HOT tier calls (Code, 15 min)
- [ ] T071: Replace mock in store_strategic() with real meta-learner calls (Code, 15 min)
- [ ] T072: Write integration test for complete storage flow (Test, 15 min)
- [ ] T073: Manual test on VPS - verify 6 entities + 7 relationships (Verify, 10 min)

### Final Validation
- [ ] T074: Run full test suite, verify all pass (Verify, 5 min)
- [ ] T075: Run coverage report, verify >90% for new code (Verify, 5 min)
- [ ] T076: Verify SC-001: Energy level variance >0 in 10 snapshots (Verify, 10 min)
- [ ] T077: Verify SC-002: Thoughtseed selection >70% optimal (Verify, 15 min)
- [ ] T078: Verify SC-003-010: All success criteria met (Verify, 20 min)
- [ ] T079: Create PR with summary of changes (Admin, 15 min)

---

## Completed

- [x] **T001**: Read and understand active inference wrapper interface ✓
  - Wrapper uses `score_thought(thought, goal_vector, context_probs)` → `ActiveInferenceScore`
  - Returns EFE, surprise, prediction_error, precision
  - Formula: `EFE = (1/precision) * entropy + precision * divergence`
  - Methods: `get_active_inference_wrapper()`, `wrapper.score_thought()`

- [x] **T002**: Read attractor basin service to understand depth query API ✓
  - Service: `get_memory_basin_router()` → `MemoryBasinRouter`
  - Method: `async get_basin_stats(basin_name=None)` → Dict with basins
  - Basin properties: `strength` (0.5-2.0), `stability` (0.5-1.0), `activation_count`
  - Active threshold: `strength > 0.3`
  - Energy: `sum(b['strength'] for b in active_basins)`

- [x] **T003**: Write test for capture_system_moment() with real energy_level computation ✓
  - Created tests/unit/test_meta_evolution_service.py with 5 tests
  - test_energy_level_computed_from_basin_strengths (US1-AS1, FR-001)
  - test_energy_level_excludes_weak_basins, test_active_basins_count_computed_from_threshold (FR-002)
  - test_zero_active_basins_cold_start, test_energy_level_validation_in_range (FR-011)
  - All tests currently FAIL (expected - TDD red phase) ✓
  - Committed: 350192c

- [x] **T004**: Implement real energy_level and active_basins_count calculation ✓
  - Imported get_memory_basin_router in meta_evolution_service.py
  - Replaced placeholders (100.0, 5) with real basin query
  - energy_level = sum(basin['strength'] for basins with strength > 0.3)
  - active_basins_count = len(active_basins)
  - Added validation [0, 10] range with warning logs and clamping (FR-011)
  - All 6 tests now PASS (TDD green phase) ✓
  - Committed: 59bf545
  - **Note**: T005-T010 completed in this task (both metrics + validation done together)

- [x] **T011**: Write test for expand_node() with unique scores per child ✓
  - Created tests/unit/test_core_meta_tot.py with 7 tests
  - All tests PASS - scoring already correctly implemented! ✓
  - Tests verify: unique scores, wrapper called, goal alignment, precision weighting
  - Discovered: TODO comment outdated, real scoring already works
  - Committed: 834a0ba

- [x] **T012**: Replace TODO in meta_tot.py:62 with accurate documentation ✓
  - Removed misleading TODO comment
  - Added accurate documentation: real scoring IS implemented via ai_wrapper.score_thought()
  - No code changes - comment clarification only
  - Tests still pass (verified) ✓
  - Committed: 8e4b686
  - **Note**: T013-T016 already complete (scoring fully functional)

- [x] **T017**: Write test for graceful handling of None/error from wrapper ✓
  - Updated test_expand_node_handles_wrapper_failure_gracefully to expect fallback
  - Added test_expand_node_handles_wrapper_returning_none for None handling
  - Tests verify: children created despite failure, valid fallback scores
  - Both tests FAIL (expected - TDD red phase) ✓
  - Committed: 63e392d

- [x] **T018**: Implement fallback to neutral score on wrapper failure ✓
  - Added try-except wrapper around score_thought() call
  - Handle None return explicitly with warning log
  - Created _create_neutral_fallback_score() helper (EFE=5.0, high uncertainty)
  - System continues functioning instead of crashing
  - Both error handling tests now PASS (TDD green phase) ✓
  - Committed: 3e0b00a
  - **US2 COMPLETE**: Real Active Inference Scoring ✓

- [x] **T019**: Read Beautiful Loop spec (056) to understand epistemic depth theory ✓
  - Epistemic depth = recursive self-knowing through hyper-model precision forecasting
  - depth_score (0-1) = weighted avg of luminosity factors (hyper_model_active, bidirectional_sharing, meta_precision_level, binding_coherence)
  - Aware processes = bound into consciousness (active_bindings), Transparent = running but not "known" (transparent_processes)
  - OODA integration: forecast at START, apply during OBSERVE/ORIENT, collect errors at END, update hyper-model between cycles
  - Research complete - ready to implement EpistemicFieldService ✓

- [x] **T020**: Create api/services/epistemic_field_service.py stub ✓
  - File already exists (from 056-beautiful-loop-hyper merge)
  - Has real implementation of get_epistemic_state() with luminosity factor computation
  - Missing: track_sharing_depth() and classify_process() methods (will add as tests require)
  - Singleton pattern already implemented with get_epistemic_field_service()
  - Ready for test un-skipping ✓

---

## Discovered

_New tasks found during implementation will be added here_

---

## Blocked

_Tasks that can't proceed - document blocker and proposed solution_

---

## Notes

**Total Estimated Tasks**: 79
**Estimated Time**: ~18-22 hours (assuming 15 min avg per task)
**P1 Tasks**: 18 (4-5 hours)
**P2 Tasks**: 39 (10-12 hours)
**P3 Tasks**: 15 (3-4 hours)
**Validation**: 7 (1-2 hours)

**Critical Path**: T001 → T011 → T020 → T037 → T058 → T066 → T074

**Dependencies**:
- T011+ requires T001 (understand active inference API)
- T020+ requires T019 (understand epistemic depth theory)
- T037+ requires Beautiful Loop services operational
- T058+ requires GHL API credentials
- T066+ requires Graphiti + multi-tier services operational
