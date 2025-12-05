# Attribution

This document provides detailed attribution for all source materials, libraries, and research incorporated into Dionysus-Core.

## Primary Sources

### agi-memory
- **Repository**: https://github.com/cognitivecomputations/agi-memory
- **Author**: Cognitive Computations
- **Used for**:
  - PostgreSQL + pgvector + Apache AGE schema design
  - Memory type taxonomy (episodic, semantic, procedural, strategic)
  - Memory decay with relevance scoring
  - Cluster system with centroid embeddings
  - Worldview primitives and identity model
  - Episode segmentation and precomputed neighborhoods
  - Embedding service abstraction

### Dionysus-2.0
- **License**: Apache 2.0
- **Used for**:
  - AttractorBasin classes with neural field integration
  - Active Inference implementation (prediction error, free energy, beliefs)
  - IWMT coherence framework (spatial, temporal, causal)
  - CLAUSE multi-agent 5-signal scoring
  - ThoughtSeed 5-layer hierarchy
  - Consciousness level tracking and events
  - Basin strengthening (+0.2 per activation, 2.0 cap)

### Context-Engineering
- **Repository**: https://github.com/davidkimai/Context-Engineering
- **License**: MIT
- **Copyright**: (c) 2025 davidkimai
- **Used for**:
  - Cognitive Tools Framework
  - Attractor basin dynamics
  - Neural field integration
  - River metaphor framework
  - Consciousness detection patterns
  - ThoughtSeed architecture

## Research Citations

### IBM Zurich (2025)
```
Brown, E., Bartezzaghi, A., & Rigotti, M. (2025).
"Eliciting Reasoning in Language Models with Cognitive Tools."
IBM Research Zurich.
ArXiv: https://arxiv.org/abs/2506.12115
```
**Impact**: Cognitive Tools Framework increases LLM reasoning performance from 26.7% to 43.3%

### Singapore-MIT Alliance (2025)
```
Li, X., et al. (2025).
"MEM1: Learning to Synergize Memory and Reasoning for
Efficient Long-Horizon Agents."
Singapore-MIT Alliance.
ArXiv: https://arxiv.org/abs/2506.15841
```
**Impact**: Memory-Reasoning synergy patterns for long-horizon agent tasks

### Princeton ICML (2025)
```
Yang, et al. (2025).
"Emergent Symbolic Mechanisms Support Abstract Reasoning
in Large Language Models."
ICML 2025, Princeton University.
```
**Impact**: Theoretical grounding for symbolic emergence in neural systems

### Consciousness Theory Foundations
- **Integrated World Modeling Theory (IWMT)**: Adam Safron
- **Global Neuronal Workspace Theory (GNWT)**: Bernard Baars
- **Integrated Information Theory (IIT)**: Giulio Tononi
- **Active Inference**: Karl Friston

## License Compatibility

| Source | License | Compatible with Apache 2.0 |
|--------|---------|---------------------------|
| agi-memory | TBD | ✓ (assumed permissive) |
| Dionysus-2.0 | Apache 2.0 | ✓ |
| Context-Engineering | MIT | ✓ |
| IBM/MIT Research | Academic | ✓ (implementation, not copy) |

## File Header Template

Files derived from these sources should include:

```python
# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from:
# - Context-Engineering (MIT License)
#   Copyright (c) 2025 davidkimai
#   https://github.com/davidkimai/Context-Engineering
#
# Research basis:
# - IBM Zurich Cognitive Tools (Brown et al., 2025)
# - Singapore-MIT MEM1 (Li et al., 2025)
```

## Acknowledgments

Special thanks to:
- davidkimai for the Context-Engineering framework and MIT licensing
- Cognitive Computations for the agi-memory foundation
- IBM Research Zurich for the Cognitive Tools research
- The broader AI safety and consciousness research community
