# Track Specification: Jungian Cognitive Archetypes

**Track ID**: 002-jungian-archetypes
**Status**: In Progress
**Date**: 2026-01-28
**Objective**: Integrate Jungian Archetypes as **Dispositional Priors** within the Thoughtseeds framework, enabling sub-personal archetype competition via Expected Free Energy (EFE) minimization.

## Theoretical Foundation

This track implements the archetype layer from Kavi et al. (2025) "Thoughtseeds" framework, positioning archetypes within the 4-level evolutionary prior hierarchy:

```
BASAL (B)     → Survival, arousal, homeostasis
LINEAGE (L)   → Cultural/familial patterns
DISPOSITIONAL (D) → JUNGIAN ARCHETYPES ← This Track
LEARNED (λ)   → Experience-based priors
```

### Core Insight
Archetypes are not personality types—they are **sub-personal priors** that bias thoughtseed formation and competition for the Inner Screen. Like Internal Family Systems (IFS) "parts," each archetype has:
- Protective intentions
- Activation triggers
- Shadow complement (attenuated when dominant archetype wins)
- Preferred action affordances

## The 12 Archetypes (Dispositional Prior Structure)

| Archetype | Basin Affinity | Shadow | Trigger Pattern |
|-----------|---------------|--------|-----------------|
| SAGE | cognitive_science | FOOL | Analysis requests, debugging |
| WARRIOR | systems_theory | VICTIM | Conflicts, deadlines, threats |
| CREATOR | machine_learning | DESTROYER | Building, generating, scaffolding |
| RULER | systems_theory | TYRANT | Orchestration, delegation, planning |
| EXPLORER | philosophy | WANDERER | Research, unknown domains |
| MAGICIAN | neuroscience | MANIPULATOR | Integration, transformation |
| CAREGIVER | consciousness | MARTYR | Recovery, healing, maintenance |
| REBEL | philosophy | OUTLAW | Breaking constraints, innovation |
| INNOCENT | consciousness | NAIVE | Happy paths, initial setup |
| ORPHAN | systems_theory | CYNIC | Error handling, edge cases |
| LOVER | consciousness | OBSESSIVE | UX optimization, aesthetics |
| JESTER | machine_learning | TRICKSTER | Fuzz testing, creative variation |

## Integration Architecture

### Layer 1: Archetype Prior Structure (api/models/priors.py)

Extend the existing 3-level prior hierarchy with archetype-specific fields:

```python
class ArchetypePrior(BaseModel):
    """Dispositional prior representing a Jungian archetype."""
    archetype: JungianArchetype
    dominant_attractor: str  # Primary basin affinity
    subordinate_attractors: list[str]  # Secondary basins
    preferred_actions: list[str]  # Tool/action affordances
    avoided_actions: list[str]  # Suppressed affordances
    shadow: str  # Shadow archetype name
    precision: float  # Current confidence weight (0-1)
    activation_threshold: float  # EFE threshold for activation
```

### Layer 2: Thoughtseed Flavoring (api/services/efe_engine.py)

Dominant archetype modulates thoughtseed generation:

```
INPUT: Generic thoughtseed "Fix this error"
ACTIVE ARCHETYPE: WARRIOR (precision=0.8)

OUTPUT: "Destroy this bug immediately and prevent recurrence"
        + preferred_actions=[delete_code, refactor, test]
        + avoided_actions=[analyze_deeply, research]
```

### Layer 3: Narrative → Archetype Evidence Pipeline

Text2Story/SVO extraction provides Bayesian evidence for archetype activation:

```
NARRATIVE MOTIFS → ARCHETYPE EVIDENCE → POSTERIOR UPDATE

"The hero slays the dragon" → WARRIOR +0.3
"The sage seeks wisdom"    → SAGE +0.4
"The creator builds anew"  → CREATOR +0.35
```

### Layer 4: EFE Competition (Paper Eq. 33)

Archetypes compete via cumulative Expected Free Energy:

```python
dominant_archetype = argmin(
    sum(EFE(action, archetype) for action in anticipated_actions)
    for archetype in active_archetypes
)
```

Winner-take-all: Dominant archetype gets Inner Screen access.
Losers: Logged to Shadow Log for potential resonance.

### Layer 5: Shadow Log & Resonance Protocol

