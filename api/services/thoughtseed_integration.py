"""
ThoughtSeed Integration Service
Feature: 005-mental-models (Enhanced Integration)

Connects Mental Models to ThoughtSeed 5-layer hierarchy:
- Predictions → ThoughtSeeds at conceptual/abstract layers
- ThoughtSeed competition winners → Basin activation
- Prediction resolution → Basin strengthening (CLAUSE)

Database: Neo4j via WebhookNeo4jDriver (n8n webhooks)
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID, uuid4

from api.services.remote_sync import get_neo4j_driver

logger = logging.getLogger("dionysus.thoughtseed_integration")


# =============================================================================
# ThoughtSeed Layer Mapping
# =============================================================================

DOMAIN_TO_LAYER = {
    "user": "conceptual",
    "self": "metacognitive",
    "world": "abstract",
    "task_specific": "perceptual",
}

def confidence_to_activation(confidence: float) -> float:
    return min(1.0, confidence * 1.2)


# =============================================================================
# ThoughtSeed Integration Service
# =============================================================================


class ThoughtSeedIntegrationService:
    """
    Integrates Mental Models with ThoughtSeed cognitive hierarchy.
    """

    def __init__(self, driver=None):
        """Initialize with Neo4j driver."""
        self._driver = driver or get_neo4j_driver()

    async def generate_thoughtseed_from_prediction(
        self,
        prediction_id: UUID,
        model_id: UUID,
        model_domain: str,
        prediction_content: dict,
        confidence: float,
        context: dict | None = None,
        parent_thought_id: UUID | None = None,
        child_thought_ids: list[UUID] | None = None,
    ) -> dict:
        """
        Create a ThoughtSeed from a model prediction.
        """
        thoughtseed_id = str(uuid4())
        layer = DOMAIN_TO_LAYER.get(model_domain, "conceptual")
        activation_level = confidence_to_activation(confidence)

        packet = {
            "source": "mental_model_prediction",
            "prediction_id": str(prediction_id),
            "model_id": str(model_id),
            "model_domain": model_domain,
            "prediction": prediction_content,
            "context": context,
            "generated_at": datetime.utcnow().isoformat(),
        }

        cypher = """
        MATCH (m:MentalModel {id: $model_id})
        CREATE (t:ThoughtSeed {
            id: $id,
            layer: $layer,
            activation_level: $activation,
            competition_status: 'pending',
            neuronal_packet: $packet,
            parent_thought_id: $parent_id,
            child_thought_ids: $child_ids,
            created_at: datetime()
        })
        CREATE (m)-[:PRODUCED_SEED]->(t)
        
        WITH t
        FOREACH (_ IN CASE WHEN $parent_id IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p:ThoughtSeed {id: $parent_id})
            MERGE (p)-[:HAS_CHILD]->(t)
        )
        RETURN t
        """
        
        try:
            await self._driver.execute_query(cypher, {
                "model_id": str(model_id),
                "id": thoughtseed_id,
                "layer": layer,
                "activation": activation_level,
                "packet": json.dumps(packet),
                "parent_id": str(parent_thought_id) if parent_thought_id else None,
                "child_ids": [str(cid) for cid in (child_thought_ids or [])]
            })
            
            logger.info(f"Created ThoughtSeed {thoughtseed_id} from model {model_id}")
            return {
                "id": thoughtseed_id,
                "layer": layer,
                "activation_level": activation_level,
                "competition_status": "pending"
            }
        except Exception as e:
            logger.error(f"Error creating ThoughtSeed: {e}")
            raise

    async def activate_basins_from_winner(
        self,
        thoughtseed_id: UUID,
        activation_strength: float = 0.5,
    ) -> list[dict]:
        """
        Activate basins when a ThoughtSeed wins.
        """
        cypher = """
        MATCH (t:ThoughtSeed {id: $id, competition_status: 'won'})
        MATCH (m:MentalModel)-[:PRODUCED_SEED]->(t)
        WITH m.constituent_basins as basin_ids
        UNWIND basin_ids as bid
        MATCH (b:Basin {id: bid})
        SET b.activation = b.activation + $strength
        RETURN b
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "id": str(thoughtseed_id),
                "strength": activation_strength
            })
            return [{"id": row["b"]["id"]} for row in result]
        except Exception as e:
            logger.error(f"Error activating basins: {e}")
            return []

# Factory
_instance: Optional[ThoughtSeedIntegrationService] = None

def get_thoughtseed_integration_service(driver=None) -> ThoughtSeedIntegrationService:
    global _instance
    if _instance is None:
        _instance = ThoughtSeedIntegrationService(driver=driver)
    return _instance