# Plan: Track 072 - MemEvolve Ingest Guardrails

**Status:** In Progress

## Phase 1: Policy & Tests (TDD)
- [~] **Task 1.1**: Add failing tests to reject pre-extracted entities/edges on MemEvolve ingest.

## Phase 2: Implementation
- [~] **Task 2.1**: Enforce raw-only ingestion in MemEvolve ingest route.
- [~] **Task 2.2**: Remove hardcoded HMAC secrets from ingestion scripts and require env config.
- [~] **Task 2.3**: Deprecate pre-extracted Vigilant Sentinel ingest script.
