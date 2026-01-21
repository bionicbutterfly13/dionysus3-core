"""
Unit tests for QA Sweep system.

Tests analyzer agents, repair crews, and orchestrator.
"""

import pytest
import tempfile
from pathlib import Path
from textwrap import dedent

from api.agents.qa_sweep.models import (
    QAFinding,
    RepairWorkOrder,
    Severity,
    IssueClass,
    RepairStatus,
    SweepResult,
)
from api.agents.qa_sweep.analyzers import (
    PromiseKeeperAnalyzer,
    OrphanHunterAnalyzer,
    DocAlignmentAnalyzer,
)
from api.agents.qa_sweep.orchestrator import QASweepOrchestrator


# ============================================================================
# Model Tests
# ============================================================================


class TestQAFinding:
    """Tests for QAFinding model."""

    def test_finding_creation(self):
        """Test creating a QA finding."""
        finding = QAFinding(
            id="test-001",
            file_path="/test/file.py",
            line_number=10,
            issue_class=IssueClass.BROKEN_PROMISE,
            severity=Severity.HIGH,
            title="Test finding",
            description="A test finding",
            context="def test(): pass",
            analyzer="test_analyzer",
        )

        assert finding.id == "test-001"
        assert finding.severity == Severity.HIGH
        assert finding.issue_class == IssueClass.BROKEN_PROMISE

    def test_finding_summary(self):
        """Test finding summary generation."""
        finding = QAFinding(
            id="test-002",
            file_path="src/module.py",
            line_number=42,
            issue_class=IssueClass.ORPHAN_CODE,
            severity=Severity.MEDIUM,
            title="Unused import",
            description="Import never used",
            context="import os",
            analyzer="orphan_hunter",
        )

        summary = finding.to_summary()
        assert "MEDIUM" in summary
        assert "src/module.py:42" in summary
        assert "Unused import" in summary


class TestRepairWorkOrder:
    """Tests for RepairWorkOrder model."""

    def test_work_order_creation(self):
        """Test creating a work order."""
        findings = [
            QAFinding(
                id="f1",
                file_path="test.py",
                line_number=1,
                issue_class=IssueClass.BROKEN_PROMISE,
                severity=Severity.HIGH,
                title="TODO",
                description="TODO item",
                context="# TODO: fix",
                analyzer="promise_keeper",
            ),
            QAFinding(
                id="f2",
                file_path="test.py",
                line_number=5,
                issue_class=IssueClass.BROKEN_PROMISE,
                severity=Severity.MEDIUM,
                title="FIXME",
                description="FIXME item",
                context="# FIXME: fix",
                analyzer="promise_keeper",
            ),
        ]

        work_order = RepairWorkOrder(
            id="wo-001",
            issue_class=IssueClass.BROKEN_PROMISE,
            findings=findings,
        )

        assert work_order.status == RepairStatus.PENDING
        assert len(work_order.findings) == 2

    def test_severity_score(self):
        """Test severity scoring calculation."""
        findings = [
            QAFinding(
                id="f1",
                file_path="test.py",
                line_number=1,
                issue_class=IssueClass.BROKEN_PROMISE,
                severity=Severity.CRITICAL,
                title="Critical issue",
                description="Critical",
                context="",
                analyzer="test",
            ),
            QAFinding(
                id="f2",
                file_path="test.py",
                line_number=2,
                issue_class=IssueClass.BROKEN_PROMISE,
                severity=Severity.LOW,
                title="Low issue",
                description="Low",
                context="",
                analyzer="test",
            ),
        ]

        work_order = RepairWorkOrder(
            id="wo-002",
            issue_class=IssueClass.BROKEN_PROMISE,
            findings=findings,
        )

        score = work_order.severity_score()
        assert score == 105  # 100 (critical) + 5 (low)


