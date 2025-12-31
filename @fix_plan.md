# Task Queue - Code Verification & Neo4j Data Processing

## Current Task
> **Verify webhook_neo4j_driver.py patterns**
> Check that all Neo4j operations use webhooks, no direct Cypher execution, proper error handling.
>
> Acceptance: All Neo4j access confirmed to go through webhooks; no direct driver connections found

## Backlog

### Code Quality Verification
- [ ] Audit api/services/ for unused imports
- [ ] Verify all Pydantic models have proper validators
- [ ] Check error handling in all routers (no bare except)
- [ ] Validate async/await propagation in service layer
- [ ] Identify dead code in api/agents/
- [ ] Verify type hints on all public functions in services/

### Neo4j Data Processing Checks
- [ ] Validate graphiti_service.py uses proper patterns
- [ ] Cross-check neo4j/schema/*.cypher with actual operations
- [ ] Verify MOSAEIC node constraints are enforced
- [ ] Check entity upsert operations for data consistency
- [ ] Validate relationship creation patterns
- [ ] Audit memory/recall operations for schema compliance

### Service Health Validation
- [ ] Verify singleton initialization order
- [ ] Check session_manager.py for proper cleanup
- [ ] Validate embedding service initialization
- [ ] Audit heartbeat_scheduler.py lifecycle
- [ ] Check coordination_service.py pool management

### Test Coverage Gaps
- [ ] Run pytest --cov and identify <80% coverage files
- [ ] Add missing contract tests for new routers
- [ ] Verify integration tests can run without live Neo4j
- [ ] Check test isolation (no shared state bleeding)

### MCP Server Verification
- [ ] Validate dionysus_mcp/tools/ registry
- [ ] Check MCP tool parameter validation
- [ ] Verify resource handlers in dionysus_mcp/resources/

## Completed
_None yet_

## Discovered
_Tasks found during verification_

## Blocked
_Tasks that can't proceed - document why_
