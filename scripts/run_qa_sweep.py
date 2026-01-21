#!/usr/bin/env python3
"""
QA Sweep CLI

Run comprehensive codebase quality analysis with optional auto-repair.

Usage:
    python scripts/run_qa_sweep.py                    # Scan only
    python scripts/run_qa_sweep.py --repair           # Scan and repair
    python scripts/run_qa_sweep.py --repair --dry-run # Show what would be repaired
    python scripts/run_qa_sweep.py --analyzer promise_keeper  # Single analyzer
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.agents.qa_sweep import QASweepOrchestrator
from api.agents.qa_sweep.models import Severity


async def main():
    parser = argparse.ArgumentParser(
        description="Run QA sweep on codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Quick scan, show medium+ severity issues
    python scripts/run_qa_sweep.py

    # Full scan including low severity
    python scripts/run_qa_sweep.py --severity low

    # Scan and repair
    python scripts/run_qa_sweep.py --repair

    # Dry run (show what would be repaired)
    python scripts/run_qa_sweep.py --repair --dry-run

    # Run specific analyzer
    python scripts/run_qa_sweep.py --analyzer orphan_hunter
        """
    )

    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        default="medium",
        help="Minimum severity threshold (default: medium)"
    )
    parser.add_argument(
        "--analyzer",
        choices=["promise_keeper", "orphan_hunter", "doc_alignment"],
        help="Run only specific analyzer"
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt to repair findings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --repair, show what would be repaired without making changes"
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write report to file"
    )

    args = parser.parse_args()

    # Convert severity string to enum
    severity_map = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
    }
    severity = severity_map[args.severity]

    # Initialize orchestrator
    print(f"Initializing QA Sweep for: {PROJECT_ROOT}")
    print(f"Severity threshold: {args.severity}")
    print()

    orchestrator = QASweepOrchestrator(PROJECT_ROOT)

    # Determine analyzers
    analyzers = [args.analyzer] if args.analyzer else None

    # Run sweep
    print("Running analyzers...")
    result = await orchestrator.run_sweep(
        analyzers=analyzers,
        severity_threshold=severity,
        repair=args.repair,
        dry_run=args.dry_run
    )

    # Generate report
    report = orchestrator.generate_report(format=args.format)

    # Output
    if args.output:
        args.output.write_text(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)

    # Print detailed findings if not too many
    if len(result.findings) <= 50:
        print("\nDetailed Findings:")
        print("-" * 40)
        for finding in sorted(result.findings, key=lambda f: f.severity.value):
            print(finding.to_summary())
    else:
        print(f"\n{len(result.findings)} findings total. Use --output to save full report.")

    # Return appropriate exit code
    critical_count = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
    high_count = sum(1 for f in result.findings if f.severity == Severity.HIGH)

    if critical_count > 0:
        sys.exit(2)  # Critical issues found
    elif high_count > 0:
        sys.exit(1)  # High severity issues found
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    asyncio.run(main())
