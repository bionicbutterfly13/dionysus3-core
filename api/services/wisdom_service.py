"""
Wisdom Distillation Service
Feature: 031-wisdom-distillation

Handles aggregation and persistence of distilled wisdom units.
"""

import json
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from api.models.wisdom import WisdomUnit, WisdomType, MentalModel, StrategicPrinciple, CaseStudy
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger(__name__)

class WisdomService:
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    def load_raw_extracts(self, file_path: str = "wisdom_extraction_raw.json") -> List[Dict]:
        """Load raw wisdom fragments from the fleet output."""
        if not os.path.exists(file_path):
            logger.warning(f"Raw extracts file not found: {file_path}")
            return []
            
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse raw extracts: {e}")
                return []

    async def persist_distilled_unit(self, unit: WisdomUnit) -> bool:
        """
        Write a distilled wisdom unit to Neo4j.
        T005: Creates links to original episodes in the provenance chain.
        """
        # 1. Persist the unit node
        cypher = """
        MERGE (w:WisdomUnit {id: $wisdom_id})
        SET w.name = $name,
            w.type = $type,
            w.summary = $summary,
            w.confidence = $confidence,
            w.richness_score = $richness,
            w.last_updated = datetime(),
            w.metadata = $metadata
        RETURN w.id
        """
        params = {
            "wisdom_id": unit.wisdom_id,
            "name": unit.name,
            "type": unit.type.value,
            "summary": unit.summary,
            "confidence": unit.confidence,
            "richness": unit.richness_score,
            "metadata": json.dumps(unit.model_dump(mode='json', exclude={"wisdom_id", "name", "type", "summary", "confidence", "richness"}))
        }
        
        try:
            await self._driver.execute_query(cypher, params)
            
            # 2. Link to Provenance (DERIVED_FROM)
            for session_id in unit.provenance_chain:
                link_cypher = """
                MATCH (w:WisdomUnit {id: $wisdom_id})
                MATCH (e:Episode) WHERE e.source_description CONTAINS $session_id
                MERGE (w)-[:DERIVED_FROM]->(e)
                """
                await self._driver.execute_query(link_cypher, {
                    "wisdom_id": unit.wisdom_id,
                    "session_id": session_id
                })
                
            return True
        except Exception as e:
            logger.error(f"Failed to persist wisdom unit {unit.wisdom_id}: {e}")
            return False

_wisdom_service: Optional[WisdomService] = None

def get_wisdom_service() -> WisdomService:
    global _wisdom_service
    if _wisdom_service is None:
        _wisdom_service = WisdomService()
    return _wisdom_service
