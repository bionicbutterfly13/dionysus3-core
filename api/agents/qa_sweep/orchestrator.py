"""
QA Sweep Orchestrator

Coordinates the full QA sweep process:
1. Run all analyzer agents
2. Aggregate findings
3. Create repair work orders
4. Spawn repair crews
5. Track progress and report results
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from .models import (
    QAFinding,
    SweepResult,
    RepairWorkOrder,
    IssueClass,
    Severity,
    AnalyzerConfig,
)
from .analyzers import (
    PromiseKeeperAnalyzer,
    OrphanHunterAnalyzer,
    DocAlignmentAnalyzer,
)
from .repair_crew import RepairCrewSpawner


class QASweepOrchestrator:
    """
    Orchestrates the complete QA sweep process.

    Usage:
        orchestrator = QASweepOrchestrator(Path("/path/to/project"))
        result = await orchestrator.run_sweep()
        print(result.summary())
    """

    def __init__(
        self,
        project_root: Path,
        config: Optional[Dict[str, AnalyzerConfig]] = None
    ):
        self.project_root = project_root
        self.config = config or {}

        # Initialize analyzers
        self.analyzers = {
            "promise_keeper": PromiseKeeperAnalyzer(
                self.config.get("promise_keeper", AnalyzerConfig(name="promise_keeper"))
            ),
            "orphan_hunter": OrphanHunterAnalyzer(
                self.config.get("orphan_hunter", AnalyzerConfig(name="orphan_hunter"))
            ),
            "doc_alignment": DocAlignmentAnalyzer(
                self.config.get("doc_alignment", AnalyzerConfig(name="doc_alignment"))
            ),
        }

        # Initialize repair crew spawner
        self.spawner = RepairCrewSpawner(project_root)

        # Current sweep result
        self.current_sweep: Optional[SweepResult] = None

    async def run_sweep(
        self,
        analyzers: Optional[List[str]] = None,
        severity_threshold: Severity = Severity.LOW,
        repair: bool = False,
        dry_run: bool = False
    ) -> SweepResult:
        """
        Run the full QA sweep.

        Args:
            analyzers: List of analyzer names to run (default: all)
            severity_threshold: Minimum severity to report
            repair: Whether to attempt repairs
            dry_run: If True with repair, show what would be repaired

        Returns:
            SweepResult with all findings and repair results
        """
        # Initialize sweep result
        self.current_sweep = SweepResult(
            sweep_id=f"sweep-{uuid.uuid4().hex[:8]}",
            started_at=datetime.now(),
        )

        # Determine which analyzers to run
        analyzer_names = analyzers or list(self.analyzers.keys())

        # Run analyzers
        all_findings = []
        for name in analyzer_names:
            if name not in self.analyzers:
                continue

            analyzer = self.analyzers[name]

            # Update severity threshold
            analyzer.config.severity_threshold = severity_threshold

            # Run analysis
            findings = await analyzer.analyze_codebase(self.project_root)
            all_findings.extend(findings)

        # Count files scanned (estimate based on findings)
        unique_files = set(f.file_path for f in all_findings)
        self.current_sweep.files_scanned = len(unique_files)
        self.current_sweep.findings = all_findings

        # Run repairs if requested
        if repair and all_findings:
            await self._run_repairs(dry_run)

        self.current_sweep.completed_at = datetime.now()
        return self.current_sweep

    async def _run_repairs(self, dry_run: bool = False) -> None:
        """Run repair process on findings."""
        # Create work orders
        work_orders = self.spawner.create_work_orders(
            self.current_sweep.findings,
            batch_size=5  # Smaller batches for safety
        )
        self.current_sweep.work_orders = work_orders

        # Execute work orders
        results = await self.spawner.execute_all(work_orders, dry_run)

        # Update sweep result
        for result in results:
            if result.status.value == "completed":
                self.current_sweep.repairs_succeeded += len(result.findings)
            elif result.status.value == "failed":
                self.current_sweep.repairs_failed += len(result.findings)
            self.current_sweep.repairs_attempted += len(result.findings)

    async def run_single_analyzer(
        self,
        analyzer_name: str,
        severity_threshold: Severity = Severity.LOW
    ) -> List[QAFinding]:
        """Run a single analyzer and return findings."""
        if analyzer_name not in self.analyzers:
            raise ValueError(f"Unknown analyzer: {analyzer_name}")

        analyzer = self.analyzers[analyzer_name]
        analyzer.config.severity_threshold = severity_threshold

        return await analyzer.analyze_codebase(self.project_root)

    def get_findings_by_file(self) -> Dict[str, List[QAFinding]]:
        """Get findings grouped by file."""
        if not self.current_sweep:
            return {}

        by_file = {}
        for finding in self.current_sweep.findings:
            if finding.file_path not in by_file:
                by_file[finding.file_path] = []
            by_file[finding.file_path].append(finding)

        return by_file

    def get_findings_by_severity(self) -> Dict[Severity, List[QAFinding]]:
        """Get findings grouped by severity."""
        if not self.current_sweep:
            return {}

        by_severity = {s: [] for s in Severity}
        for finding in self.current_sweep.findings:
            by_severity[finding.severity].append(finding)

        return by_severity

    def generate_report(self, format: str = "text") -> str:
        """
        Generate a report of the sweep results.

        Args:
            format: Output format ("text" or "markdown")

        Returns:
            Formatted report string
        """
        if not self.current_sweep:
            return "No sweep has been run yet."

        summary = self.current_sweep.summary()

        if format == "markdown":
            return self._format_markdown_report(summary)
        else:
            return self._format_text_report(summary)

    def _format_text_report(self, summary: dict) -> str:
        """Format report as plain text."""
        lines = [
            "=" * 60,
            f"QA Sweep Report: {summary['sweep_id']}",
            "=" * 60,
            "",
            f"Files Scanned: {summary['files_scanned']}",
            f"Total Findings: {summary['total_findings']}",
            "",
            "Findings by Class:",
        ]

        for cls, count in summary["by_class"].items():
            lines.append(f"  - {cls}: {count}")

        lines.extend([
            "",
            "Findings by Severity:",
        ])

        for sev, count in summary["by_severity"].items():
            lines.append(f"  - {sev}: {count}")

        if summary["work_orders"] > 0:
            lines.extend([
                "",
                "Repair Summary:",
                f"  - Work Orders: {summary['work_orders']}",
                f"  - Attempted: {summary['repairs']['attempted']}",
                f"  - Succeeded: {summary['repairs']['succeeded']}",
                f"  - Failed: {summary['repairs']['failed']}",
            ])

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_markdown_report(self, summary: dict) -> str:
        """Format report as markdown."""
        lines = [
            f"# QA Sweep Report: {summary['sweep_id']}",
            "",
            "## Summary",
            "",
            f"- **Files Scanned**: {summary['files_scanned']}",
            f"- **Total Findings**: {summary['total_findings']}",
            "",
            "## Findings by Class",
            "",
            "| Issue Class | Count |",
            "|-------------|-------|",
        ]

        for cls, count in summary["by_class"].items():
            lines.append(f"| {cls} | {count} |")

        lines.extend([
            "",
            "## Findings by Severity",
            "",
            "| Severity | Count |",
            "|----------|-------|",
        ])

        for sev, count in summary["by_severity"].items():
            lines.append(f"| {sev} | {count} |")

        if summary["work_orders"] > 0:
            lines.extend([
                "",
                "## Repair Summary",
                "",
                f"- **Work Orders Created**: {summary['work_orders']}",
                f"- **Repairs Attempted**: {summary['repairs']['attempted']}",
                f"- **Repairs Succeeded**: {summary['repairs']['succeeded']}",
                f"- **Repairs Failed**: {summary['repairs']['failed']}",
            ])

        return "\n".join(lines)


# Convenience function for quick scans
async def quick_scan(
    project_root: Path,
    severity: Severity = Severity.MEDIUM
) -> List[QAFinding]:
    """
    Quick scan without repair.

    Args:
        project_root: Path to project
        severity: Minimum severity threshold

    Returns:
        List of findings
    """
    orchestrator = QASweepOrchestrator(project_root)
    result = await orchestrator.run_sweep(severity_threshold=severity)
    return result.findings
