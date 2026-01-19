# Track Plan: Context Engineering Integration

**Track ID**: 061-context-engineering-integration
**Status**: In Progress

## Phase 1: P0 Correctness + Archetype/Basin Linkage ✅

**Goal**: Fix critical misalignments between Nemori, archetypes, and basin linkage; restore correctness in distillation flow.

- [x] **Task 1.1**: [TDD] Fix `predict_and_calibrate` tuple handling in `ConsciousnessMemoryCore` and add failing test for residue retention. (9ee3f49)
- [x] **Task 1.2**: [TDD] Implement explicit archetype→basin linkage (seed/lookup or mapping) and verify `RESONATES_WITH` edges attach. (099359e, ce11465) - Added `ARCHETYPE_TO_BASIN` mapping in `autobiographical_service.py`; added basin seeding test coverage

## Phase 2: P1 Nemori & Narrative Alignment ✅

**Goal**: Align narrative/archetype outputs with schema and persist stabilizing attractors.

- [x] **Task 2.1**: [TDD] Align Nemori archetype prompt to `DevelopmentArchetype` enum and add coverage for enum parsing. (099359e) - Fixed prompt in `nemori_river_flow.py` to use valid enum values
- [x] **Task 2.2**: [TDD] Persist `stabilizing_attractor` on `DevelopmentEpisode` and ensure storage/retrieval. (099359e) - Added field to `api/models/autobiographical.py`

## Phase 3: P1 Context Engineering Integration ✅

**Goal**: Bridge symbolic residue and context packaging into memory operations.

- [x] **Task 3.1**: [TDD] Integrate symbolic residue into `ContextCell` and retrieval cues; ensure residue survives distillation. (099359e) - Added ContextCell creation and SymbolicResidueTracker in `nemori_river_flow.py`
- [x] **Task 3.2**: [TDD] Wire context packaging to memory operations (budgeting + cell selection for recall). (099359e) - Integrated TokenBudgetManager in `predict_and_calibrate()`

## Phase 4: P2 Basin Dynamics Parity ✅

**Goal**: Add decay, importance signals, and cross-basin connections for long-term stability.

- [x] **Task 4.1**: [TDD] Add decay/importance signals for basin strength updates. (099359e) - Added `_apply_decay_to_other_basins()` in `memory_basin_router.py`
- [x] **Task 4.2**: [TDD] Implement cross-basin connections (co-activation or relatedness edges). (cf182cf) - Added `_link_basins()` and basin transition linking in `memory_basin_router.py`

## Phase 5: P2 Integration Verification

**Goal**: Add integration coverage for Nemori flow bridging basin routing and context packaging.

- [~] **Task 5.1**: [TDD] Add integration test for Nemori predict-calibrate routing and context packaging residue tracking.

## Dependencies

```
Task 1.1 → Task 1.2 → Task 2.1 → Task 2.2 → Task 3.1 → Task 3.2 → Task 4.1 → Task 4.2
```
