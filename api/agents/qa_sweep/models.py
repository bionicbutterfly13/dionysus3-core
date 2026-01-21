"""
QA Sweep Data Models

Pydantic v2 models for QA findings, repair work orders, and sweep results.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for QA findings."""
    CRITICAL = "critical"  # Security issues, API contract violations
    HIGH = "high"          # Broken core functionality, public API misalignment
    MEDIUM = "medium"      # Internal misalignment, incomplete features
    LOW = "low"            # Style issues, minor TODOs


class IssueClass(str, Enum):
    """Categories of QA issues."""
    BROKEN_PROMISE = "broken_promise"    # TODOs, stubs, incomplete impls
    ORPHAN_CODE = "orphan_code"          # Dead code, unused imports
    DOC_MISALIGNMENT = "doc_misalignment"  # Docs don't match code


class RepairStatus(str, Enum):
    """Status of repair work orders."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class QAFinding(BaseModel):
    """A single QA issue found during sweep."""

    id: str = Field(description="Unique identifier for tracking")
    file_path: str = Field(description="Path to the file containing the issue")
    line_number: int = Field(description="Line number where issue starts")
    line_end: Optional[int] = Field(default=None, description="Line number where issue ends")
    issue_class: IssueClass = Field(description="Category of the issue")
    severity: Severity = Field(description="Severity level")
    title: str = Field(description="Short summary of the issue")
    description: str = Field(description="Detailed description of the issue")
    context: str = Field(description="Code snippet showing the issue")
    suggested_fix: Optional[str] = Field(default=None, description="Suggested remediation")
    analyzer: str = Field(description="Name of analyzer that found this")
    detected_at: datetime = Field(default_factory=datetime.now)

    def to_summary(self) -> str:
        """Return a one-line summary for reporting."""
        return f"[{self.severity.value.upper()}] {self.file_path}:{self.line_number} - {self.title}"


class RepairWorkOrder(BaseModel):
    """Work order for a repair crew."""

    id: str = Field(description="Unique work order ID")
    issue_class: IssueClass = Field(description="Class of issues to repair")
    findings: List[QAFinding] = Field(default_factory=list, description="Findings to address")
    branch_name: Optional[str] = Field(default=None, description="Git branch for repairs")
    status: RepairStatus = Field(default=RepairStatus.PENDING)

    repair_agent: Optional[str] = Field(default=None, description="Agent handling repairs")
    doc_agent: Optional[str] = Field(default=None, description="Agent handling docs")

    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    commits: List[str] = Field(default_factory=list, description="Commit SHAs for repairs")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")

    def severity_score(self) -> int:
        """Calculate priority score based on severity of findings."""
        scores = {
            Severity.CRITICAL: 100,
            Severity.HIGH: 50,
            Severity.MEDIUM: 20,
            Severity.LOW: 5,
        }
        return sum(scores.get(f.severity, 0) for f in self.findings)


class SweepResult(BaseModel):
    """Result of a full QA sweep."""

    sweep_id: str = Field(description="Unique sweep ID")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)

    files_scanned: int = Field(default=0)
    findings: List[QAFinding] = Field(default_factory=list)
    work_orders: List[RepairWorkOrder] = Field(default_factory=list)

    repairs_attempted: int = Field(default=0)
    repairs_succeeded: int = Field(default=0)
    repairs_failed: int = Field(default=0)

    def summary(self) -> dict:
        """Return summary statistics."""
        by_class = {}
        by_severity = {}
        for f in self.findings:
            by_class[f.issue_class.value] = by_class.get(f.issue_class.value, 0) + 1
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1

        return {
            "sweep_id": self.sweep_id,
            "files_scanned": self.files_scanned,
            "total_findings": len(self.findings),
            "by_class": by_class,
            "by_severity": by_severity,
            "work_orders": len(self.work_orders),
            "repairs": {
                "attempted": self.repairs_attempted,
                "succeeded": self.repairs_succeeded,
                "failed": self.repairs_failed,
            },
        }


class AnalyzerConfig(BaseModel):
    """Configuration for an analyzer agent."""

    name: str
    enabled: bool = True
    severity_threshold: Severity = Severity.LOW  # Minimum severity to report
    file_patterns: List[str] = Field(default_factory=lambda: ["**/*.py"])
    exclude_patterns: List[str] = Field(default_factory=lambda: [
        "**/test_*.py",
        "**/__pycache__/**",
        "**/.venv/**",
        "**/venv/**",
        "**/marker-env/**",
        "**/node_modules/**",
        "**/site-packages/**",
        "**/.git/**",
        "**/dionysus-ralph-orchestrator/**",
        "**/build/**",
        "**/dist/**",
        "**/*.egg-info/**",
        "**/.checkpoints/**",
        "**/notebooklm-mcp/**",
        "**/dionysus-dashboard/**",
        "**/research/**",
    ])
    max_findings: int = Field(default=1000, description="Max findings per analyzer")
