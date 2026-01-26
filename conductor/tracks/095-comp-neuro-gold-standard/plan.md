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
- [ ] Create `api/services/attractor_basin_service.py`
- [ ] Implement Hopfield energy function: `E = -0.5 * Σ_ij w_ij * s_i * s_j`
- [ ] Implement state update rule: `s_i(t+1) = sign(Σ_j w_ij * s_j(t))`
- [ ] Add basin convergence detection
- [ ] Create unit tests in `tests/unit/test_attractor_basin_service.py`
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
- `api/services/attractor_basin_service.py` → NEW service
- `api/agents/consciousness_manager.py` → Existing OODA orchestrator
- `api/services/efe_engine.py` → Existing EFE calculations
- `api/services/memory_basin_router.py` → Existing basin routing

### Inputs
- Thoughtseed state vectors from `thoughtseed_integration.py`
- Memory patterns from `memory_basin_router.py`
- EFE calculations from `efe_engine.py`

### Outputs
- Attractor basin convergence states
- Memory recall patterns
- ACT-R-annotated cognitive processing logs

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
