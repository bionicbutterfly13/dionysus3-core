# Router Contract Test Status

## Routers with Contract Tests ✅

1. **beautiful_loop** - `test_beautiful_loop_api.py`
2. **coordination** - `test_coordination_api.py`
3. **discovery** - `test_discovery_api.py`
4. **heartbeat** - `test_heartbeat_api.py`
5. **hexis** - `test_hexis_api.py`
6. **kg_learning** - `test_kg_learning_api.py`
7. **monitoring** - `test_monitoring_api.py`
8. **monitoring_pulse** - `test_monitoring_pulse_api.py`
9. **mosaeic** - `test_mosaeic_api.py`
10. **network_state** - `test_network_state_api.py` (minimal app + overrides)
11. **rollback** - `test_rollback_api.py`
12. **session** - `test_session_api.py`
13. **skills** - `test_skills_api.py`
14. **memory** (traverse) - `test_memory_traverse.py`
15. **sync** (webhook) - `test_webhook_sync.py`
16. **trajectory** - `test_trajectory_api.py`

## Routers WITHOUT Contract Tests ❌

1. **agents** - Agent management endpoints
2. **avatar** - Avatar knowledge graph operations
3. **belief_journey** - Belief journey tracking (has integration test)
4. **concept_extraction** - Concept extraction endpoints
5. **consciousness** - Consciousness state endpoints
6. **documents** - Document upload/processing
7. **domain_specialization** - Domain specialization
8. **graphiti** - Graphiti KG operations
9. **ias** - IAS coaching endpoints
10. **maintenance** - System maintenance
11. **memevolve** - MemEvolve webhook endpoints
12. **meta_tot** - Meta-ToT decision endpoints
13. **metacognition** - Metacognition endpoints
14. **models** - Model management
15. **voice** - Voice/speech endpoints

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
