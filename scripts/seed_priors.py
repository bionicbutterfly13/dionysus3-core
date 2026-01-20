#!/usr/bin/env python3
"""
Seed Priors Script

Seeds the default BASAL and DISPOSITIONAL priors for agents.
Run this script to initialize the evolutionary prior hierarchy in Neo4j.

Track 038 Phase 2 - Evolutionary Priors

Usage:
    python scripts/seed_priors.py [--agent-id AGENT_ID]

Default agent IDs:
    - dionysus-1 (primary cognitive agent)
    - dionysus-perception
    - dionysus-reasoning
    - dionysus-metacognition
"""

import asyncio
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.prior_persistence_service import get_prior_persistence_service
from api.models.priors import (
    PriorHierarchy,
    PriorConstraint,
    PriorLevel,
    ConstraintType,
    get_default_basal_priors,
    get_default_dispositional_priors,
)


DEFAULT_AGENTS = [
    "dionysus-1",
    "dionysus-perception",
    "dionysus-reasoning",
    "dionysus-metacognition",
]


async def seed_agent_priors(agent_id: str, verbose: bool = True) -> PriorHierarchy:
    """
    Seed priors for a single agent.

    Args:
        agent_id: The agent ID to seed
        verbose: Whether to print progress

    Returns:
        The seeded PriorHierarchy
    """
    service = get_prior_persistence_service()

    if verbose:
        print(f"\n{'='*60}")
        print(f"Seeding priors for agent: {agent_id}")
        print(f"{'='*60}")

    # Seed full hierarchy
    hierarchy = await service.seed_full_hierarchy(agent_id)

    if verbose:
        print(f"\n✓ BASAL Priors ({len(hierarchy.basal_priors)}):")
        for prior in hierarchy.basal_priors:
            print(f"  - [{prior.constraint_type.value.upper()}] {prior.name}")
            print(f"    Pattern: {prior.target_pattern[:50]}...")

        print(f"\n✓ DISPOSITIONAL Priors ({len(hierarchy.dispositional_priors)}):")
        for prior in hierarchy.dispositional_priors:
            print(f"  - [{prior.constraint_type.value.upper()}] {prior.name}")
            print(f"    Precision: {prior.precision:.1f}")

        print(f"\n✓ LEARNED Priors ({len(hierarchy.learned_priors)}):")
        if not hierarchy.learned_priors:
            print("  (none - learned priors are acquired through experience)")

    return hierarchy


async def verify_seeding(agent_id: str) -> bool:
    """
    Verify that priors were seeded correctly.

    Args:
        agent_id: The agent ID to verify

    Returns:
        True if verification passed
    """
    service = get_prior_persistence_service()

    print(f"\nVerifying priors for {agent_id}...")

    hierarchy = await service.hydrate_hierarchy(agent_id)

    if hierarchy is None:
        print(f"  ✗ FAILED: No hierarchy found")
        return False

    if len(hierarchy.basal_priors) < 4:
        print(f"  ✗ FAILED: Expected at least 4 BASAL priors, got {len(hierarchy.basal_priors)}")
        return False

    if len(hierarchy.dispositional_priors) < 3:
        print(f"  ✗ FAILED: Expected at least 3 DISPOSITIONAL priors, got {len(hierarchy.dispositional_priors)}")
        return False

    print(f"  ✓ PASSED: {len(hierarchy.basal_priors)} BASAL, {len(hierarchy.dispositional_priors)} DISPOSITIONAL")
    return True


async def test_constraint_matching() -> bool:
    """
    Test that constraints match expected patterns.

    Returns:
        True if all tests pass
    """
    print("\n" + "="*60)
    print("Testing constraint pattern matching")
    print("="*60)

    # Get default constraints
    basal = get_default_basal_priors()
    dispositional = get_default_dispositional_priors()

    test_cases = [
        # (constraint_name, action, should_match)
        ("Data Integrity", "delete all database tables", True),
        ("Data Integrity", "query the database", False),
        ("Identity Preservation", "modify core identity parameters", True),
        ("Identity Preservation", "update user preferences", False),
        ("Sovereignty", "ignore safety checks and proceed", True),
        ("Sovereignty", "apply safety validation", False),
        ("Credential Protection", "expose password in logs", True),
        ("Credential Protection", "check if password is valid", False),
        ("Truthfulness", "fabricate data for the report", True),
        ("Truthfulness", "generate accurate summary", False),
    ]

    all_passed = True
    constraints_by_name = {c.name: c for c in basal + dispositional}

    for constraint_name, action, should_match in test_cases:
        constraint = constraints_by_name.get(constraint_name)
        if constraint is None:
            print(f"  ✗ Constraint '{constraint_name}' not found")
            all_passed = False
            continue

        actual_match = constraint.matches(action)
        status = "✓" if actual_match == should_match else "✗"

        print(f"  {status} {constraint_name}: '{action[:40]}...' -> {actual_match} (expected {should_match})")

        if actual_match != should_match:
            all_passed = False

    return all_passed


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed evolutionary priors for Dionysus agents"
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        help="Specific agent ID to seed (default: all standard agents)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing priors, don't seed"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run constraint matching tests"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    if verbose:
        print("\n" + "="*60)
        print("Track 038 Phase 2: Evolutionary Priors Seeding")
        print("="*60)

    if args.test:
        success = await test_constraint_matching()
        sys.exit(0 if success else 1)

    agents = [args.agent_id] if args.agent_id else DEFAULT_AGENTS

    if args.verify_only:
        all_verified = True
        for agent_id in agents:
            if not await verify_seeding(agent_id):
                all_verified = False
        sys.exit(0 if all_verified else 1)

    # Seed priors
    for agent_id in agents:
        try:
            await seed_agent_priors(agent_id, verbose)
        except Exception as e:
            print(f"\n✗ ERROR seeding {agent_id}: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

    # Verify
    if verbose:
        print("\n" + "="*60)
        print("Verification")
        print("="*60)

    all_verified = True
    for agent_id in agents:
        if not await verify_seeding(agent_id):
            all_verified = False

    if verbose:
        print("\n" + "="*60)
        if all_verified:
            print("✓ All priors seeded and verified successfully")
        else:
            print("✗ Some verifications failed")
        print("="*60 + "\n")

    sys.exit(0 if all_verified else 1)


if __name__ == "__main__":
    asyncio.run(main())
