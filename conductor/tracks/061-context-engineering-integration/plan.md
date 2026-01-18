# Track Plan: Context Engineering Integration

**Track ID**: 061-context-engineering-integration  
**Status**: Planned (0%)

## Phase 1: P0 Correctness + Archetype/Basin Linkage

**Goal**: Fix critical misalignments between Nemori, archetypes, and basin linkage; restore correctness in distillation flow.

- [x] **Task 1.1**: [TDD] Fix `predict_and_calibrate` tuple handling in `ConsciousnessMemoryCore` and add failing test for residue retention. (9ee3f49)
- [ ] **Task 1.2**: [TDD] Implement explicit archetype→basin linkage (seed/lookup or mapping) and verify `RESONATES_WITH` edges attach.

## Phase 2: P1 Nemori & Narrative Alignment

**Goal**: Align narrative/archetype outputs with schema and persist stabilizing attractors.

- [ ] **Task 2.1**: [TDD] Align Nemori archetype prompt to `DevelopmentArchetype` enum and add coverage for enum parsing.
- [ ] **Task 2.2**: [TDD] Persist `stabilizing_attractor` on `DevelopmentEpisode` and ensure storage/retrieval.

## Phase 3: P1 Context Engineering Integration

**Goal**: Bridge symbolic residue and context packaging into memory operations.

- [ ] **Task 3.1**: [TDD] Integrate symbolic residue into `ContextCell` and retrieval cues; ensure residue survives distillation.
- [ ] **Task 3.2**: [TDD] Wire context packaging to memory operations (budgeting + cell selection for recall).

## Phase 4: P2 Basin Dynamics Parity

**Goal**: Add decay, importance signals, and cross-basin connections for long-term stability.

- [ ] **Task 4.1**: [TDD] Add decay/importance signals for basin strength updates.
- [ ] **Task 4.2**: [TDD] Implement cross-basin connections (co-activation or relatedness edges).

## Dependencies

```
Task 1.1 → Task 1.2 → Task 2.1 → Task 2.2 → Task 3.1 → Task 3.2 → Task 4.1 → Task 4.2
```
