# Plan: 100 – Identity-Aware Memory Seeding

## Phase 1: Identity Layer (Foundation)
- [x] **T100-001: Update `SessionManager` for `participant_id` linkage.**
- [x] **T100-002: Update `Journey` models to include `participant_id`.**
- [x] **T100-003: Update `ConsolidatedMemoryStore` to filter `get_active_journey` by identity.**

## Phase 2: Agent Hydration
- [x] **T100-004: Update `ConsciousnessManager._fetch_biographical_context` to use `device_id`.**
- [ ] **T100-005: Integrate `device_id` into `BiologicalAgencyService` Presence logic.**

## Phase 3: Identity-Aware Retrieval
- [x] **T100-006: Update `recall.py` (MCP Tool) to handle `device_id` filtering.**
- [x] **T100-007: Propagate `device_id` through `VectorSearchService` and `MemEvolveAdapter`.**

## Phase 4: Recognition & Continuity
- [ ] **T100-008: Add "Recognition" acknowledgement to the initial response.**
- [ ] **T100-009: Verification Script: Cross-session continuity test.**

## Phase 5: Documentation & Merging
- [ ] **T100-010: Update Quartz Journal.**
- [ ] **T100-011: Merge to main and delete feature branch.**
