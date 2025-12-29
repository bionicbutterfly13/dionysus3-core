"""
Hebbian Service - Manages co-activation learning for knowledge relationships.
"""

import logging
from typing import List, Optional
from datetime import datetime
from api.models.hebbian import HebbianConnection
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger("dionysus.hebbian")

class HebbianService:
    def __init__(self, driver=None):
        self.driver = driver or get_neo4j_driver()

    async def record_coactivation(self, source_id: str, target_id: str, v1: float = 1.0, v2: float = 1.0):
        """Record a co-activation event between two nodes (T045)."""
        # 1. Fetch current weight from Neo4j
        cypher = """
        MATCH (n {uuid: $src})-[r:RELATES_TO]->(m {uuid: $tgt})
        RETURN r.weight as weight
        """
        async with self.driver.session() as session:
            res = await session.run(cypher, {"src": source_id, "tgt": target_id})
            record = await res.single()
            current_weight = record["weight"] if record and record["weight"] is not None else 0.5
            
            # 2. Apply Hebbian update
            conn = HebbianConnection(source_id=source_id, target_id=target_id, weight=current_weight)
            conn.apply_hebbian_update(v1, v2)
            
            # 3. Persist back to Neo4j (T047)
            update_cypher = """
            MATCH (n {uuid: $src})-[r:RELATES_TO]->(m {uuid: $tgt})
            SET r.weight = $weight,
                r.last_activated = $now
            """
            await session.run(update_cypher, {
                "src": source_id,
                "tgt": target_id,
                "weight": conn.weight,
                "now": conn.last_activated.isoformat()
            })
            
            logger.info(f"Updated Hebbian weight for {source_id}->{target_id}: {conn.weight:.4f}")

_service = None
def get_hebbian_service():
    global _service
    if _service is None:
        _service = HebbianService()
    return _service
