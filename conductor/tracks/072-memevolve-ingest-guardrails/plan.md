# Plan: Track 072 - MemEvolve Ingest Guardrails

**Status:** In Progress

## Phase 1: Policy & Tests (TDD)
- [x] **Task 1.1**: Add failing tests to reject pre-extracted entities/edges on MemEvolve ingest. (8ca743e)

## Phase 2: Implementation
- [x] **Task 2.1**: Enforce raw-only ingestion in MemEvolve ingest route. (8ca743e)
- [x] **Task 2.2**: Remove hardcoded HMAC secrets from ingestion scripts and require env config. (8ca743e)
- [x] **Task 2.3**: Deprecate pre-extracted Vigilant Sentinel ingest script. (8ca743e)
- [x] **Task 2.4**: Deprecate Vigilant Sentinel v2 ingest script (pre-extracted payload). (pending)
