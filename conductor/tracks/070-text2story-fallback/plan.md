# Plan: Track 070 - Text2Story Narrative Fallback (English Only)

**Status:** In Progress

## Phase 1: Preparation
- [~] **Task 1.1**: Document tech stack change for Text2Story (English-only) and fallback policy.
- [~] **Task 1.2**: Add Text2Story dependency (optional import, guarded).

## Phase 2: Tests (TDD)
- [~] **Task 2.1**: Add unit tests for narrative extraction fallback (Text2Story -> LLM).
- [ ] **Task 2.2**: Add unit test for basin ingestion enrichment (narrative relationships merged + deduped).

## Phase 3: Implementation
- [~] **Task 3.1**: Implement NarrativeExtractionService with Text2Story primary and LLM fallback.
- [ ] **Task 3.2**: Integrate narrative enrichment into MemoryBasinRouter ingestion.
