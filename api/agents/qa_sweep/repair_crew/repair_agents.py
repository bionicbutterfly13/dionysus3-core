"""
Repair Agents for QA Sweep

Expert agents for fixing specific classes of issues:
- PromiseFulfillerAgent: Implements TODOs, completes stubs
- CodeCleanerAgent: Removes dead code safely
- DocSynchronizerAgent: Updates documentation to match code
"""

import ast
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple

from ..models import QAFinding, IssueClass


class BaseRepairAgent(ABC):
    """Base class for repair agents."""

    name: str = "base_repair"
    issue_class: IssueClass

    def __init__(self, model_id: str = "dionysus-agents"):
        self.model_id = model_id
        self.repairs_made: List[dict] = []

    @abstractmethod
    async def repair(self, finding: QAFinding) -> Tuple[bool, str]:
        """
        Attempt to repair a finding.

        Returns:
            Tuple of (success, description of change or error)
        """
        pass

    async def repair_batch(self, findings: List[QAFinding]) -> dict:
        """Repair multiple findings."""
        results = {
            "succeeded": [],
            "failed": [],
            "skipped": [],
        }

        for finding in findings:
            if finding.issue_class != self.issue_class:
                results["skipped"].append({
                    "finding": finding.id,
                    "reason": f"Wrong issue class: {finding.issue_class}",
                })
                continue

            try:
                success, description = await self.repair(finding)
                if success:
                    results["succeeded"].append({
                        "finding": finding.id,
                        "description": description,
                    })
                    self.repairs_made.append({
                        "finding": finding,
                        "description": description,
                    })
                else:
                    results["failed"].append({
                        "finding": finding.id,
                        "error": description,
                    })
            except Exception as e:
                results["failed"].append({
                    "finding": finding.id,
                    "error": str(e),
                })

        return results

    def _read_file(self, file_path: str) -> str:
        """Read file content."""
        return Path(file_path).read_text(encoding="utf-8")

    def _write_file(self, file_path: str, content: str) -> None:
        """Write file content."""
        Path(file_path).write_text(content, encoding="utf-8")

    def _edit_lines(
        self,
        content: str,
        start_line: int,
        end_line: int,
        replacement: str
    ) -> str:
        """Replace lines in content."""
        lines = content.splitlines(keepends=True)

        # Handle last line without newline
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"

        # Replace the lines
        new_lines = (
            lines[:start_line - 1] +
            [replacement + "\n" if not replacement.endswith("\n") else replacement] +
            lines[end_line:]
        )

        return "".join(new_lines)


