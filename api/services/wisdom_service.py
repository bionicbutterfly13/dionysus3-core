"""
Wisdom Service - Manages the distillation pipeline.
"""

import json
import logging
import os
from typing import List, Dict, Any
from api.models.wisdom import WisdomUnit, MentalModel, StrategicPrinciple, CaseStudy
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
        # Prepare specialized properties based on unit type
        props = unit.model_dump()
        wisdom_id = props.pop("wisdom_id")
        wisdom_type = props.pop("type")
        
        # Calculate richness if not already set (T006)
        if unit.richness_score <= 0:
            unit.richness_score = self.calculate_richness(unit)
            props["richness_score"] = unit.richness_score

        cypher = """
        MERGE (w:WisdomUnit {id: $id})
        SET w.type = $type,
            w.name = $name,
            w.summary = $summary,
            w.confidence = $confidence,
            w.richness_score = $richness_score,
            w.created_at = $created_at,
            w.last_updated = datetime(),
            w.metadata = $metadata
        """
        
        # Add type-specific labels and properties
        if isinstance(unit, MentalModel):
            cypher += " SET w:MentalModel, w.core_logic = $core_logic, w.principles = $principles"
        elif isinstance(unit, StrategicPrinciple):
            cypher += " SET w:StrategicPrinciple, w.rationale = $rationale, w.directive = $actionable_directive"
        elif isinstance(unit, CaseStudy):
            cypher += " SET w:CaseStudy, w.problem = $problem_state, w.result = $result_state"

        cypher += """
        WITH w
        UNWIND $provenance as p_id
        MATCH (e:Episodic {uuid: p_id})
        MERGE (w)-[:DERIVED_FROM]->(e)
        """
        
        async with self.driver.session() as session:
            await session.run(cypher, {
                "id": wisdom_id,
                "type": wisdom_type,
                **props,
                "created_at": unit.created_at.isoformat(),
                "metadata": json.dumps(unit.metadata),
                "provenance": unit.provenance_chain
            })
            logger.info(f"Persisted distilled wisdom: {unit.name} ({wisdom_id})")

    def calculate_richness(self, unit: WisdomUnit) -> float:
        """Calculate richness scoring (FR-031-003) based on coverage (T006)."""
        score = 0.0
        # Criteria 1: Multi-session provenance (Evidence weight)
        if len(unit.provenance_chain) > 1:
            score += 0.3
        
        # Criteria 2: Detail density
        if len(unit.summary) > 200:
            score += 0.2
            
        # Criteria 3: Specialized attribute coverage
        if isinstance(unit, MentalModel) and unit.principles:
            score += 0.3
        elif isinstance(unit, StrategicPrinciple) and unit.rationale:
            score += 0.3
        elif isinstance(unit, CaseStudy) and unit.breakthrough_moment:
            score += 0.3
            
        # Criteria 4: Metadata tags
        if unit.metadata:
            score += 0.2
            
        return min(1.0, score)

_service = None
def get_wisdom_service():
    global _service
    if _service is None:
        _service = WisdomService()
    return _service