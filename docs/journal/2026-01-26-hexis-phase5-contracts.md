# Hexis Phase 5: Contract Tests

## Why
- Lock in Hexis API behavior (consent, boundaries, termination) with contract tests.
- Ensure the Hexis IO map stays wired to the API layer and remains stable.

## What Changed
- Added contract tests for:
  - `GET /hexis/consent/status`
  - `POST /hexis/consent`
  - `GET /hexis/boundaries`
  - `POST /hexis/boundaries`
  - `POST /hexis/terminate`
  - `POST /hexis/terminate/confirm`
- Tests use a stubbed `HexisService` and dependency overrides to avoid Graphiti access.

## Notes
- Tests are in `tests/contract/test_hexis_api.py`.
