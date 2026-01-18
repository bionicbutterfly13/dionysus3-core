# Feature 062: Implementation Plan

## Phase 1: Marker Integration + REST Upload (P0)

### T062-001: Install and configure Marker
- [x] Add `marker-pdf` to requirements.txt
- [x] Verify GPU/CPU mode configuration (CPU mode, isolated in marker-env)
- [~] Test Marker on sample PDFs (simple, complex, scanned) - Marker installing
- [x] Document system requirements (RAM, GPU optional) - subprocess isolation

### T062-002: Create MarkerExtractionService
- [x] Create `api/services/marker_extraction.py`
- [x] Implement `extract_pdf()` - Marker extraction via subprocess to marker-env
- [x] Implement `extract_with_fallback()` - Marker → PyMuPDF → Tesseract chain
- [x] Add structured output model: `MarkerResult`
- [x] Handle: tables, equations, figures, multi-column
- [ ] Unit tests: `tests/unit/test_marker_extraction.py`

### T062-003: Create document upload router
- [x] Create `api/routers/documents.py`
- [x] `POST /api/documents/upload` - multipart file upload
- [x] `GET /api/documents/{doc_id}/status` - status check
- [x] `GET /api/documents/{doc_id}/results` - extraction results
- [x] `GET /api/documents` - list all documents
- [x] `DELETE /api/documents/{doc_id}` - remove document
- [x] Register router in `api/main.py`

### T062-004: Create document registry (SQLite)
- [x] Create `api/services/document_lifecycle.py`
- [x] Define `Document` model with status tracking
- [x] SQLite database: `data/documents.db`
- [x] CRUD operations: create, read, update, delete
- [x] Status enum: `uploaded`, `processing`, `completed`, `failed`
- [x] Timestamp tracking: upload, start, complete

### T062-005: Basic async processing
- [x] Upload returns immediately with doc_id
- [x] Background task starts processing
- [x] Status endpoint reflects current state
- [x] Store extraction results to filesystem
- [x] Update document record on completion/failure
- [x] Retry logic (3 attempts, exponential backoff)

### T062-006: CLI script for Marker extraction
- [ ] Create `scripts/extract_with_marker.py`
- [ ] Accept: PDF path, output path, options
- [ ] Support: single file, directory batch
- [ ] Output: markdown + metadata JSON
- [ ] Progress reporting for large files

---

## Phase 2: Recursive Processing Pipeline (P1)

### T062-007: Integrate Nemori boundary detection
- [ ] Import `NemoriRiverFlow` into recursive processor
- [ ] Adapt `check_boundary()` for document sections (not conversation)
- [ ] Define boundary heuristics: headings, topic shifts, page breaks
- [ ] Test on academic papers (section detection)

### T062-008: Create recursive document processor
- [ ] Create `api/services/recursive_processor.py`
- [ ] Implement hierarchical decomposition:
  ```
  Document → Chapters → Sections → Paragraphs
  ```
- [ ] Entity extraction at each level with context
- [ ] Preserve parent context during child processing
- [ ] Aggregate entities bottom-up

### T062-009: Hierarchical summarization
- [ ] Generate summaries per section
- [ ] Roll up to chapter summaries
- [ ] Create document-level summary
- [ ] Store summaries as Graphiti nodes
- [ ] Link summaries to source sections

### T062-010: Connect to MemEvolve trajectory
- [ ] Create trajectory for document ingestion
- [ ] Track: extraction steps, entities found, relationships
- [ ] Call `memevolve.ingest_trajectory()` on completion
- [ ] Enable meta-evolution learning from ingestion patterns

### T062-011: Graphiti storage integration
- [ ] Route extracted entities to `graphiti.ingest_message()`
- [ ] Set `group_id` = document identifier
- [ ] Set `valid_at` = document publication date (if available)
- [ ] Create document node linking all sections
- [ ] Test bi-temporal storage

---

## Phase 3: Async Queue + Lifecycle (P1)

### T062-012: Implement task queue
- [ ] Create `api/services/task_queue.py`
- [ ] asyncio.Queue for in-memory queue (MVP)
- [ ] Optional: Redis backend for persistence
- [ ] Priority support: urgent, normal, batch
- [ ] Queue status endpoint: pending, processing, completed

### T062-013: Worker pool management
- [ ] Configurable worker count (default: 4)
- [ ] Worker lifecycle: start, process, shutdown
- [ ] Graceful shutdown on SIGTERM
- [ ] Health monitoring per worker

### T062-014: Error recovery and retry
- [ ] Max retry count: 3 (configurable)
- [ ] Exponential backoff: 1s, 4s, 16s
- [ ] Dead letter queue for permanent failures
- [ ] Error categorization: transient vs permanent
- [ ] Partial completion: track chunks processed

### T062-015: WebSocket progress updates
- [ ] Create WebSocket endpoint: `/ws/documents/{doc_id}`
- [ ] Emit events: started, progress, completed, failed
- [ ] Progress payload: `{chunks_done, chunks_total, current_section}`
- [ ] Client example in documentation

### T062-016: Cancellation support
- [ ] API endpoint: `POST /api/documents/{doc_id}/cancel`
- [ ] Graceful worker interruption
- [ ] Cleanup partial results
- [ ] Update status to `cancelled`

