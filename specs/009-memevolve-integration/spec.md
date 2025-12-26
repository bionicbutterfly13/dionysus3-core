# Feature Specification: MemEvolve-Dionysus Integration

**Feature Branch**: `009-memevolve-integration`  
**Created**: 2025-12-26  
**Status**: Draft  
**Input**: Connect MemEvolve (Flash-Searcher main codebase) to Dionysus3-core via n8n webhooks with HMAC. Persist agent memories (vector + graph) in PostgreSQL/pgvector and Neo4j/Graphiti with temporal validity. Enable entity/relationship extraction from trajectories, cross-agent knowledge reuse, and consciousness-level reflection. Allow MemEvolve’s AutoEvolver to optimize Dionysus retrieval strategies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persist Agent Memories (Priority: P1)

MemEvolve agents need to reliably persist their memories (both vector embeddings and graph structures) in Dionysus, ensuring these memories have temporal validity.

**Why this priority**: This is fundamental. Without memory persistence, agents cannot learn, share knowledge, or reflect across sessions. Temporal validity ensures freshness and accuracy.

**Independent Test**: An agent generates a memory, sends it to Dionysus, then later queries for it. The memory should be retrieved with its correct content and validity period.

**Acceptance Scenarios**:

1.  **Given** a MemEvolve agent generates a new memory (e.g., a strategic insight or an episodic experience), **When** it sends this memory to Dionysus for ingestion, **Then** the memory is stored in both the vector store (for semantic search) and the graph database (for contextual relationships) with a `valid_at` timestamp.
2.  **Given** an agent stores a memory related to a fact (e.g., "OAuth 1.0a is current"), **When** a new fact invalidating it is stored (e.g., "OAuth 2.0 is current"), **Then** the old fact's memory entry in the graph database is marked with an `invalid_at` timestamp.

---

### User Story 2 - Cross-Agent Knowledge Reuse (Priority: P1)

Agents should be able to query Dionysus for relevant knowledge, allowing for shared learning and preventing redundant discovery.

**Why this priority**: Enables the core benefit of a centralized memory system: agents become smarter collectively and over time. Directly supports complex multi-agent systems.

**Independent Test**: One agent ingests knowledge about a topic; a different agent queries for that topic and successfully retrieves the knowledge.

**Acceptance Scenarios**:

1.  **Given** a GAIA agent ingests knowledge about "arXiv citation format", **When** a WebWalkerQA agent later searches for "citation formats", **Then** the GAIA agent's knowledge about "arXiv citation format" is returned.
2.  **Given** the Dionysus Heartbeat system identifies a recurring pattern (e.g., "clarify timezone" due to date parsing failures), **When** any agent queries for common system issues or best practices, **Then** this strategic memory is available.

---

### User Story 3 - Consciousness-Level Reflection (Priority: P2)

Dionysus's Heartbeat system should be able to integrate MemEvolve trajectories to generate higher-order strategic memories and update mental models based on observed patterns.

**Why this priority**: This leverages the full cognitive architecture of Dionysus, moving beyond simple storage and retrieval to true meta-cognition and self-improvement.

**Independent Test**: The Heartbeat system observes a series of agent failures on a specific task type, and as a result, generates a strategic memory and proposes a mental model revision.

**Acceptance Scenarios**:

1.  **Given** the Heartbeat system receives data indicating 9 out of 47 runs failed on "date parsing" for a specific agent, **When** the Heartbeat system processes this trajectory, **Then** it generates a strategic memory (e.g., "clarify timezone" as a common failure pattern) and stores it in the graph.
2.  **Given** the Heartbeat system detects 200 runs revealing "unit-conversion failures", **When** it analyzes these patterns, **Then** it proposes the creation of a new mental model (e.g., "UnitTrackingPattern") with associated confidence tracking.

---

### User Story 4 - Meta-Evolution of Retrieval Strategies (Priority: P2)

MemEvolve's AutoEvolver should be able to optimize Dionysus's memory retrieval strategies, providing continuous improvement in how agents access information.

**Why this priority**: This is a direct feedback loop for self-improving memory management, leading to more efficient and accurate agent operations over time.

