#!/usr/bin/env python3
"""
Metacognition Storage Orchestrator
Orchestrates episodic memory storage with API-first + file-backup fallback strategy

Flow:
1. Try to store via consciousness integration pipeline (API: 72.61.78.89:8000)
2. If API unavailable, fallback to local file storage
3. Log results with attractor basin activation
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metacognition_orchestrator")

PROJECT_ROOT = Path(__file__).parent.parent


async def try_api_storage() -> tuple[bool, Dict[str, Any]]:
    """Try to store events via consciousness integration pipeline API."""

    logger.info("Attempting API storage via consciousness integration pipeline...")

    try:
        # Import inside function to avoid errors if dependencies missing
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))

        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")

        from store_metacognition_events import store_metacognition_events

        result = await store_metacognition_events()
        logger.info("API storage successful!")
        return True, result

    except Exception as e:
        logger.warning(f"API storage failed: {e}")
        return False, {"error": str(e)}


def try_file_storage() -> tuple[bool, Dict[str, Any]]:
    """Fallback to file-based storage."""

    logger.info("Falling back to file-based storage...")

    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

        from store_metacognition_events_backup import store_metacognition_events_backup

        result = store_metacognition_events_backup()
        logger.info("File storage successful!")
        return True, result

    except Exception as e:
        logger.error(f"File storage also failed: {e}")
        return False, {"error": str(e)}


async def orchestrate_storage():
    """Main orchestration logic."""

    logger.info("=" * 80)
    logger.info("METACOGNITION STORAGE ORCHESTRATOR")
    logger.info("=" * 80)

    # Try API storage first
    api_success, api_result = await try_api_storage()

    if api_success:
        logger.info("\n✓ Storage via consciousness integration pipeline successful")
        logger.info(f"  Integration event: {api_result.get('integration_event')}")
        logger.info(f"  Decision event: {api_result.get('decision_event')}")
        logger.info(f"  Documentation event: {api_result.get('documentation_event')}")
        return api_result

    # Fallback to file storage
    logger.info("\nAPI unavailable, attempting file-based fallback...")
    file_success, file_result = try_file_storage()

    if file_success:
        logger.info("\n✓ Fallback file storage successful")
        logger.info(f"  Storage location: {file_result.get('storage_location')}")
        logger.info(f"  Total events: {file_result.get('total_events')}")
        logger.info("  Note: Events stored locally. Sync to Neo4j when API becomes available.")
        return file_result

    # Both failed
    logger.error("\nCritical: Both API and file storage failed!")
    return {
        "status": "failed",
        "api_error": api_result.get("error"),
        "file_error": file_result.get("error")
    }


async def main():
    """Main entry point."""

    result = await orchestrate_storage()

    logger.info("\n" + "=" * 80)
    logger.info("RESULT SUMMARY")
    logger.info("=" * 80)

    print("\n" + json.dumps(result, indent=2, default=str))

    # Attractor basin summary
    logger.info("\nAttractor Basins Activated:")
    basins = [
        "cognitive_science",
        "consciousness",
        "systems_theory",
        "machine_learning",
        "philosophy",
        "neuroscience"
    ]
    for basin in basins:
        logger.info(f"  - {basin}")

    # Success/failure determination
    if result.get("status") in ["success", "file_backup_success"]:
        logger.info("\n✓ Metacognition framework successfully stored to episodic memory")
        return 0
    else:
        logger.error("\n✗ Failed to store metacognition framework")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