class TestSweepResult:
    """Tests for SweepResult model."""

    def test_summary(self):
        """Test sweep result summary."""
        result = SweepResult(
            sweep_id="sweep-001",
            files_scanned=50,
            findings=[
                QAFinding(
                    id="f1",
                    file_path="a.py",
                    line_number=1,
                    issue_class=IssueClass.BROKEN_PROMISE,
                    severity=Severity.HIGH,
                    title="TODO",
                    description="",
                    context="",
                    analyzer="test",
                ),
                QAFinding(
                    id="f2",
                    file_path="b.py",
                    line_number=1,
                    issue_class=IssueClass.ORPHAN_CODE,
                    severity=Severity.LOW,
                    title="Unused",
                    description="",
                    context="",
                    analyzer="test",
                ),
            ],
            repairs_attempted=2,
            repairs_succeeded=1,
            repairs_failed=1,
        )

        summary = result.summary()
        assert summary["files_scanned"] == 50
        assert summary["total_findings"] == 2
        assert summary["by_class"]["broken_promise"] == 1
        assert summary["by_class"]["orphan_code"] == 1
        assert summary["repairs"]["succeeded"] == 1


# ============================================================================
# Analyzer Tests
# ============================================================================


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestPromiseKeeperAnalyzer:
    """Tests for PromiseKeeperAnalyzer."""

    @pytest.mark.asyncio
    async def test_finds_todo_comments(self, temp_project):
        """Test detection of TODO comments."""
        test_file = temp_project / "test_module.py"
        test_file.write_text(dedent("""
            def my_function():
                # TODO: implement this
                pass

            def other_function():
                return 42  # FIXME: wrong value
        """))

        analyzer = PromiseKeeperAnalyzer()
        findings = await analyzer.analyze_file(test_file, test_file.read_text())

        todo_findings = [f for f in findings if "TODO" in f.title]
        fixme_findings = [f for f in findings if "FIXME" in f.title]

        assert len(todo_findings) >= 1
        assert len(fixme_findings) >= 1

    @pytest.mark.asyncio
    async def test_finds_stub_methods(self, temp_project):
        """Test detection of stub methods."""
        test_file = temp_project / "stubs.py"
        test_file.write_text(dedent("""
            class MyClass:
                def not_implemented(self):
                    raise NotImplementedError("Coming soon")

                def empty_method(self):
                    pass
        """))

        analyzer = PromiseKeeperAnalyzer()
        findings = await analyzer.analyze_file(test_file, test_file.read_text())

        stub_findings = [f for f in findings if "Stub" in f.title or "Empty" in f.title]
        assert len(stub_findings) >= 1


class TestOrphanHunterAnalyzer:
    """Tests for OrphanHunterAnalyzer."""

    @pytest.mark.asyncio
    async def test_finds_unused_imports(self, temp_project):
        """Test detection of unused imports."""
        test_file = temp_project / "imports.py"
        test_file.write_text(dedent("""
            import os
            import sys
            import json

            def use_sys():
                return sys.version
        """))

        analyzer = OrphanHunterAnalyzer()
        findings = await analyzer.analyze_file(test_file, test_file.read_text())

        unused = [f for f in findings if "Unused import" in f.title]
        # os and json should be flagged as unused
        assert len(unused) >= 2

    @pytest.mark.asyncio
    async def test_finds_commented_code(self, temp_project):
        """Test detection of commented-out code blocks."""
        test_file = temp_project / "commented.py"
        test_file.write_text(dedent("""
            def active_function():
                return True

            # def old_function():
            #     x = 1
            #     y = 2
            #     return x + y

            def another_active():
                return False
        """))

        analyzer = OrphanHunterAnalyzer()
        findings = await analyzer.analyze_file(test_file, test_file.read_text())

        commented = [f for f in findings if "Commented-out" in f.title]
        assert len(commented) >= 1


