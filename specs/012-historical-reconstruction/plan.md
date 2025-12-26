# Implementation Plan: Historical Task Reconstruction

**Branch**: `012-historical-reconstruction` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary

Build a bridge between local Archon task management and VPS-native Neo4j persistence. This tool will perform a deep scan of Archon's task database and mirror all historical records into the graph, ensuring long-term continuity even when sessions are reset.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `httpx`, `smolagents` (for tool interface)  
**Storage**: Neo4j (target), Archon SQLite (source via local MCP)  
**Testing**: `scripts/test_mcp_bridge.py`

## Project Structure

```text
api/
├── services/
│   └── reconstruction_service.py    # Core logic
└── agents/
    └── tools/
        └── reconstruction_tool.py   # Agent-facing tool
```
