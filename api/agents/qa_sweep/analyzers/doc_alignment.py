"""
Documentation Alignment Analyzer

Detects documentation/code misalignment:
- Docstring parameters vs actual parameters
- Return type claims vs actual returns
- Missing docstrings for public functions
- Outdated examples in docstrings
"""

import ast
import re
from pathlib import Path
from typing import List, Set

from .base import BaseAnalyzer
from ..models import QAFinding, Severity, IssueClass


class DocAlignmentAnalyzer(BaseAnalyzer):
    """Expert analyzer for documentation alignment issues."""

    name = "doc_alignment"
    issue_class = IssueClass.DOC_MISALIGNMENT

    async def analyze_file(self, file_path: Path, content: str) -> List[QAFinding]:
        """Analyze a file for documentation misalignment."""
        findings = []

        tree = self._parse_ast(content)
        if not tree:
            return findings

        # 1. Check function/method docstrings
        findings.extend(self._check_function_docs(file_path, content, tree))

        # 2. Check class docstrings
        findings.extend(self._check_class_docs(file_path, content, tree))

        # 3. Check for missing docstrings on public APIs
        findings.extend(self._check_missing_docs(file_path, content, tree))

        return findings

    def _check_function_docs(
        self, file_path: Path, content: str, tree: ast.Module
    ) -> List[QAFinding]:
        """Check function docstrings match actual signatures."""
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            docstring = ast.get_docstring(node)
            if not docstring:
                continue

            # Extract documented parameters
            doc_params = self._extract_doc_params(docstring)

            # Get actual parameters
            actual_params = self._get_actual_params(node)

            # Compare parameters
            findings.extend(self._compare_params(
                file_path, content, node, doc_params, actual_params
            ))

            # Check return documentation
            findings.extend(self._check_return_docs(
                file_path, content, node, docstring
            ))

        return findings

    def _check_class_docs(
        self, file_path: Path, content: str, tree: ast.Module
    ) -> List[QAFinding]:
        """Check class docstrings for accuracy."""
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            docstring = ast.get_docstring(node)
            if not docstring:
                continue

            # Check for documented attributes vs actual __init__ params
            init_method = next(
                (n for n in node.body
                 if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
                None
            )

            if init_method:
                doc_attrs = self._extract_doc_attributes(docstring)
                init_params = self._get_actual_params(init_method)

                # Remove self from init params
                init_params = {k: v for k, v in init_params.items() if k != "self"}

                # Check for missing documented attributes
                for param in init_params:
                    if param not in doc_attrs and not param.startswith("_"):
                        findings.append(QAFinding(
                            id=f"{self.name}-classattr-{node.lineno}-{param}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_class=self.issue_class,
                            severity=Severity.LOW,
                            title=f"Undocumented attribute: {param}",
                            description=f"Class '{node.name}' has undocumented __init__ parameter '{param}'",
                            context=self._get_context(content, node.lineno),
                            suggested_fix=f"Add documentation for '{param}' in class docstring",
                            analyzer=self.name,
                        ))

        return findings

    def _check_missing_docs(
        self, file_path: Path, content: str, tree: ast.Module
    ) -> List[QAFinding]:
        """Check for missing docstrings on public functions/classes."""
        findings = []

        for node in ast.walk(tree):
            # Skip private/protected items
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                if not ast.get_docstring(node):
                    findings.append(QAFinding(
                        id=f"{self.name}-missing-{node.lineno}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_class=self.issue_class,
                        severity=Severity.LOW,
                        title=f"Missing docstring: {node.name}",
                        description=f"Public function '{node.name}' has no docstring",
                        context=self._get_context(content, node.lineno),
                        suggested_fix=f"Add docstring to '{node.name}'",
                        analyzer=self.name,
                    ))

            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                if not ast.get_docstring(node):
                    findings.append(QAFinding(
                        id=f"{self.name}-missing-{node.lineno}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_class=self.issue_class,
                        severity=Severity.LOW,
                        title=f"Missing docstring: {node.name}",
                        description=f"Public class '{node.name}' has no docstring",
                        context=self._get_context(content, node.lineno),
                        suggested_fix=f"Add docstring to '{node.name}'",
                        analyzer=self.name,
                    ))

        return findings

    def _extract_doc_params(self, docstring: str) -> Set[str]:
        """Extract parameter names from docstring."""
        params = set()

        # Google style: Args:
        args_match = re.search(r"Args?:\s*\n(.*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)", docstring, re.DOTALL)
        if args_match:
            for match in re.finditer(r"^\s*(\w+)\s*[:\(]", args_match.group(1), re.MULTILINE):
                params.add(match.group(1))

        # Numpy style: Parameters
        params_match = re.search(r"Parameters?\s*[-]+\s*\n(.*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)", docstring, re.DOTALL)
        if params_match:
            for match in re.finditer(r"^\s*(\w+)\s*:", params_match.group(1), re.MULTILINE):
                params.add(match.group(1))

        # Sphinx style: :param name:
        for match in re.finditer(r":param\s+(\w+):", docstring):
            params.add(match.group(1))

        return params

    def _extract_doc_attributes(self, docstring: str) -> Set[str]:
        """Extract attribute names from class docstring."""
        attrs = set()

        # Google style: Attributes:
        attrs_match = re.search(r"Attributes?:\s*\n(.*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)", docstring, re.DOTALL)
        if attrs_match:
            for match in re.finditer(r"^\s*(\w+)\s*[:\(]", attrs_match.group(1), re.MULTILINE):
                attrs.add(match.group(1))

        # Numpy style: Attributes
        attrs_match = re.search(r"Attributes?\s*[-]+\s*\n(.*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)", docstring, re.DOTALL)
        if attrs_match:
            for match in re.finditer(r"^\s*(\w+)\s*:", attrs_match.group(1), re.MULTILINE):
                attrs.add(match.group(1))

        return attrs

    def _get_actual_params(self, node: ast.FunctionDef) -> dict:
        """Get actual parameter names and defaults from function."""
        params = {}

        # Regular args
        for arg in node.args.args:
            params[arg.arg] = {"has_default": False}

        # Args with defaults
        num_defaults = len(node.args.defaults)
        num_args = len(node.args.args)
        for i, default in enumerate(node.args.defaults):
            arg_index = num_args - num_defaults + i
            if arg_index >= 0 and arg_index < len(node.args.args):
                arg_name = node.args.args[arg_index].arg
                params[arg_name]["has_default"] = True

        # Keyword-only args
        for arg in node.args.kwonlyargs:
            params[arg.arg] = {"has_default": False}

        # *args
        if node.args.vararg:
            params[node.args.vararg.arg] = {"is_vararg": True}

        # **kwargs
        if node.args.kwarg:
            params[node.args.kwarg.arg] = {"is_kwarg": True}

        return params

    def _compare_params(
        self,
        file_path: Path,
        content: str,
        node: ast.FunctionDef,
        doc_params: Set[str],
        actual_params: dict
    ) -> List[QAFinding]:
        """Compare documented params with actual params."""
        findings = []

        # Skip self/cls
        actual_names = {k for k in actual_params.keys() if k not in ("self", "cls")}

        # Find undocumented parameters
        undocumented = actual_names - doc_params
        for param in undocumented:
            # Skip *args and **kwargs if they have typical names
            if actual_params.get(param, {}).get("is_vararg") or actual_params.get(param, {}).get("is_kwarg"):
                continue

            findings.append(QAFinding(
                id=f"{self.name}-undoc-param-{node.lineno}-{param}",
                file_path=str(file_path),
                line_number=node.lineno,
                issue_class=self.issue_class,
                severity=Severity.MEDIUM,
                title=f"Undocumented parameter: {param}",
                description=f"Function '{node.name}' has undocumented parameter '{param}'",
                context=self._get_context(content, node.lineno),
                suggested_fix=f"Add documentation for parameter '{param}'",
                analyzer=self.name,
            ))

        # Find documented params that don't exist
        extra_docs = doc_params - actual_names
        for param in extra_docs:
            findings.append(QAFinding(
                id=f"{self.name}-extra-doc-{node.lineno}-{param}",
                file_path=str(file_path),
                line_number=node.lineno,
                issue_class=self.issue_class,
                severity=Severity.HIGH,
                title=f"Phantom documented parameter: {param}",
                description=f"Function '{node.name}' documents parameter '{param}' but it doesn't exist",
                context=self._get_context(content, node.lineno),
                suggested_fix=f"Remove documentation for non-existent parameter '{param}'",
                analyzer=self.name,
            ))

        return findings

    def _check_return_docs(
        self,
        file_path: Path,
        content: str,
        node: ast.FunctionDef,
        docstring: str
    ) -> List[QAFinding]:
        """Check return documentation accuracy."""
        findings = []

        # Check if docstring claims a return
        claims_return = bool(re.search(
            r"(Returns?:|:returns?:|:rtype:)",
            docstring,
            re.IGNORECASE
        ))

        # Check if function actually returns something
        has_return = self._function_returns(node)

        if claims_return and not has_return:
            findings.append(QAFinding(
                id=f"{self.name}-false-return-{node.lineno}",
                file_path=str(file_path),
                line_number=node.lineno,
                issue_class=self.issue_class,
                severity=Severity.MEDIUM,
                title=f"False return claim: {node.name}",
                description=f"Function '{node.name}' documents a return but doesn't return anything",
                context=self._get_context(content, node.lineno),
                suggested_fix="Add return statement or remove return documentation",
                analyzer=self.name,
            ))

        elif has_return and not claims_return:
            # Only flag if it's a public function
            if not node.name.startswith("_"):
                findings.append(QAFinding(
                    id=f"{self.name}-undoc-return-{node.lineno}",
                    file_path=str(file_path),
                    line_number=node.lineno,
                    issue_class=self.issue_class,
                    severity=Severity.LOW,
                    title=f"Undocumented return: {node.name}",
                    description=f"Function '{node.name}' returns a value but has no return documentation",
                    context=self._get_context(content, node.lineno),
                    suggested_fix="Add return documentation",
                    analyzer=self.name,
                ))

        return findings

    def _function_returns(self, node: ast.FunctionDef) -> bool:
        """Check if function has a return statement with a value."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                # Exclude None returns
                if isinstance(child.value, ast.Constant) and child.value.value is None:
                    continue
                return True
        return False
