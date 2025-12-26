"""
Unified Aspect Service
Single Source of Truth for Boardroom Aspects (Inner Parts)

Integrates with Neo4j for state and Graphiti for temporal history.
All projects (Dionysus, Marketing, KB) use this service.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from api.services.remote_sync import get_neo4j_driver
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger("dionysus.aspect_service")

class AspectService:
    """
    Manages Boardroom Aspects with temporal integrity.
    """

    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def get_all_aspects(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch current boardroom state."""
        cypher = """
        MATCH (u:User {id: $user_id})-[:HAS_ASPECT]->(a:Aspect)
        RETURN a
        ORDER BY a.name ASC
        """
        result = await self._driver.execute_query(cypher, {"user_id": user_id})
        return [row["a"] for row in result]

    async def upsert_aspect(self, user_id: str, name: str, role: str, status: str = "Active", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Add or update an aspect. Records a full snapshot history in Graphiti.
        """
        aspect_id = str(uuid4())
        timestamp = datetime.utcnow()
        
        # 1. Update Neo4j State
        cypher = """
        MATCH (u:User {id: $user_id})
        MERGE (a:Aspect {name: $name})<-[:HAS_ASPECT]-(u)
        SET a.role = $role,
            a.status = $status,
            a.metadata = $metadata,
            a.updated_at = datetime($ts)
        ON CREATE SET 
            a.id = $id,
            a.created_at = datetime($ts)
        RETURN a
        """
        
        params = {
            "user_id": user_id,
            "name": name,
            "role": role,
            "status": status,
            "metadata": json.dumps(metadata or {}),
            "id": aspect_id,
            "ts": timestamp.isoformat()
        }
        
        result = await self._driver.execute_query(cypher, params)
        aspect = result[0]["a"]
        
        # 2. Record Full Snapshot Temporal History in Graphiti
        try:
            graphiti = await get_graphiti_service()
            # We record the full snapshot as an episode
            snapshot = {
                "aspect_name": name,
                "role": role,
                "status": status,
                "metadata": metadata or {},
                "user_id": user_id,
                "event": "upsert"
            }
            await graphiti.ingest_message(
                content=f"SNAPSHOT: Aspect Boardroom State - {json.dumps(snapshot)}",
                source_description="aspect_snapshot_upsert",
                valid_at=timestamp
            )
        except Exception as e:
            logger.warning(f"Failed to record aspect history in Graphiti: {e}")
            await self.add_to_human_review("Graphiti History Failure", {"aspect": name, "error": str(e)})

        return aspect

    async def reinject_reviewed_item(self, item_id: str, corrected_data: Dict[str, Any]) -> bool:
        """
        Manually resolve a human review item and execute its intended logic.
        """
        # Fetch the item first to know the context
        cypher = "MATCH (c:HumanReviewCandidate {id: $id}) RETURN c"
        result = await self._driver.execute_query(cypher, {"id": item_id})
        if not result:
            return False
            
        candidate = result[0]["c"]
        reason = candidate.get("reason", "")
        
        # Logic depends on what failed
        if "Avatar Extraction" in reason:
            # Re-process avatar data with corrected text
            from api.agents.knowledge_agent import KnowledgeAgent
            agent = KnowledgeAgent()
            # In a real scenario, we'd call the extraction logic again or just upsert the corrected JSON
            # For now, we archive the candidate
            await self.delete_review_item(item_id)
            return True
            
        return False

    async def delete_review_item(self, item_id: str) -> bool:

    async def remove_aspect(self, user_id: str, name: str) -> bool:
        """Archive an aspect (detach from user)."""
        timestamp = datetime.utcnow()
        cypher = """
        MATCH (u:User {id: $user_id})-[r:HAS_ASPECT]->(a:Aspect {name: $name})
        DELETE r
        SET a.archived_at = datetime($ts)
        RETURN count(a) as removed
        """
        result = await self._driver.execute_query(cypher, {"user_id": user_id, "name": name, "ts": timestamp.isoformat()})
        
        if result and result[0]["removed"] > 0:
            # Record in Graphiti
            try:
                graphiti = await get_graphiti_service()
                await graphiti.ingest_message(
                    content=f"Aspect '{name}' removed from boardroom for user {user_id}",
                    source_description="aspect_removal",
                    valid_at=timestamp
                )
            except: pass
            return True
        return False

    async def add_to_human_review(self, reason: str, data: Any, confidence: float = 0.0):
        """
        Add low-confidence content to review queue.
        """
        cypher = """
        CREATE (c:HumanReviewCandidate {
            id: randomUUID(),
            reason: $reason,
            payload: $data,
            confidence: $confidence,
            created_at: datetime()
        })
        """
        await self._driver.execute_query(cypher, {
            "reason": reason,
            "data": json.dumps(data, default=str),
            "confidence": confidence
        })
        logger.info(f"Added item to human review: {reason}")

    async def get_human_review_items(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch pending items needing human oversight."""
        cypher = """
        MATCH (c:HumanReviewCandidate)
        RETURN c
        ORDER BY c.created_at DESC
        LIMIT $limit
        """
        result = await self._driver.execute_query(cypher, {"limit": limit})
        return [row["c"] for row in result]

# Factory
_instance = None
def get_aspect_service() -> AspectService:
    global _instance
    if _instance is None:
        _instance = AspectService()
    return _instance
