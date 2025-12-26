# Tasks: Core Services Neo4j Migration

**Input**: Design documents from `/specs/011-core-services-migration/`
**Prerequisites**: spec.md (required)

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Audit `api/services/` for any remaining `db_pool` usages
- [ ] T002 Ensure `WebhookNeo4jDriver` supports parallel transactional execution if needed

---

## Phase 2: User Story 1 - Neo4j-Native Mental Models (Priority: P1) 🎯 MVP

**Goal**: Models and Predictions in Neo4j.

- [ ] T003 Refactor `api/services/model_service.py` to use Cypher for model creation and listing
- [ ] T004 Implement `_node_to_model` converter for Neo4j responses
- [ ] T005 Refactor `generate_prediction` to store `ModelPrediction` nodes

---

## Phase 3: User Story 2 - Precision-Weighted Belief Updates (Priority: P2)

- [ ] T006 Update `WorldviewIntegrationService` to use Cypher for belief retrieval
- [ ] T007 Implement the variance-tracking Cypher query in `record_prediction_error`
- [ ] T008 Port `resolve_prediction_with_propagation` to Neo4j

---

## Phase 4: User Story 3 - Relational ThoughtSeeds (Priority: P3)

- [ ] T009 Refactor `ThoughtSeedIntegrationService` to store seeds as nodes
- [ ] T010 Implement winning thoughtseed activation logic via graph traversal

---

## Phase 5: Cleanup

- [ ] T011 Delete `migrations/008_create_mental_models.sql` (PostgreSQL)
- [ ] T012 Remove `asyncpg` from `requirements.txt` and `pyproject.toml`