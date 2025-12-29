"""
Wisdom Service - Manages the distillation pipeline.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from api.models.wisdom import WisdomUnit, WisdomType, MentalModel, StrategicPrinciple, CaseStudy
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger("dionysus.wisdom_service")

class WisdomService:
    def __init__(self, driver=None):
        self.driver = driver or get_neo4j_driver()

    def load_raw_extracts(self, file_path: str = "wisdom_extraction_raw.json") -> List[Dict[str, Any]]:
        """Load raw insights from fleet distillation."""
        if not os.path.exists(file_path):
            logger.warning(f"Raw extracts file not found: {file_path}")
            return []
            
        with open(file_path, "r") as f:
            return json.load(f)

    async def persist_distilled_unit(self, unit: WisdomUnit):
        """Persist a canonical wisdom unit to Neo4j (T005)."""
        cypher = """
        CREATE (w:WisdomUnit {
            id: $id,
            type: $type,
            name: $name,
            description: $description,
            richness_score: $score,
            created_at: $created_at,
            metadata: $metadata
        })
        WITH w
        UNWIND $provenance as p_id
        MATCH (e:Episodic {uuid: p_id})
        CREATE (w)-[:DERIVED_FROM]->(e)
        """
        async with self.driver.session() as session:
            await session.run(cypher, {
                "id": unit.id,
                "type": unit.wisdom_type.value,
                "name": unit.name,
                "description": unit.description,
                "score": unit.richness_score,
                "created_at": unit.created_at.isoformat(),
                "metadata": json.dumps(unit.metadata),
                "provenance": unit.provenance_ids
            })
            logger.info(f"Persisted distilled wisdom: {unit.name}")

_service = None
def get_wisdom_service():
    global _service
    if _service is None:
        _service = WisdomService()
    return _service