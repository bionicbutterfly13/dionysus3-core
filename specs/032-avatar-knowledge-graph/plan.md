# Implementation Plan: Avatar Knowledge Graph

**Branch**: `032-avatar-knowledge-graph` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary
Multi-agent avatar research system using smolagents + Graphiti. Specialized agents extract pain points, objections, and voice patterns from content, storing insights in Neo4j knowledge graph.

## Technical Context
- **Language**: Python 3.11+
- **Stack**: smolagents, FastAPI, Graphiti, Neo4j, Pydantic v2
- **Targets**: `api/agents/knowledge/`, `api/models/avatar.py`, `api/routers/avatar.py`
- **Testing**: pytest; agent integration tests; endpoint contract tests

## Constitution Check
- [x] Data integrity: Graphiti handles Neo4j transactions
- [x] Observable systems: Structured logging with trace IDs
- [x] Versioned contracts: Pydantic models define API shapes

## Architecture

### Agent Hierarchy
```
AvatarResearcher (Manager)
├── PainAnalyst      - Pain point extraction with intensity/triggers
├── ObjectionHandler - Objection mapping with counter-narratives
└── VoiceExtractor   - Linguistic pattern capture
```

### Data Flow
```
Content → Agents → Insights → Graphiti → Neo4j
                                ↓
                        Query/Research
```

## Milestones
1. ✅ Core agent implementations (PainAnalyst, ObjectionHandler, VoiceExtractor)
2. ✅ Manager agent (AvatarResearcher) with smolagents orchestration
3. ✅ Graphiti tools for knowledge graph operations
4. ✅ FastAPI endpoints for all operations
5. ⏳ Ground truth ingestion and testing
6. ⏳ Research query validation

## Deliverables
- Multi-agent system in `api/agents/knowledge/`
- Pydantic models for avatar insights
- FastAPI router with full endpoint coverage
- Graphiti integration for Neo4j persistence
