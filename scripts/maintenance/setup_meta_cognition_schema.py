"""
Script to initialize Neo4j indices for Meta-Cognitive Learning (Feature 043).
Uses n8n cypher webhook (Neo4j-only access).
"""
import asyncio
import os
import sys


def ensure_project_root_on_path() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)


ensure_project_root_on_path()

from api.services.remote_sync import RemoteSyncService

async def setup_meta_cognition_indices():
    sync_service = RemoteSyncService()
    
    queries = [
        """
        CREATE FULLTEXT INDEX cognitive_task_index IF NOT EXISTS
        FOR (n:CognitiveEpisode) ON EACH [n.task_query, n.lessons_learned]
        """
    ]
    
    for q in queries:
        try:
            result = await sync_service.run_cypher(q, mode="write")
            if not result.get("success", True):
                print(f"Failed to execute query: {result.get('error', 'unknown error')}")
            else:
                print(f"Executed: {q.strip()}")
        except Exception as e:
            print(f"Failed to execute query: {e}")

    print("Meta-cognition indices setup complete.")

if __name__ == "__main__":
    asyncio.run(setup_meta_cognition_indices())
