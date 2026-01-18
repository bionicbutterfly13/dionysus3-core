# Feature 041: Code Quality & Verification Audit

## Overview
Comprehensive code quality verification across the Dionysus Core codebase to ensure webhook patterns, proper error handling, type safety, and Neo4j schema compliance.

## Requirements

### FR-041-001: Neo4j Access Architecture Verification
**Priority:** P0
**Description:** Verify Neo4j access follows the approved architecture: GraphitiService as sole connector, MemEvolve as high-level abstraction.

**Actual Architecture (Verified):**
```
Application Code
    ↓
MemEvolve Adapter (api/services/memevolve_adapter.py)
    ↓  (calls graphiti.execute_cypher())
GraphitiService (api/services/graphiti_service.py)  ← SOLE NEO4J CONNECTOR
    ↓
graphiti-core library (internal neo4j driver)
    ↓
Neo4j Database
```

**Key Components:**
| Component | File | Role |
|-----------|------|------|
| **GraphitiService** | `api/services/graphiti_service.py` | SOLE authorized Neo4j connector |
| **MemEvolveAdapter** | `api/services/memevolve_adapter.py` | High-level memory abstraction, routes to Graphiti |
| **WebhookNeo4jDriver** | `api/services/webhook_neo4j_driver.py` | Legacy compatibility shim, proxies to MemEvolve → Graphiti |
| **RemoteSyncService** | `api/services/remote_sync.py` | n8n webhook routing (production sync) |

**Critical Finding: Inconsistent Access Patterns**
- **Direct Graphiti Users (50+ locations):** `avatar_tools.py`, `cognitive_tools.py`, `marketing_tools.py`, `aspect_service.py`, `consolidation_service.py`, `reconstruction_service.py`, `meta_tot_decision.py`, `belief_tracking_service.py`, routers (`session.py`, `ias.py`, `graphiti.py`, `maintenance.py`)
- **MemEvolve Adapter Users (8 locations):** `memevolve.py` (router), `vector_search.py`, `memory_basin_router.py`, `thoughtseed_integration.py`, `context_stream.py`, `mosaeic_service.py`, `kg_learning_service.py`, `webhook_neo4j_driver.py`

**What's Lost by Bypassing MemEvolve:**
1. No webhook sync - Direct Graphiti calls don't trigger n8n webhooks
2. No trajectory tracking - MemEvolve wraps calls with trajectory context
3. No centralized audit - No unified logging of all Neo4j operations
4. Tight coupling - Code depends directly on Graphiti implementation

**Acceptance Criteria:**
- [ ] No `from neo4j import GraphDatabase` in `api/` directory (dev scripts excepted)
- [ ] All `execute_cypher` calls route through GraphitiService
- [ ] MemEvolveAdapter routes to Graphiti (not direct Neo4j)
- [ ] WebhookNeo4jDriver proxies to MemEvolve (not direct Neo4j/n8n)
- [ ] Destruction gate active in `GraphitiService.execute_cypher()` blocks DELETE/DROP
- [ ] HMAC validation in RemoteSyncService for n8n webhook calls
- [ ] Document intentional Graphiti direct-access patterns vs MemEvolve pipeline

### FR-041-002: Import Hygiene
**Priority:** P1
**Description:** Remove unused imports across all service files.
**Acceptance:**
- No unused imports in `api/services/`
- All imports are utilized in their respective files

### FR-041-003: Pydantic Model Validation
**Priority:** P1
**Description:** Ensure all Pydantic models have proper field validators.
**Acceptance:**
- All models in `api/models/` and `api/schemas/` have validators
- Required fields are properly marked
- Custom validators for complex constraints

### FR-041-004: Error Handling Standards
**Priority:** P0
**Description:** Standardize error handling in all routers.
**Acceptance:**
- No bare `except:` clauses
- Proper exception types caught
- Consistent error response format

### FR-041-005: Async/Await Consistency
**Priority:** P1
**Description:** Validate async function propagation in service layer.
**Acceptance:**
- All async functions properly await their calls
- No blocking calls in async functions
- Proper async context management

### FR-041-006: Dead Code Elimination
**Priority:** P2
**Description:** Identify and remove unused code in agents.
**Acceptance:**
- No unreachable code paths
- No unused functions or classes
- Proper deprecation markers if needed

### FR-041-007: Type Hint Coverage
**Priority:** P1
**Description:** Complete type hints on all public service functions.
**Acceptance:**
- 100% type hint coverage on public APIs
- Proper return type annotations
- Generic types where appropriate

### FR-041-008: Neo4j Schema Compliance
**Priority:** P0
**Description:** Verify database operations match schema definitions.
**Acceptance:**
- Schema files match actual operations
- MOSAEIC constraints enforced
- Relationship patterns validated
- Entity upsert consistency maintained

### FR-041-009: Service Health Validation
**Priority:** P1
**Description:** Verify service lifecycle management.
**Acceptance:**
- Proper singleton initialization order
- Session cleanup implemented
- Resource lifecycle tracked
- Connection pools properly managed

### FR-041-010: Test Coverage Analysis
**Priority:** P0
**Description:** Achieve >80% test coverage on critical paths.
**Acceptance:**
- Coverage report generated
- <80% files identified and improved
- Contract tests for all routers
- Integration tests runnable without live services
- Test isolation verified

### FR-041-011: MCP Server Validation
**Priority:** P2
**Description:** Verify MCP tool and resource implementations.
**Acceptance:**
- Tool registry validated
- Parameter validation in place
- Resource handlers reviewed

## Technical Approach

### Phase 1: Static Analysis
- Use `mypy` for type checking
- Use `ruff` for linting and unused imports
- Use `pylint` for code quality metrics

### Phase 2: Pattern Verification
- Grep for direct Neo4j driver usage
- Check webhook patterns in all services
- Validate error handling patterns

### Phase 3: Test Coverage
- Run `pytest --cov` for coverage analysis
- Identify gaps and create tests
- Verify test isolation

### Phase 4: Manual Review
- Review complex async patterns
- Check service initialization order
- Validate schema compliance

## Success Criteria
1. All P0 requirements completed
2. Test coverage >80% on new/modified code
3. No linting errors or type checking failures
4. All Neo4j operations verified to use webhooks
5. Documentation updated with findings
