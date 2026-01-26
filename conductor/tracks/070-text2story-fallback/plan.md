# Plan: Track 070 - Text2Story Narrative Fallback (English Only)

**Status:** Done

## Integration (IO Map)

**Attachment Points:**
- `api/services/narrative_extraction_service.py` - New service
- `api/services/memory_basin_router.py:380` - Integration via `_get_narrative_service()`

**Inlets:**
- Raw text content from `MemoryBasinRouter.route_memory()` ingestion flow
- Content string passed to `NarrativeExtractionService.extract_relationships()`

**Outlets:**
- Returns `list[dict]` of relationship dicts with keys: `source`, `target`, `relation_type`, `confidence`, `status`, `evidence`
- Relationships merged into MemEvolve ingestion via `MemoryBasinRouter` (deduped with existing relationships)
- Flow: Content → NarrativeExtractionService → relationships → MemEvolveAdapter → GraphitiService → Neo4j

**Fallback Chain:**
1. Text2Story (English-only, optional dependency)
2. LLM NarrativeStructureExtractor (if Text2Story unavailable or fails)

---

## Phase 1: Preparation
- [x] **Task 1.1**: Document tech stack change for Text2Story (English-only) and fallback policy. (f835d3e)
- [x] **Task 1.2**: Add Text2Story dependency (optional import, guarded). (f835d3e)

## Phase 2: Tests (TDD)
- [x] **Task 2.1**: Add unit tests for narrative extraction fallback (Text2Story -> LLM). (f835d3e)
- [x] **Task 2.2**: Add unit test for basin ingestion enrichment (narrative relationships merged + deduped). (f835d3e)

## Phase 3: Implementation
- [x] **Task 3.1**: Implement NarrativeExtractionService with Text2Story primary and LLM fallback. (f835d3e)
- [x] **Task 3.2**: Integrate narrative enrichment into MemoryBasinRouter ingestion. (f835d3e)
