#!/usr/bin/env python3
"""
Insight Generator - Queries Graphiti and memory for current system state.
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insight_generator")

# Load environment variables
load_dotenv()

# Force VPS Neo4j if not specified
if not os.getenv("NEO4J_URI"):
    os.environ["NEO4J_URI"] = "bolt://72.61.78.89:7687"
    logger.info(f"NEO4J_URI not set, defaulting to VPS: {os.environ['NEO4J_URI']}")

from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, GPT5_NANO

async def generate_insights():
    logger.info("Starting Insight Generation...")
    
    try:
        graphiti = await get_graphiti_service()
        
        # 1. Fetch recent episodes
        logger.info("Fetching recent episodes...")
        episodes_cypher = """
        MATCH (e:Episode)
        WHERE e.group_id = 'dionysus'
        RETURN e.uuid as uuid, e.episode_body as body, e.reference_time as time
        ORDER BY e.reference_time DESC
        LIMIT 10
        """
        recent_episodes = await graphiti.execute_cypher(episodes_cypher)
        
        # 2. Fetch active attractor basins
        logger.info("Fetching active attractor basins...")
        basins_cypher = """
        MATCH (b:MemoryCluster)
        WHERE b.basin_state IN ['active', 'activating', 'saturated']
        RETURN b.name as name, b.basin_state as state, b.current_activation as activation
        ORDER BY b.current_activation DESC
        LIMIT 5
        """
        active_basins = await graphiti.execute_cypher(basins_cypher)
        
        # 3. Fetch IWMT Coherence
        logger.info("Fetching IWMT coherence...")
        iwmt_cypher = """
        MATCH (i:IWMTCoherence)
        RETURN i.consciousness_level as level, i.spatial_coherence as spatial, i.temporal_coherence as temporal
        ORDER BY i.created_at DESC
        LIMIT 1
        """
        iwmt_state = await graphiti.execute_cypher(iwmt_cypher)
        
        # 4. Fetch semantic entities related to current focus
        # Using branch name as a hint if possible, or just general concepts
        logger.info("Fetching semantic entities...")
        entities_cypher = """
        MATCH (n:Entity)
        RETURN n.name as name, n.summary as summary
        ORDER BY n.updated_at DESC
        LIMIT 10
        """
        recent_entities = await graphiti.execute_cypher(entities_cypher)
        
        # 5. Synthesize Worldview
        logger.info("Synthesizing Synthetic Worldview...")
        context = {
            "recent_episodes": recent_episodes,
            "active_basins": active_basins,
            "iwmt_state": iwmt_state[0] if iwmt_state else None,
            "recent_entities": recent_entities
        }
        
        system_prompt = (
            "You are the Dionysus Worldview Synthesis engine. "
            "Analyze the provided graph state and episodic context to create a "
            "coherent summary of the current project trajectory and system state."
        )
        
        user_message = f"System State Snapshot:\n{json.dumps(context, indent=2, default=str)}"
        
        worldview = await chat_completion(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            model=GPT5_NANO,
            max_tokens=1000
        )
        
        # Prepare final report
        report = {
            "timestamp": datetime.now().isoformat(),
            "worldview_summary": worldview,
            "active_basins": active_basins,
            "consciousness_level": iwmt_state[0].get("level") if iwmt_state else 0.0,
            "recent_insights": [e.get("name") for e in recent_entities]
        }
        
        print("\n" + "="*50)
        print("DIONYSUS INSIGHT REPORT")
        print("="*50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Consciousness Level: {report['consciousness_level']}")
        print("\nWORLDVIEW SUMMARY:")
        print(worldview)
        print("\nACTIVE BASINS:")
        for b in active_basins:
            print(f"- {b['name']} ({b['state']}): {b['activation']:.2f}")
        print("="*50 + "\n")
        
        return report

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(generate_insights())
