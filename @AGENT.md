# Build & Run Instructions

## Environment Setup
```bash
cd /Volumes/Asylum/dev/dionysus3-core
source .venv/bin/activate
```

## Build Commands
```bash
# Install dependencies
pip install -e ".[dev]"

# Type checking
mypy api/ --ignore-missing-imports

# Linting
black api/ dionysus_mcp/ tests/ --check
isort api/ dionysus_mcp/ tests/ --check-only
```

## Test Commands
```bash
# Run all tests (fast fail)
pytest tests/ -x --tb=short

# Unit tests only
pytest tests/unit/ -v

# Contract tests only
pytest tests/contract/ -v

# Integration tests only (requires Neo4j via webhooks)
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_hebbian.py -v

# With coverage
pytest tests/ --cov=api --cov-report=term-missing
```

## Run Commands
```bash
# Run API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run MCP server
dionysus-core

# Run specific script
python scripts/init_neo4j_schema.py
```

## Neo4j Verification (via n8n webhooks)
```bash
# Test webhook connectivity
curl -X POST http://localhost:5678/webhook/memory/v1/health

# Verify schema via webhook
python scripts/init_neo4j_schema.py --verify-only
```

## Common Fixes
```bash
# Format code
black api/ dionysus_mcp/ tests/
isort api/ dionysus_mcp/ tests/

# Clear pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__
```
