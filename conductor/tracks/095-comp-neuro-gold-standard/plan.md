# Implementation Plan: Computational Neuroscience Gold Standard Integration

**Track ID**: 095-comp-neuro-gold-standard
**Created**: 2026-01-26
**Spec**: [spec.md](./spec.md)

## Phase 1: Foundation & Documentation

### P1.1: Research Integration
- [x] Verify PDF exists at `data/Computational-Neuroscience-and-Cognitive-Modelling.pdf`
- [x] Create conductor track with spec.md
- [x] Document NotebookLM integration instructions (manual upload required)
- [x] Add Anderson (2014) to NotebookLM (computational neuroscience document now available for querying)

### P1.2: Documentation Structure (Quartz)
- [x] Create master chapter mapping `docs/garden/content/comp-neuro-gold-standard.md`
- [x] Create atomic concepts in `docs/garden/content/concepts/`

## Phase 2: High-Priority Chapter Integration

### P2.1: Chapter 13 - Hopfield Networks & Attractor Basins (FR-001)
- [x] Create `api/services/attractor_basin_service.py`
- [x] Implement Hopfield energy function: `E = -0.5 * Σ_ij w_ij * s_i * s_j` (with bias support per Wang 2024)
- [x] Implement state update rule: `s_i(t+1) = sign(Σ_j w_ij * s_j(t) + θ_i)`
- [x] Add basin convergence detection
- [x] Implement overlap function M(s) = Σ_i ξ_i * s_i (Wang 2024)
- [x] Implement strong attractors (degree > 1) per Edalat & Mancinelli (2013)
- [x] Implement effective condition number per Lin, Yeap, & Kiringa (2024)
- [x] Create unit tests in `tests/unit/test_attractor_basin_service.py` (21 tests)
- [x] Create atomic concept doc `docs/garden/content/concepts/hopfield-attractors.md`

### P2.2: Chapter 21 - ACT-R & OODA Loop Enhancement (FR-002)
- [ ] Annotate `api/agents/consciousness_manager.py` with ACT-R module mappings
- [ ] Document OODA-to-ACT-R correspondence:
  - Observe → Perceptual-Motor Module
  - Orient → Declarative Memory
  - Decide → Procedural Memory (production rules)
  - Act → Motor Module
- [ ] Add chapter references to existing code comments
- [x] Create atomic concept doc `docs/garden/content/concepts/act-r-ooda.md`

### P2.3: Chapter 22 - Agent-Based Modeling Alignment (FR-003)
- [ ] Audit `api/agents/managed/` against ABM principles
- [ ] Document agent autonomy patterns in managed agents
- [ ] Validate environment interaction protocols
- [x] Create atomic concept doc `docs/garden/content/concepts/abm-smolagents.md`

## Phase 3: Medium-Priority Chapter Integration

### P3.1: Chapters 2-5 - Differential Equations
- [ ] Review `api/services/dynamics_service.py` for alignment
- [ ] Add references to integrate-and-fire neuron concepts
- [ ] Document precision-weighted belief update mathematics

### P3.2: Chapters 14-15 - Probability & Random Walks
- [ ] Review `api/services/efe_engine.py` probability calculations
- [ ] Add mathematical references to entropy calculations
- [ ] Document random walk connections to active inference

### P3.3: Chapter 19 - Production Rules
- [ ] Map thoughtseed competition to production rule firing
- [ ] Document conflict resolution strategies
- [ ] Add references to action selection mechanisms

## Phase 4: Reference Documentation

### P4.1: Chapter 7 - Hodgkin-Huxley (Historical Context)
- [ ] Create reference note in documentation
- [ ] Link to biological grounding concepts

### P4.2: Chapters 17-18 - Boolean Logic
- [ ] Document foundational logic concepts
- [ ] Link to decision-making patterns

## Integration (IO Map)

### Attachment Points
- `api/services/attractor_basin_service.py:332` → HopfieldNetwork.recall_pattern()
- `api/services/attractor_basin_service.py:389` → AttractorBasinService (high-level API)
- `api/agents/consciousness_manager.py` → Existing OODA orchestrator (ACT-R annotations pending)
- `api/services/efe_engine.py` → Existing EFE calculations
- `api/services/memory_basin_router.py:380` → Integration point for basin activation

### Inlets
- **HopfieldNetwork**: Binary patterns (-1/+1 arrays), degree for strong attractors
- **AttractorBasinService**: Content strings, seed patterns for basin creation
- Memory patterns from `memory_basin_router.py` (future integration)
- EFE calculations from `efe_engine.py` (future integration)

### Outlets
- **BasinState**: name, pattern (np.ndarray), energy, activation, stability, metadata
- **ConvergenceResult**: converged (bool), iterations, final_state, energy_trajectory
- Effective condition number for capacity monitoring
- Normalized overlap for basin membership detection

### Key Methods
- `HopfieldNetwork.store_pattern(pattern, degree)` - Hebbian learning with strong attractors
- `HopfieldNetwork.compute_energy(state)` - Energy with optional bias
- `HopfieldNetwork.compute_overlap(state, pattern)` - Basin membership indicator
- `HopfieldNetwork.run_until_convergence(initial, max_iter)` - Pattern recall
- `HopfieldNetwork.compute_effective_condition_number()` - Capacity metric
- `AttractorBasinService.create_basin(name, content)` - Content-addressed basin
- `AttractorBasinService.find_nearest_basin(query)` - Basin lookup

## Testing Strategy

| Component | Test Type | Location |
|-----------|-----------|----------|
| AttractorBasinService | Unit | `tests/unit/test_attractor_basin_service.py` |
| Hopfield energy function | Unit | Same as above |
| ACT-R annotations | Documentation review | Manual |
| ABM alignment | Audit | Manual |

## Commit Checkpoints

- [ ] `feat(095): create conductor track and spec`
- [ ] `docs(095): add chapter mapping document`
- [ ] `feat(095): implement attractor basin service`
- [ ] `docs(095): annotate consciousness_manager with ACT-R`
- [ ] `docs(095): create atomic concept pages`

## Notes

- NotebookLM PDF upload is a manual step (user must upload to existing notebook)
- Existing code already implements many concepts; focus is on formalization and documentation
- Mathematical rigor requires citing specific page numbers from Anderson (2014)