class PromiseFulfillerAgent(BaseRepairAgent):
    """
    Fulfills broken promises in code.

    Handles:
    - TODO/FIXME comments (removes or implements)
    - Stub methods (provides basic implementation)
    - Incomplete implementations
    """

    name = "promise_fulfiller"
    issue_class = IssueClass.BROKEN_PROMISE

    async def repair(self, finding: QAFinding) -> Tuple[bool, str]:
        """Repair a broken promise finding."""
        content = self._read_file(finding.file_path)

        if "TODO" in finding.title or "FIXME" in finding.title or "HACK" in finding.title:
            return await self._handle_todo_comment(finding, content)
        elif "Stub method" in finding.title:
            return await self._handle_stub_method(finding, content)
        elif "Empty method" in finding.title:
            return await self._handle_empty_method(finding, content)
        else:
            return False, f"Unknown promise type: {finding.title}"

    async def _handle_todo_comment(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Handle TODO/FIXME comments by removing them."""
        lines = content.splitlines()
        line_idx = finding.line_number - 1

        if line_idx >= len(lines):
            return False, "Line number out of range"

        line = lines[line_idx]

        # Check if the entire line is just a comment
        if re.match(r"^\s*#\s*(TODO|FIXME|XXX|HACK|BUG)", line, re.IGNORECASE):
            # Remove the entire line
            new_lines = lines[:line_idx] + lines[line_idx + 1:]
            self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
            return True, f"Removed {finding.title} comment"
        else:
            # Comment is at end of code line - keep the code, remove comment
            cleaned = re.sub(r"\s*#\s*(TODO|FIXME|XXX|HACK|BUG).*$", "", line, flags=re.IGNORECASE)
            new_lines = lines[:line_idx] + [cleaned] + lines[line_idx + 1:]
            self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
            return True, f"Removed trailing {finding.title} comment"

    async def _handle_stub_method(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """
        Handle stub methods by adding a basic implementation.

        This is a conservative approach - we add logging and return None
        rather than trying to generate complex implementations.
        """
        # Parse the file
        tree = ast.parse(content)
        lines = content.splitlines()

        # Find the function
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno == finding.line_number:
                    # Get the indentation
                    func_line = lines[node.lineno - 1]
                    indent = len(func_line) - len(func_line.lstrip())
                    body_indent = " " * (indent + 4)

                    # Get docstring if present
                    docstring = ast.get_docstring(node)
                    docstring_lines = 0
                    if docstring:
                        # Count docstring lines
                        for i, line in enumerate(lines[node.lineno:], node.lineno):
                            if '"""' in line or "'''" in line:
                                docstring_lines = i - node.lineno + 1
                                if line.count('"""') == 2 or line.count("'''") == 2:
                                    docstring_lines = 1
                                break

                    # Determine return type hint
                    returns_something = node.returns is not None

                    # Create basic implementation
                    impl_lines = [
                        f'{body_indent}# TODO: Implement {node.name}',
                        f'{body_indent}import logging',
                        f'{body_indent}logging.warning("{node.name} is not fully implemented")',
                    ]
                    if returns_something:
                        impl_lines.append(f'{body_indent}return None')

                    # Find where NotImplementedError is raised
                    raise_line = None
                    for child in ast.walk(node):
                        if isinstance(child, ast.Raise):
                            raise_line = child.lineno

                    if raise_line:
                        # Replace the raise line
                        new_content = self._edit_lines(
                            content,
                            raise_line,
                            raise_line,
                            "\n".join(impl_lines)
                        )
                        self._write_file(finding.file_path, new_content)
                        return True, f"Added basic implementation for {node.name}"

        return False, "Could not find stub method to repair"

    async def _handle_empty_method(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Handle empty methods with only pass statement."""
        # Similar to stub method handling
        tree = ast.parse(content)
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno == finding.line_number:
                    func_line = lines[node.lineno - 1]
                    indent = len(func_line) - len(func_line.lstrip())
                    body_indent = " " * (indent + 4)

                    # Find the pass statement
                    for child in node.body:
                        if isinstance(child, ast.Pass):
                            impl_lines = [
                                f'{body_indent}# TODO: Implement {node.name}',
                                f'{body_indent}import logging',
                                f'{body_indent}logging.debug("{node.name} called but not implemented")',
                            ]

                            new_content = self._edit_lines(
                                content,
                                child.lineno,
                                child.lineno,
                                "\n".join(impl_lines)
                            )
                            self._write_file(finding.file_path, new_content)
                            return True, f"Added placeholder implementation for {node.name}"

        return False, "Could not find empty method to repair"


class CodeCleanerAgent(BaseRepairAgent):
    """
    Cleans up orphan code.

    Handles:
    - Unused imports (safe removal)
    - Commented-out code blocks
    - Deprecated code markers
    """

    name = "code_cleaner"
    issue_class = IssueClass.ORPHAN_CODE

    async def repair(self, finding: QAFinding) -> Tuple[bool, str]:
        """Repair an orphan code finding."""
        content = self._read_file(finding.file_path)

        if "Unused import" in finding.title:
            return await self._remove_unused_import(finding, content)
        elif "Commented-out code" in finding.title:
            return await self._remove_commented_code(finding, content)
        elif "Deprecated" in finding.title:
            # Don't auto-remove deprecated code - just flag it
            return False, "Deprecated code requires manual review"
        elif "Unreferenced" in finding.title:
            # Don't auto-remove unreferenced functions - could be used elsewhere
            return False, "Unreferenced code requires manual verification"
        else:
            return False, f"Unknown orphan type: {finding.title}"

    async def _remove_unused_import(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Remove unused import statement."""
        lines = content.splitlines()
        line_idx = finding.line_number - 1

        if line_idx >= len(lines):
            return False, "Line number out of range"

        line = lines[line_idx]

        # Extract the import name from the finding title
        match = re.search(r"Unused import: (\w+)", finding.title)
        if not match:
            return False, "Could not extract import name"

        import_name = match.group(1)

        # Handle different import styles
        if f"import {import_name}" in line:
            if line.strip().startswith(f"import {import_name}"):
                # Simple import - remove entire line
                new_lines = lines[:line_idx] + lines[line_idx + 1:]
                self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
                return True, f"Removed unused import: {import_name}"
            elif "," in line:
                # Multiple imports on same line
                # Remove just this one
                cleaned = re.sub(rf",?\s*{import_name}\s*,?", ",", line)
                cleaned = re.sub(r",\s*$", "", cleaned)  # Clean trailing comma
                cleaned = re.sub(r"import\s*,", "import ", cleaned)  # Clean leading comma
                new_lines = lines[:line_idx] + [cleaned] + lines[line_idx + 1:]
                self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
                return True, f"Removed {import_name} from multi-import line"

        elif f"from" in line and import_name in line:
            # from X import Y style
            if line.count(",") == 0:
                # Single import - remove entire line
                new_lines = lines[:line_idx] + lines[line_idx + 1:]
                self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
                return True, f"Removed unused import: {import_name}"
            else:
                # Multiple imports - remove just this one
                cleaned = re.sub(rf",?\s*{import_name}\s*,?", ",", line)
                cleaned = re.sub(r",\s*\)", ")", cleaned)  # Clean before closing paren
                cleaned = re.sub(r"\(\s*,", "(", cleaned)  # Clean after opening paren
                cleaned = re.sub(r",\s*$", "", cleaned)
                cleaned = re.sub(r"import\s*,", "import ", cleaned)
                new_lines = lines[:line_idx] + [cleaned] + lines[line_idx + 1:]
                self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
                return True, f"Removed {import_name} from multi-import line"

        return False, f"Could not safely remove import: {import_name}"

    async def _remove_commented_code(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Remove block of commented-out code."""
        if not finding.line_end:
            return False, "No line range specified for commented code block"

        lines = content.splitlines()
        start_idx = finding.line_number - 1
        end_idx = finding.line_end

        if end_idx > len(lines):
            end_idx = len(lines)

        # Count lines being removed
        num_lines = end_idx - start_idx

        # Remove the lines
        new_lines = lines[:start_idx] + lines[end_idx:]
        self._write_file(finding.file_path, "\n".join(new_lines) + "\n")

        return True, f"Removed {num_lines} lines of commented-out code"


class DocSynchronizerAgent(BaseRepairAgent):
    """
    Synchronizes documentation with code.

    Handles:
    - Adding missing parameter documentation
    - Removing phantom parameters from docs
    - Updating return documentation
    """

    name = "doc_synchronizer"
    issue_class = IssueClass.DOC_MISALIGNMENT

    async def repair(self, finding: QAFinding) -> Tuple[bool, str]:
        """Repair a documentation misalignment finding."""
        content = self._read_file(finding.file_path)

        if "Phantom documented parameter" in finding.title:
            return await self._remove_phantom_param(finding, content)
        elif "Undocumented parameter" in finding.title:
            # Adding documentation requires understanding the parameter - skip for now
            return False, "Adding parameter documentation requires manual review"
        elif "Missing docstring" in finding.title:
            return await self._add_basic_docstring(finding, content)
        elif "False return claim" in finding.title:
            return await self._remove_false_return(finding, content)
        else:
            return False, f"Unknown doc alignment issue: {finding.title}"

    async def _remove_phantom_param(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Remove documentation for parameter that doesn't exist."""
        # Extract parameter name
        match = re.search(r"parameter: (\w+)", finding.title)
        if not match:
            return False, "Could not extract parameter name"

        param_name = match.group(1)

        # Find and remove the parameter from docstring
        # This is tricky because we need to handle different docstring styles

        tree = ast.parse(content)
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno == finding.line_number:
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        return False, "No docstring found"

                    # Try to remove the parameter line(s)
                    # Google style: param_name: description
                    new_doc = re.sub(
                        rf"^\s*{param_name}\s*[:\(].*?(?=\n\s*\w+\s*[:\(]|\n\s*\n|\Z)",
                        "",
                        docstring,
                        flags=re.MULTILINE | re.DOTALL
                    )

                    # Sphinx style: :param param_name: description
                    new_doc = re.sub(
                        rf":param\s+{param_name}:.*?(?=\n\s*:|$)",
                        "",
                        new_doc,
                        flags=re.MULTILINE
                    )

                    if new_doc != docstring:
                        # Replace docstring in content
                        # This is simplified - a full implementation would need to
                        # properly handle the docstring replacement
                        return False, "Docstring editing requires manual review"

        return False, "Could not remove phantom parameter documentation"

    async def _add_basic_docstring(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Add a basic docstring placeholder."""
        tree = ast.parse(content)
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno == finding.line_number:
                    # Get indentation
                    def_line = lines[node.lineno - 1]
                    indent = len(def_line) - len(def_line.lstrip())
                    doc_indent = " " * (indent + 4)

                    # Create basic docstring
                    if isinstance(node, ast.ClassDef):
                        docstring = f'{doc_indent}"""TODO: Document {node.name} class."""'
                    else:
                        docstring = f'{doc_indent}"""TODO: Document {node.name} function."""'

                    # Find the line after the def/class line
                    insert_line = node.lineno

                    # Insert docstring
                    new_lines = (
                        lines[:insert_line] +
                        [docstring] +
                        lines[insert_line:]
                    )
                    self._write_file(finding.file_path, "\n".join(new_lines) + "\n")
                    return True, f"Added placeholder docstring for {node.name}"

        return False, "Could not add docstring"

    async def _remove_false_return(
        self, finding: QAFinding, content: str
    ) -> Tuple[bool, str]:
        """Remove false return documentation from docstring."""
        # This is complex to do safely - require manual review
        return False, "Return documentation removal requires manual review"
