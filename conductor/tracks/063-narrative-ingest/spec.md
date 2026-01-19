# Specification: Track 063 - Narrative as Active Inference Ingestion

**Goal:** Ingest the seminal paper "Narrative as Active Inference" by Bouizegarene et al. into the Dionysus Graphiti memory store.

**Context:** The user requires this document to "make it all the way to neo4j including capturing relevant relations and system dynamics". To ensure reliability and observability, we are breaking this into granular subtasks using the Conductor Protocol.

**Requirements:**
1.  **Chunking:** The document (~18k chars) must be split into logical sections to avoid context window overflows and allow for precise error handling.
2.  **Ingestion:** Each chunk must be processed by `KGLearningService` with `MemoryType.SEMANTIC`.
3.  **Verification:** We must verify that:
    *   Entities (e.g., "Active Inference", "Master Narrative") are created.
    *   Relations (e.g., "Narrative -> minimizes -> Prediction Error") are captured.
    *   The "Cognitive River" flow (Basin -> Extraction -> Graphiti) is respected.

**Architecture:**
*   **Source:** `scripts/narrative_active_inference_paper.md`
*   **Splitter:** New script `scripts/split_document.py`
*   **Ingester:** Refactored `scripts/ingest_chunk.py` (accepts chunk path)
*   **Verifier:** `scripts/verify_ingestion.py`
