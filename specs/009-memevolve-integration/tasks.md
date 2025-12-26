# Task Breakdown: MemEvolve Integration

**Feature**: [009-memevolve-integration](./spec.md)
**Plan**: [plan.md](./plan.md)

## Phase 1: Foundation (2-3 days)

- [ ] T001 [P] Create `api/models/memevolve.py` with initial Pydantic schemas for `MemoryIngestRequest`, `MemoryRecallRequest`, and `MemoryRecallResponse`.
- [ ] T002 [P] Create `api/routers/memevolve.py` with a placeholder `/health` endpoint.
- [ ] T003 [P] Create `api/services/memevolve_adapter.py` with placeholder functions for `ingest`, `recall`, and `evolve`.
- [ ] T004 [P] Create a reusable HMAC verification dependency in `api/services/hmac_utils.py`.
- [ ] T005 Apply HMAC dependency to the `/health` endpoint in `api/routers/memevolve.py`.
- [ ] T006 Register the new `memevolve_router` in `api/main.py`.
- [ ] T007 Create `n8n-workflows/memevolve-health.json` that verifies HMAC and returns a success message.
- [ ] T008 Create test script `scripts/test_memevolve_ping.py` to send a signed request to the `/health` endpoint.

## Phase 2: Retrieval (3-4 days) - User Story 1 & 2

- [ ] T009 [US1] Implement the `/recall` endpoint in `api/routers/memevolve.py`.
- [ ] T010 [US1] Implement `recall` logic in `api/services/memevolve_adapter.py` to call `VectorSearchService`.
- [ ] T011 [US2] Create `n8n-workflows/memevolve-recall.json` to handle vector search and graph traversal in Neo4j.
- [ ] T012 [US2] Create test script `scripts/test_memevolve_recall.py` to query for memories by topic.

## Phase 3: Ingestion (4-5 days) - User Story 1

- [ ] T013 [US1] Implement the `/ingest` endpoint in `api/routers/memevolve.py`.
- [ ] T014 [US1] Implement `ingest` logic in `api/services/memevolve_adapter.py` to forward trajectories to `GraphitiService`.
- [ ] T015 [US1] Modify `api/services/graphiti_service.py` to handle entity/relationship extraction from trajectory data.
- [ ] T016 [US1] Create `n8n-workflows/memevolve-ingest.json` to manage the upsert logic in Neo4j and the vector index.
- [ ] T017 [US1] Create test script `scripts/test_memevolve_ingest.py` to send a trajectory and verify its persistence.

## Phase 4: Consciousness & Meta-Evolution (Future) - User Story 3 & 4

- [ ] T018 [US3] Modify `api/services/heartbeat_service.py` to consume MemEvolve trajectories in its OBSERVE phase.
- [ ] T019 [US3] Implement pattern detection logic within the Heartbeat to identify recurring failures (e.g., date parsing).
- [ ] T020 [US3] Implement strategic memory generation within the Heartbeat's ACT phase.
- [ ] T021 [US4] Implement the `/evolve` endpoint in `api/routers/memevolve.py` to accept new retrieval strategies from AutoEvolver.
- [ ] T022 [US4] Create `n8n-workflows/memevolve-evolve.json` to apply and validate new retrieval strategies.

## Dependencies

- **Phase 2** depends on **Phase 1**.
- **Phase 3** depends on **Phase 1**.
- **Phase 4** depends on **Phase 2** and **Phase 3**.

## Parallel Execution Strategy

- The **Supabase to Neo4j Migration** can proceed in parallel.
- Within this feature, a separate developer can begin work on the `n8n` workflows (T007, T011, T016) as soon as the API contracts are defined in `api/models/memevolve.py` (T001).
- Test script creation (T008, T012, T017) can be done in parallel with endpoint implementation.
