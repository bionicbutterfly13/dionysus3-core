# Changelog

All notable changes to dionysus3-core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-28

### Added - Marketing Framework & Ingestion
- **Marketing Models**: Added `api/models/marketing.py` with `FunnelStrategy` and `PDPArchitecture` supporting RMBC2 and Chat VSL frameworks.
- **Expert Asset Ingestion**: Ingested macro-to-micro funnel strategies, advertorial best practices, and master hook databases into Graphiti.
- **Marketing Knowledge Distillation**: Created `scripts/ingest_marketing_libraries.py` to distill Stefan Georgi and Jon Benson libraries.

### Changed - System Core & Connectivity
- **LLM Service Migration**: Renamed `api/services/claude.py` to `api/services/llm_service.py`. Updated all dependent agents (`KnowledgeAgent`, `CoachingAgent`) to use the new unified service.
- **Model Remapping**: Forced `LLM_PROVIDER` to `openai` and remapped `HAIKU` and `SONNET` to `gpt-5-nano` for cost-efficient processing and bill protection.
- **SSH Tunnel Resilience**: Implemented robust SSH tunnel management with ServerAlive intervals to prevent timeouts during large knowledge ingestion sessions.
- **Neo4j Connectivity**: Fixed `bolt://` connectivity from Docker containers using `host.docker.internal` and verified authentication with updated credentials.

## [1.1.0] - 2025-12-15

### Added - Session Continuity (Feature 001)

#### New MCP Tools
- `get_or_create_journey` - Get existing journey for device or create new one
- `query_journey_history` - Search past sessions by keyword, time range, or metadata
- `add_document_to_journey` - Link documents (WOOP plans, artifacts) to a journey

#### New API Features
- Session continuity via `X-Device-Id` header on `/session`, `/woop`, `/recall` endpoints
- Journey-based session tracking across multiple conversations
- Document linking for WOOP plans and artifacts
- Timeline view with interleaved sessions and documents

#### Database Schema
- `journeys` table - One per device, tracks conversation history
- `sessions` table - Individual conversations linked to journeys
- `journey_documents` table - Documents and artifacts linked to journeys
- Full-text search on session summaries using pg_trgm GIN index

#### Performance & Reliability
- Performance logging with 50ms/200ms thresholds
- Race condition protection using PostgreSQL UPSERT
- Database unavailability error handling
- Structured logging for all journey operations

## [1.0.0] - Initial Release

### Added
- Inner Architect System (IAS) coaching API
- Claude-powered diagnosis and coaching
- WOOP plan generation
- Framework knowledge base
