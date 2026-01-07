# Coverage Tool Path Fix

## Problem
Using filesystem paths like `--cov=api/services/module_name` causes coverage to report:
```
WARNING: Module api/services/module_name was never imported
No data was collected
```

## Solution
Use Python import paths with dots instead of slashes:
```bash
# WRONG (filesystem path):
--cov=api/services/epistemic_field_service

# CORRECT (Python import path):
--cov=api.services.epistemic_field_service
```

## Examples

Test with coverage for epistemic service:
```bash
python -m pytest tests/unit/test_epistemic_field_service.py \
  --cov=api.services.epistemic_field_service \
  --cov-report=term-missing -v
```

Test with coverage for meta_tot:
```bash
python -m pytest tests/unit/test_core_meta_tot.py \
  --cov=api.core.engine.meta_tot \
  --cov-report=term-missing -v
```

Test with coverage for meta_evolution:
```bash
python -m pytest tests/unit/test_meta_evolution_service.py \
  --cov=api.services.meta_evolution_service \
  --cov-report=term-missing -v
```
