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
            logger.warning(f"Review item {item_id} not found for re-injection.")
            return False
            
        candidate = result[0]["c"]
        reason = candidate.get("reason", "")
        
        logger.info(f"Re-injecting reviewed item: {reason} ({item_id})")

        try:
            # Logic depends on what failed
            if "Avatar" in reason or "Extraction" in reason:
                # Corrected avatar data should be ingested into Graphiti
                from api.services.graphiti_service import get_graphiti_service
                graphiti = await get_graphiti_service()
                
                # Ingest the corrected data
                await graphiti.ingest_message(
                    content=f"CORRECTED AVATAR INSIGHT: {json.dumps(corrected_data)}",
                    source_description="human_reviewed_avatar_correction",
                    group_id="ias_avatar"
                )
                logger.info(f"Successfully re-injected corrected avatar data for {item_id}")
                
            elif "Aspect" in reason or "Boardroom" in reason:
                # Corrected boardroom aspect
                await self.upsert_aspect(
                    user_id=corrected_data.get("user_id", "dionysus_system"),
                    name=corrected_data.get("name"),
                    role=corrected_data.get("role"),
                    status=corrected_data.get("status", "Active"),
                    metadata=corrected_data.get("metadata")
                )
                logger.info(f"Successfully re-injected corrected aspect for {item_id}")
                
            else:
                logger.warning(f"No specific re-injection logic found for reason: {reason}")
                # We still archive it if the user provided data
                
            # Archive the candidate after successful re-injection
            await self.delete_review_item(item_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to re-inject reviewed item {item_id}: {e}")
            return False

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

    async def delete_review_item(self, item_id: str) -> bool:
        """Remove an item from the review queue."""
        cypher = "MATCH (c:HumanReviewCandidate {id: $id}) DETACH DELETE c RETURN count(c) as deleted"
        result = await self._driver.execute_query(cypher, {"id": item_id})
        return result[0]["deleted"] > 0

# Factory
_instance = None
def get_aspect_service() -> AspectService:
    global _instance
    if _instance is None:
        _instance = AspectService()
    return _instance
