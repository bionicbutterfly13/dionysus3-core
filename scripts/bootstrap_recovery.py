#!/usr/bin/env python3
"""
Bootstrap Recovery Script
Feature: 002-remote-persistence-safety
Task: T025

Standalone script to restore local PostgreSQL database from remote Neo4j via n8n webhook.
This is the critical recovery mechanism when LLM causes local data loss.

IMPORTANT: This script does NOT connect to Neo4j directly.
All Neo4j access goes through n8n webhooks for safety.

Usage:
    # Dry run (preview what would be recovered)
    python scripts/bootstrap_recovery.py --dry-run

    # Recover all memories
    python scripts/bootstrap_recovery.py

    # Recover specific project
    python scripts/bootstrap_recovery.py --project dionysus-core

    # Recover memories since a specific date
    python scripts/bootstrap_recovery.py --since 2025-01-01T00:00:00

Environment Variables Required:
    N8N_RECALL_URL - n8n recall webhook URL (default: http://localhost:5678/webhook/memory/v1/recall)
    MEMORY_WEBHOOK_TOKEN - HMAC token for webhook authentication
    DATABASE_URL - PostgreSQL connection string (required for actual recovery)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def fetch_memories_from_n8n(
    project_id: Optional[str] = None,
    since: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Fetch memories from Neo4j via n8n recall webhook.

    Args:
        project_id: Optional project filter
        since: Optional datetime ISO string filter

    Returns:
        List of memory dictionaries
    """
    from api.services.hmac_utils import generate_signature

    recall_url = os.getenv(
        "N8N_RECALL_URL", "http://localhost:5678/webhook/memory/v1/recall"
    )
    webhook_token = os.getenv("MEMORY_WEBHOOK_TOKEN", "")

    # Build recall payload
    payload = {
        "action": "recall",
        "filters": {},
    }
    if project_id:
        payload["filters"]["project_id"] = project_id
    if since:
        payload["filters"]["since"] = since

    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = generate_signature(payload_bytes, webhook_token)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(recall_url, content=payload_bytes, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(
                f"n8n recall webhook failed: {response.status_code} - {response.text}"
            )

        result = response.json()
        return result.get("memories", [])


async def insert_memories_to_postgres(
    memories: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Insert recovered memories into local PostgreSQL.

    Args:
        memories: List of memory dictionaries from n8n
        dry_run: If True, only report what would be inserted

    Returns:
        Summary of operation
    """
    if dry_run:
        return {
            "would_insert": len(memories),
            "dry_run": True,
        }

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Import asyncpg for PostgreSQL
    try:
        import asyncpg
    except ImportError:
        logger.error("asyncpg not installed. Install with: pip install asyncpg")
        raise

    # Connect to PostgreSQL
    conn = await asyncpg.connect(database_url)

    try:
        inserted = 0
        skipped = 0
        errors = []

        for memory in memories:
            try:
                # Check if memory already exists
                existing = await conn.fetchval(
                    "SELECT id FROM memories WHERE id = $1",
                    memory["id"],
                )

                if existing:
                    skipped += 1
                    logger.debug(f"Memory {memory['id']} already exists, skipping")
                    continue

                # Insert memory
                await conn.execute(
                    """
                    INSERT INTO memories (
                        id, content, memory_type, importance,
                        source_project, session_id, tags,
                        sync_status, sync_version, synced_at,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7,
                        'synced', $8, NOW(),
                        $9::timestamp, $10::timestamp
                    )
                    """,
                    memory["id"],
                    memory["content"],
                    memory["memory_type"],
                    memory.get("importance", 0.5),
                    memory["source_project"],
                    memory.get("session_id"),
                    memory.get("tags", []),
                    memory.get("sync_version", 1),
                    datetime.fromisoformat(
                        memory["created_at"].replace("Z", "+00:00")
                    )
                    if memory.get("created_at")
                    else datetime.utcnow(),
                    datetime.fromisoformat(
                        memory["updated_at"].replace("Z", "+00:00")
                    )
                    if memory.get("updated_at")
                    else datetime.utcnow(),
                )
                inserted += 1
                logger.debug(f"Inserted memory {memory['id']}")

            except Exception as e:
                errors.append({"memory_id": memory["id"], "error": str(e)})
                logger.error(f"Failed to insert memory {memory['id']}: {e}")

        return {
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors,
            "total": len(memories),
        }

    finally:
        await conn.close()


async def run_recovery(
    project_id: Optional[str] = None,
    since: Optional[str] = None,
    dry_run: bool = False,
    output_file: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run the complete recovery process via n8n webhook.

    Args:
        project_id: Optional project filter
        since: Optional datetime filter
        dry_run: If True, only preview recovery
        output_file: Optional file to write recovered memories

    Returns:
        Recovery summary
    """
    start_time = time.time()

    # Fetch memories via n8n webhook
    logger.info("Fetching memories via n8n recall webhook...")
    filters = []
    if project_id:
        filters.append(f"project={project_id}")
    if since:
        filters.append(f"since={since}")
    filter_str = f" ({', '.join(filters)})" if filters else ""
    logger.info(f"Filters:{filter_str}")

    memories = await fetch_memories_from_n8n(
        project_id=project_id,
        since=since,
    )
    logger.info(f"Found {len(memories)} memories via n8n")

    # Optionally write to file
    if output_file:
        with open(output_file, "w") as f:
            json.dump(memories, f, indent=2, default=str)
        logger.info(f"Wrote {len(memories)} memories to {output_file}")

    # Insert to PostgreSQL (if not dry run)
    if dry_run:
        logger.info("DRY RUN - No changes will be made to local database")
        result = {"would_recover": len(memories), "dry_run": True}
    else:
        logger.info("Inserting memories to local PostgreSQL...")
        result = await insert_memories_to_postgres(memories, dry_run=dry_run)

    duration_ms = int((time.time() - start_time) * 1000)
    result["duration_ms"] = duration_ms
    result["n8n_count"] = len(memories)

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap recovery from Neo4j (via n8n) to local PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--project",
        "-p",
        help="Recover only specific project",
    )
    parser.add_argument(
        "--since",
        "-s",
        help="Recover memories created after this datetime (ISO format)",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Preview what would be recovered without making changes",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write recovered memories to JSON file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check required environment variables
    if not os.getenv("MEMORY_WEBHOOK_TOKEN"):
        logger.warning("MEMORY_WEBHOOK_TOKEN not set - webhook auth may fail")

    if not args.dry_run and not os.getenv("DATABASE_URL"):
        logger.error("DATABASE_URL environment variable required for actual recovery")
        logger.error("Use --dry-run to preview recovery without database connection")
        sys.exit(1)

    # Run recovery
    try:
        result = asyncio.run(
            run_recovery(
                project_id=args.project,
                since=args.since,
                dry_run=args.dry_run,
                output_file=args.output,
            )
        )

        # Print summary
        print("\n" + "=" * 60)
        print("RECOVERY SUMMARY")
        print("=" * 60)

        if args.dry_run:
            print(f"Status: DRY RUN (no changes made)")
            print(f"Memories from n8n: {result.get('n8n_count', 0)}")
            print(f"Would recover: {result.get('would_recover', 0)}")
        else:
            print(f"Status: COMPLETED")
            print(f"Memories from n8n: {result.get('n8n_count', 0)}")
            print(f"Inserted: {result.get('inserted', 0)}")
            print(f"Skipped (already existed): {result.get('skipped', 0)}")
            if result.get("errors"):
                print(f"Errors: {len(result['errors'])}")

        print(f"Duration: {result.get('duration_ms', 0)}ms")
        print("=" * 60)

        if result.get("errors"):
            print("\nErrors:")
            for err in result["errors"][:10]:  # Show first 10
                print(f"  - {err['memory_id']}: {err['error']}")
            if len(result["errors"]) > 10:
                print(f"  ... and {len(result['errors']) - 10} more")

    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
