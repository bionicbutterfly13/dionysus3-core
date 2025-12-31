# Feature Spec: Multi-Tier Memory Lifecycle (Feature 047)

**Created**: 2025-12-31
**Status**: Draft
**Branch**: 047-multi-tier-memory

## 1. Overview
Implement a three-tier memory architecture to handle multi-year cognitive persistence without performance degradation. This prevents "Neo4j bloat" by migrating older or less relevant facts to cheaper/slower storage while keeping active session context in high-speed cache.

Ported and enhanced from Dionysus 2.0 (`backend/src/services/multi_tier_memory.py`).

## 2. Goals
- **Hot Memory (Tier 1)**: Sub-millisecond retrieval using Redis (or high-speed in-memory cache) for the current session and the last 24 hours of activity.
- **Warm Memory (Tier 2)**: Semantic knowledge graph in Neo4j for relationships, facts, and entities relevant to the current projects (months/years).
- **Cold Memory (Tier 3)**: Compressed vector storage or file-based archives for historical data (years/decades).
- **Automated Migration**: Background process to move items: Hot -> Warm (after 24h) -> Cold (after 30 days or low importance).
- **Importance-Based Pruning**: Use `importance_score` to decide retention priority.

## 3. Implementation Details

### 3.1 Data Models (`api/models/memory_tier.py`)
- `MemoryItem`: Extends base memory with `tier` (HOT, WARM, COLD), `last_accessed`, and `importance_score`.
- `MigrationReport`: Details of items moved between tiers.

### 3.2 Service Layer (`api/services/multi_tier_service.py`)
Implement `MultiTierMemoryManager`:
- **`store(item)`**: Intelligently routes to the correct tier.
- **`retrieve(query)`**: Searches Tiers in order: Hot -> Warm -> Cold.
- **`migrate_tiers()`**: Scans for items exceeding age/importance thresholds and moves them.
- **`compress_cold_memory()`**: Aggregates old Cold memories into high-level summaries.

### 3.3 Integration
- Update `MemoryService` to use the multi-tier manager as its backend.
- Hook into OODA loop via the `ConsciousnessIntegrationPipeline` to tag memory tiers.

## 4. Dependencies
- `redis` (optional fallback to in-memory if Redis not available).
- `api.services.remote_sync` (Neo4j/n8n).
- `api.services.graphiti_service`.

## 5. Testing Strategy
- **Unit Tests**: Verify that an item stored in Hot is moved to Warm after a simulated 24h period.
- **Performance Benchmarks**: Compare retrieval speed from Hot vs. Warm.

## 6. Success Criteria
- Items successfully transition between tiers based on age.
- Retrieval latency for "Hot" items is significantly lower than Neo4j queries.
- Total Neo4j node count remains stable despite high ingestion volume.