"""
CLI wrapper for legacy component discovery.
Feature: 019-legacy-component-discovery
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.services.discovery_service import DiscoveryService, DiscoveryConfig


def main():
    parser = argparse.ArgumentParser(description="Discover legacy components and scores")
    parser.add_argument("codebase", type=str, help="Path to codebase to scan")
    parser.add_argument("--top", type=int, default=10, help="Number of results to show")
    parser.add_argument("--output", type=str, help="Optional JSON output path")
    args = parser.parse_args()

    service = DiscoveryService(DiscoveryConfig())
    assessments = service.discover_components(args.codebase)
    top = assessments[: args.top]

    payload = [
        {
            "component_id": a.component_id,
            "name": a.name,
            "file_path": a.file_path,
            "composite_score": a.composite_score,
            "migration_recommended": a.migration_recommended,
            "enhancement_opportunities": a.enhancement_opportunities,
            "risk_factors": a.risk_factors,
        }
        for a in top
    ]

    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
