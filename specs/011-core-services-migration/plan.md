# Implementation Plan: Core Services Neo4j Migration

**Branch**: `011-core-services-migration` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary

Complete the transition to Neo4j by refactoring the three primary cognitive services. This involves replacing all `asyncpg` pool calls with `WebhookNeo4jDriver` sessions and converting SQL queries to Cypher statements.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `fastapi`, `pydantic`, `neo4j` (driver for types), `graphiti-core`  
**Storage**: Neo4j (via n8n Cypher webhook)  
**Testing**: `pytest`, integration tests against Neo4j

## Constitution Check

- [x] **I. Data Integrity First**: All Cypher queries use parameterized inputs to prevent injection.
- [x] **II. Test-Driven Development**: Port existing integration tests to Neo4j.
- [x] **III. Memory Safety & Correctness**: Temporal validity (`valid_at`) preserved.
- [x] **IV. Observable Systems**: Webhook logging captures all database traffic.
- [x] **V. Versioned Contracts**: No changes to existing REST API signatures.

## Project Structure

```text
api/
├── services/
│   ├── model_service.py             # Refactor to Cypher
│   ├── worldview_integration.py     # Refactor to Cypher + PW Formula
│   └── thoughtseed_integration.py   # Refactor to Cypher
```
