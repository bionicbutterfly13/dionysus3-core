#!/usr/bin/env python3
"""
Test script for MemEvolve Phase 4: Heartbeat Integration.
Verifies that unconsumed trajectories are picked up by the heartbeat,
processed for patterns, and result in strategic memory generation.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from api.services.remote_sync import get_neo4j_driver
from api.services.heartbeat_service import get_heartbeat_service

async def setup_mock_trajectory():
    """Inject a mock unconsumed trajectory into Neo4j."""
    driver = get_neo4j_driver()
    trajectory_id = f"test-traj-{uuid4()}"
    
    print(f"Creating mock trajectory: {trajectory_id}")
    
    async with driver.session() as session:
        await session.run(
            """
            CREATE (t:Trajectory {
                id: $id,
                summary: $summary,
                metadata: $metadata,
                created_at: datetime()
            })
            """,
            id=trajectory_id,
            summary="Agent encountered a recurring failure when trying to parse dates in the CSV tool.",
            metadata=json.dumps({"agent_id": "test-analyst", "type": "integration-test"})
        )
    return trajectory_id

async def verify_processed(trajectory_id):
    """Verify that the trajectory has been marked as processed."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (t:Trajectory {id: $id}) RETURN t.processed_at as processed_at",
            id=trajectory_id
        )
        record = await result.single()
        return record["processed_at"] is not None if record else False

async def check_strategic_memories():
    """Check for newly created strategic memories."""
    driver = get_neo4j_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (m:Memory {memory_type: 'strategic'})
            WHERE m.created_at > datetime() - duration('PT5M')
            RETURN m.content as content, m.source as source
            ORDER BY m.created_at DESC
            LIMIT 5
            """
        )
        return await result.data()

async def main():
    print("=== Testing MemEvolve Phase 4 Integration ===")
    
    # 1. Setup
    traj_id = await setup_mock_trajectory()
    
    # 2. Trigger Heartbeat
    print("\nTriggering manual heartbeat...")
    service = get_heartbeat_service()
    
    # Mocking environment for manual trigger
    try:
        summary = await service.heartbeat()
        print(f"Heartbeat #{summary.heartbeat_number} completed.")
        print(f"Narrative: {summary.narrative}")
    except Exception as e:
        print(f"Heartbeat failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Verification
    print("\nVerifying results...")
    
    is_processed = await verify_processed(traj_id)
    if is_processed:
        print(f"✅ Trajectory {traj_id} successfully marked as processed.")
    else:
        print(f"❌ Trajectory {traj_id} was NOT processed.")

    strategic_mems = await check_strategic_memories()
    if strategic_mems:
        print(f"✅ Found {len(strategic_mems)} new strategic memories:")
        for m in strategic_mems:
            print(f"   - [{m['source']}] {m['content']}")
    else:
        print("❌ No new strategic memories were generated.")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
