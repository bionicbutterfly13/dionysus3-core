"""
Hebbian Service - Manages co-activation learning for knowledge relationships.
"""

import logging
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

    async def apply_decay_batch(self, decay_rate: float = 0.01, min_days_inactive: int = 1) -> int:
        """
        Apply exponential decay to all inactive connections (T046).

        Runs as a scheduled job to decay connections that haven't been
        activated recently.

        Args:
            decay_rate: Decay rate constant (default: 0.01)
            min_days_inactive: Minimum days since last activation to apply decay

        Returns:
            Number of connections updated
        """
        from api.utils.math_utils import weight_decay
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=min_days_inactive)

        # Fetch all connections that need decay
        fetch_cypher = """
        MATCH (n)-[r:RELATES_TO]->(m)
        WHERE r.last_activated IS NOT NULL
          AND datetime(r.last_activated) < datetime($cutoff)
          AND r.weight > 0.01
        RETURN n.uuid as source, m.uuid as target, r.weight as weight, r.last_activated as last_activated
        LIMIT 1000
        """

        updated_count = 0

        async with self.driver.session() as session:
            result = await session.run(fetch_cypher, {"cutoff": cutoff.isoformat()})
            records = await result.data()

            for record in records:
                source_id = record["source"]
                target_id = record["target"]
                current_weight = record["weight"]
                last_activated_str = record["last_activated"]

                # Parse last activation time
                try:
                    last_activated = datetime.fromisoformat(last_activated_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

                # Calculate days since activation
                days_inactive = (datetime.utcnow() - last_activated.replace(tzinfo=None)).total_seconds() / (24 * 3600)

                # Apply decay
                new_weight = weight_decay(current_weight, decay_rate, days_inactive)

                if new_weight != current_weight:
                    update_cypher = """
                    MATCH (n {uuid: $src})-[r:RELATES_TO]->(m {uuid: $tgt})
                    SET r.weight = $weight
                    """
                    await session.run(update_cypher, {
                        "src": source_id,
                        "tgt": target_id,
                        "weight": new_weight
                    })
                    updated_count += 1

        logger.info(f"Applied decay to {updated_count} connections (rate={decay_rate})")
        return updated_count


_service = None
def get_hebbian_service():
    global _service
    if _service is None:
        _service = HebbianService()
    return _service