---

## Phase 4: Trajectory Visualizer (P1) ✅

### T062-017: Create trajectory capture callback
- [x] Reused existing `api/agents/callbacks/execution_trace_callback.py`
- [x] ExecutionTraceCollector implements smolagents callback interface
- [x] Captures: tool calls, planning steps, basin activations
- [x] Stores structured trace per session via ExecutionTraceService

### T062-018: Define trace storage format
- [x] Created `api/services/trajectory_viz.py` with models
- [x] Models: `TrajectoryTrace`, `OODAPhase`, `AgentCall`, `BasinTransition`
- [x] JSON serialization via `generate_json()`
- [x] Uses existing Neo4j storage via ExecutionTraceService

### T062-019: Create trajectory visualization service
- [x] Created `api/services/trajectory_viz.py`
- [x] `generate_mermaid()` - Mermaid sequence diagram
- [x] `generate_json()` - Raw trace export
- [x] `generate_html()` - Standalone HTML viewer with tabs

### T062-020: Mermaid diagram generator
- [x] OODA cycle visualization (Observe → Orient → Decide → Act)
- [x] Agent hierarchy (HeartbeatAgent → ConsciousnessManager → sub-agents)
- [x] Tool call annotations with truncated args
- [x] Basin transition markers with strength
- [ ] Thoughtseed activation indicators (future enhancement)

### T062-021: REST endpoint for trajectories
- [x] Created `api/routers/trajectory.py`
- [x] `GET /api/trajectory/{trace_id}` - get trace metadata
- [x] `GET /api/trajectory/{trace_id}/mermaid` - Mermaid output
- [x] `GET /api/trajectory/{trace_id}/html` - HTML viewer
- [x] `GET /api/trajectory` - list recent traces
- [x] `GET /api/trajectory/demo/sample` - demo visualization
- [ ] Query params: time_range, agent_type, basin_filter (future)

### T062-022: HTML dashboard component
- [ ] Create `dionysus-dashboard/pages/trajectory.tsx`
- [ ] Real-time trace updates via WebSocket
- [ ] Interactive timeline view
- [ ] Filter controls: agent, basin, time
- [ ] Mermaid rendering (mermaid.js)
- [ ] Export buttons: PNG, SVG, JSON

### T062-023: Integration with HeartbeatAgent
- [ ] Register trajectory callback on agent init
- [ ] Capture OODA phase transitions
- [ ] Log planning_interval replans
- [ ] Test with sample cognitive tasks

---

## Phase 5: Polish + Configuration (P2)

### T062-024: Content deduplication
- [ ] SHA256 hash on document upload
- [ ] Check hash against existing documents
- [ ] Options: skip, update existing, create version
- [ ] Chunk-level deduplication across documents
- [ ] Deduplication report in status endpoint

### T062-025: Configuration system
- [ ] Create `config/ingestion.yaml`
- [ ] Load config on startup
- [ ] Environment variable overrides
- [ ] Runtime config via `PATCH /api/config/ingestion`
- [ ] Validation with Pydantic settings

### T062-026: Documentation
- [ ] Update `docs/pdf-ingestion-pipeline.md`
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Configuration reference
- [ ] Trajectory visualizer user guide
- [ ] Example scripts + notebooks

### T062-027: Integration tests
- [ ] End-to-end: upload → process → Graphiti storage
- [ ] Recursive processing on long document (100+ pages)
- [ ] Error recovery: simulate failures
- [ ] Trajectory capture on agent execution
- [ ] WebSocket progress updates

### T062-028: Performance optimization
- [ ] Profile Marker extraction (GPU vs CPU)
- [ ] Optimize chunk batch size
- [ ] Connection pooling for Graphiti
- [ ] Memory usage for large documents
- [ ] Benchmark: pages/second throughput

---

## Dependencies

```
T062-001 → T062-002 (Marker installed before service)
T062-003 → T062-004 (Router needs registry)
T062-004 → T062-005 (Registry before async processing)
T062-007 → T062-008 (Nemori before recursive processor)
T062-008 → T062-009 → T062-010 → T062-011 (Sequential pipeline)
T062-012 → T062-013 → T062-014 (Queue before workers before retry)
T062-017 → T062-018 → T062-019 (Capture before storage before viz)
T062-019 → T062-020 → T062-021 (Service before generator before endpoint)
T062-021 → T062-022 (API before dashboard)
```

---

## Acceptance Criteria

1. **P0 Complete:**
   - PDF uploaded via REST API
   - Marker extraction produces structured markdown
   - Document status trackable via API

2. **P1 Complete:**
   - Long documents (100+ pages) processed with recursive chunking
   - Nemori boundary detection segments documents semantically
   - Trajectory visualizer shows OODA cycles
   - Failed documents retry automatically

3. **P2 Complete:**
   - Duplicate documents detected
   - Configuration via YAML + env vars
   - Test coverage >80%

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Marker GPU requirements | CPU fallback mode, PyMuPDF fallback chain |
| Long document memory | Streaming processing, chunk-at-a-time |
| Queue persistence | Redis backend option, checkpoint on disk |
| Trajectory storage growth | Retention policy, compression, archival |
