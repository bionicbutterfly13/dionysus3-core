# Implementation Plan: Agentic Knowledge Graph Learning Loop

**Branch**: `022-agentic-kg-learning` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

## Summary
Integrate D2.0's agentic KG loop (dynamic relationships, attractor basins, cognition-base learning) into D3 on top of Graphiti/Neo4j, with smolagent orchestration.

## Technical Context
- **Language**: Python 3.11+
- **Stack**: smolagents, Graphiti, Neo4j, structlog
- **Targets**: extraction agent/tool, basin store, cognition-base updates, Graphiti client hooks
- **Testing**: pytest; integration against Neo4j test instance or mock Graphiti

## Constitution Check
- [x] Data integrity: provenance per edge; confidence stored
- [x] Observable systems: logs of basin use and strategy boosts
- [x] Human-in-loop: low-confidence edges flagged to review queue

## Milestones
1) Extraction agent/tool: LLM-assisted relationship proposals with dynamic types and confidences
2) Attractor basins: concept clustering + strength updates; feed into prompts
3) Cognition-base learning: record successful patterns; apply boosts on next runs
4) Graph storage: store relations via Graphiti with provenance, confidence, model IDs
5) Review hooks: route low-confidence edges to human review (reuse existing queue)
6) Tests: dynamic type creation, basin strengthening, learning boost applied

## Deliverables
- Extraction tool/agent + basin manager + cognition-base store
- Graphiti integration for dynamic relations
- Tests and docs snippet
