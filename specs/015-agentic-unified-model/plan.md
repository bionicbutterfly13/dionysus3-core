# Implementation Plan: Agentic Unified Model

**Branch**: `015-agentic-unified-model` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary

Unify all sub-projects (Dionysus 3 Core, Marketing Suite, Knowledge Base) under a single agentic architecture using `smolagents`. Implement a unified `AspectService` for boardroom integrity with temporal history via Graphiti, and establish a human-in-the-loop review queue for low-confidence autonomous outputs.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `smolagents`, `litellm`, `neo4j`, `graphiti-core`  
**Architecture**: Hierarchical Managed Agents + Webhook-driven Neo4j  
**Storage**: Neo4j (current state) + Graphiti (history)

## Constitution Check

- [x] **I. Data Integrity First**: All inner state changes recorded in Graphiti temporal graph.
- [x] **II. Test-Driven Development**: Port existing project tests to the new agentic framework.
- [x] **III. Memory Safety & Correctness**: Agent outputs with <0.7 confidence diverted to human review.
- [x] **IV. Observable Systems**: Agent logs and human review queue visible via maintenance API.
- [x] **V. Versioned Contracts**: Unified Aspect service maintains backwards compatibility.

## Project Structure

```text
api/
├── agents/
│   ├── marketing_agent.py    # CodeAgent for Marketing Suite
│   └── knowledge_agent.py    # CodeAgent for KB Maintenance
└── services/
    ├── aspect_service.py     # Unified Source of Truth for Aspects
    └── maintenance_service.py # Review Queue & Reconstruction
```

## Phase 0: Research

- **Decision**: Use `managed_agents` for the Engine, but keep Marketing/KB as independent specialized agents for now.
- **Rationale**: Marketing and KB tasks are often episodic/independent rather than part of the core OODA cycle.
- **Alternatives**: Unifying ALL agents under one `ConsciousnessManager` (rejected for performance/context noise).

## Phase 1: Design

- **Data Model**: `Aspect` node + `HAS_ASPECT` relationship. `HumanReviewCandidate` node.
- **Contracts**: `POST /api/maintenance/review-queue`, `POST /api/aspects/upsert`.