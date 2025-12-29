"""
Self-Modeling Service - Predicts and resolves agent internal states.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

import numpy as np
from api.models.prediction import PredictionRecord, PredictionAccuracy
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger("dionysus.self_modeling")

class SelfModelingService:
    def __init__(self, driver=None):
        self.driver = driver or get_neo4j_driver()

    async def predict_next_state(self, agent_id: str, current_state: Dict[str, float]) -> PredictionRecord:
        """Create a prediction for the next state based on current state (T029)."""
        prediction = PredictionRecord(
            agent_id=agent_id,
            predicted_state=current_state
        )
        
        await self._persist_prediction(prediction)
        return prediction

    async def resolve_prediction(self, prediction_id: str, actual_state: Dict[str, float]) -> Optional[PredictionRecord]:
        """Compare prediction with actual outcome and calculate error (T030)."""
        cypher = "MATCH (p:PredictionRecord {id: $id}) RETURN p"
        async with self.driver.session() as session:
            res = await session.run(cypher, {"id": prediction_id})
            record = await res.single()
            if not record:
                return None
            
            p_data = record["p"]
            predicted = p_data["predicted_state"]
            
            # Calculate L2 error (T031)
            error = self._calculate_l2_error(predicted, actual_state)
            
            update_cypher = """
            MATCH (p:PredictionRecord {id: $id})
            SET p.actual_state = $actual,
                p.prediction_error = $error,
                p.resolved_at = datetime()
            RETURN p
            """
            await session.run(update_cypher, {
                "id": prediction_id,
                "actual": actual_state,
                "error": error
            })
            
            return PredictionRecord(
                id=prediction_id,
                agent_id=p_data["agent_id"],
                predicted_state=predicted,
                actual_state=actual_state,
                prediction_error=error,
                resolved_at=datetime.utcnow()
            )

    def _calculate_l2_error(self, predicted: Dict[str, float], actual: Dict[str, float]) -> float:
        keys = sorted(set(predicted.keys()) | set(actual.keys()))
        p_vec = np.array([predicted.get(k, 0.0) for k in keys])
        a_vec = np.array([actual.get(k, 0.0) for k in keys])
        
        norm = np.linalg.norm(a_vec)
        if norm == 0: return 0.0
        return float(np.linalg.norm(p_vec - a_vec) / norm)

    async def _persist_prediction(self, prediction: PredictionRecord):
        cypher = """
        CREATE (p:PredictionRecord {
            id: $id,
            agent_id: $agent_id,
            timestamp: $timestamp,
            predicted_state: $predicted
        })
        """
        async with self.driver.session() as session:
            await session.run(cypher, {
                "id": prediction.id,
                "agent_id": prediction.agent_id,
                "timestamp": prediction.timestamp.isoformat(),
                "predicted": prediction.predicted_state
            })

_service = None
def get_self_modeling_service():
    global _service
    if _service is None:
        _service = SelfModelingService()
    return _service