class TestDocAlignmentAnalyzer:
    """Tests for DocAlignmentAnalyzer."""

    @pytest.mark.asyncio
    async def test_finds_phantom_params(self, temp_project):
        """Test detection of documented params that don't exist."""
        test_file = temp_project / "docs.py"
        test_file.write_text(dedent('''
            def my_function(a, b):
                """Do something.

                Args:
                    a: First arg
                    b: Second arg
                    c: Third arg that doesn't exist
                """
                return a + b
        '''))

        analyzer = DocAlignmentAnalyzer()
        findings = await analyzer.analyze_file(test_file, test_file.read_text())

        phantom = [f for f in findings if "Phantom" in f.title]
        assert len(phantom) >= 1

    @pytest.mark.asyncio
    async def test_finds_missing_docstrings(self, temp_project):
        """Test detection of missing docstrings."""
        test_file = temp_project / "no_docs.py"
        test_file.write_text(dedent("""
            def public_function():
                return 42

            class PublicClass:
                def method(self):
                    pass
        """))

        analyzer = DocAlignmentAnalyzer()
        findings = await analyzer.analyze_file(test_file, test_file.read_text())

        missing = [f for f in findings if "Missing docstring" in f.title]
        assert len(missing) >= 2  # function and class


# ============================================================================
# Orchestrator Tests
# ============================================================================


class TestQASweepOrchestrator:
    """Tests for QASweepOrchestrator."""

    @pytest.mark.asyncio
    async def test_run_sweep(self, temp_project):
        """Test running a full sweep."""
        # Create test files
        (temp_project / "module.py").write_text(dedent("""
            import os  # unused

            def my_function():
                # TODO: implement
                pass
        """))

        orchestrator = QASweepOrchestrator(temp_project)
        result = await orchestrator.run_sweep()

        assert result.sweep_id.startswith("sweep-")
        assert result.files_scanned >= 1
        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_generate_report(self, temp_project):
        """Test report generation."""
        (temp_project / "test.py").write_text("# TODO: test")

        orchestrator = QASweepOrchestrator(temp_project)
        await orchestrator.run_sweep()

        # Text report
        text_report = orchestrator.generate_report(format="text")
        assert "QA Sweep Report" in text_report

        # Markdown report
        md_report = orchestrator.generate_report(format="markdown")
        assert "# QA Sweep Report" in md_report

    @pytest.mark.asyncio
    async def test_single_analyzer(self, temp_project):
        """Test running a single analyzer."""
        (temp_project / "test.py").write_text("import unused\n# TODO: fix")

        orchestrator = QASweepOrchestrator(temp_project)
        findings = await orchestrator.run_single_analyzer("promise_keeper")

        # Should only find TODO, not unused import
        assert all(f.analyzer == "promise_keeper" for f in findings)


# ============================================================================
# Integration Tests
# ============================================================================


class TestQASweepIntegration:
    """Integration tests for QA sweep system."""

    @pytest.mark.asyncio
    async def test_full_workflow_dry_run(self, temp_project):
        """Test full workflow in dry-run mode."""
        # Create test files with various issues
        (temp_project / "main.py").write_text(dedent("""
            import os
            import sys  # actually used

            def process():
                '''Process data.

                Returns:
                    dict: Processed result
                '''
                # TODO: implement processing
                pass

            def helper():
                return sys.version
        """))

        orchestrator = QASweepOrchestrator(temp_project)

        # Run with repair in dry-run mode
        result = await orchestrator.run_sweep(
            severity_threshold=Severity.LOW,
            repair=True,
            dry_run=True
        )

        # Should find issues but not actually repair
        assert len(result.findings) >= 1
        summary = result.summary()
        assert "by_class" in summary

    @pytest.mark.asyncio
    async def test_severity_filtering(self, temp_project):
        """Test severity threshold filtering."""
        (temp_project / "test.py").write_text(dedent("""
            # TODO: low priority
            # FIXME: high priority
        """))

        orchestrator = QASweepOrchestrator(temp_project)

        # High severity only
        result_high = await orchestrator.run_sweep(severity_threshold=Severity.HIGH)
        high_findings = [f for f in result_high.findings if f.severity == Severity.HIGH]

        # All severities
        result_all = await orchestrator.run_sweep(severity_threshold=Severity.LOW)

        # Should have more findings with lower threshold
        assert len(result_all.findings) >= len(high_findings)
