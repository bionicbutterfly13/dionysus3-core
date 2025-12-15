# Changelog

All notable changes to dionysus3-core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
