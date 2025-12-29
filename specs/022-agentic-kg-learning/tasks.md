# Tasks: Agentic Knowledge Graph Learning Loop

**Input**: spec.md
**Status**: In-Progress

## Phase 1: Foundation Enhancement (P1)

- [x] T001 Implement dynamic relationship extraction in `KGLearningService.extract_and_learn` (FR-001)

- [x] T002 Implement attractor basin context injection (FR-002)

- [x] T003 Enhance `RelationshipProposal` model with provenance fields (run_id, model_id, confidence) (FR-004)

- [x] T004 Implement low-confidence threshold gating for human review (FR-004)



## Phase 2: Interfaces & Tools (P1)

- [x] T005 Create `agentic_kg_extract` smolagent tool in `api/agents/tools/kg_learning_tools.py`

- [x] T006 Expose `POST /api/v1/kg/learn` endpoint in `api/routers/kg_learning.py`

- [x] T007 Implement `GET /api/v1/kg/review-queue` for low-confidence extractions



## Phase 3: Evaluation & Learning (P2)
- [x] T008 Implement strategy boosting in `KGLearningService._record_learning` (FR-003)
- [x] T009 Implement `ExtractionEvaluator` smolagent tool to calculate precision/recall proxies (FR-005)
- [x] T010 Implement `AutomaticFeedbackLoop`: Evaluator triggers strategy boosts for high-precision runs
- [x] T014 Add `learning_metrics` nodes to Neo4j to track system evolution over time
- [x] T015 Implement token-count context budgeting in `BootstrapRecallService` (Priority 1.2)




## Phase 4: Testing & Verification (P1)

- [x] T011 Unit test for dynamic relation extraction with provenance

- [x] T012 Integration test for basin-guided improvement over 3+ runs (SC-002)

- [x] T013 Contract test for review queue API
