# Track 074: Codebase QA Sweep

## Overview

Comprehensive codebase quality assurance system with expert-level analyzer agents that identify issues and spawn targeted repair crews for autonomous remediation.

## Problem Statement

Large codebases accumulate technical debt through:
- **Broken Promises**: TODO/FIXME comments, incomplete implementations, unfulfilled docstrings
- **Orphan Code**: Unused functions, dead imports, unreferenced modules
- **Documentation Drift**: Docstrings that don't match implementation, outdated README sections
- **Incomplete Patterns**: Half-implemented features, missing error handling, stub methods

Manual audits are time-consuming and inconsistent. We need an automated, agent-driven approach.

## Solution

Multi-agent QA orchestration system with specialized analyzer agents and repair crews.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    QA Sweep Orchestrator                         │
│  - Coordinates full codebase scan                                │
│  - Aggregates findings by issue class                            │
│  - Spawns repair crews for each class                            │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Promise Keeper │  │  Orphan Hunter  │  │  Doc Alignment  │
│     Analyzer    │  │    Analyzer     │  │    Analyzer     │
│                 │  │                 │  │                 │
│ - TODO/FIXME    │  │ - Dead code     │  │ - Docstring     │
│ - Stub methods  │  │ - Unused imports│  │   mismatches    │
│ - Incomplete    │  │ - Unreferenced  │  │ - README drift  │
│   implementations│ │   functions     │  │ - Missing docs  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Issue Aggregator                              │
│  - Groups findings by severity and class                         │
│  - Creates repair work orders                                    │
│  - Tracks remediation status                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Repair Crew Spawner                           │
│  For each issue class:                                           │
│  1. Create feature branch: fix/qa-{issue-class}-{timestamp}      │
│  2. Spawn expert repair agent (matched to issue type)            │
│  3. Spawn paired documentation agent                             │
│  4. Validate repairs                                             │
│  5. Merge when tests pass                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Specifications

#### 1. Promise Keeper Analyzer
**Purpose**: Find broken promises in code

**Detection Patterns**:
- `TODO:`, `FIXME:`, `XXX:`, `HACK:` comments
- Stub methods: `raise NotImplementedError`, `pass` in non-empty methods
- Incomplete implementations: Functions that return None unexpectedly
- Unfulfilled type annotations: Return types that don't match actual returns
- Docstrings claiming functionality not implemented

**Output**: List of `BrokenPromise` findings with:
- File path and line number
- Promise type (TODO, stub, incomplete, etc.)
- Severity (critical, high, medium, low)
- Context (surrounding code)
- Suggested remediation

#### 2. Orphan Hunter Analyzer
**Purpose**: Find dead and unreferenced code

**Detection Patterns**:
- Unused imports (imported but never used)
- Dead functions (defined but never called)
- Unreferenced classes
- Orphan test files (testing removed code)
- Deprecated code still present
- Commented-out code blocks

**Output**: List of `OrphanCode` findings with:
- File path and line range
- Orphan type (import, function, class, etc.)
- Reference analysis (why it's orphaned)
- Safe to remove confidence score

#### 3. Documentation Alignment Analyzer
**Purpose**: Find doc/code misalignment

**Detection Patterns**:
- Docstring parameter lists vs actual parameters
- Return type claims vs actual returns
- Example code that doesn't work
- README sections referencing moved/deleted files
- API documentation with wrong endpoints
- Outdated architecture descriptions

**Output**: List of `DocMisalignment` findings with:
- Doc location and code location
- Misalignment type
- Diff of expected vs actual
- Suggested correction

### Repair Crew Structure

Each repair crew consists of:

1. **Expert Repair Agent** (matched to issue class)
   - Promise Fulfiller: Implements TODOs, completes stubs
   - Code Cleaner: Safely removes orphan code
   - Doc Synchronizer: Updates documentation to match code

2. **Documentation Agent** (always paired)
   - Updates docstrings for changed functions
   - Updates README if architectural changes
   - Creates migration notes if breaking changes

3. **Validation Agent**
   - Runs affected tests
   - Verifies no regressions
   - Checks documentation accuracy

### Workflow

```
1. ANALYZE
   - Run all analyzer agents in parallel
   - Aggregate findings into issue registry
   - Prioritize by severity and dependency

2. PLAN
   - Group related issues for batch repair
   - Create repair work orders
   - Estimate effort and risk

3. REPAIR
   For each work order:
   a. Create branch: fix/qa-{class}-{id}
   b. Spawn repair + doc agents
   c. Implement fixes
   d. Run validation
   e. Create PR with findings summary

4. VALIDATE
   - Full test suite passes
   - Documentation is accurate
   - No new issues introduced

5. MERGE
   - Auto-merge if validation passes
   - Manual review if high-risk changes
```

## Success Criteria

1. **Coverage**: All Python files in `api/`, `dionysus_mcp/`, `tests/` analyzed
2. **Detection Rate**: >90% of known issues caught (based on manual sample)
3. **Repair Rate**: >80% of issues auto-remediated
4. **Quality**: Zero regressions introduced by repairs
5. **Documentation**: All changes have corresponding doc updates

## Constraints

- **No Production Impact**: QA sweep is analysis-only; repairs are on branches
- **Atomic Commits**: Each repair is a single commit with clear message
- **Test Preservation**: Never delete tests without explicit approval
- **Branch Hygiene**: Clean up branches after merge

## Dependencies

- Existing test suite for validation
- Git for branch management
- smolagents for agent orchestration

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| False positives in detection | Human review threshold for high-severity |
| Repair introduces bugs | Full test suite validation before merge |
| Scope creep during repair | Strict issue-class focus per branch |
| Merge conflicts | Rebase before merge, atomic changes |

## Deliverables

1. `api/agents/qa_sweep/` - QA sweep agent implementations
2. `api/services/qa_sweep_service.py` - Orchestration service
3. `scripts/run_qa_sweep.py` - CLI entry point
4. `tests/unit/test_qa_sweep.py` - Unit tests
5. Documentation in `docs/garden/content/concepts/`
