# Feature Specification: UnifiedRealityModel Live Integration

**Track ID**: 071-urm-live-integration
**Created**: 2026-01-20
**Status**: Planned
**Depends On**: 056-beautiful-loop-hyper (Done)

---

## Executive Summary

The UnifiedRealityModel (URM) service is implemented with correct data structures and update methods, but nothing in the OODA cycle is feeding it live data. This track wires the ConsciousnessManager to populate the URM with real-time cognitive state, making it a true "living" representation of consciousness rather than a mock container.

**Current State**: URM has empty fields for `belief_states`, `active_inference_states`, `current_context`, and `resonance`.

**Target State**: URM reflects the actual cognitive state at each OODA cycle, enabling downstream services (ResonanceDetector, EpistemicFieldService) to operate on real data.

---

## Gap Analysis

### What Exists (Track 056 Complete)

| Component | Status | Location |
|-----------|--------|----------|
| `UnifiedRealityModel` model | ✅ Done | `api/models/beautiful_loop.py:121` |
| `UnifiedRealityModelService` | ✅ Done | `api/services/unified_reality_model.py` |
| `update_bound_inferences()` | ✅ Called | Via `BayesianBinder.evaluate()` |
| `ResonanceDetector.detect()` | ✅ Done | `api/services/resonance_detector.py` |
| 203 Beautiful Loop tests | ✅ Pass | Unit, integration, contract |

### What's Missing (This Track)

| Gap | Impact | Fix Required |
|-----|--------|--------------|
| `update_belief_states()` never called | Empty belief container | Wire to BeliefStateService or OODA context |
| `update_active_inference_states()` never called | No AI state tracking | Wire to Meta-ToT ai_state creation (line 442) |
| `update_context()` never called | No context in URM | Call at OODA cycle start |
| `resonance` field never set | Resonance computed but not stored | Set after `resonance_detector.detect()` |
| `add_metacognitive_particle()` missing | Line 542 calls non-existent method | Add method to service |
| No EventBus subscriptions | URM doesn't react to events | Subscribe to cognitive events |

---

## User Stories

| Story | Priority | Title | Description |
|-------|----------|-------|-------------|
| US1 | P0 | Context Population | URM receives OODA cycle context at cycle start |
| US2 | P0 | Active Inference State | URM tracks ai_state from Meta-ToT/ConsciousnessManager |
| US3 | P1 | Resonance Storage | Resonance signal stored in URM after detection |
| US4 | P1 | Metacognitive Particle API | Add method for particle accumulation |
| US5 | P2 | Belief State Sync | URM syncs with BeliefStateService |
| US6 | P2 | EventBus Subscriptions | URM auto-updates from cognitive events |

---

## Functional Requirements

**Context Integration (US1)**
- **FR-001**: `update_context()` called at START of each OODA cycle in `ConsciousnessManager.run()`
- **FR-002**: Context includes task_query, coordination_plan, and cycle_id
- **FR-003**: Context cleared/reset between cycles (not accumulated)

**Active Inference State (US2)**
- **FR-010**: When `ActiveInferenceState` created (line 442-447), call `update_active_inference_states()`
- **FR-011**: Support list of states (multi-agent scenarios)
- **FR-012**: State includes surprise, prediction_error, precision, beliefs

**Resonance Storage (US3)**
- **FR-020**: Add `update_resonance(signal: ResonanceSignal)` method
- **FR-021**: After `resonance_detector.detect()`, store signal in URM
- **FR-022**: Resonance accessible via `urm.get_model().resonance`

**Metacognitive Particles (US4)**
- **FR-030**: Add `add_metacognitive_particle(particle)` method
- **FR-031**: Particles accumulate (append, not replace)
- **FR-032**: Optional: Decay old particles after N cycles

**Belief State Sync (US5)**
- **FR-040**: If BeliefStateService exists, sync at cycle end
- **FR-041**: Extract belief distributions from reasoning results
- **FR-042**: Support hierarchical beliefs (layer-specific)

**EventBus Integration (US6)**
- **FR-050**: Subscribe to `cognitive_event` on service init
- **FR-051**: Extract ai_state from event and update URM
- **FR-052**: Subscribe to `precision_update` events

---

## Success Criteria

- **SC-001**: `urm.get_model().current_context` is non-empty during active OODA cycle
- **SC-002**: `urm.get_model().active_inference_states` populated after Meta-ToT
- **SC-003**: `urm.get_model().resonance` set after each cycle completion
- **SC-004**: All 203 existing Beautiful Loop tests still pass (no regression)
- **SC-005**: New integration tests verify live data flow
- **SC-006**: ResonanceDetector operates on real (not mock) data in production

---

## Technical Design

### ConsciousnessManager Integration Points

```python
# consciousness_manager.py - START of run()
async def run(self, task_query: str, initial_context: Dict, ...) -> str:
    cycle_id = str(uuid4())
    urm_service = get_unified_reality_model()

    # FR-001: Context population
    urm_service.update_context(
        {"task_query": task_query, **initial_context},
        cycle_id=cycle_id
    )

    # ... existing OODA logic ...
```

```python
# consciousness_manager.py - After ai_state creation (line 447)
if ai_state is None:
    ai_state = ActiveInferenceState(...)

# FR-010: Active inference state update
urm_service.update_active_inference_states([ai_state])
```

```python
# consciousness_manager.py - After resonance detection (line 527)
resonance_signal = resonance_detector.detect(urm_service.get_model(), cycle_id=cycle_id)

# FR-021: Store resonance
urm_service.update_resonance(resonance_signal)
```

### UnifiedRealityModelService Additions

```python
def update_resonance(self, signal: ResonanceSignal) -> None:
    """Store resonance signal in model."""
    self._model.resonance = signal
    self._touch()

def add_metacognitive_particle(self, particle: MetacognitiveParticle) -> None:
    """Append metacognitive particle to accumulator."""
    self._model.metacognitive_particles.append(particle)
    self._touch()

def clear_cycle_state(self) -> None:
    """Reset transient state for new cycle (keeps bound_inferences)."""
    self._model.metacognitive_particles = []
    self._model.resonance = None
    self._touch()
```

---

## Test Strategy

### Unit Tests (TDD)
- Test `update_resonance()` stores signal correctly
- Test `add_metacognitive_particle()` appends (not replaces)
- Test `clear_cycle_state()` resets transient fields
- Test context update with cycle_id tracking

### Integration Tests
- Test full OODA cycle populates all URM fields
- Test ResonanceDetector reads real data from URM
- Test multiple cycles maintain proper state transitions

### Contract Tests
- Verify API returns populated (not empty) model fields
- Verify resonance field serializes correctly

---

## Dependencies

- **Track 056**: Beautiful Loop Hyper-Model (✅ Done - 203 tests)
- **Track 038**: Thoughtseeds Framework (✅ Done - Active inference)
- `api/agents/consciousness_manager.py`: Primary integration target
- `api/models/meta_tot.py`: ActiveInferenceState model
- `api/models/meta_cognition.py`: MetacognitiveParticle model

---

## Out of Scope

- Belief state extraction from LLM responses (complex NLP)
- Multi-agent URM synchronization
- Persistent URM state across sessions (use Graphiti for that)
- Real-time URM visualization
