"""
Orphan Hunter Analyzer

Detects dead and unreferenced code:
- Unused imports
- Dead functions (defined but never called)
- Unreferenced classes
- Commented-out code blocks
- Deprecated code markers
"""

import ast
import re
from pathlib import Path
from typing import List, Set, Dict

from .base import BaseAnalyzer
from ..models import QAFinding, Severity, IssueClass


class OrphanHunterAnalyzer(BaseAnalyzer):
    """Expert analyzer for orphan/dead code."""

    name = "orphan_hunter"
    issue_class = IssueClass.ORPHAN_CODE

    async def analyze_file(self, file_path: Path, content: str) -> List[QAFinding]:
        """Analyze a file for orphan code."""
        findings = []

        # 1. Find unused imports
        findings.extend(self._find_unused_imports(file_path, content))

        # 2. Find commented-out code blocks
        findings.extend(self._find_commented_code(file_path, content))

        # 3. Find deprecated markers without removal
        findings.extend(self._find_deprecated_code(file_path, content))

        # 4. Find unreferenced private functions (within file)
        findings.extend(self._find_unreferenced_private(file_path, content))

        return findings

    def _find_unused_imports(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find imports that are never used in the file."""
        findings = []
        tree = self._parse_ast(content)
        if not tree:
            return findings

        # Collect all imported names
        imported_names: Dict[str, int] = {}  # name -> line number

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported_names[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        if alias.name == "*":
                            continue  # Skip star imports
                        name = alias.asname or alias.name
                        imported_names[name] = node.lineno

        # Find all Name references in the AST (excluding imports)
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Get the root name of attribute access
                root = node
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    used_names.add(root.id)

        # Check for unused imports
        for name, line_num in imported_names.items():
            if name not in used_names:
                # Check if it's a type annotation import (often used only in TYPE_CHECKING)
                if self._is_type_only_import(content, name):
                    continue

                findings.append(QAFinding(
                    id=f"{self.name}-import-{line_num}",
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_class=self.issue_class,
                    severity=Severity.LOW,
                    title=f"Unused import: {name}",
                    description=f"Import '{name}' is defined but never used",
                    context=self._get_context(content, line_num),
                    suggested_fix=f"Remove unused import '{name}'",
                    analyzer=self.name,
                ))

        return findings

    def _find_commented_code(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find blocks of commented-out code."""
        findings = []
        lines = content.splitlines()

        # Patterns that indicate commented code (not just comments)
        code_patterns = [
            r"^\s*#\s*(def|class|if|for|while|try|with|return|import|from)\s+",
            r"^\s*#\s*\w+\s*=\s*",  # Assignment
            r"^\s*#\s*\w+\.\w+\(",  # Method call
            r"^\s*#\s*@\w+",        # Decorator
        ]

        consecutive_code_comments = 0
        block_start = None

        for i, line in enumerate(lines, 1):
            is_code_comment = any(re.match(p, line) for p in code_patterns)

            if is_code_comment:
                if block_start is None:
                    block_start = i
                consecutive_code_comments += 1
            else:
                if consecutive_code_comments >= 3:
                    findings.append(QAFinding(
                        id=f"{self.name}-commented-{block_start}",
                        file_path=str(file_path),
                        line_number=block_start,
                        line_end=i - 1,
                        issue_class=self.issue_class,
                        severity=Severity.LOW,
                        title=f"Commented-out code block ({consecutive_code_comments} lines)",
                        description="Block of commented-out code detected",
                        context=self._get_context(content, block_start),
                        suggested_fix="Remove commented code or restore if needed",
                        analyzer=self.name,
                    ))
                consecutive_code_comments = 0
                block_start = None

        # Check for trailing block
        if consecutive_code_comments >= 3:
            findings.append(QAFinding(
                id=f"{self.name}-commented-{block_start}",
                file_path=str(file_path),
                line_number=block_start,
                line_end=len(lines),
                issue_class=self.issue_class,
                severity=Severity.LOW,
                title=f"Commented-out code block ({consecutive_code_comments} lines)",
                description="Block of commented-out code detected",
                context=self._get_context(content, block_start),
                suggested_fix="Remove commented code or restore if needed",
                analyzer=self.name,
            ))

        return findings

    def _find_deprecated_code(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find code marked as deprecated."""
        findings = []
        tree = self._parse_ast(content)
        if not tree:
            return findings

        # Check for @deprecated decorators or warnings.warn with DeprecationWarning
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Check decorators
                for decorator in node.decorator_list:
                    dec_name = self._get_decorator_name(decorator)
                    if dec_name and "deprecated" in dec_name.lower():
                        findings.append(QAFinding(
                            id=f"{self.name}-deprecated-{node.lineno}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_class=self.issue_class,
                            severity=Severity.MEDIUM,
                            title=f"Deprecated code: {node.name}",
                            description=f"'{node.name}' is marked deprecated but still present",
                            context=self._get_context(content, node.lineno),
                            suggested_fix="Remove deprecated code or update deprecation plan",
                            analyzer=self.name,
                        ))

        # Check for deprecation warnings in comments
        deprecation_patterns = [
            r"#.*deprecated",
            r"#.*DEPRECATED",
            r"#.*to be removed",
            r"#.*will be removed",
        ]

        for i, line in enumerate(content.splitlines(), 1):
            for pattern in deprecation_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(QAFinding(
                        id=f"{self.name}-deprecated-comment-{i}",
                        file_path=str(file_path),
                        line_number=i,
                        issue_class=self.issue_class,
                        severity=Severity.LOW,
                        title="Deprecation marker in comment",
                        description=f"Code marked for deprecation: {line.strip()}",
                        context=self._get_context(content, i),
                        suggested_fix="Remove deprecated code or track removal timeline",
                        analyzer=self.name,
                    ))
                    break  # One finding per line

        return findings

    def _find_unreferenced_private(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find private functions/methods that are never called within the file."""
        findings = []
        tree = self._parse_ast(content)
        if not tree:
            return findings

        # Collect private function definitions (start with _ but not __)
        private_funcs: Dict[str, int] = {}  # name -> line number

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    private_funcs[node.name] = node.lineno

        # Find all function calls
        called_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)

        # Check for uncalled private functions
        for name, line_num in private_funcs.items():
            if name not in called_names:
                findings.append(QAFinding(
                    id=f"{self.name}-unreferenced-{line_num}",
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_class=self.issue_class,
                    severity=Severity.MEDIUM,
                    title=f"Unreferenced private function: {name}",
                    description=f"Private function '{name}' is never called in this file",
                    context=self._get_context(content, line_num),
                    suggested_fix=f"Remove '{name}' if unused or verify cross-file usage",
                    analyzer=self.name,
                ))

        return findings

    def _is_type_only_import(self, content: str, name: str) -> bool:
        """Check if import is only used for type annotations."""
        # Simple heuristic: check if name appears in TYPE_CHECKING block
        if "TYPE_CHECKING" in content:
            type_checking_pattern = rf"if\s+TYPE_CHECKING:.*?{name}"
            if re.search(type_checking_pattern, content, re.DOTALL):
                return True
        return False

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""
