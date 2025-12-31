# Dionysus3-Core - Ralph Instructions

## Goal
Comprehensive code verification and Neo4j data processing validation. Ensure all code paths work correctly, Neo4j schema is properly enforced, data integrity constraints are validated, and webhook-based Neo4j access patterns are correct.

## Current State
Production codebase with:
- FastAPI backend (`api/`)
- MCP server (`dionysus_mcp/`)
- Neo4j schema definitions (`neo4j/schema/`)
- Unit, contract, and integration tests (`tests/`)
- Graphiti-based knowledge graph operations
- Webhook-based Neo4j driver (NO direct Cypher - all via n8n webhooks)

## Tech Stack
- Language: Python 3.11+
- Framework: FastAPI, Pydantic 2.x
- Database: Neo4j (accessed via webhooks and Graphiti ONLY)
- Testing: pytest with pytest-asyncio
- MCP: mcp>=1.12.2, smolagents
- AI: OpenAI, Anthropic, LiteLLM

## Critical Constraints
**NEVER ACCESS NEO4J DIRECTLY**
- No Cypher queries in code
- No neo4j-driver direct connections
- All Neo4j access via `webhook_neo4j_driver.py` or Graphiti service
- n8n webhooks are the ONLY path to Neo4j

## Working Rules
1. Read `@fix_plan.md` for current task
2. Complete ONE task per iteration (2-5 min max)
3. Run tests after each change: `pytest tests/ -x --tb=short`
4. Commit with: `ralph: [description]`
5. Update `@fix_plan.md` after each task
6. If blocked, document in Blocked section and move to next task

## Verification Categories

### 1. Code Quality Verification
- Import validation (no circular imports, unused imports)
- Type hint completeness (Pydantic models, function signatures)
- Error handling (try/except with proper logging)
- Dead code detection (unused functions, unreachable paths)

### 2. Neo4j Data Processing Checks
- Schema validation against `neo4j/schema/*.cypher`
- Webhook driver patterns in `api/services/webhook_neo4j_driver.py`
- Graphiti service operations in `api/services/graphiti_service.py`
- Entity/relationship constraint validation
- Data consistency checks via n8n workflows

### 3. Service Health Validation
- All service singletons initialize correctly
- Dependency injection patterns are consistent
- Async/await patterns are properly propagated
- Resource cleanup on shutdown

### 4. Test Coverage
- All routers have contract tests
- All services have unit tests
- Critical paths have integration tests

## Task Completion Criteria
- [ ] Code change implemented
- [ ] No new linting errors
- [ ] Tests pass: `pytest tests/ -x`
- [ ] Changes committed
- [ ] `@fix_plan.md` updated

## Anti-Patterns (DO NOT)
- Skip tests
- Batch multiple tasks
- Leave uncommitted changes
- Work on tasks not in @fix_plan.md
- Access Neo4j directly (always use webhooks/Graphiti)
- Add unnecessary abstractions
- Over-engineer simple fixes

## File Reference
```
api/
  routers/      # FastAPI route handlers
  services/     # Business logic, Neo4j drivers
  models/       # Pydantic models
  agents/       # AI agent implementations
dionysus_mcp/   # MCP server
tests/
  unit/         # Unit tests
  contract/     # API contract tests
  integration/  # Integration tests
neo4j/schema/   # Cypher schema definitions
```
