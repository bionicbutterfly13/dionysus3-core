#!/usr/bin/env python3
"""
Memory Gateway (Markov Blanket) verification.

Ensures no code bypasses the singleton gateway (GraphitiService, WebhookNeo4jDriver).
Fails if 'from neo4j import GraphDatabase' or 'GraphDatabase.driver' appears
outside the allowlisted dev-only verification scripts.

Run: python scripts/verification/check_memory_gateway.py
Exit: 0 if clean, 1 if violations found.

See .conductor/constraints.md "Memory Gateway (Markov Blanket)".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Root of the project (parent of scripts/)
ROOT = Path(__file__).resolve().parents[2]

# Dev-only scripts allowed to use direct Neo4j for verification (bolt, auth, audit).
ALLOWLIST = {
    "scripts/verification/test_bolt_connection.py",
    "scripts/verification/test_auth.py",
    "scripts/verification/audit_memory_architecture.py",
}
# Do not scan the checker itself (it contains pattern strings).
SKIP_SELF = "scripts/verification/check_memory_gateway.py"

# Patterns that indicate direct Neo4j driver use (forbidden outside allowlist).
PATTERNS = [
    (re.compile(r"from\s+neo4j\s+import\s+GraphDatabase"), "from neo4j import GraphDatabase"),
    (re.compile(r"GraphDatabase\.driver\s*\("), "GraphDatabase.driver("),
]


def main() -> int:
    violations: list[tuple[str, int, str]] = []

    for py_path in ROOT.rglob("*.py"):
        rel = py_path.relative_to(ROOT)
        rel_str = str(rel).replace("\\", "/")
        if rel_str in ALLOWLIST or rel_str == SKIP_SELF:
            continue
        # Skip virtualenvs, .venv, etc.
        if any(p.startswith(".") or p == "venv" or p == ".venv" for p in rel.parts):
            continue

        try:
            text = py_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            for pattern, label in PATTERNS:
                if pattern.search(line):
                    # Exclude neo4j.graph / neo4j.time (type imports only, used by graphiti_service).
                    if "neo4j.graph" in line or "neo4j.time" in line:
                        continue
                    violations.append((rel_str, i, label))

    if not violations:
        print("check_memory_gateway: OK – no direct Neo4j driver use outside allowlist.")
        return 0

    print("check_memory_gateway: FAIL – direct Neo4j driver use violates Memory Gateway (Markov blanket).")
    print("See .conductor/constraints.md 'Memory Gateway (Markov Blanket) – Deterministic No-Bypass'.")
    print()
    for path, line_no, label in violations:
        print(f"  {path}:{line_no}: {label}")
    print()
    print("Use GraphitiService / WebhookNeo4jDriver (get_graphiti_service, get_neo4j_driver) only.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
