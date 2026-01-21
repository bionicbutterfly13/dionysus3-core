"""
Base Analyzer Agent

Common patterns and utilities for QA analyzer agents.
"""

import ast
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Generator
from datetime import datetime

from ..models import QAFinding, Severity, IssueClass, AnalyzerConfig


class BaseAnalyzer(ABC):
    """Base class for QA analyzer agents."""

    name: str = "base_analyzer"
    issue_class: IssueClass = IssueClass.BROKEN_PROMISE

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or AnalyzerConfig(name=self.name)
        self.findings: List[QAFinding] = []

    @abstractmethod
    async def analyze_file(self, file_path: Path, content: str) -> List[QAFinding]:
        """Analyze a single file for issues."""
        pass

    async def analyze_codebase(self, root: Path) -> List[QAFinding]:
        """Analyze all matching files in the codebase."""
        self.findings = []

        for file_path in self._iter_files(root):
            if len(self.findings) >= self.config.max_findings:
                break

            try:
                content = file_path.read_text(encoding="utf-8")
                file_findings = await self.analyze_file(file_path, content)
                self.findings.extend(file_findings)
            except Exception as e:
                self._add_finding(
                    file_path=str(file_path),
                    line_number=0,
                    severity=Severity.LOW,
                    title=f"Analysis error: {type(e).__name__}",
                    description=f"Could not analyze file: {e}",
                    context="",
                )

        return self.findings

    def _iter_files(self, root: Path) -> Generator[Path, None, None]:
        """Iterate over files matching configured patterns."""
        import fnmatch

        for pattern in self.config.file_patterns:
            # Handle glob patterns properly
            # rglob needs just the filename pattern, e.g., "*.py"
            if "**" in pattern:
                glob_pattern = pattern.replace("**/", "")
            else:
                glob_pattern = pattern

            for file_path in root.rglob(glob_pattern):
                if not file_path.is_file():
                    continue

                # Check exclude patterns
                rel_path = str(file_path.relative_to(root))
                excluded = any(
                    fnmatch.fnmatch(rel_path, ex.replace("**/", "")) or
                    fnmatch.fnmatch(file_path.name, ex.replace("**/", ""))
                    for ex in self.config.exclude_patterns
                )
                if excluded:
                    continue

                yield file_path

    def _add_finding(
        self,
        file_path: str,
        line_number: int,
        severity: Severity,
        title: str,
        description: str,
        context: str,
        line_end: Optional[int] = None,
        suggested_fix: Optional[str] = None,
    ) -> QAFinding:
        """Create and add a finding."""
        if severity.value < self.config.severity_threshold.value:
            return None

        finding = QAFinding(
            id=f"{self.name}-{uuid.uuid4().hex[:8]}",
            file_path=file_path,
            line_number=line_number,
            line_end=line_end,
            issue_class=self.issue_class,
            severity=severity,
            title=title,
            description=description,
            context=context,
            suggested_fix=suggested_fix,
            analyzer=self.name,
            detected_at=datetime.now(),
        )
        self.findings.append(finding)
        return finding

    def _get_context(self, content: str, line_number: int, context_lines: int = 3) -> str:
        """Extract context around a line number."""
        lines = content.splitlines()
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        context_parts = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            context_parts.append(f"{prefix}{i + 1}: {lines[i]}")

        return "\n".join(context_parts)

    def _parse_ast(self, content: str) -> Optional[ast.Module]:
        """Parse Python content into AST."""
        try:
            return ast.parse(content)
        except SyntaxError:
            return None


class PatternMatcher:
    """Utility for regex-based pattern matching in code."""

    @staticmethod
    def find_comments(content: str, patterns: List[str]) -> List[tuple]:
        """Find comments matching patterns. Returns (line_num, match, line_content)."""
        results = []
        for i, line in enumerate(content.splitlines(), 1):
            for pattern in patterns:
                if match := re.search(pattern, line, re.IGNORECASE):
                    results.append((i, match.group(0), line.strip()))
        return results

    @staticmethod
    def find_pattern(content: str, pattern: str) -> List[tuple]:
        """Find all matches of a pattern. Returns (line_num, match, line_content)."""
        results = []
        for i, line in enumerate(content.splitlines(), 1):
            if match := re.search(pattern, line):
                results.append((i, match.group(0), line.strip()))
        return results
