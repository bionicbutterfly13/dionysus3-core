
import logging
from typing import Optional
from api.models.biological_agency import DissonanceEvent
from api.services.graphiti_service import GraphitiService

logger = logging.getLogger(__name__)

class ShadowLogService:
    """
    The Shadow Log: Persists Cognitive Dissonance (Epistemic Debt).
    
    Prevents Model Collapse (Canalization) by tracking the gap between
    Reality (Observation) and Identity (Prediction).
    """

    def __init__(self):
        self._graphiti: Optional[GraphitiService] = None

    async def _get_graph_service(self) -> GraphitiService:
        if self._graphiti is None:
            self._graphiti = await GraphitiService.get_instance()
        return self._graphiti

    async def log_dissonance(
        self,
        agent_id: str,
        surprisal: float,
        ignored_observation: str,
        maintained_belief: str,
        context: str
    ) -> None:
        """
        Log a dissonance event to the Shadow Graph.
        
        Schema:
        (:Agent {id: ...})-[:HAS_SHADOW]->(:ShadowLog)
        (:ShadowLog)-[:CONTAINS]->(:DissonanceEvent { ... })
        """
        
        event = DissonanceEvent(
            surprisal=surprisal,
            ignored_observation=ignored_observation,
            maintained_belief=maintained_belief,
            context=context
        )
        
        query = """
        MATCH (a:Agent {id: $agent_id})
        MERGE (a)-[:HAS_SHADOW]->(sl:ShadowLog)
        CREATE (e:DissonanceEvent {
            id: $event_id,
            timestamp: $timestamp,
            surprisal: $surprisal,
            ignored_observation: $ignored_observation,
            maintained_belief: $maintained_belief,
            context: $context,
            resolved: false
        })
        CREATE (sl)-[:CONTAINS]->(e)
        RETURN e
        """
        
        params = {
            "agent_id": agent_id,
            "event_id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "surprisal": event.surprisal,
            "ignored_observation": event.ignored_observation,
            "maintained_belief": event.maintained_belief,
            "context": event.context
        }
        
        try:
            graph = await self._get_graph_service()
            await graph.execute_cypher(query, params)
            logger.info(
                f"Shadow Logged: Agent {agent_id} ignored reality (VFE={surprisal:.2f}) "
                f"in context '{context}'"
            )
        except Exception as e:
            logger.error(f"Failed to log dissonance for {agent_id}: {e}")
