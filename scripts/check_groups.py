import asyncio
import logging
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import os
print(f"DEBUG: NEO4J_URI={os.getenv('NEO4J_URI')}")
print(f"DEBUG: NEO4J_USER={os.getenv('NEO4J_USER')}")

from api.services.graphiti_service import get_graphiti_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_groups")

async def main():
    graphiti = await get_graphiti_service()
    
    # Check Groups
    query_groups = """
    MATCH (g:Group)
    RETURN g.id as group_id, count { (e:Episode)-[:BELONGS_TO]->(g) } as episode_count
    """
    logger.info("Checking Groups...")
    groups = await graphiti.execute_cypher(query_groups)
    print("\n--- GROUPS ---")
    if not groups:
        print("No Groups found!")
    for g in groups:
        print(f"Group: {g['group_id']} | Episodes: {g['episode_count']}")
    
    # Check if ANY Episodes exist (maybe they aren't linked to groups?)
    query_episodes = "MATCH (e:Episode) RETURN count(e) as total"
    total_episodes = await graphiti.execute_cypher(query_episodes)
    print(f"\nTotal Episodes in DB: {total_episodes[0]['total']}")

if __name__ == "__main__":
    asyncio.run(main())
