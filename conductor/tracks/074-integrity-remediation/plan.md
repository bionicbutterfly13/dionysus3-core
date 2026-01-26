# Plan: 074-Integrity-Remediation

This plan outlines the steps to address the critical errors, runtime risks, and code quality issues identified in the System Health Audit (Track 073). The goal is to restore the codebase to a state of high integrity and reliability.

## Phase 1: Critical Fixes (Stop the Bleeding)

- [x] **T001: Resolve Test Discovery Blocker.** (adapted)
  - **Goal:** `pytest` collects all tests without import errors.
  - **Done:** Fixed `ImportError` in `scripts/verification/test_active_inference_integration.py` (import `BeliefState` from `api.models.belief_state`). Collection now succeeds (2706 tests).

- [x] **T002: Correct Critical Syntax Errors.**
  - **Goal:** Fix `invalid-syntax` errors to make scripts runnable.
  - **Done:** `scripts/ingestion/ingest_chunk.py` (duplicate/corrupt lines, stray backtick). `scripts/maintenance/init_neo4j_schema.py` (orphaned `except`, restructured try/except).

## Phase 2: Runtime Error Prevention (Eliminate Silent Failures)

- [x] **T003: Fix Undefined `httpx` and `logger` Names.**
  - **Done:** `import httpx` in `api/services/remote_sync.py`. Module-level `logger` in `api/routers/ias.py` and `api/routers/session.py`.

- [x] **T004: Resolve Undefined IAS Session Management.**
  - **Done:** Defined `sessions: dict[str, dict] = {}` and `get_session(session_id)` in `api/routers/ias.py`.

- [x] **T005: Define Missing AI Model Types.**
  - **Done:** `ActiveInferenceScore` imported and used in `api/core/engine/meta_tot.py`. `TimingState` imported and used in `api/services/network_state_service.py`.

## Phase 3: Code Quality & Refactoring (Pay Down Technical Debt)

- [x] **T006: Apply Automated Linting Fixes.**
  - **Done:** `ruff check . --fix` (430 fixes applied). Remaining issues left for T007/T008 or follow-up.

- [x] **T007: Manually Fix Import Order (E402).** (partial)
  - **Done:** Moved all imports to top in `api/agents/consciousness_manager.py`. ~107 E402 remain elsewhere; defer full sweep to follow-up.

- [x] **T008: Manually Refactor Bare Exceptions (E722).**
  - **Done:** Replaced bare `except:` in `api/services/action_executor.py` (JSONDecodeError, TypeError, ValueError), `api/services/memevolve_adapter.py` (JSONDecodeError, TypeError), `api/services/reconstruction_service.py` (ValueError). `ruff check --select E722` clean.

## Phase 4: Final Verification

- [x] **T009: Verification.**
  - **Done:** `pytest --collect-only` succeeds (2706 tests). Unit tests for meta_tot, network_state, vps_gateway pass (41). `py_compile` on ingest_chunk and init_neo4j_schema succeeds. One pre-existing failure: `test_concept_extraction_router::test_store_extraction_results` (mock mismatch, out of 074 scope).
