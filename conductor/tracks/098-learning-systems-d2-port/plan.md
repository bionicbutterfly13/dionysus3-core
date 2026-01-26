# Plan: 098 – In-Context, Meta-Learning & Episodic Meta-Learning (D2 Port)

**Track:** 098-learning-systems-d2-port  
**Branch:** `feature/098-learning-systems-d2-port`

---

## Phase 1: Inventory & Gateway Compliance (Episodic Meta-Learning)

- [ ] **T001: Remove direct Neo4j usage from `MetaCognitiveLearner`.**
  - **Goal:** Comply with gateway-only access. No `get_neo4j_driver()`, no direct Cypher.
  - **Strategy:** Introduce a small **episodic store abstraction** (e.g. `EpisodicMetaLearningStore`) that:
    - **Write:** Persist episodes via Graphiti ingest and/or n8n webhook (e.g. MemEvolve-style trajectory ingest) or a dedicated `/api/memory/cognitive-episode` endpoint. Choose one approved path and document it.
    - **Read:** Retrieve episodes via Graphiti search or recall webhook, keyed by task description / semantic similarity.
  - **Files:** `api/services/meta_cognitive_service.py`, new store adapter if needed.
  - **Acceptance:** No imports of `neo4j` driver or `get_neo4j_driver` in meta_cognitive_service; all I/O via gateway.

- [ ] **T002: Persist `agency_score` and align `CognitiveEpisode` with store schema.**
  - **Goal:** `record_episode` persists `agency_score`; retrieve returns it. Schema used by the gateway (Graphiti/n8n/API) matches the model.
  - **Strategy:** Update store adapter and any Graphiti/n8n payloads to include `agency_score`; update `CognitiveEpisode` parsing in retrieve.
  - **Files:** `api/models/meta_cognition.py`, meta_cognitive_service, store/adapter.

- [ ] **T003: Episodic retrieval via Graphiti or recall webhook.**
  - **Goal:** Replace fulltext/`CONTAINS` Neo4j query with gateway-based retrieval (e.g. Graphiti `search` or n8n recall) for similar past tasks.
  - **Strategy:** Use task description (and optionally `task_context`) as query; map recall results to `CognitiveEpisode` instances. Prefer vector/semantic search if available.
  - **Files:** `api/services/meta_cognitive_service.py`, store adapter.

- [ ] **T004: Verify schema and index setup.**
  - **Goal:** Ensure `:CognitiveEpisode` (or gateway-equivalent) indices exist and are used. Document how to run setup (e.g. `setup_meta_cognition_schema.py` or gateway-specific init).
  - **Strategy:** Review `scripts/maintenance/setup_meta_cognition_schema.py`; adapt for gateway if indices live in Neo4j behind Graphiti; otherwise document gateway-specific setup.
  - **Files:** Script, `docs/` or track spec.

---

## Phase 2: Wire Meta-Learning Document Enhancer

- [ ] **T005: Invoke `MetaLearningEnhancer` from document processing.**
  - **Goal:** At least one document pipeline path runs meta-learning enhancement (classification, pattern extraction).
  - **Strategy:** Identify the primary document ingestion or extraction pipeline (e.g. concept extraction, PDF ingest, Graphiti ingest). Add a step that calls `get_meta_learning_enhancer()` and processes the document (or extracted text). Store results (e.g. `paper_type`, algorithms, patterns) via Graphiti or existing ingest.
  - **Files:** Pipeline service (e.g. `consciousness_integration_pipeline`, concept extraction, or ingest router), `api/services/meta_learning_enhancer.py`.
  - **Acceptance:** Integration test or manual run shows enhancer output used (e.g. stored in graph or returned in API response).

- [ ] **T006: Add routing or config toggle for meta-learning enhancement.**
  - **Goal:** Feature-flag or explicit opt-in so enhancement can be disabled without code changes.
  - **Strategy:** Env var or request-level flag (e.g. `meta_learning_enhancement: bool`) and skip enhancer when false.
  - **Files:** Pipeline, config, or router.

---

## Phase 3: In-Context Learning Clarity & Tests

- [ ] **T007: Document and assert in-context learning behavior.**
  - **Goal:** In-context learning is explicitly defined and exercised in tests.
  - **Strategy:** Short doc (e.g. in track spec or `docs/`) stating that in-context learning = use of meta-cognitive lessons + few-shot-style content in OODA prompt. Add an integration test: run OODA with pre-seeded lessons and assert they appear in the payload or prompt passed to the reasoner.
  - **Files:** `conductor/tracks/098-.../spec.md` or `docs/`, `tests/integration/` or `tests/unit/`.

- [ ] **T008: Integration test for episodic meta-learning loop.**
  - **Goal:** Full loop: record episode via gateway → retrieve → synthesize lessons → inject. No direct Neo4j.
  - **Strategy:** Test that uses the store adapter (or gateway endpoints) to record 1–2 episodes, then calls `retrieve_relevant_episodes` + `synthesize_lessons`, and checks that lessons are non-empty and valid. Mock LLM for `synthesize_lessons` if needed.
  - **Files:** `tests/integration/test_episodic_meta_learning.py` (or equivalent).

---

## Phase 4: D2 Diff & Sunset Readiness

- [ ] **T009: Compare D2 `meta_cognitive_integration` vs D3 `MetaCognitiveLearner`.**
  - **Goal:** List any D2 behavior or fields not yet in D3; port or explicitly defer before D2 sunset.
  - **Strategy:** Review D2 `backend/services/enhanced_daedalus/meta_cognitive_integration.py` (and related meta-learning code). Produce a short checklist: implemented in D3 / ported / deferred (with reason). Implement any high-value gaps.
  - **Deliverable:** Brief section in track spec or `docs/journal/` (e.g. `098-learning-systems-d2-diff.md`).

- [ ] **T010: Final regression and track completion.**
  - **Goal:** All new and existing tests for learning systems pass; track tasks closed.
  - **Strategy:** `pytest` for unit and integration tests; run any manual checks for document enhancement and OODA lessons. Update `conductor/tracks.md` and create Quartz journal entry `docs/journal/YYYY-MM-DD-098-learning-systems-d2-port.md`.
  - **Acceptance:** Track marked Done in `tracks.md`; journal summarizes what was ported, fixed, and wired.

---

## Task Summary

| ID | Phase | Description |
|----|-------|-------------|
| T001 | 1 | Remove direct Neo4j from MetaCognitiveLearner; gateway-only store |
| T002 | 1 | Persist `agency_score`; align episode schema with store |
| T003 | 1 | Episodic retrieval via Graphiti/recall webhook |
| T004 | 1 | Verify schema/index setup for episodic store |
| T005 | 2 | Wire MetaLearningEnhancer into document pipeline |
| T006 | 2 | Config toggle for meta-learning enhancement |
| T007 | 3 | Document and test in-context learning |
| T008 | 3 | Integration test for episodic meta-learning loop |
| T009 | 4 | D2 vs D3 diff; port missing pieces |
| T010 | 4 | Regression, track completion, journal |

---

## Notes

- **Zero-data migration:** Port logic and schema only; do not migrate D2 data.
- **Gateway:** All Neo4j access via Graphiti, n8n, or API. See CLAUDE.md and AGENTS.md.
- **Conductor:** Feature branch, TDD, plan task updates, phase checkpoints per `conductor/workflow.md`.
