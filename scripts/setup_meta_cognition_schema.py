"""
Script to initialize Neo4j indices for Meta-Cognitive Learning (Feature 043).
Uses Graphiti internal driver to bypass n8n for local setup.
"""
import asyncio
import os
from api.services.graphiti_service import get_graphiti_service

async def setup_meta_cognition_indices():
    # Use GraphitiService to get a direct Bolt connection
    # Ensure environment variables are set for Bolt
    os.environ["NEO4J_URI"] = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    service = await get_graphiti_service()
    graphiti = service._get_graphiti()
    driver = graphiti.driver # This is the graphiti_core Neo4j driver
    
    queries = [
        """
        CREATE FULLTEXT INDEX cognitive_task_index IF NOT EXISTS
        FOR (n:CognitiveEpisode) ON EACH [n.task_query, n.lessons_learned]
        """
    ]
    
    for q in queries:
        try:
            # graphiti driver has execute_query
            await driver.execute_query(q)
            print(f"Executed: {q.strip()}")
        except Exception as e:
            print(f"Failed to execute query: {e}")

    print("Meta-cognition indices setup complete.")

if __name__ == "__main__":
    asyncio.run(setup_meta_cognition_indices())