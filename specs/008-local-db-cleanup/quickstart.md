# Quickstart: Local PostgreSQL Cleanup & VPS Consolidation

**Feature**: 008-local-db-cleanup
**Date**: 2025-12-21

## Prerequisites

- SSH access to VPS: `ssh -i ~/.ssh/mani_vps mani@72.61.78.89`
- VPS PostgreSQL running (verified healthy)
- Docker running locally (for audit step)

## Phase 1: Data Audit & Migration

### Step 1.1: Start Local PostgreSQL (if exists)

```bash
docker compose -f docker-compose.local.yml up -d db 2>/dev/null || echo "No local DB or already running"
```

### Step 1.2: Audit Local Data

```bash
# Check if container exists
docker ps | grep dionysus_brain

# If running, audit tables
docker compose -f docker-compose.local.yml exec db \
  psql -U dionysus -d dionysus -c "
    SELECT schemaname, relname, n_live_tup
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC;"
```

**Decision point**: If row counts > 0 for important tables, proceed to Step 1.3. Otherwise, skip to Phase 2.

### Step 1.3: Export Local Data (if needed)

```bash
docker compose -f docker-compose.local.yml exec db \
  pg_dump -U dionysus -d dionysus --data-only > local_data_backup.sql

echo "Backup created: local_data_backup.sql ($(wc -l < local_data_backup.sql) lines)"
```

### Step 1.4: Import to VPS (if exported)

```bash
# Copy backup to VPS
scp -i ~/.ssh/mani_vps local_data_backup.sql mani@72.61.78.89:~/

# SSH to VPS and import
ssh -i ~/.ssh/mani_vps mani@72.61.78.89 << 'EOF'
cd ~/dionysus-api
docker exec -i dionysus-postgres psql -U dionysus -d dionysus < ~/local_data_backup.sql
echo "Import complete"
EOF
```

### Step 1.5: Verify Migration

```bash
# Compare row counts
ssh -i ~/.ssh/mani_vps mani@72.61.78.89 << 'EOF'
docker exec dionysus-postgres psql -U dionysus -d dionysus -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC;"
EOF
```

## Phase 2: Code Modifications

### Step 2.1: Update DATABASE_URL Pattern

Replace localhost fallbacks with required env var:

**BEFORE**:
```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dionysus:dionysus2024@localhost:5432/dionysus"
)
```

**AFTER**:
```python
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable required")
```

Files to modify:
- `api/services/session_manager.py:41-43`
- `api/services/db.py:21`
- `dionysus_mcp/server.py:29-31`
- `tests/conftest.py:22-23`
- `tests/integration/test_session_continuity.py:29-31`

### Step 2.2: Update .env.example

Add VPS connection instructions:

```bash
# VPS PostgreSQL (via SSH tunnel)
# First start tunnel: ssh -L 5432:localhost:5432 -i ~/.ssh/mani_vps mani@72.61.78.89
DATABASE_URL=postgresql://dionysus:PASSWORD@localhost:5432/dionysus
```

### Step 2.3: Update CLAUDE.md

Remove references to "local PostgreSQL" and update architecture section.

## Phase 3: File Cleanup

### Step 3.1: Stop Local Container

```bash
docker compose -f docker-compose.local.yml down 2>/dev/null || true
```

### Step 3.2: Remove Files

```bash
git rm docker-compose.local.yml
git rm db-manage.sh
git rm wait-for-db.sh
git rm test.py
```

## Phase 4: Verification

### Step 4.1: Start SSH Tunnel

```bash
ssh -L 5432:localhost:5432 -i ~/.ssh/mani_vps mani@72.61.78.89
```

### Step 4.2: Test Application

```bash
# In another terminal
export DATABASE_URL="postgresql://dionysus:PASSWORD@localhost:5432/dionysus"
python -c "import asyncpg; print('Connection test passed')"
```

### Step 4.3: Run Tests with Ephemeral DB

```bash
docker compose -f docker-compose.test.yml up -d db-test
DATABASE_URL="postgresql://dionysus:dionysus2024@localhost:5434/dionysus_test" \
  python -m pytest tests/ -v
docker compose -f docker-compose.test.yml down -v
```

### Step 4.4: Commit Changes

```bash
git add -A
git commit -m "refactor: Remove local PostgreSQL, consolidate to VPS

- Remove docker-compose.local.yml, db-manage.sh, wait-for-db.sh, test.py
- Update code to require DATABASE_URL (no localhost fallbacks)
- Preserve docker-compose.test.yml for ephemeral test database
- Update .env.example with VPS connection instructions

Closes #008-local-db-cleanup"

git push origin 008-local-db-cleanup
```

## VPS Deployment Workflow (Ongoing)

After cleanup is complete, use this workflow for deploying code changes:

```bash
# 1. Local: Commit and push
git add -A && git commit -m "feat: ..." && git push origin main

# 2. VPS: Pull and rebuild
ssh -i ~/.ssh/mani_vps mani@72.61.78.89 << 'EOF'
cd ~/dionysus-api
git pull origin main
docker compose up -d --build api
EOF
```
