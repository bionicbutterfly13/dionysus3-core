# Implementation Plan: Legacy Component Discovery & Scoring

**Branch**: `019-legacy-component-discovery` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

## Summary
Port the Dionysus 2.0 consciousness-aware discovery and quality assessment into D3 as a smolagent tool + CLI/API surface. Output structured component scores (awareness/inference/memory + strategic value) to drive migration priorities.

## Technical Context
- **Language**: Python 3.11+
- **Stack**: smolagents, FastAPI, Pydantic, AST parsing, structlog
- **Targets**: `api/agents` (tool), `api/routers` (endpoint), `scripts` (CLI wrapper)
- **Testing**: pytest; fixture repo scan; contract tests on score shape

## Constitution Check
- [x] Data integrity: deterministic scoring, hashed component IDs
- [x] Observable systems: structured logs + trace ids
- [x] Versioned contracts: keep response models stable

## Milestones
1) Extract & adapt discovery core: lift AST pattern detection + scoring into a reusable module
2) Expose as smolagent tool + FastAPI route; add CLI harness
3) Config/logging: thresholds, weights, structured logs
4) Tests: golden file for sample repo, threshold gate, enhancement/risk presence

## Deliverables
- Reusable discovery module under `api/services/discovery_service.py`
- Smolagent tool to run discovery with top-N output
- FastAPI endpoint + CLI command
- Tests + docs snippet
