# Dionysus 2.0 Paths (Learning Systems)

**D2 root:** `/Volumes/Asylum/dev/Dionysus-2.0`

Use these paths for T009 (D2 vs D3 diff) and any port work before D2 sunset and open-source.

---

## Episodic meta-learning

| Purpose | D2 path |
|--------|---------|
| MetaCognitiveEpisodicLearner, CognitiveToolEpisode, prompt learning, procedural meta-learning | `backend/services/enhanced_daedalus/meta_cognitive_integration.py` |
| epLSTM (episodic LSTM, DND, reinstatement gates) | `extensions/context_engineering/eplstm_architecture.py` |
| ASI-Arch + epLSTM integration | `extensions/context_engineering/theoretical_foundations.py` (`create_asi_arch_context_engineering_system`) |
| Spec | `spec-management/Consciousness-Specs/EPISODIC_META_LEARNING_SPEC.md` |

**D2 deps:** `cognitive_tools_implementation`, `cognitive_meta_coordinator`, `eplstm_architecture`, `theoretical_foundations`. Optional: `ai_mri_pattern_learning_integration`.

---

## Meta-learning (document)

| Purpose | D2 path |
|--------|---------|
| MetaLearningDocumentEnhancer, paper types, extraction | `backend/src/services/meta_learning_document_enhancer.py` |
| Uses | `UnifiedDocumentProcessor`, `ConsciousnessIntegrationPipeline`, `MetaCognitiveEpisodicLearner` (when available) |

---

## Procedural meta-learning (EMO)

| Purpose | D2 path |
|--------|---------|
| EMO-style episodic memory (FIFO/LRU/CLOCK), cognitive gradients, aggregation | `backend/services/enhanced_daedalus/procedural_meta_learning_emo.py` |

---

## Context engineering / extensions

| Purpose | D2 path |
|--------|---------|
| Context engineering root | `extensions/context_engineering/` |
| Core impl, hybrid DB | `extensions/context_engineering/core_implementation.py`, `hybrid_database.py` |
| Attractor basins, thoughtseeds | `attractor_basin_dynamics.py`, `thoughtseed_active_inference` (referenced by backend) |

---

## Notes

- D2 `meta_cognitive_integration` uses **in-memory** episode list + optional epLSTM; no Neo4j. D3 ports to Graphiti/API.
- epLSTM lives under `extensions/context_engineering`; D2 appends that path for imports. D3 has no epLSTM port yet.
- **Zero-data migration:** port logic/schema only; do not migrate D2 DB files or episode stores.