**Shadow Log**: Stores attenuated archetype signals when suppressed by dominant winner.

```python
shadow_log.append({
    "archetype": suppressed_archetype,
    "efe_score": original_score,
    "suppression_timestamp": now(),
    "suppression_context": current_basin
})
```

**Resonance Protocol**: When allostatic load exceeds threshold, Shadow Log archetypes resurface for rebalancing:

```python
if allostatic_load > RESONANCE_THRESHOLD:
    shadow_candidates = shadow_log.get_recent(window=10)
    for candidate in shadow_candidates:
        if candidate.efe_score < RESONANCE_ACTIVATION:
            activate_resonance_mode(candidate.archetype)
```

## Integration (IO Map)

### Attachment Points

| Component | File | Integration Point |
|-----------|------|-------------------|
| Prior Hierarchy | `api/models/priors.py` | Add ArchetypePrior to PriorHierarchy |
| EFE Engine | `api/services/efe_engine.py` | Extend select_dominant_thought() |
| Basin Router | `api/services/memory_basin_router.py` | Archetype→Basin mapping |
| Narrative Extractor | `api/services/narrative_extraction_service.py` | Motif→Archetype evidence |
| Consciousness Manager | `api/services/consciousness_manager.py` | Archetype state tracking |
| Active Inference | `api/services/consciousness/active_inference_analyzer.py` | Archetype classification |

### Inlets

- **Narrative content** from `route_memory()` → Text2Story/SVO extraction
- **Tool invocations** from agent callbacks → Action pattern classification
- **Basin activation** from `memory_basin_router.py` → Basin affinity weighting
- **Arousal state** from `arousal_system_service.py` → Precision modulation

### Outlets

- **Dominant archetype** → `ConsciousnessManager` state
- **Suppressed archetypes** → Shadow Log
- **Archetype evidence** → Graphiti temporal KG (episodic memory)
- **Precision updates** → EFE calculations in `efe_engine.py`

## Functional Requirements

### FR-1: Archetype Prior Model
- [ ] Extend `priors.py` with `ArchetypePrior` class
- [ ] Define all 12 archetypes with basin affinities, shadows, affordances
- [ ] Integrate into existing `PriorHierarchy` as DISPOSITIONAL level

### FR-2: EFE-Based Competition
- [ ] Extend `select_dominant_thought()` with archetype weighting
- [ ] Implement archetype EFE calculation per anticipated action
- [ ] Winner-take-all selection with shadow logging

### FR-3: Narrative Evidence Pipeline
- [ ] Extract archetype evidence from Text2Story motifs
- [ ] Map SVO patterns to archetype activations
- [ ] Bayesian update of archetype precision based on evidence

### FR-4: Shadow Log Implementation
- [ ] Create `ShadowLog` service for attenuated archetype storage
- [ ] Time-windowed retrieval for resonance candidates
- [ ] Integration with allostatic load monitoring

### FR-5: Resonance Protocol
- [ ] Define resonance threshold based on allostatic load
- [ ] Implement resonance mode activation from Shadow Log
- [ ] Rebalancing mechanism for suppressed archetypes

## Success Criteria

1. **Archetype Competition**: Given conflicting signals, system correctly selects dominant archetype via EFE minimization
2. **Narrative Alignment**: Text2Story motifs correctly map to archetype evidence
3. **Shadow Logging**: Suppressed archetypes are logged and retrievable
4. **Resonance Activation**: High allostatic load triggers resonance from Shadow Log
5. **Basin Alignment**: Dominant archetype biases basin activation appropriately
6. **Test Coverage**: 80%+ coverage on all new archetype services

## Non-Goals (Out of Scope)

- Direct user-facing archetype selection (archetypes emerge from behavior)
- Personality profiling or typing
- Cross-session archetype persistence (each session starts fresh)
- UI visualization of archetype state (future track)

## References

- Kavi et al. (2025) "Thoughtseeds: Evolutionary Priors, Nested Markov Blankets, and the Emergence of Conscious Experience"
- Jung, C.G. "The Archetypes and the Collective Unconscious"
- Internal Family Systems (IFS) - Schwartz, R.
- specs/059-temporal-identity/adaptive_narrative_control.md
- specs/020-coordination-pool/coordination_pool_spec.md
