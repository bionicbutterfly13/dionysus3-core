"""
Unit test: Memory Gateway (Markov blanket) verification.

Runs scripts/verification/check_memory_gateway.py and asserts exit 0.
Ensures no direct Neo4j driver use outside the allowlisted dev-only scripts.

See .conductor/constraints.md "Memory Gateway (Markov Blanket) – Deterministic No-Bypass".
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CHECK_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verification" / "check_memory_gateway.py"


def test_memory_gateway_no_direct_neo4j_driver():
    """Fail if any code uses GraphDatabase / direct Neo4j driver outside allowlist."""
    proc = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert proc.returncode == 0, (
        "check_memory_gateway failed. Direct Neo4j driver use violates Memory Gateway. "
        "Use GraphitiService / WebhookNeo4jDriver only. stderr:\n"
        + (proc.stderr or proc.stdout or "")
    )