**Independent Test**: The AutoEvolver runs an optimization round, and Dionysus updates its retrieval strategy parameters, leading to measurable improvements in retrieval accuracy in subsequent queries.

**Acceptance Scenarios**:

1.  **Given** MemEvolve's AutoEvolver identifies an optimized retrieval strategy (e.g., a new weighting of BM25 + semantic reranking), **When** it reports this optimization to Dionysus, **Then** Dionysus updates its internal retrieval strategy configuration.
2.  **Given** Dionysus updates its retrieval strategy, **When** subsequent queries are made, **Then** the retrieval accuracy (e.g., precision@k or recall@k) improves from a baseline (e.g., 72% to 84%).

---

### Edge Cases

-   What happens when a trajectory payload exceeds the maximum size limit for ingestion?
-   How does Dionysus handle conflicting memory updates (e.g., two agents try to update the same fact simultaneously)?
-   What if the HMAC signature is invalid on an incoming request from MemEvolve?
-   How does Dionysus ensure PII is redacted from memories before storage, especially in ingest pipelines?

## Requirements *(mandatory)*

### Functional Requirements

-   **FR-001**: Dionysus MUST expose secure n8n webhook endpoints for memory ingestion, recall, and evolution results.
-   **FR-002**: Dionysus MUST persist agent memories in Neo4j/Graphiti (graph structure) with temporal validity.
-   **FR-003**: Dionysus MUST persist agent memories in a vector store (e.g., pgvector, Graphiti's vector index) for semantic search.
-   **FR-004**: Dionysus MUST support entity and relationship extraction from incoming trajectory data.
-   **FR-005**: Dionysus MUST enable cross-agent knowledge reuse through semantic and contextual memory recall.
-   **FR-006**: Dionysus Heartbeat MUST consume MemEvolve trajectories for pattern detection and strategic memory generation.
-   **FR-007**: Dionysus MUST allow updates to its retrieval strategies based on AutoEvolver's optimization results.
-   **FR-008**: Dionysus MUST enforce HMAC-SHA256 authentication for all incoming MemEvolve webhook requests.
-   **FR-009**: Dionysus MUST support sanitization of PII from incoming data payloads before persistence.
-   **FR-010**: Dionysus MUST ensure memory queries respect temporal validity (e.g., retrieve only currently valid facts).
-   **FR-011**: Dionysus MUST register new API router `/webhook/memevolve/v1` in `api/main.py`.

### Key Entities

-   **Memory**: Represents an agent's knowledge or experience (episodic, semantic, procedural, strategic). Stored as a graph node. Key attributes: `id`, `content`, `type`, `importance`, `embedding`, `valid_at`, `invalid_at`, `source_project`, `trace_id`.
-   **Trajectory**: A sequence of actions, observations, and thoughts from a MemEvolve agent. Used to derive memories and patterns.
-   **Entity**: Named entity extracted from a trajectory (e.g., "Elon Musk", "Tesla"). Stored as a graph node.
-   **Relationship**: Connection between entities or memories (e.g., `CEO_OF`, `PART_OF`). Stored as a graph edge with properties.
-   **Retrieval Strategy**: Configuration parameters that define how Dionysus searches and ranks memories. Can be updated by AutoEvolver.

## Success Criteria *(mandatory)*

### Measurable Outcomes

-   **SC-001**: Retrieval accuracy (e.g., precision@k, recall@k) improves by >= 5% per AutoEvolver optimization round.
-   **SC-002**: 95% of memory ingestion requests from MemEvolve are processed in under 500ms (p95 latency).
-   **SC-003**: Cross-agent knowledge reuse results in a 60%+ reduction in redundant information discovery across 10-agent simulations.
-   **SC-004**: 80%+ of identified entities and relationships from MemEvolve trajectories are correctly extracted and stored in the graph.
-   **SC-005**: HMAC authentication effectively blocks 100% of unauthorized requests while allowing 100% of authorized requests.
-   **SC-006**: Session continuity enables full context resumption on a different device in under 2 seconds.
-   **SC-007**: Strategic memories are generated by Heartbeat within 1 hour of detecting 5+ related agent failures.