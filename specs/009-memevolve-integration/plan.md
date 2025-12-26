# Implementation Plan: MemEvolve Integration

**Status**: In Progress
**Project**: MemEvolve-Dionysus Integration
**Associated Spec**: [spec.md](./spec.md)

## Technical Context & Stack

-   **Backend Framework**: FastAPI (Python)
-   **Database**: Neo4j (via Graphiti) for graph storage and n8n for webhook-based access.
-   **Vector Storage**: Neo4j's native vector index.
-   **Authentication**: HMAC-SHA256 for webhook security.
-   **Orchestration**: n8n for workflow automation.
-   **Key Dionysus Services to Integrate With**:
    -   `remote_sync.py`: For HMAC verification and webhook patterns.
    -   `graphiti_service.py`: For entity/relationship extraction and storage.
    -   `heartbeat_service.py`: To consume MemEvolve trajectories.

## Constitution Check

-   **Principle of Secure Interfaces**: The plan adheres to this by using HMAC-signed webhooks and not exposing the database directly.
-   **Principle of Independent Components**: The integration is designed as a new, separate module (`memevolve_adapter`, new router, new n8n workflows) to minimize impact on existing core services.
-   **Principle of Testability**: Each phase is designed to be independently testable, from the foundational HMAC ping to the full meta-evolution loop.

## Implementation Phases

### Phase 1: Foundation (2-3 days)

**Goal**: Establish a secure, end-to-end "ping" from MemEvolve to Dionysus.

1.  **Dionysus: Create Scaffolding**
    -   Create `api/routers/memevolve.py` with a basic `/health` endpoint.
    -   Create `api/models/memevolve.py` with initial Pydantic schemas.
    -   Create `api/services/memevolve_adapter.py` with placeholder functions.
    -   Register the new router in `api/main.py`.
2.  **Dionysus: Implement HMAC Verification**
    -   In `remote_sync.py` or a new utility file, create a reusable FastAPI dependency for HMAC signature verification.
    -   Apply this dependency to the `/health` endpoint in the new router.
3.  **n8n: Create Health Check Workflow**
    -   Create `n8n-workflows/memevolve-health.json`.
    -   This workflow listens on a webhook, verifies HMAC, and returns a success message.
4.  **MemEvolve Side (Simulated)**:
    -   A test script will be created (`scripts/test_memevolve_ping.py`) that acts as the MemEvolve client, sending a signed request to the new health endpoint.

**Exit Criteria**: The test script successfully pings the new Dionysus endpoint, passing HMAC authentication.

### Phase 2: Retrieval (3-4 days)

**Goal**: Enable MemEvolve agents to retrieve memories from Dionysus.

1.  **Dionysus: Implement Recall Endpoint**
    -   Add a `/recall` endpoint to `api/routers/memevolve.py`.
    -   The endpoint uses the `memevolve_adapter` to call existing services.
2.  **Dionysus: Implement Recall Logic**
    -   In `memevolve_adapter.py`, the `recall` function will call `VectorSearchService` and potentially the `GraphitiService` to get memories.
    -   It will respect temporal validity (`valid_at`, `invalid_at`).
3.  **n8n: Create Recall Workflow**
    -   Create `n8n-workflows/memevolve-recall.json`.
    -   This workflow verifies HMAC, then calls the underlying Neo4j instance using vector search and graph traversal queries.

**Exit Criteria**: A test script can request memories for a given topic and receive a structured, time-valid response.

### Phase 3: Ingestion (4-5 days)

**Goal**: Enable MemEvolve agents to persist memories and trajectories in Dionysus.

1.  **Dionysus: Implement Ingest Endpoint**
    -   Add an `/ingest` endpoint to `api/routers/memevolve.py`.
2.  **Dionysus: Implement Ingestion & Extraction Logic**
    -   The `memevolve_adapter`'s `ingest` function will receive the trajectory.
    -   It will call `GraphitiService` to perform entity/relationship extraction.
3.  **n8n: Create Ingest Workflow**
    -   Create `n8n-workflows/memevolve-ingest.json`.
    -   This workflow handles the complex logic of upserting nodes and relationships in Graphiti/Neo4j and adding embeddings to the vector index.

**Exit Criteria**: A test script can send a trajectory to the `/ingest` endpoint, and the corresponding entities and memories appear correctly in Neo4j.

### Phase 4 & 5 (Consciousness & Meta-Evolution): Future Work

These phases will be detailed in a subsequent plan after the core retrieval/ingestion loop is complete. They involve deeper integration with the `HeartbeatService` and `smolagents`.

## Data Model

*Initial data models will be created in `api/models/memevolve.py` based on the spec.*

-   **MemoryIngestRequest**: Contains trajectory data, agent ID, session ID.
-   **MemoryRecallRequest**: Contains query, filters (by type, time), context.
-   **MemoryRecallResponse**: Contains a list of memory objects.

## API Contracts (Initial)

*An OpenAPI specification will be generated in `specs/009-memevolve-integration/contracts/`.*

-   `POST /webhook/memevolve/v1/ingest`: Accepts `MemoryIngestRequest`.
-   `POST /webhook/memevolve/v1/recall`: Accepts `MemoryRecallRequest`, returns `MemoryRecallResponse`.
-   `POST /webhook/memevolve/v1/evolve`: (Phase 5) Accepts new retrieval strategies.
-   `GET /webhook/memevolve/v1/health`: Basic health check.