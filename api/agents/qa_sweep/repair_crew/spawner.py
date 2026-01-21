"""
Repair Crew Spawner

Orchestrates the repair process:
1. Creates feature branches for each issue class
2. Spawns appropriate repair + documentation agents
3. Validates repairs
4. Merges when tests pass
"""

import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from ..models import (
    QAFinding,
    RepairWorkOrder,
    IssueClass,
    RepairStatus,
)
from .repair_agents import (
    BaseRepairAgent,
    PromiseFulfillerAgent,
    CodeCleanerAgent,
    DocSynchronizerAgent,
)
from .documentation_agent import DocumentationAgent
from .validator import ValidationAgent


class RepairCrewSpawner:
    """
    Spawns and coordinates repair crews.

    Each repair crew consists of:
    - Expert repair agent (matched to issue class)
    - Documentation agent (paired)
    - Validation agent (shared)
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.work_orders: List[RepairWorkOrder] = []
        self.original_branch: Optional[str] = None

    def _get_current_branch(self) -> str:
        """Get current git branch name."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        return result.stdout.strip()

    def _create_branch(self, issue_class: IssueClass) -> str:
        """Create a feature branch for repairs."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"fix/qa-{issue_class.value}-{timestamp}"

        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            cwd=str(self.project_root)
        )

        return branch_name

    def _switch_branch(self, branch_name: str) -> bool:
        """Switch to a branch."""
        result = subprocess.run(
            ["git", "checkout", branch_name],
            capture_output=True,
            cwd=str(self.project_root)
        )
        return result.returncode == 0

    def _commit_changes(self, message: str, files: List[str]) -> Optional[str]:
        """Commit changes and return commit SHA."""
        # Stage files
        for file_path in files:
            subprocess.run(
                ["git", "add", file_path],
                capture_output=True,
                cwd=str(self.project_root)
            )

        # Commit with authorship
        commit_message = f"""{message}

