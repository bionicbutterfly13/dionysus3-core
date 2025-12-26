"""
Memory Consolidation Service
Feature: 007-memory-consolidation

Handles the transition of episodic memories to semantic knowledge.
Migrates transient memories into the permanent long-term knowledge graph.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional, List
from uuid import UUID

from api.services.remote_sync import get_neo4j_driver
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger("dionysus.consolidation")

class ConsolidationService:
    """
    Service for consolidating episodic memory into semantic knowledge.
    """

    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def consolidate_episodic_to_semantic(self, limit: int = 50) -> dict[str, Any]:
        """
        Identify high-importance episodic memories and extract semantic facts via Graphiti.
        """
        logger.info(f"Starting memory consolidation (limit={limit})...")
        
        # 1. Fetch episodic memories that haven't been consolidated yet
        # Criteria: importance > 0.7 OR recurrence_count > 3
        cypher = """
        MATCH (m:Memory)
        WHERE m.memory_type = 'episodic'
          AND (m.importance > 0.7 OR m.access_count > 3)
          AND NOT (m)-[:CONSOLIDATED_TO]->()
        RETURN m
        ORDER BY m.importance DESC
        LIMIT $limit
        """
        
        try:
            result = await self._driver.execute_query(cypher, {"limit": limit})
            memories = [row["m"] for row in result]
            
            if not memories:
                return {"status": "no_memories_for_consolidation", "count": 0}
                
            logger.info(f"Found {len(memories)} memories for consolidation. Processing via Graphiti...")
            
            graphiti = await get_graphiti_service()
            consolidated_count = 0
            
            for m in memories:
                # 2. Extract facts via Graphiti
                content = m.get("content", "")
                extraction = await graphiti.ingest_message(
                    content=content,
                    source_description=f"consolidation_of_{m['id']}",
                    valid_at=datetime.fromisoformat(m["created_at"].replace('Z', '+00:00')) if isinstance(m["created_at"], str) else m["created_at"]
                )
                
                # 3. Link original memory to extracted episode
                if extraction.get("episode_uuid"):
                    link_cypher = """
                    MATCH (m:Memory {id: $mem_id})
                    MERGE (e:Episode {uuid: $ep_id})
                    CREATE (m)-[:CONSOLIDATED_TO]->(e)
                    SET m.consolidated_at = datetime()
                    """
                    await self._driver.execute_query(link_cypher, {
                        "mem_id": m["id"],
                        "ep_id": extraction["episode_uuid"]
                    })
                    consolidated_count += 1
            
            return {
                "status": "success",
                "processed": len(memories),
                "consolidated": consolidated_count
            }
            
        except Exception as e:
            logger.error(f"Error in memory consolidation: {e}")
            return {"status": "error", "error": str(e)}

# Factory
_instance: Optional[ConsolidationService] = None

def get_consolidation_service() -> ConsolidationService:
    global _instance
    if _instance is None:
        _instance = ConsolidationService()
    return _instance
