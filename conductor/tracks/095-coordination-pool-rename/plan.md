# Plan: 095-coordination-pool-rename

**Track ID**: 095-coordination-pool-rename
**Status**: Done

## Completed

- [x] Rename `specs/020-daedalus-coordination-pool/` → `specs/020-coordination-pool/`
- [x] Rename `test_daedalus_guardrails.py` → `test_coordination_pool_guardrails.py`
- [x] Update spec content (7 files)
- [x] Update CLAUDE.md, GEMINI.md references
- [x] Update conductor/ references
- [x] Update docs/ references
- [x] Update scripts/ print statements
- [x] Update test class name
- [x] Verify tests pass

## Removed (Orphan Code)

- [x] Deleted `api/models/fleet.py` - uncommitted orphan with no callers
