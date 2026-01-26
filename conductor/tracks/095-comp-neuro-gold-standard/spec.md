# Feature Specification: Computational Neuroscience Gold Standard Integration

**Track ID**: 095-comp-neuro-gold-standard
**Created**: 2026-01-26
**Status**: Active
**Source**: "Computational Neuroscience and Cognitive Modelling" (Britt Anderson, 2014)
**Location**: `data/Computational-Neuroscience-and-Cognitive-Modelling.pdf`
**NotebookLM**: Anderson (2014) has been added to NotebookLM; use for chapter mapping, citations, and Q&A when implementing this track.

## Overview

This track formalizes the integration of computational neuroscience foundations from Anderson (2014) into the Dionysus cognitive architecture. The book provides mathematical rigor for:
- Attractor basin dynamics (Hopfield networks)
- Cognitive architecture patterns (ACT-R)
- Active inference mathematics (probability, random walks)
- Agent-based modeling frameworks

## Chapter-to-Codebase Mapping

### Part I: Modelling Neurons (Ch 2-8)

| Chapter | Content | Dionysus Mapping | Priority |
|---------|---------|------------------|----------|
| Ch 2-5 | Differential equations, Integrate-and-Fire neurons | Active inference dynamics, precision-weighted belief updates | Medium |
| Ch 7 | Hodgkin-Huxley model | Mathematical foundation for neuronal activation patterns | Reference |

**Key Integration Points:**
- `api/services/efe_engine.py` - Differential equation patterns for EFE calculations
- `api/services/dynamics_service.py` - Neuronal dynamics modeling

### Part II: Neural Networks (Ch 9-13) [CRITICAL]

| Chapter | Content | Dionysus Mapping | Priority |
|---------|---------|------------------|----------|
| Ch 9 | Vectors and matrices | State-space representations in thoughtseeds | Medium |
| Ch 13 | Hopfield Networks, Auto-associative Memory | **Attractor basins** - memory consolidation, basin stability | **HIGH** |

**Key Integration Points:**
- NEW: `api/services/attractor_basin_service.py` - Hopfield-inspired attractor dynamics
- `api/services/memory_basin_router.py` - Basin routing patterns
- `api/services/thoughtseed_integration.py` - Thoughtseed state-space

### Part III: Probability and Psychological Models (Ch 14-16)

| Chapter | Content | Dionysus Mapping | Priority |
|---------|---------|------------------|----------|
| Ch 14-15 | Probability, Random walks | Active inference, EFE calculations, precision weighting | Medium |

**Key Integration Points:**
- `api/services/efe_engine.py` - Probabilistic EFE calculations
- `api/models/priors.py` - Prior hierarchy with precision weights
- `api/services/active_inference_service.py` - Inference dynamics

### Part IV: Cognitive Modelling as Logic and Rules (Ch 17-22) [CRITICAL]

| Chapter | Content | Dionysus Mapping | Priority |
|---------|---------|------------------|----------|
| Ch 19 | Production Rules | Thoughtseed competition, action selection | Medium |
| Ch 21 | ACT-R Cognitive Architecture | **OODA loop architecture**, ConsciousnessManager | **HIGH** |
| Ch 22 | Agent-Based Modelling | **smolagents multi-agent framework** | **HIGH** |

**Key Integration Points:**
- `api/agents/consciousness_manager.py` - ACT-R-inspired cognitive architecture
- `api/agents/heartbeat_agent.py` - OODA loop implementation
- `api/agents/managed/` - Multi-agent orchestration
- `api/agents/tools/` - Agent tool patterns

## Requirements

### Functional Requirements

#### FR-001: Hopfield Network Integration (Ch 13)
Implement attractor basin formalization using Hopfield network mathematics:
- Energy function: `E = -0.5 * Σ_ij w_ij * s_i * s_j`
- Update rule: `s_i(t+1) = sign(Σ_j w_ij * s_j(t))`
- Basin convergence detection for memory recall

#### FR-002: ACT-R OODA Enhancement (Ch 21)
Formalize OODA loop using ACT-R module patterns:
- Declarative Memory → Perception phase
- Procedural Memory → Orientation phase
- Goal Module → Decision phase
- Motor Module → Action phase

#### FR-003: Agent-Based Modeling Alignment (Ch 22)
Validate smolagents architecture against ABM principles:
- Agent autonomy and encapsulation
- Environment interaction protocols
- Multi-agent communication patterns

### Non-Functional Requirements

#### NFR-001: Mathematical Rigor
All implementations must include docstrings citing specific chapter/section references.

#### NFR-002: Traceability
Each code module must link back to source material via `# Ref: Anderson (2014), Ch X, p. Y`

## Success Criteria

| ID | Criterion | Metric |
|----|-----------|--------|
| SC-001 | Attractor basin service implements Hopfield energy function | Unit tests pass with >95% coverage |
| SC-002 | ACT-R mapping documented in consciousness_manager.py | All OODA phases annotated |
| SC-003 | Chapter mapping document complete | All 23 chapters mapped |
| SC-004 | Documentation in Quartz format | Atomic concept pages created |

## Deliverables

1. **Code**
   - `api/services/attractor_basin_service.py` - Hopfield-inspired attractor dynamics
   - Updates to `consciousness_manager.py` with ACT-R annotations
   - Updates to `efe_engine.py` with probability theory references

2. **Documentation** (Quartz)
   - `docs/garden/content/comp-neuro-gold-standard.md` - Master mapping
   - `docs/garden/content/concepts/hopfield-attractors.md` - Atomic concept
   - `docs/garden/content/concepts/act-r-ooda.md` - Atomic concept
   - `docs/garden/content/concepts/abm-smolagents.md` - Atomic concept

3. **Research Integration**
   - PDF added to NotebookLM notebook for grounded research queries

## Dependencies

- Track 038-thoughtseeds-framework (EFE engine, prior hierarchy)
- Track 039-smolagents-v2-alignment (managed agents)
- Track 057-memory-systems-integration (memory basins)

## References

- Anderson, B. (2014). *Computational Neuroscience and Cognitive Modelling*. SAGE Publications.
- Hopfield, J.J. (1982). Neural networks and physical systems with emergent collective computational abilities.
- Anderson, J.R. (2007). *How Can the Human Mind Occur in the Physical Universe?* (ACT-R)
