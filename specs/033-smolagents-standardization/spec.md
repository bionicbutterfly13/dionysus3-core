# Feature Specification: Smolagents Standardization & Hardening

**Feature Branch**: `refactor/smolagents-alignment`
**Status**: In-Progress
**Input**: [Smolagents Architecture Refactor Plan](https://huggingface.co/blog/smolagents) and local repo at `/Volumes/Asylum/repos/smolagents`.

## Overview
Standardize all 11 agents and 9 tool files to align with `smolagents` production best practices. This eliminates security vulnerabilities (remote code execution), architectural mismatches (`nest_asyncio`), and establishes 100% observability of the OODA loop.

## Requirements
- **FR-033-001**: Implement Docker sandboxing for all `CodeAgent` orchestrators using `dionysus/agent-sandbox:latest`.
- **FR-033-002**: Migrate all leaf/analyst agents to `ToolCallingAgent` for performance and security.
- **FR-033-003**: Implement mandatory timeout wrappers and global resource gating (semaphores) for all agent runs.
- **FR-033-004**: Establish a separate Procedural/Autobiographical subgraph in Neo4j for agent trajectory persistence.
- **FR-033-005**: Eliminate `nest_asyncio` by implementing thread-per-tool execution with isolated event loops.

## Success Criteria
- **SC-001**: Zero agents running with `trust_remote_code=True`.
- **SC-002**: All orchestrator runs isolated in Alpine-based Docker containers.
- **SC-003**: Mandatory timeouts trigger alerts instead of hanging the API.
- **SC-004**: All 27+ existing tests pass under the new architecture.
