# Implementation Plan: Heartbeat Agent Handoff

**Branch**: `010-heartbeat-handoff` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary

Migrate the core cognitive loop from the procedural `HeartbeatService` to an autonomous `HeartbeatAgent` using the `smolagents` framework. This replaces the hardcoded OODA logic with a flexible, tool-using `CodeAgent` that reasons over environment state, goals, and recent agent trajectories.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `smolagents`, `litellm`, `fastapi`  
**Storage**: Neo4j (via Graphiti-backed driver shim)  
**Testing**: `pytest`, `scripts/test_heartbeat_agent.py`  
**Target Platform**: VPS (Docker)  
**Performance Goals**: <15s per cycle  
**Constraints**: Must respect energy budget (max 5 agent steps)

## Constitution Check

- [x] **I. Data Integrity First**: Trajectory processing uses `processed_at` timestamp to prevent double-consumption.
- [x] **II. Test-Driven Development**: Integration test `scripts/test_phase4_integration.py` already exists and will be expanded.
- [x] **III. Memory Safety & Correctness**: Agent execution is sandboxed via `smolagents` local executor.
- [x] **IV. Observable Systems**: HeartbeatLog persists full agent narrative and tool usage.
- [x] **V. Versioned Contracts**: Non-breaking change to internal service logic.

## Project Structure

### Source Code

```text
api/
├── agents/
│   ├── heartbeat_agent.py    # Authoritative orchestrator
│   └── tools/                # Cognitive tools used by agent
└── services/
    └── heartbeat_service.py  # Refactored to resource manager
```

## Structure Decision

Keep the `HeartbeatService` as the high-level FastAPI service, but strip out its decision logic. It will handle the timer, energy regeneration, and logging, while delegating the "Decide" and "Act" phases entirely to the `HeartbeatAgent`.