AUTHOR Mani Saint-Victor, MD"""

        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )

        if result.returncode == 0:
            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            return sha_result.stdout.strip()[:8]

        return None

    def _merge_branch(self, branch_name: str, target: str = "main") -> bool:
        """Merge branch into target."""
        # Switch to target
        subprocess.run(
            ["git", "checkout", target],
            capture_output=True,
            cwd=str(self.project_root)
        )

        # Merge
        result = subprocess.run(
            ["git", "merge", branch_name, "--no-ff", "-m", f"Merge {branch_name}"],
            capture_output=True,
            cwd=str(self.project_root)
        )

        if result.returncode == 0:
            # Delete branch
            subprocess.run(
                ["git", "branch", "-d", branch_name],
                capture_output=True,
                cwd=str(self.project_root)
            )
            return True

        return False

    def _get_repair_agent(self, issue_class: IssueClass) -> BaseRepairAgent:
        """Get the appropriate repair agent for an issue class."""
        agents = {
            IssueClass.BROKEN_PROMISE: PromiseFulfillerAgent,
            IssueClass.ORPHAN_CODE: CodeCleanerAgent,
            IssueClass.DOC_MISALIGNMENT: DocSynchronizerAgent,
        }
        return agents[issue_class]()

    def create_work_orders(
        self,
        findings: List[QAFinding],
        batch_size: int = 10
    ) -> List[RepairWorkOrder]:
        """
        Create work orders from findings.

        Groups findings by issue class and creates work orders for each batch.
        """
        # Group by issue class
        by_class: Dict[IssueClass, List[QAFinding]] = {}
        for finding in findings:
            if finding.issue_class not in by_class:
                by_class[finding.issue_class] = []
            by_class[finding.issue_class].append(finding)

        # Create work orders
        work_orders = []
        for issue_class, class_findings in by_class.items():
            # Sort by severity (most severe first)
            class_findings.sort(
                key=lambda f: ["critical", "high", "medium", "low"].index(f.severity.value)
            )

            # Batch into work orders
            for i in range(0, len(class_findings), batch_size):
                batch = class_findings[i:i + batch_size]
                work_order = RepairWorkOrder(
                    id=f"wo-{uuid.uuid4().hex[:8]}",
                    issue_class=issue_class,
                    findings=batch,
                    status=RepairStatus.PENDING,
                )
                work_orders.append(work_order)

        self.work_orders = work_orders
        return work_orders

    async def execute_work_order(
        self,
        work_order: RepairWorkOrder,
        dry_run: bool = False
    ) -> RepairWorkOrder:
        """
        Execute a single work order.

        Args:
            work_order: The work order to execute
            dry_run: If True, don't actually make changes

        Returns:
            Updated work order with results
        """
        # Save original branch
        self.original_branch = self._get_current_branch()

        # Update status
        work_order.status = RepairStatus.IN_PROGRESS
        work_order.started_at = datetime.now()

        if not dry_run:
            # Create branch
            work_order.branch_name = self._create_branch(work_order.issue_class)

        # Get agents
        repair_agent = self._get_repair_agent(work_order.issue_class)
        doc_agent = DocumentationAgent(self.project_root)
        validator = ValidationAgent(self.project_root)

        work_order.repair_agent = repair_agent.name
        work_order.doc_agent = doc_agent.name

        # Execute repairs
        repaired_files = []
        for finding in work_order.findings:
            if dry_run:
                print(f"[DRY RUN] Would repair: {finding.to_summary()}")
                continue

            success, description = await repair_agent.repair(finding)
            if success:
                repaired_files.append(finding.file_path)
                await doc_agent.document_repair(
                    description,
                    finding.file_path,
                    work_order.issue_class.value
                )

        if dry_run:
            work_order.status = RepairStatus.COMPLETED
            work_order.completed_at = datetime.now()
            return work_order

        # Validate repairs
        if repaired_files:
            unique_files = list(set(repaired_files))
            validation_passed, validation_msg = await validator.validate_all(unique_files)

            if validation_passed:
                # Commit changes
                commit_msg = await doc_agent.generate_repair_summary()
                sha = self._commit_changes(commit_msg, unique_files)
                if sha:
                    work_order.commits.append(sha)

                # Merge to original branch
                if self._merge_branch(work_order.branch_name, self.original_branch):
                    work_order.status = RepairStatus.COMPLETED
                else:
                    work_order.status = RepairStatus.FAILED
                    work_order.errors.append("Merge failed")
            else:
                work_order.status = RepairStatus.FAILED
                work_order.errors.append(validation_msg)

                # Return to original branch without merging
                self._switch_branch(self.original_branch)
        else:
            # No repairs made
            work_order.status = RepairStatus.SKIPPED
            self._switch_branch(self.original_branch)
            # Clean up empty branch
            if work_order.branch_name:
                subprocess.run(
                    ["git", "branch", "-D", work_order.branch_name],
                    capture_output=True,
                    cwd=str(self.project_root)
                )

        work_order.completed_at = datetime.now()
        return work_order

    async def execute_all(
        self,
        work_orders: Optional[List[RepairWorkOrder]] = None,
        dry_run: bool = False
    ) -> List[RepairWorkOrder]:
        """Execute all work orders."""
        orders = work_orders or self.work_orders
        results = []

        for work_order in orders:
            result = await self.execute_work_order(work_order, dry_run)
            results.append(result)

        return results

    def get_summary(self) -> dict:
        """Get summary of all work orders."""
        return {
            "total": len(self.work_orders),
            "pending": sum(1 for wo in self.work_orders if wo.status == RepairStatus.PENDING),
            "in_progress": sum(1 for wo in self.work_orders if wo.status == RepairStatus.IN_PROGRESS),
            "completed": sum(1 for wo in self.work_orders if wo.status == RepairStatus.COMPLETED),
            "failed": sum(1 for wo in self.work_orders if wo.status == RepairStatus.FAILED),
            "skipped": sum(1 for wo in self.work_orders if wo.status == RepairStatus.SKIPPED),
            "findings_by_class": {
                ic.value: sum(len(wo.findings) for wo in self.work_orders if wo.issue_class == ic)
                for ic in IssueClass
            },
        }
