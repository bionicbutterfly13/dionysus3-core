# Feature Specification: Avatar Knowledge Graph

**Feature Branch**: `032-avatar-knowledge-graph`  \
**Created**: 2025-12-26  \
**Status**: In Progress  \
**Input**: Build a multi-agent system for researching and maintaining avatar profiles (target audience personas) using smolagents and Graphiti knowledge graph.

## User Scenarios & Testing

### User Story 1 - Content Analysis (Priority: P1)
As a marketer, I want to analyze content (copy, transcripts) to extract pain points, objections, and voice patterns, so I can build detailed avatar profiles.

**Independent Test**: POST content to `/avatar/analyze/content` and receive structured insights with pain points, objections, and linguistic patterns.

### User Story 2 - Ground Truth Ingestion (Priority: P1)
As a marketer, I want to ingest authoritative avatar documents as ground truth, so the system has a baseline understanding of my target audience.

**Independent Test**: POST a copy brief to `/avatar/ingest/ground-truth` and verify entities are created in Neo4j knowledge graph.

### User Story 3 - Avatar Research (Priority: P1)
As a marketer, I want to run research queries against the avatar knowledge graph, so I can retrieve synthesized insights for copy and messaging.

**Independent Test**: POST a research query to `/avatar/research` and receive agent-synthesized response with relevant insights.

## Requirements

### Functional Requirements
- **FR-001**: Provide multi-agent system with specialized analysts (PainAnalyst, ObjectionHandler, VoiceExtractor) orchestrated by AvatarResearcher.
- **FR-002**: Store all extracted insights in Neo4j via Graphiti for persistent knowledge graph.
- **FR-003**: Expose FastAPI endpoints for content analysis, document ingestion, research queries, and profile retrieval.
- **FR-004**: Support ground truth document ingestion to establish authoritative avatar baselines.
- **FR-005**: Integrate with IAS (Inner Architect System) copy workflows.

### Success Criteria
- **SC-001**: Ground truth document (IAS-copy-brief.md) successfully ingested with entities in Neo4j.
- **SC-002**: Research queries return relevant, synthesized insights from knowledge graph.
- **SC-003**: All endpoints return structured Pydantic responses with proper error handling.

## Implementation Notes (Progress)
- Multi-agent system in `api/agents/knowledge/` with smolagents framework.
- Pydantic models in `api/models/avatar.py`.
- FastAPI router in `api/routers/avatar.py`.
- Graphiti-backed tools in `api/agents/knowledge/tools.py`.
- Deployed to VPS, PR #3 pending merge.
