# Plan: Track 063 - Narrative Ingestion

**Status:** In Progress

## Phase 1: Preparation (Chunking)
- [ ] **Task 1.1**: Create `scripts/split_document.py` to divide the markdown file into 4 logical chunks:
    1.  `chunk_01_intro.md` (Abstract, Intro, Active Inference)
    2.  `chunk_02_event_narrative.md` (Event narratives as active inference)
    3.  `chunk_03_identity_social.md` (Narrative Identity + Socio-cultural)
    4.  `chunk_04_conclusion.md` (Future directions, Conclusion)
- [ ] **Task 1.2**: Execute split.

## Phase 2: Execution (Granular IO)
> [!WARNING]
> **PAUSED (2026-01-18):** Ingestion halted due to local Docker vs VPS networking issues.
> Requires established SSH tunnel to `72.61.78.89:7687` with identity file `~/.ssh/mani_vps`.
> DO NOT ATTEMPT local Neo4j.

- [-] **Task 2.1**: Refactor `ingest_ultrathink.py` into `scripts/ingest_chunk.py`.
    *   *Status:* Script created but has syntax error. Needs `MemEvolveAdapter` init fix.
- [-] **Task 2.2**: Ingest Chunk 1 (Intro).
- [ ] **Task 2.3**: Ingest Chunk 2 (Event Narrative).
- [ ] **Task 2.3**: Ingest Chunk 2 (Event Narrative).
- [ ] **Task 2.4**: Ingest Chunk 3 (Identity).
- [ ] **Task 2.5**: Ingest Chunk 4 (Conclusion).

## Phase 3: Verification (The "Ultrathink" Check)
- [ ] **Task 3.1**: Run `scripts/verify_ingestion.py` to query Graphiti for key relationships defined in the paper.
    *   *Query:* `MATCH (n:Entity)-[r]->(m:Entity) WHERE n.name CONTAINS 'Narrative' RETURN r`
