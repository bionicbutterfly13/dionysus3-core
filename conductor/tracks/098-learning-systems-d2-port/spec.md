# Track 098: In-Context, Meta-Learning & Episodic Meta-Learning (D2 Port)

**Status:** Planned  
**Branch:** `feature/098-learning-systems-d2-port`  
**Goal:** Ensure in-context learning, meta-learning, and episodic meta-learning are **somewhat implemented** in Dionysus 3, with missing or D2-only logic ported and gateway-compliant, **before** sunsetting Dionysus 2.0 and contributing it to open source.

---

## 1. Scope: Three Pillars

| Pillar | Description | D3 Location | D2 Reference |
|--------|-------------|-------------|--------------|
| **In-context learning** | Learning from examples supplied in the prompt (few-shot, lessons injection). Model adapts within context. | Meta-cognitive "lessons" injection into ReasoningAgent; few-shot patterns in `MetaLearningEnhancer`. | Implicit in D2 prompting and episodic learner. |
| **Meta-learning** | Learning *how* to learn: paper classification, algorithm extraction, pattern library. Document-level. | `api/models/meta_learning.py`, `api/services/meta_learning_enhancer.py` (D2 port). | `meta_learning_document_enhancer.py`. |
| **Episodic meta-learning** | Learning from *reasoning episodes* (task → strategy → outcome). Optimize tool use and OODA over time. | `api/models/meta_cognition.py`, `api/services/meta_cognitive_service.py` (Feature 043). | `backend/services/enhanced_daedalus/meta_cognitive_integration.py` (`MetaCognitiveEpisodicLearner`). |

Product guidelines (17–18): *"metamemory as well as episodic, semantic, and procedural metalearning"*; *"adding experiential/episodic memories as well as semantic, procedural, and strategic learning and metalearning."*

---

## 2. Current State (D3)

### 2.1 Episodic meta-learning (043)

- **Implemented:** `CognitiveEpisode` model, `MetaCognitiveLearner` (retrieve, record, synthesize). Wired into `ConsciousnessManager`: pre-OODA retrieval + lesson injection, post-OODA episode recording.
- **Gaps:**
  - **Gateway violation:** `MetaCognitiveLearner` uses `get_neo4j_driver()` and direct Cypher. Must use **Graphiti, n8n, or API only** (CLAUDE.md prime directive).
  - Retrieval uses fulltext/`CONTAINS` fallback; no vector search via Graphiti.
  - `CognitiveEpisode.agency_score` is not persisted in `record_episode` Cypher.
  - Schema/index setup: `cognitive_task_index` may be missing; `scripts/maintenance/setup_meta_cognition_schema.py` exists but may not be run in deployment.

### 2.2 Meta-learning (document enhancer)

- **Implemented:** `MetaLearningPaperType`, `MetaLearningAlgorithm`, `MetaLearningPattern`, `MetaLearningEnhancer`. Unit tests in `tests/unit/test_meta_learning.py`.
- **Gaps:** Enhancer is **not** invoked by the document processing pipeline (see wisdom_extraction_raw). No route or ingest flow calls it. Effectively isolated.

### 2.3 In-context learning

- **Implemented:** Meta-cognitive lessons injected into `initial_context["meta_cognitive_lessons"]` and used in the OODA prompt. Few-shot–style patterns in `MetaLearningEnhancer`.
- **Gaps:** No dedicated "in-context learning" module. Relies on episodic meta-learning for lessons; if that’s broken or empty, in-context learning degrades.

---

## 3. D2 Port Responsibilities

**D2 root:** `/Volumes/Asylum/dev/Dionysus-2.0`. See `conductor/tracks/098-learning-systems-d2-port/d2-paths.md` for exact file paths.

- **Episodic meta-learning:** Core logic already ported (043). D2 `MetaCognitiveEpisodicLearner` lives in `backend/services/enhanced_daedalus/meta_cognitive_integration.py`. Optional epLSTM in `extensions/context_engineering/eplstm_architecture.py`. Remaining work: gateway-compliant persistence and retrieval in D3; any D2-specific behavior not yet in D3 must be identified and ported before D2 sunset.
- **Meta-learning (document):** Models and enhancer ported from D2 `backend/src/services/meta_learning_document_enhancer.py`. Remaining work: wire into document pipeline (or equivalent) so enhancement is actually used.
- **In-context:** No separate D2 module; reinforce via episodic meta-learning + explicit use of lessons in prompts.

---

## 4. Success Criteria

1. **Gateway compliance:** No direct Neo4j access in learning systems. All persistence/retrieval via Graphiti, n8n webhooks, or Dionysus API.
2. **Episodic meta-learning:** Retrieve → inject → record loop works end-to-end; episodes stored and recalled through gateway; `agency_score` persisted.
3. **Meta-learning (document):** Enhancer is invoked by at least one document processing path (e.g. extraction pipeline, ingest route).
4. **In-context learning:** Lessons from episodic meta-learning are consistently injected and reflected in OODA prompt; behavior is testable.
5. **Tests:** Unit and integration tests for all three pillars; no regressions.
6. **Documentation:** Track spec, plan, and any new endpoints or config documented; Quartz journal entry on completion.

---

## 5. Dependencies

- `api.services.graphiti_service` (or approved gateway) for episodic persistence/retrieval.
- `conductor/workflow.md`, TDD, feature branch, wake-up.
- Zero-data migration policy: port **logic and schema**, not D2 data.

---

## 6. Out of Scope (This Track)

- Procedural meta-learning (explicit implementation).
- Semantic meta-learning beyond existing Graphiti/Nemori usage.
- Full D2 codebase audit; only learning-related D2 references called out in specs and this track.
