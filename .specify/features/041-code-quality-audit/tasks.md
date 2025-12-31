# Feature 041: Tasks

## Phase 1: Neo4j Pattern Verification (P0)

### T041-001: Verify webhook_neo4j_driver.py patterns
- [ ] Search for direct Neo4j driver imports (`from neo4j import`)
- [ ] Verify all operations use webhook endpoints
- [ ] Check HMAC signature validation
- [ ] Document webhook pattern compliance
**Status:** In Progress

### T041-002: Audit graphiti_service.py
- [ ] Check Neo4j access patterns in graphiti_service.py
- [ ] Verify webhook usage for graph operations
- [ ] Validate error handling

### T041-003: Cross-check schema files with operations
- [ ] List all `neo4j/schema/*.cypher` files
- [ ] Map schema definitions to service operations
- [ ] Identify mismatches

### T041-004: Verify MOSAEIC constraints
- [ ] Check constraint enforcement in node operations
- [ ] Validate uniqueness constraints
- [ ] Test constraint violations

### T041-005: Audit entity upsert operations
- [ ] Review all upsert patterns
- [ ] Check data consistency validation
- [ ] Test concurrent upsert scenarios

### T041-006: Validate relationship creation
- [ ] Review relationship creation patterns
- [ ] Check error handling
- [ ] Verify bidirectional relationships

### T041-007: Audit memory/recall operations
- [ ] Check schema compliance in recall operations
- [ ] Verify memory persistence patterns
- [ ] Test edge cases

---

## Phase 2: Code Quality (P1)

### T041-008: Run ruff for unused imports
- [ ] Run `ruff check api/services/ --select F401`
- [ ] Fix unused imports in each file
- [ ] Run `ruff check api/agents/ --select F401`
- [ ] Fix unused imports in agents

### T041-009: Verify Pydantic model validators
- [ ] List all models in `api/models/`
- [ ] Check for field validators
- [ ] Add missing validators for new models
- [ ] Test validator edge cases

### T041-010: Audit router error handling
- [ ] Check `api/routers/*.py` for bare except
- [ ] Standardize exception handling
- [ ] Implement consistent error responses
- [ ] Document error codes

### T041-011: Validate async/await patterns
- [ ] Check service layer async functions
- [ ] Identify blocking calls in async code
- [ ] Fix async context issues
- [ ] Add async tests

### T041-012: Run mypy type checking
- [ ] Run `mypy api/services/ --ignore-missing-imports`
- [ ] Fix type errors
- [ ] Add missing type hints
- [ ] Run full suite: `mypy api/ --ignore-missing-imports`

---

## Phase 3: Service Health (P1)

### T041-013: Verify singleton initialization
- [ ] Map service dependencies
- [ ] Check initialization order
- [ ] Test circular dependency scenarios
- [ ] Document initialization flow

### T041-014: Audit session_manager.py
- [ ] Check resource cleanup methods
- [ ] Verify session lifecycle
- [ ] Test cleanup on errors
- [ ] Add cleanup tests

### T041-015: Validate embedding service
- [ ] Check initialization logic
- [ ] Verify error handling
- [ ] Test service recovery
- [ ] Document configuration

### T041-016: Audit heartbeat_scheduler.py
- [ ] Review lifecycle management
- [ ] Check graceful shutdown
- [ ] Test restart scenarios
- [ ] Validate timing accuracy

### T041-017: Check coordination_service.py
- [ ] Verify pool creation
- [ ] Check connection limits
- [ ] Test pool exhaustion
- [ ] Validate cleanup

---

## Phase 4: Test Coverage (P0)

### T041-018: Run coverage analysis
- [ ] Activate venv: `source .venv/bin/activate`
- [ ] Run `pytest tests/ --cov=api --cov-report=term-missing --cov-report=html`
- [ ] Generate coverage report
- [ ] Identify <80% coverage files
**Status:** Ready

### T041-019: Add tests for low coverage files
- [ ] Create tests for identified files
- [ ] Aim for >80% coverage
- [ ] Focus on critical paths

### T041-020: Create contract tests for routers
- [ ] List routers without contract tests
- [ ] Create contract test suite
- [ ] Validate API contracts
- [ ] Test error responses

### T041-021: Verify test isolation
- [ ] Check for shared state in tests
- [ ] Run tests in random order
- [ ] Fix isolation issues
- [ ] Add isolation markers

### T041-022: Mock Neo4j in integration tests
- [ ] Identify tests requiring live Neo4j
- [ ] Create Neo4j mocks
- [ ] Update tests to use mocks
- [ ] Verify test behavior

---

## Phase 5: Dead Code & Type Hints (P2)

### T041-023: Identify dead code in agents
- [ ] Use `vulture` for dead code detection
- [ ] Review flagged code manually
- [ ] Remove confirmed dead code
- [ ] Add deprecation warnings if needed

### T041-024: Complete type hints in services
- [ ] Check all public functions in `api/services/`
- [ ] Add missing type hints
- [ ] Use generics where appropriate
- [ ] Run mypy to verify

---

## Phase 6: MCP Server Validation (P2)

### T041-025: Validate MCP tool registry
- [ ] Check `dionysus_mcp/tools/` registry
- [ ] Verify all tools registered
- [ ] Test tool discovery

### T041-026: Check MCP parameter validation
- [ ] Review tool parameter schemas
- [ ] Add validation where missing
- [ ] Test invalid parameters

### T041-027: Verify MCP resource handlers
- [ ] Review `dionysus_mcp/resources/`
- [ ] Check error handling
- [ ] Test resource lifecycle

---

## Dependencies

```
T041-018 → T041-019 (Coverage analysis before adding tests)
T041-008 → T041-012 (Fix imports before type checking)
T041-001 → T041-002 → T041-003 (Sequential Neo4j verification)
```

## Acceptance Criteria

1. All P0 tasks completed (Neo4j patterns, error handling, test coverage)
2. Test coverage >80% on api/services/ and api/agents/
3. Zero linting errors from ruff
4. Zero type errors from mypy (with --ignore-missing-imports)
5. All Neo4j operations confirmed to use webhooks
6. Documentation updated with audit findings
