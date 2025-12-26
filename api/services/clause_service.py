"""
CLAUSE Multi-Agent Scoring Service
Ported from Dionysus-2.0

Implements the 5-signal cognitive scoring architecture:
1. Coherence (Spatial/Temporal alignment)
2. Logic (Causal/Propositional validity)
3. Affect (Emotional valence/Affective tone)
4. Urgency (Action tendency/Impulse intensity)
5. Salience (Sensory prominence/Signal-to-noise)

Emergence: The combined signal that drives ThoughtSeed activation.
"""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel

logger = logging.getLogger("dionysus.clause")

class ClauseSignals(BaseModel):
    coherence: float = 0.5
    logic: float = 0.5
    affect: float = 0.5
    urgency: float = 0.5
    salience: float = 0.5

    @property
    def emergence(self) -> float:
        """Combined signal strength (average)."""
        return (self.coherence + self.logic + self.affect + self.urgency + self.salience) / 5.0

class ClauseService:
    """
    Service for calculating CLAUSE scores for cognitive entities.
    """

    def calculate_from_mosaeic(self, capture_data: Dict[str, Any]) -> ClauseSignals:
        """
        Map MoSAEIC windows to CLAUSE signals.
        - Senses -> Salience
        - Actions -> Logic (Procedural logic)
        - Emotions -> Affect
        - Impulses -> Urgency
        - Cognitions -> Coherence (Mental model alignment)
        """
        # Heuristic mapping based on data presence and intensity
        salience = self._score_window(capture_data.get("senses"))
        logic = self._score_window(capture_data.get("actions"))
        affect = self._score_window(capture_data.get("emotions"))
        urgency = self._score_window(capture_data.get("impulses"))
        coherence = self._score_window(capture_data.get("cognitions"))
        
        # Adjust based on emotional intensity if provided
        intensity = capture_data.get("emotional_intensity", 5.0) / 10.0
        affect = (affect + intensity) / 2.0
        
        return ClauseSignals(
            coherence=coherence,
            logic=logic,
            affect=affect,
            urgency=urgency,
            salience=salience
        )

    def _score_window(self, window_data: Any) -> float:
        """Heuristic scoring of a MoSAEIC window."""
        if not window_data:
            return 0.1
        if isinstance(window_data, str):
            return min(len(window_data) / 500.0, 1.0)
        if isinstance(window_data, dict):
            # Check for content or intensity keys
            content = window_data.get("content", "")
            base = min(len(str(content)) / 500.0, 0.8)
            intensity = window_data.get("intensity", 0.5)
            return (base + intensity) / 2.0
        return 0.5

    async def apply_strengthening(self, basin_id: str, signals: ClauseSignals) -> float:
        """
        Apply CLAUSE strengthening to an attractor basin.
        Ported rule: +0.2 per activation, scaled by emergence, cap 2.0.
        """
        from api.services.remote_sync import get_neo4j_driver
        driver = get_neo4j_driver()
        
        boost = 0.2 * signals.emergence
        
        cypher = """
        MATCH (b:MemoryCluster {id: $id})
        SET b.clause_strength = CASE 
            WHEN coalesce(b.clause_strength, 1.0) + $boost > 2.0 THEN 2.0
            ELSE coalesce(b.clause_strength, 1.0) + $boost
        END,
        b.last_strengthened = datetime()
        RETURN b.clause_strength as new_strength
        """
        
        result = await driver.execute_query(cypher, {"id": basin_id, "boost": boost})
        return result[0]["new_strength"] if result else 1.0

# Factory
_instance = None
def get_clause_service() -> ClauseService:
    global _instance
    if _instance is None:
        _instance = ClauseService()
    return _instance
