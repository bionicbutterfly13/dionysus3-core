# Track 074: Codebase QA Sweep - Implementation Plan

## Phase 0: Foundation Setup
**Goal**: Create directory structure and base classes

### Tasks
- [x] T074-001: Create `api/agents/qa_sweep/` directory structure
- [x] T074-002: Create `QAFinding` Pydantic model for issue representation
- [x] T074-003: Create `RepairWorkOrder` Pydantic model for repair tasks
- [x] T074-004: Create base `QAAnalyzerAgent` class with common patterns
- [x] T074-005: Create `QASweepOrchestrator` skeleton

## Phase 1: Analyzer Agents
**Goal**: Implement expert-level detection agents

### Tasks
- [x] T074-010: Implement `PromiseKeeperAnalyzer` agent
  - Detect TODO/FIXME/XXX/HACK comments
  - Find stub methods (NotImplementedError, pass statements)
  - Identify incomplete implementations
  - Parse docstrings for unfulfilled claims

- [x] T074-011: Implement `OrphanHunterAnalyzer` agent
  - Detect unused imports
  - Find unreferenced functions/classes
  - Identify dead code blocks
  - Check for orphan test files

- [x] T074-012: Implement `DocAlignmentAnalyzer` agent
  - Compare docstring params vs actual params
  - Verify return type claims
  - Check README accuracy
  - Validate example code

- [x] T074-013: Write unit tests for all analyzers

## Phase 2: Issue Aggregation
**Goal**: Collect and prioritize findings

### Tasks
- [x] T074-020: Create `IssueRegistry` class (implemented in SweepResult)
  - Store findings by class (promise, orphan, doc)
  - Track severity levels
  - Support querying by file/severity/class

- [x] T074-021: Implement severity scoring algorithm
  - Critical: Security issues, API contract violations
  - High: Broken core functionality, public API misalignment
  - Medium: Internal misalignment, incomplete features
  - Low: Style issues, minor TODOs

- [x] T074-022: Create work order generator
  - Group related issues
  - Estimate risk and effort
  - Generate dependency graph

## Phase 3: Repair Crew System
**Goal**: Implement autonomous repair agents

### Tasks
- [x] T074-030: Create `RepairCrewSpawner` service
  - Branch creation: `fix/qa-{class}-{timestamp}`
  - Agent selection based on issue class
  - Parallel execution for independent repairs

- [x] T074-031: Implement `PromiseFulfillerAgent`
  - Complete TODO items (with LLM generation)
  - Implement stub methods
  - Add missing functionality

- [x] T074-032: Implement `CodeCleanerAgent`
  - Safe removal of dead code
  - Import cleanup
  - Deprecated code removal

- [x] T074-033: Implement `DocSynchronizerAgent`
  - Update docstrings to match implementation
  - Fix README sections
  - Correct example code

- [x] T074-034: Implement paired `DocumentationAgent`
  - Auto-generate docstrings for changes
  - Update README for architectural changes
  - Create migration notes

## Phase 4: Validation & Merge
**Goal**: Ensure quality and automate merging

### Tasks
- [x] T074-040: Create `ValidationAgent`
  - Run affected tests
  - Check for regressions
  - Verify documentation accuracy

- [x] T074-041: Implement auto-merge workflow
  - Full test suite validation
  - PR creation with findings summary
  - Auto-merge on green CI

- [x] T074-042: Create rollback capability
  - Track all changes per repair
  - Enable selective rollback

## Phase 5: Orchestration Service
**Goal**: Wire everything together

### Tasks
- [x] T074-050: Complete `QASweepOrchestrator` implementation
  - Coordinate analyzer execution
  - Manage repair crew spawning
  - Track overall progress

- [ ] T074-051: Create `api/services/qa_sweep_service.py`
  - FastAPI integration
  - Status reporting
  - Manual override capabilities

- [x] T074-052: Create CLI entry point `scripts/run_qa_sweep.py`
  - Full sweep mode
  - Single analyzer mode
  - Dry-run mode

## Phase 6: Testing & Documentation
**Goal**: Comprehensive testing and docs

### Tasks
- [x] T074-060: Write integration tests
  - End-to-end sweep on test codebase
  - Repair verification
  - Merge workflow

- [ ] T074-061: Write documentation
  - Usage guide
  - Agent descriptions
  - Configuration options

- [ ] T074-062: Create silver bullet pages
  - `docs/garden/content/silver-bullets/concepts/qa-sweep.md`
  - `docs/garden/content/silver-bullets/concepts/repair-crews.md`

## Implementation Notes

### Agent Pattern (smolagents)

```python
from smolagents import ToolCallingAgent
from api.services.llm_service import get_router_model

class QAAnalyzerAgent:
    def __init__(self, model_id: str = "dionysus-agents"):
        self.model = get_router_model(model_id)
        self.agent = ToolCallingAgent(
            tools=self._get_tools(),
            model=self.model,
            max_steps=20,
            name="qa_analyzer",
            description="Expert QA analyzer for codebase issues"
        )

    async def analyze(self, files: List[str]) -> List[QAFinding]:
        # Implementation
        pass
```

### Repair Branch Pattern

```python
import subprocess
from datetime import datetime

def create_repair_branch(issue_class: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"fix/qa-{issue_class}-{timestamp}"
    subprocess.run(["git", "checkout", "-b", branch_name])
    return branch_name

def merge_repair_branch(branch_name: str) -> bool:
    # Run tests
    result = subprocess.run(["python", "-m", "pytest", "tests/unit/", "-v"])
    if result.returncode != 0:
        return False

    # Merge
    subprocess.run(["git", "checkout", "main"])
    subprocess.run(["git", "merge", branch_name])
    subprocess.run(["git", "branch", "-d", branch_name])
    return True
```

### Finding Model

```python
from pydantic import BaseModel
from enum import Enum
from typing import Optional

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IssueClass(str, Enum):
    BROKEN_PROMISE = "broken_promise"
    ORPHAN_CODE = "orphan_code"
    DOC_MISALIGNMENT = "doc_misalignment"

class QAFinding(BaseModel):
    file_path: str
    line_number: int
    issue_class: IssueClass
    severity: Severity
    description: str
    context: str
    suggested_fix: Optional[str] = None
```

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| False positive repairs | Medium | High | Human review threshold |
| Test failures from repairs | Medium | Medium | Atomic commits, easy rollback |
| Merge conflicts | Low | Medium | Rebase before merge |
| LLM hallucination in repairs | Medium | High | Validation agent checks |

## Success Metrics

1. **Detection Coverage**: >90% of manually identified issues found
2. **Repair Success Rate**: >80% of repairs compile and pass tests
3. **Zero Regressions**: No new test failures introduced
4. **Documentation Sync**: 100% of repairs have corresponding doc updates

## Phase Checkpoints

- **Phase 1 Complete**: All analyzers detect issues correctly (unit tests pass) ✓
- **Phase 3 Complete**: Repair agents can fix issues on branches ✓
- **Phase 5 Complete**: Full sweep runs end-to-end with merge ✓
