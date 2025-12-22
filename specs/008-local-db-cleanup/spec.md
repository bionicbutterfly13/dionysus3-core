# Feature Specification: Local PostgreSQL Cleanup & VPS Consolidation

**Feature Branch**: `008-local-db-cleanup`
**Created**: 2025-12-21
**Status**: Draft
**Input**: Remove local PostgreSQL infrastructure from dionysus3-core and consolidate to VPS as single source of truth.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Migration Safety (Priority: P1)

As a developer, I need to safely migrate any useful data from local PostgreSQL to VPS before cleanup, so that no valuable information is lost during the consolidation.

**Why this priority**: Data safety is paramount - must preserve any existing work before removing infrastructure.

**Independent Test**: Run data audit commands locally and verify imported data appears on VPS.

**Acceptance Scenarios**:

1. **Given** a local PostgreSQL database may contain data, **When** I run the audit command, **Then** I see a report of all tables and row counts.
2. **Given** local data exists, **When** I run the export command, **Then** a backup file is created with all relevant data.
3. **Given** exported data file exists, **When** I run the import command on VPS, **Then** data appears in VPS PostgreSQL and is verified.

---

### User Story 2 - Single Source of Truth (Priority: P1)

As a developer, I need all code to connect only to the VPS PostgreSQL database, so that there is no confusion about which database is authoritative.

**Why this priority**: Eliminating dual-database confusion is the core goal.

**Independent Test**: Remove all localhost fallbacks and verify application requires DATABASE_URL environment variable.

**Acceptance Scenarios**:

1. **Given** DATABASE_URL is not set, **When** I start the application, **Then** it fails with a clear error message.
2. **Given** DATABASE_URL points to VPS, **When** I run tests, **Then** all tests connect to VPS via SSH tunnel and pass.
3. **Given** code has been cleaned, **When** I search for "localhost:5432", **Then** no production code contains these fallbacks.

---

### User Story 3 - Local Infrastructure Removal (Priority: P2)

As a developer, I need obsolete local database files removed from the repository, so that the codebase is clean.

**Why this priority**: Depends on P1 completion.

**Independent Test**: Verify listed files no longer exist and application still functions.

**Acceptance Scenarios**:

1. **Given** data migration is complete, **When** I check for docker-compose.local.yml, **Then** it no longer exists.
2. **Given** local infrastructure files are removed, **When** I run git status, **Then** db-manage.sh, wait-for-db.sh, and test.py show as deleted.

---

### User Story 4 - Test Infrastructure Preservation (Priority: P2)

As a developer, I need the ephemeral test database configuration preserved for CI/CD and local testing.

**Why this priority**: Testing infrastructure must remain functional.

**Independent Test**: Run test suite with docker-compose.test.yml on port 5434.

**Acceptance Scenarios**:

1. **Given** docker-compose.test.yml exists, **When** I start test database, **Then** ephemeral PostgreSQL runs on port 5434.
2. **Given** test database is running, **When** I execute test suite, **Then** tests run against isolated test database.

---

### User Story 5 - VPS Deployment Documentation (Priority: P3)

As a developer, I need clear documentation for deploying code changes to VPS.

**Why this priority**: Documentation supports ongoing development but is not blocking.

**Independent Test**: Follow documented steps and verify successful deployment.

**Acceptance Scenarios**:

1. **Given** code changes are committed, **When** I follow deployment documentation, **Then** changes deploy to VPS successfully.

---

### Edge Cases

- What happens when local PostgreSQL container is not running during audit? System provides clear instructions to start it.
- What happens when local database has no useful data? Migration step is skipped with confirmation.
- What happens when VPS is unreachable during import? Process fails with clear error and rollback instructions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST audit local PostgreSQL for tables and row counts before cleanup.
- **FR-002**: System MUST export local data to a backup file if useful data exists.
- **FR-003**: System MUST import backup data to VPS PostgreSQL with verification.
- **FR-004**: System MUST remove docker-compose.local.yml from repository.
- **FR-005**: System MUST remove db-manage.sh from repository.
- **FR-006**: System MUST remove wait-for-db.sh from repository.
- **FR-007**: System MUST remove test.py from repository.
- **FR-008**: System MUST modify code to require DATABASE_URL environment variable with no localhost fallbacks.
- **FR-009**: System MUST preserve docker-compose.test.yml for ephemeral test database on port 5434.
- **FR-010**: System MUST NOT modify Archon MCP server or any external systems.
- **FR-011**: System MUST update .env.example with VPS connection instructions.
- **FR-012**: System MUST update CLAUDE.md to remove local PostgreSQL references.
- **FR-013**: System MUST document VPS deployment workflow.

### Key Entities

- **Local PostgreSQL**: Development database in Docker (to be removed)
- **VPS PostgreSQL**: Production database at 72.61.78.89:5432 (single source of truth)
- **Test PostgreSQL**: Ephemeral database on port 5434 (preserved)
- **DATABASE_URL**: Required environment variable for database connection

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero local PostgreSQL containers running after cleanup.
- **SC-002**: Zero localhost database fallbacks in production code.
- **SC-003**: All application tests pass when connected to VPS via SSH tunnel.
- **SC-004**: New developer can deploy code to VPS within 5 minutes using documentation.
- **SC-005**: No data loss during migration (verified by row count comparison).
- **SC-006**: Test suite executes successfully with ephemeral database on port 5434.

## Assumptions

- VPS PostgreSQL (72.61.78.89:5432) is operational with 15 tables.
- SSH key (~/.ssh/mani_vps) provides access to VPS.
- Local data may or may not exist - migration step is conditional.
- Archon MCP server uses a separate database and is unaffected.

## Out of Scope

- Modifying Archon MCP server or its database
- Changing Neo4j configuration (already VPS-only via n8n)
- Modifying n8n workflows
- Automated CI/CD deployment
- Database schema changes on VPS
