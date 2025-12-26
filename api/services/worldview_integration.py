"""
Worldview Integration Service
Feature: 005-mental-models (US6 - Identity/Worldview Integration)

Implements bidirectional flow between Mental Models and Identity/Worldview:
- Prediction errors update beliefs via precision-weighted accumulation
- Predictions are filtered by worldview alignment (Bayesian prior + gating)

Database: Neo4j via WebhookNeo4jDriver (n8n webhooks)
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import httpx
from api.services.remote_sync import get_neo4j_driver

logger = logging.getLogger("dionysus.worldview_integration")


class WorldviewIntegrationService:
    """
    Integrates Mental Models with Identity and Worldview systems.
    """

    def __init__(
        self,
        driver=None,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
        llm_client=None,
    ):
        self._driver = driver or get_neo4j_driver()
        self._webhook_url = webhook_url
        self._webhook_secret = webhook_secret
        self._llm_client = llm_client

    # FR-019: Prediction Filtering by Worldview
    async def filter_prediction_by_worldview(
        self,
        prediction: dict,
        worldview_belief: str,
        base_confidence: float,
        alignment_threshold: float = 0.3,
        suppression_factor: float = 0.5,
    ) -> dict:
        # Calculate alignment (semantic similarity)
        alignment_score = await self._calculate_alignment(prediction, worldview_belief)
        flagged = alignment_score < alignment_threshold
        actual_suppression = suppression_factor if flagged else 0.0
        final_confidence = base_confidence * (1 - actual_suppression)

        return {
            "flagged_for_review": flagged,
            "suppression_factor": actual_suppression,
            "alignment_score": alignment_score,
            "final_confidence": final_confidence,
        }

    async def _calculate_alignment(self, prediction: dict, worldview_belief: str) -> float:
        # Simplified heuristic fallback
        return 0.5

    # FR-016: Record Prediction Errors with Precision-Weighted updates
    async def record_prediction_error(
        self,
        model_id: UUID,
        prediction_id: UUID,
        prediction_error: float,
        auto_update: bool = True,
    ) -> dict:
        """
        Record a prediction error and update worldview via precision-weighted accumulation.
        Formula: update = error / (1 + variance)
        """
        cypher = """
        MATCH (m:MentalModel {id: $model_id})
        MATCH (p:ModelPrediction {id: $prediction_id})
        
        // 1. Create the error node
        CREATE (e:PredictionError {
            id: randomUUID(),
            model_id: $model_id,
            prediction_id: $prediction_id,
            error_value: $error,
            created_at: datetime()
        })
        CREATE (p)-[:HAS_ERROR]->(e)
        
        // 2. Propagate to linked worldviews
        WITH e, m
        OPTIONAL MATCH (m)-[:INFORMS]->(w:Worldview)
        WHERE w IS NOT NULL
        
        // Calculate new variance and precision-weighted update
        // We use a rolling variance estimate: var = (1-alpha)*var + alpha*(error - mean)^2
        // For simplicity in Cypher, we'll track count, sum, and sum_sq
        SET w.error_count = coalesce(w.error_count, 0) + 1,
            w.error_sum = coalesce(w.error_sum, 0) + $error,
            w.error_sum_sq = coalesce(w.error_sum_sq, 0) + ($error * $error),
            w.updated_at = datetime()
            
        WITH w, e
        WHERE w.error_count > 1
        
        // mean = sum / count
        // var = (sum_sq / count) - (mean^2)
        // update = error / (1 + var)
        WITH w, e,
             (w.error_sum / w.error_count) as mean,
             ((w.error_sum_sq / w.error_count) - ((w.error_sum / w.error_count) * (w.error_sum / w.error_count))) as variance
             
        SET w.current_variance = variance,
            w.confidence = coalesce(w.confidence, 0.5) - ($error / (1.0 + variance))
            
        RETURN count(w) as affected
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "model_id": str(model_id),
                "prediction_id": str(prediction_id),
                "error": prediction_error
            })
            affected = int(result[0]["affected"]) if result else 0
            return {
                "worldviews_affected": affected,
                "status": "success" if affected > 0 else "no_linked_worldview"
            }
        except Exception as e:
            logger.error(f"Error recording prediction error: {e}")
            return {"worldviews_affected": 0, "error": str(e)}

    async def resolve_prediction_with_propagation(
        self,
        prediction_id: UUID,
        observation: dict,
        prediction_error: float,
    ) -> dict:
        """
        Resolve a prediction and propagate error to linked worldviews/identity.
        """
        cypher = """
        MATCH (p:ModelPrediction {id: $id})
        SET p.observation = $observation,
            p.prediction_error = $error,
            p.resolved_at = datetime()
        WITH p
        MATCH (m:MentalModel {id: p.model_id})
        SET m.prediction_accuracy = (m.prediction_accuracy * 0.9) + ((1.0 - $error) * 0.1),
            m.updated_at = datetime()
        RETURN p.model_id as model_id, m.domain as domain
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "id": str(prediction_id),
                "observation": json.dumps(observation),
                "error": prediction_error
            })
            
            if not result:
                raise ValueError(f"Prediction not found: {prediction_id}")
                
            model_id = result[0]["model_id"]
            model_domain = result[0]["domain"]
            
            # Record error for worldviews
            await self.record_prediction_error(UUID(model_id), prediction_id, prediction_error)
            
            return {
                "prediction_id": str(prediction_id),
                "model_id": model_id,
                "prediction_error": prediction_error,
                "webhook_sent": False
            }
        except Exception as e:
            logger.error(f"Error in resolve_prediction_with_propagation: {e}")
            raise

# Factory
_instance: Optional[WorldviewIntegrationService] = None

def get_worldview_integration_service(driver=None) -> WorldviewIntegrationService:
    global _instance
    if _instance is None:
        _instance = WorldviewIntegrationService(driver=driver)
    return _instance