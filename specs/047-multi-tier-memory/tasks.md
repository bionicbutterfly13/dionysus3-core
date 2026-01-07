# Tasks: Multi-Tier Memory Lifecycle (Feature 047)

- [x] T001: Define `MemoryTier` enum and `TieredMemoryItem` model
- [x] T002: Implement `HotMemoryManager` (In-memory/Redis wrapper)
- [x] T003: Implement `WarmMemoryManager` (Neo4j bridge)
- [x] T004: Implement `ColdMemoryManager` (Compressed storage)
- [x] T005: Implement `MultiTierMemoryService` orchestrator
- [x] T006: Implement `migrate_hot_to_warm` logic based on TTL (24h)
- [x] T007: Implement `migrate_warm_to_cold` logic based on importance/age
- [ ] T008: Refactor `MemoryService` to support tiered storage
- [x] T009: Integration Test: Store in HOT, verify retrieval speed, simulate migration to WARM
- [ ] T010: Integrate tiered storage into `ConsciousnessIntegrationPipeline.process_cognitive_event`