# Track Plan: Jungian Cognitive Archetypes

**Track ID**: 002-jungian-archetypes
**Status**: Planned

## Phase 1: Data Model Refactor
- [ ] **Task 1.1**: Update `api/models/autobiographical.py`
    -   Replace `DevelopmentArchetype` legacy values with standard Jungian set (CREATOR, RULER, SAGE, etc.).
    -   Ensure backward compatibility (or migration strategy) if we had existing data (we don't).

## Phase 2: Cognitive Mapping (Active Inference)
- [ ] **Task 2.1**: Update `api/services/consciousness/active_inference_analyzer.py`
    -   Implement `_classify_jungian_archetype` method.
    -   Map specific tools/actions to Archetypes (e.g., `write_to_file` -> CREATOR, `grep_search` -> EXPLORER/SAGE).

## Phase 3: Service & Tool Alignment
- [ ] **Task 3.1**: Update `api/services/autobiographical_service.py`
    -   Ensure heuristic logic in `analyze_and_record_event` uses the new analyzer method.
- [ ] **Task 3.2**: Update `api/agents/tools/autobiographical_tools.py`
    -   Update `RecordSelfMemoryTool` inputs to accept Jungian types (or auto-detect them).

## Phase 4: Integration Verification
- [ ] **Task 4.1**: Update `scripts/test_autobiographical_memory.py`
    -   Test that a "write code" action results in `THE_CREATOR` archetype.
    -   Test that a "search web" action results in `THE_EXPLORER` archetype.
