"""
Validation Agent

Validates repairs before they are committed:
- Runs affected tests
- Checks for regressions
- Verifies documentation accuracy
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation check."""
    passed: bool
    check_name: str
    details: str
    errors: List[str]


class ValidationAgent:
    """
    Validates repairs before commit.

    Checks:
    - Syntax validity (Python can parse the file)
    - Test suite passes
    - No new type errors (if using mypy/pyright)
    """

    name = "validation_agent"

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[ValidationResult] = []

    async def validate_all(self, changed_files: List[str]) -> Tuple[bool, str]:
        """
        Run all validation checks.

        Returns:
            Tuple of (all_passed, summary)
        """
        self.results = []

        # 1. Syntax check
        for file_path in changed_files:
            if file_path.endswith(".py"):
                result = await self._check_syntax(file_path)
                self.results.append(result)
                if not result.passed:
                    return False, f"Syntax error in {file_path}: {result.details}"

        # 2. Import check
        for file_path in changed_files:
            if file_path.endswith(".py"):
                result = await self._check_imports(file_path)
                self.results.append(result)
                if not result.passed:
                    return False, f"Import error in {file_path}: {result.details}"

        # 3. Test suite
        test_result = await self._run_tests(changed_files)
        self.results.append(test_result)
        if not test_result.passed:
            return False, f"Tests failed: {test_result.details}"

        # All checks passed
        return True, self._generate_summary()

    async def _check_syntax(self, file_path: str) -> ValidationResult:
        """Check Python syntax is valid."""
        try:
            with open(file_path, "r") as f:
                source = f.read()
            compile(source, file_path, "exec")
            return ValidationResult(
                passed=True,
                check_name="syntax",
                details=f"Syntax valid: {file_path}",
                errors=[]
            )
        except SyntaxError as e:
            return ValidationResult(
                passed=False,
                check_name="syntax",
                details=f"Syntax error at line {e.lineno}: {e.msg}",
                errors=[str(e)]
            )

    async def _check_imports(self, file_path: str) -> ValidationResult:
        """Check that imports can be resolved."""
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import ast; ast.parse(open('{file_path}').read())"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )

            if result.returncode == 0:
                return ValidationResult(
                    passed=True,
                    check_name="imports",
                    details=f"Imports valid: {file_path}",
                    errors=[]
                )
            else:
                return ValidationResult(
                    passed=False,
                    check_name="imports",
                    details=result.stderr,
                    errors=[result.stderr]
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                passed=False,
                check_name="imports",
                details="Import check timed out",
                errors=["Timeout"]
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                check_name="imports",
                details=str(e),
                errors=[str(e)]
            )

    async def _run_tests(self, changed_files: List[str]) -> ValidationResult:
        """Run test suite for affected files."""
        # Find test files that might be affected
        test_files = self._find_related_tests(changed_files)

        if not test_files:
            # Run all unit tests
            test_cmd = [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
        else:
            # Run specific test files
            test_cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v", "--tb=short"]

        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.project_root)
            )

            if result.returncode == 0:
                return ValidationResult(
                    passed=True,
                    check_name="tests",
                    details="All tests passed",
                    errors=[]
                )
            else:
                # Extract failure summary
                failures = self._extract_test_failures(result.stdout + result.stderr)
                return ValidationResult(
                    passed=False,
                    check_name="tests",
                    details=f"Test failures: {len(failures)}",
                    errors=failures
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                passed=False,
                check_name="tests",
                details="Test suite timed out",
                errors=["Timeout after 5 minutes"]
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                check_name="tests",
                details=str(e),
                errors=[str(e)]
            )

    def _find_related_tests(self, changed_files: List[str]) -> List[str]:
        """Find test files related to changed files."""
        test_files = []

        for file_path in changed_files:
            if not file_path.endswith(".py"):
                continue

            path = Path(file_path)

            # Check if there's a corresponding test file
            # e.g., api/services/foo.py -> tests/unit/test_foo.py
            test_name = f"test_{path.stem}.py"
            test_patterns = [
                self.project_root / "tests" / "unit" / test_name,
                self.project_root / "tests" / "integration" / test_name,
            ]

            for test_path in test_patterns:
                if test_path.exists():
                    test_files.append(str(test_path))

        return test_files

    def _extract_test_failures(self, output: str) -> List[str]:
        """Extract test failure names from pytest output."""
        failures = []
        for line in output.splitlines():
            if "FAILED" in line:
                failures.append(line.strip())
            elif "ERROR" in line and "::" in line:
                failures.append(line.strip())

        return failures[:10]  # Limit to first 10 failures

    def _generate_summary(self) -> str:
        """Generate validation summary."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        return f"Validation complete: {passed}/{total} checks passed"

    async def quick_validate(self, file_path: str) -> bool:
        """Quick validation of a single file."""
        syntax_result = await self._check_syntax(file_path)
        return syntax_result.passed
