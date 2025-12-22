# Tasks: Local PostgreSQL Cleanup & VPS Consolidation

**Input**: Design documents from `/specs/008-local-db-cleanup/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: Not explicitly requested - no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Preparation and safety measures

- [ ] T001 Verify VPS PostgreSQL is healthy via SSH: `ssh -i ~/.ssh/mani_vps mani@72.61.78.89 'docker exec dionysus-postgres pg_isready'`
- [ ] T002 Create backup of VPS database before any changes: `~/backup.sh` on VPS

---

## Phase 2: User Story 1 - Data Migration Safety (Priority: P1) 🎯 MVP

**Goal**: Safely audit and migrate any useful local data to VPS before cleanup

**Independent Test**: Run audit commands, verify export file created, verify data appears on VPS

### Implementation for User Story 1

- [ ] T003 [US1] Start local PostgreSQL container: `docker compose -f docker-compose.local.yml up -d db`
- [ ] T004 [US1] Audit local database tables and row counts: `docker compose exec db psql -U dionysus -d dionysus -c "SELECT relname, n_live_tup FROM pg_stat_user_tables"`
- [ ] T005 [US1] Export local data to backup file if data exists: `docker compose exec db pg_dump -U dionysus -d dionysus --data-only > local_data_backup.sql`
- [ ] T006 [US1] Copy backup to VPS: `scp -i ~/.ssh/mani_vps local_data_backup.sql mani@72.61.78.89:~/`
- [ ] T007 [US1] Import backup to VPS PostgreSQL: `docker exec -i dionysus-postgres psql -U dionysus -d dionysus < ~/local_data_backup.sql`
- [ ] T008 [US1] Verify import by comparing row counts on VPS
- [ ] T009 [US1] Stop local PostgreSQL container: `docker compose -f docker-compose.local.yml down`

**Checkpoint**: Local data safely migrated to VPS (or confirmed empty)

---

## Phase 3: User Story 2 - Single Source of Truth (Priority: P1)

**Goal**: Update all code to require DATABASE_URL without localhost fallbacks

**Independent Test**: Start application without DATABASE_URL, verify it fails with clear error

### Implementation for User Story 2

- [ ] T010 [P] [US2] Update api/services/session_manager.py:41-43 - Remove localhost fallback, require DATABASE_URL
- [ ] T011 [P] [US2] Update api/services/db.py:21 - Add validation that DATABASE_URL is set
- [ ] T012 [P] [US2] Update dionysus_mcp/server.py:29-31 - Remove localhost:5433/agi_memory fallback
- [ ] T013 [P] [US2] Update tests/conftest.py:22-23 - Remove localhost fallback
- [ ] T014 [P] [US2] Update tests/integration/test_session_continuity.py:29-31 - Remove localhost fallback
- [ ] T015 [US2] Verify grep shows zero localhost database fallbacks in production code

**Checkpoint**: All code requires explicit DATABASE_URL

---

## Phase 4: User Story 3 - Local Infrastructure Removal (Priority: P2)

**Goal**: Remove obsolete local database files from repository

**Independent Test**: Verify files no longer exist, application still runs

### Implementation for User Story 3

- [ ] T016 [P] [US3] Remove docker-compose.local.yml: `git rm docker-compose.local.yml`
- [ ] T017 [P] [US3] Remove db-manage.sh: `git rm db-manage.sh`
- [ ] T018 [P] [US3] Remove wait-for-db.sh: `git rm wait-for-db.sh`
- [ ] T019 [P] [US3] Remove test.py: `git rm test.py`

**Checkpoint**: Obsolete files removed from repository

---

## Phase 5: User Story 4 - Test Infrastructure Preservation (Priority: P2)

**Goal**: Verify ephemeral test database still works

**Independent Test**: Run test suite with docker-compose.test.yml

### Implementation for User Story 4

- [ ] T020 [US4] Verify docker-compose.test.yml exists and is correct (port 5434)
- [ ] T021 [US4] Test ephemeral database: `docker compose -f docker-compose.test.yml up -d db-test`
- [ ] T022 [US4] Run tests against ephemeral database: `DATABASE_URL=postgresql://dionysus:dionysus2024@localhost:5434/dionysus_test python -m pytest tests/ -v`
- [ ] T023 [US4] Tear down test database: `docker compose -f docker-compose.test.yml down -v`

