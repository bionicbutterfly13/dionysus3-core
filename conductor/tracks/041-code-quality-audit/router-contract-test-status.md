# Router Contract Test Status

## Routers with Contract Tests ✅

1. **beautiful_loop** - `test_beautiful_loop_api.py`
2. **coordination** - `test_coordination_api.py`
3. **discovery** - `test_discovery_api.py`
4. **kg_learning** - `test_kg_learning_api.py`
5. **monitoring** - `test_monitoring_api.py`
6. **mosaeic** - `test_mosaeic_api.py`
7. **network_state** - `test_network_state_api.py`
8. **rollback** - `test_rollback_api.py`
9. **skills** - `test_skills_api.py`
10. **memory** (traverse) - `test_memory_traverse.py`
11. **sync** (webhook) - `test_webhook_sync.py`

## Routers WITHOUT Contract Tests ❌

1. **agents** - Agent management endpoints
2. **avatar** - Avatar knowledge graph operations
3. **belief_journey** - Belief journey tracking (has integration test)
4. **concept_extraction** - Concept extraction endpoints
5. **consciousness** - Consciousness state endpoints
6. **documents** - Document upload/processing
7. **domain_specialization** - Domain specialization
8. **graphiti** - Graphiti KG operations
9. **heartbeat** - Heartbeat/OODA loop endpoints
10. **ias** - IAS coaching endpoints
11. **maintenance** - System maintenance
12. **memevolve** - MemEvolve webhook endpoints
13. **meta_tot** - Meta-ToT decision endpoints
14. **metacognition** - Metacognition endpoints
15. **models** - Model management
16. **monitoring_pulse** - Monitoring pulse endpoints
17. **session** - Session management
18. **trajectory** - Trajectory tracking
19. **voice** - Voice/speech endpoints

## Priority for Contract Tests

**High Priority (P0):**
- `heartbeat` - Core OODA loop, critical for system operation
- `memevolve` - External integration, needs validation
- `session` - Session continuity, user-facing
- `ias` - User-facing coaching endpoints

**Medium Priority (P1):**
- `agents` - Agent management
- `consciousness` - Consciousness state
- `documents` - Document processing
- `graphiti` - Knowledge graph operations

**Lower Priority (P2):**
- `avatar`, `belief_journey`, `concept_extraction`, `domain_specialization`
- `meta_tot`, `metacognition`, `models`, `monitoring_pulse`
- `trajectory`, `voice`
