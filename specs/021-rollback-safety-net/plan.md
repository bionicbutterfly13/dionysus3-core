# Implementation Plan: Rollback Safety Net for Agentic Changes

**Branch**: `021-rollback-safety-net` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

## Summary
Port the D2.0 rollback/checkpoint system to protect smolagent-driven edits and migrations with fast restore, retention, and audit history.

## Technical Context
- **Language**: Python 3.11+
- **Stack**: FastAPI, structlog, asyncio, pathlib/shutil
- **Targets**: `api/services/rollback_service.py`, `api/routers/rollback.py`, smolagent tool wrapper
- **Testing**: pytest; checksum validation; timed rollback

## Constitution Check
- [x] Data integrity: checksums on backups; deterministic paths
- [x] Observable systems: structured logs + history records
- [x] Safety: confirmation on destructive actions; retention cleanup

## Milestones
1) Checkpoint creation: file + related file backup, metadata, optional DB snapshot hook
2) Rollback execution: restore files, update statuses, record history + duration
3) Interfaces: API endpoints + tool/CLI for checkpoint/rollback
4) Retention/cleanup and audit reporting
5) Tests: round-trip restore, timeout (<30s), retention cleanup

## Deliverables
- Rollback service module
- FastAPI router + tool hook
- Tests and docs snippet