**Checkpoint**: Test infrastructure confirmed working

---

## Phase 6: User Story 5 - VPS Deployment Documentation (Priority: P3)

**Goal**: Update documentation with VPS-only architecture

**Independent Test**: New developer can follow docs to deploy

### Implementation for User Story 5

- [ ] T024 [P] [US5] Update .env.example with VPS connection instructions and SSH tunnel command
- [ ] T025 [P] [US5] Update CLAUDE.md - Remove "local PostgreSQL" references, update architecture section
- [ ] T026 [US5] Verify quickstart.md in specs/008-local-db-cleanup/ is complete

**Checkpoint**: Documentation updated for VPS-only workflow

---

## Phase 7: Polish & Verification

**Purpose**: Final verification and commit

- [ ] T027 Start SSH tunnel: `ssh -L 5432:localhost:5432 -i ~/.ssh/mani_vps mani@72.61.78.89`
- [ ] T028 Verify application connects to VPS via tunnel
- [ ] T029 Verify all tests pass with ephemeral test database
- [ ] T030 Commit all changes: `git add -A && git commit -m "refactor: Remove local PostgreSQL, consolidate to VPS"`
- [ ] T031 Push branch: `git push origin 008-local-db-cleanup`
- [ ] T032 Create PR or merge to main

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (US1 Data Migration)**: Depends on Setup - MUST complete before US3 (file removal)
- **Phase 3 (US2 Code Changes)**: Can run parallel with US1
- **Phase 4 (US3 File Removal)**: Depends on US1 completion (data safety first)
- **Phase 5 (US4 Test Verification)**: Can run after US2 and US3
- **Phase 6 (US5 Documentation)**: Can run parallel with US4
- **Phase 7 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Data Migration)**: First priority - safety gate for US3
- **US2 (Code Changes)**: Independent - can run parallel with US1
- **US3 (File Removal)**: Depends on US1 completion
- **US4 (Test Verification)**: Depends on US2 and US3
- **US5 (Documentation)**: Independent - can run anytime

### Parallel Opportunities

Within Phase 3 (US2):
```bash
# All code modifications can run in parallel:
Task: T010 "Update api/services/session_manager.py"
Task: T011 "Update api/services/db.py"
Task: T012 "Update dionysus_mcp/server.py"
Task: T013 "Update tests/conftest.py"
Task: T014 "Update tests/integration/test_session_continuity.py"
```

Within Phase 4 (US3):
```bash
# All file removals can run in parallel:
Task: T016 "Remove docker-compose.local.yml"
Task: T017 "Remove db-manage.sh"
Task: T018 "Remove wait-for-db.sh"
Task: T019 "Remove test.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (verify VPS healthy)
2. Complete Phase 2: US1 Data Migration (safety first)
3. Complete Phase 3: US2 Code Changes
4. **STOP and VALIDATE**: Test application with VPS via tunnel
5. Proceed to file cleanup only after validation

### Critical Path

```
Setup → US1 (Data Migration) → US3 (File Removal) → Polish
           ↓
        US2 (Code Changes) → US4 (Test Verification)
           ↓
        US5 (Documentation)
```

---

## Notes

- US1 is a safety gate - DO NOT remove files until data migration is verified
- All code modifications in US2 are independent and can be parallelized
- If local database has no data, US1 steps T005-T008 can be skipped
- Test ephemeral database (US4) validates test infrastructure still works
- Commit frequently after each phase completion
