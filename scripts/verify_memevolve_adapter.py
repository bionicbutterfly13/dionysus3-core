
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.services.memevolve_adapter import get_memevolve_adapter
from api.models.memevolve import TrajectoryData, MemoryIngestRequest, MemoryRecallRequest

async def verify_memevolve_adapter():
    logger.info("Initializing MemEvolveAdapter...")
    adapter = get_memevolve_adapter()
    
    from api.models.memevolve import TrajectoryData, MemoryIngestRequest, MemoryRecallRequest, TrajectoryMetadata

    # 1. Create a mock trajectory
    mock_traj = TrajectoryData(
        query="Test query",
        trajectory=[{"observation": "test"}],
        metadata=TrajectoryMetadata(
            agent_id="test-agent-v1",
            session_id="test-session-123",
            project_id="default",
            success=True,
            reward=1.0
        ),
        summary="Test summary for MemEvolve adapter Phase 4 verification."
    )
    
    ingest_req = MemoryIngestRequest(trajectory=mock_traj)
    
    logger.info("\n1. Testing Trajectory Ingest (Validation)...")
    try:
        # We want to verify THIS call uses Graphiti behind the scenes
        result = await adapter.ingest_trajectory(ingest_req)
        logger.info(f"Ingest Result: {result}")
    except Exception as e:
        logger.error(f"Ingest Logic Failed: {e}")

    logger.info("\n2. Testing Evolve/Recall (Graphiti Connectivity)...")
    try:
        from api.services.graphiti_service import get_graphiti_service
        graphiti = await get_graphiti_service()
        
        # Check if we can recall what we just ingested
        recall_req = MemoryRecallRequest(
            query="Test input for MemEvolve",
            limit=5,
            project_id="default"
        )
        response = await adapter.recall_memories(recall_req)
        
        logger.info(f"Recall Check: Found {response.get('result_count')} memories.")
        for mem in response.get('memories', []):
            logger.info(f" - [{mem.get('similarity', 0):.2f}] {mem.get('content')[:50]}...")

        # Explicitly check for the Trajectory node
        logger.info("\n3. Verifying Trajectory Node Existence (Cypher)...")
        records = await graphiti.execute_cypher(
            "MATCH (t:Trajectory {agent_id: $agent_id}) RETURN t LIMIT 1",
            {"agent_id": "test-agent-v1"}
        )
        if records:
            logger.info(f"SUCCESS: Found Trajectory node: {records[0].get('t', {}).get('id')}")
        else:
            logger.error("FAILURE: Trajectory node not found!")
            
    except Exception as e:
        logger.error(f"Recall/Verify Logic Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_memevolve_adapter())
