import asyncio
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4
import logging

# Add project root to path
sys.path.append(os.getcwd())

from api.services.graphiti_service import get_graphiti_service
from api.agents.consolidated_memory_stores import get_consolidated_memory_store, DevelopmentEpisode, RiverStage
from api.models.memevolve import TrajectoryData
from api.models.autobiographical import DevelopmentArchetype

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_protocol_060")

async def verify_protocol_060():
    logger.info("Initializing Verification for Protocol 060...")
    
    # Initialize Services
    graphiti = await get_graphiti_service()
    store = get_consolidated_memory_store()
    
    # Test Data
    test_run_id = uuid4().hex[:8]
    traj_id = f"traj_test_{test_run_id}"
    logger.info(f"Test Run ID: {test_run_id}")
    
    # 1. SETUP: Create a Mock Trajectory Node
    logger.info("Step 1: Creating Mock Trajectory Node...")
    setup_cypher = """
    MERGE (t:Trajectory {id: $traj_id})
    SET t.summary = 'Protocol 060 Verification Run',
        t.created_at = datetime()
    RETURN t.id
    """
    await graphiti.execute_cypher(setup_cypher, {"traj_id": traj_id})
    
    # 2. PHASE 1 TEST: Ingest Entities linking to Trajectory
    logger.info("Step 2: Testing GraphitiService.ingest_extracted_relationships...")
    
    initial_rels = [
        {
            "source": f"EntityA_{test_run_id}",
            "target": f"EntityB_{test_run_id}",
            "relation_type": "TESTS",
            "evidence": "Verification evidence",
            "status": "approved"
        }
    ]
    
    # Simulate MemEvolve calling Graphiti with prefixed ID
    source_id_arg = f"memevolve:{traj_id}"
    
    ingest_result = await graphiti.ingest_extracted_relationships(
        relationships=initial_rels,
        source_id=source_id_arg
    )
    logger.info(f"Ingest Result: {ingest_result}")
    
    # 3. PHASE 2 TEST: Create Episode linking to Trajectory
    logger.info("Step 3: Testing ConsolidatedMemoryStore link to Trajectory...")
    
    episode_id = f"ep_test_{test_run_id}"
    episode = DevelopmentEpisode(
        episode_id=episode_id,
        journey_id="journey_verification",
        title="Protocol 060 Verification Episode",
        summary="Testing linking logic",
        narrative="We verified the linkage.",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        events=[], 
        source_trajectory_ids=[traj_id], # CRITICAL: Linking to Trajectory
        dominant_archetype=DevelopmentArchetype.SAGE,
        river_stage=RiverStage.TRIBUTARY
    )
    
    success = await store.create_episode(episode)
    logger.info(f"Episode Creation Success: {success}")

    # 4. VERIFICATION: Check Graph Structure
    logger.info("Step 4: Audit Graph Structure...")
    
    # Check 1: Entity -> Trajectory Link
    check_entity_cypher = """
    MATCH (e:Entity {name: $entity_name})-[r:MENTIONED_IN]->(t:Trajectory {id: $traj_id})
    RETURN count(r) as link_count
    """
    res1 = await graphiti.execute_cypher(check_entity_cypher, {
        "entity_name": f"EntityA_{test_run_id}",
        "traj_id": traj_id
    })
    entity_link_count = res1[0]['link_count'] if res1 else 0
    
    # Check 2: Episode -> Trajectory Link
    check_episode_cypher = """
    MATCH (ep:DevelopmentEpisode {id: $ep_id})-[r:SUMMARIZES]->(t:Trajectory {id: $traj_id})
    RETURN count(r) as link_count
    """
    res2 = await graphiti.execute_cypher(check_episode_cypher, {
        "ep_id": episode_id,
        "traj_id": traj_id
    })
    episode_link_count = res2[0]['link_count'] if res2 else 0
    
    # Check 3: NO Redundant Episodes
    # Graphiti ingest used to create Episodes for facts. We want to ensure NO Episode is created for the relationship evidence.
    # The only episode should be the one we manually created.
    check_redundancy_cypher = """
    MATCH (n:Episode)
    WHERE n.source_description = $source_id
    RETURN count(n) as redundancy_count
    """
    res3 = await graphiti.execute_cypher(check_redundancy_cypher, {"source_id": source_id_arg})
    redundancy_count = res3[0]['redundancy_count'] if res3 else 0

    logger.info("-" * 40)
    logger.info(f"VERIFICATION RESULTS:")
    logger.info(f"Entity->Trajectory Links (Expected 1): {entity_link_count}")
    logger.info(f"Episode->Trajectory Links (Expected 1): {episode_link_count}")
    logger.info(f"Redundant Fact Episodes    (Expected 0): {redundancy_count}")
    logger.info("-" * 40)
    
    if entity_link_count >= 1 and episode_link_count >= 1 and redundancy_count == 0:
        logger.info("✅ PROTOCOL 060 VERIFICATION PASSED")
    else:
        logger.error("❌ PROTOCOL 060 VERIFICATION FAILED")

    # Cleanup
    logger.info("Cleaning up...")
    cleanup_cypher = """
    MATCH (n) WHERE n.id IN [$traj_id, $ep_id] DETACH DELETE n
    WITH n
    MATCH (e:Entity) WHERE e.name IN [$ename1, $ename2] DETACH DELETE e
    """
    # Note: Cleanup simplified for demo, robust cleanup might be needed if IDs vary.
    # Just deleting by ID is safe for traj/ep.
    await graphiti.execute_cypher("""
        MATCH (t:Trajectory {id: $traj_id}) DETACH DELETE t
    """, {"traj_id": traj_id})
    await graphiti.execute_cypher("""
        MATCH (ep:DevelopmentEpisode {id: $ep_id}) DETACH DELETE ep
    """, {"ep_id": episode_id})
    await graphiti.execute_cypher("""
        MATCH (e:Entity) WHERE e.name IN [$n1, $n2] DETACH DELETE e
    """, {"n1": f"EntityA_{test_run_id}", "n2": f"EntityB_{test_run_id}"})


if __name__ == "__main__":
    asyncio.run(verify_protocol_060())
