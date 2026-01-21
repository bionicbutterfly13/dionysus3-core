"""
Promise Keeper Analyzer

Detects broken promises in code:
- TODO/FIXME/XXX/HACK comments
- Stub methods (NotImplementedError, pass statements)
- Incomplete implementations
- Unfulfilled docstrings
"""

import ast
import re
from pathlib import Path
from typing import List

from .base import BaseAnalyzer, PatternMatcher
from ..models import QAFinding, Severity, IssueClass


class PromiseKeeperAnalyzer(BaseAnalyzer):
    """Expert analyzer for broken promises in code."""

    name = "promise_keeper"
    issue_class = IssueClass.BROKEN_PROMISE

    # Patterns for comment-based promises
    PROMISE_PATTERNS = [
        r"#\s*TODO\s*[:\-]?\s*(.+)",
        r"#\s*FIXME\s*[:\-]?\s*(.+)",
        r"#\s*XXX\s*[:\-]?\s*(.+)",
        r"#\s*HACK\s*[:\-]?\s*(.+)",
        r"#\s*BUG\s*[:\-]?\s*(.+)",
        r"#\s*OPTIMIZE\s*[:\-]?\s*(.+)",
        r"#\s*REVIEW\s*[:\-]?\s*(.+)",
    ]

    async def analyze_file(self, file_path: Path, content: str) -> List[QAFinding]:
        """Analyze a file for broken promises."""
        findings = []

        # 1. Find TODO/FIXME comments
        findings.extend(self._find_comment_promises(file_path, content))

        # 2. Find stub methods
        findings.extend(self._find_stub_methods(file_path, content))

        # 3. Find pass statements in non-empty contexts
        findings.extend(self._find_suspicious_pass(file_path, content))

        # 4. Find docstring claims without implementation
        findings.extend(self._find_unfulfilled_docstrings(file_path, content))

        return findings

    def _find_comment_promises(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find TODO/FIXME/XXX/HACK comments."""
        findings = []

        for pattern in self.PROMISE_PATTERNS:
            matches = PatternMatcher.find_pattern(content, pattern)
            for line_num, match, line_content in matches:
                # Extract keyword from the match (e.g., "# TODO:" -> "TODO")
                keyword_match = re.search(r"(TODO|FIXME|XXX|HACK|BUG|OPTIMIZE|REVIEW)", match, re.IGNORECASE)
                keyword = keyword_match.group(1).upper() if keyword_match else "TODO"
                severity = self._severity_for_keyword(keyword)

                findings.append(QAFinding(
                    id=f"{self.name}-comment-{line_num}",
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_class=self.issue_class,
                    severity=severity,
                    title=f"{keyword} comment found",
                    description=f"Unresolved {keyword}: {line_content}",
                    context=self._get_context(content, line_num),
                    suggested_fix=f"Implement or remove the {keyword} item",
                    analyzer=self.name,
                ))

        return findings

    def _find_stub_methods(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find methods that raise NotImplementedError."""
        findings = []
        tree = self._parse_ast(content)
        if not tree:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for NotImplementedError
                for child in ast.walk(node):
                    if isinstance(child, ast.Raise):
                        if isinstance(child.exc, ast.Call):
                            if (isinstance(child.exc.func, ast.Name) and
                                child.exc.func.id == "NotImplementedError"):
                                findings.append(QAFinding(
                                    id=f"{self.name}-stub-{node.lineno}",
                                    file_path=str(file_path),
                                    line_number=node.lineno,
                                    issue_class=self.issue_class,
                                    severity=Severity.HIGH,
                                    title=f"Stub method: {node.name}",
                                    description=f"Method '{node.name}' raises NotImplementedError",
                                    context=self._get_context(content, node.lineno),
                                    suggested_fix=f"Implement the method '{node.name}'",
                                    analyzer=self.name,
                                ))

        return findings

    def _find_suspicious_pass(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find pass statements in non-trivial contexts."""
        findings = []
        tree = self._parse_ast(content)
        if not tree:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function body is just pass (or docstring + pass)
                body = node.body
                if not body:
                    continue

                # Remove docstring from consideration
                non_docstring_body = [
                    n for n in body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))
                ]

                # Check for single Pass statement
                if (len(non_docstring_body) == 1 and
                    isinstance(non_docstring_body[0], ast.Pass)):
                    # Check if this is an abstract method (acceptable)
                    is_abstract = any(
                        isinstance(d, ast.Name) and "abstract" in d.id.lower()
                        for d in node.decorator_list
                        if isinstance(d, ast.Name)
                    ) or any(
                        isinstance(d, ast.Attribute) and "abstract" in d.attr.lower()
                        for d in node.decorator_list
                        if isinstance(d, ast.Attribute)
                    )

                    if not is_abstract:
                        findings.append(QAFinding(
                            id=f"{self.name}-pass-{node.lineno}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_class=self.issue_class,
                            severity=Severity.MEDIUM,
                            title=f"Empty method: {node.name}",
                            description=f"Method '{node.name}' has only 'pass' statement",
                            context=self._get_context(content, node.lineno),
                            suggested_fix=f"Implement '{node.name}' or mark as @abstractmethod",
                            analyzer=self.name,
                        ))

        return findings

    def _find_unfulfilled_docstrings(self, file_path: Path, content: str) -> List[QAFinding]:
        """Find docstrings that claim functionality not implemented."""
        findings = []
        tree = self._parse_ast(content)
        if not tree:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    continue

                # Check for documented returns that don't exist
                if self._claims_return(docstring) and not self._has_return(node):
                    findings.append(QAFinding(
                        id=f"{self.name}-docreturn-{node.lineno}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_class=self.issue_class,
                        severity=Severity.MEDIUM,
                        title=f"Docstring claims return: {node.name}",
                        description=f"Method '{node.name}' docstring claims return value but none found",
                        context=self._get_context(content, node.lineno),
                        suggested_fix="Add return statement or update docstring",
                        analyzer=self.name,
                    ))

        return findings

    def _claims_return(self, docstring: str) -> bool:
        """Check if docstring claims a return value."""
        return_patterns = [
            r"Returns?\s*:",
            r"Returns?\s+\w+",
            r":returns:",
            r":rtype:",
        ]
        for pattern in return_patterns:
            if re.search(pattern, docstring, re.IGNORECASE):
                return True
        return False

    def _has_return(self, node: ast.FunctionDef) -> bool:
        """Check if function has a return statement with a value."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False

    def _severity_for_keyword(self, keyword: str) -> Severity:
        """Determine severity based on comment keyword."""
        severity_map = {
            "FIXME": Severity.HIGH,
            "BUG": Severity.HIGH,
            "XXX": Severity.HIGH,
            "HACK": Severity.MEDIUM,
            "TODO": Severity.MEDIUM,
            "OPTIMIZE": Severity.LOW,
            "REVIEW": Severity.LOW,
        }
        return severity_map.get(keyword, Severity.LOW)
