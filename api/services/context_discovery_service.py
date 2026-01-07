"""
Context Reasoning Service - Dionysus3 Bridge for cgr3.
Implements the Retrieve-Rank-Reason (CGR3) and Dual-Evolution (ToG-3) loops
with instrumentation for Meta-Evolutionary analysis.
"""

import logging
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from our modular package
from cgr3.macer.reasoner import MACERReasoner
from cgr3.neo4j_provider import GraphitiContextGraph
from cgr3.utils.llm_util import LLMInterface

from api.services.graphiti_service import get_graphiti_service
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger("dionysus.context_reasoning")

class ContextDiscoveryService:
    """
    Bridge between Dionysus3 Core and the CGR3 Reasoning Engine.
    Exposes discovery with automated meta-evolutionary tracking.
    """
    
    def __init__(self, max_iterations: int = 3):
        self._reasoner = None
        self.max_iterations = max_iterations

    async def _get_reasoner(self) -> MACERReasoner:
        if self._reasoner is None:
            # Configure CGR3 to use Dionysus's Neo4j via Graphiti bridge
            # Note: We pass the credentials from env as GraphitiContextGraph needs them for its internal driver
            from api.services.graphiti_service import GraphitiConfig
            config = GraphitiConfig()
            
            provider = GraphitiContextGraph(
                uri=config.neo4j_uri,
                user=config.neo4j_user,
                password=config.neo4j_password
            )
            
            # Map LLMInterface to Dionysus LLM Service (conceptually)
            # For this bridge, we use a specialized adapter
            llm = DionysusLLMAdapter()
            
            self._reasoner = MACERReasoner(provider, llm, max_iterations=self.max_iterations)
        return self._reasoner

    async def discover(self, query: str, context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a context-aware discovery task and logs the trajectory.
        """
        reasoner = await self._get_reasoner()
        start_time = time.time()
        
        # Execute MACER Loop (Async)
        results = await reasoner.reason(query)
        
        duration = time.time() - start_time
        
        # Log Trajectory for Meta-Evolution (Feature 016 Synergy)
        await self._log_trajectory(query, results, duration, context_id)
        
        return results

    async def _log_trajectory(self, query: str, results: Dict[str, Any], duration: float, context_id: Optional[str]):
        """
        Persists the reasoning trajectory as a CognitiveEpisode for Meta-Evolution.
        """
        driver = get_neo4j_driver()
        episode_id = str(uuid.uuid4())
        
        # Calculate surprise / failure metrics for Meta-Evolution
        # If iterations == max_iterations and no answer, high surprise
        surprise_score = 0.0
        if results.get("iterations", 0) >= self.max_iterations and not results.get("answer"):
            surprise_score = 0.9
        elif not results.get("answer"):
            surprise_score = 0.5
            
        cypher = """
        CREATE (e:CognitiveEpisode:MACERTrajectory {id: $id})
        SET e.timestamp = $timestamp,
            e.query = $query,
            e.iterations = $iterations,
            e.duration_sec = $duration,
            e.surprise_score = $surprise,
            e.has_answer = $has_answer,
            e.context_id = $context_id
        """
        params = {
            "id": episode_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "iterations": results.get("iterations"),
            "duration": duration,
            "surprise": surprise_score,
            "has_answer": bool(results.get("answer")),
            "context_id": context_id
        }
        
        await driver.execute_query(cypher, params)
        logger.info(f"MACER Trajectory logged for meta-evolution: {episode_id} (Surprise: {surprise_score})")

class DionysusLLMAdapter(LLMInterface):
    """Adapts cgr3 LLMInterface to use Dionysus3's llm_service."""
    
    async def generate_async(self, prompt: str) -> str:
        from api.services.llm_service import chat_completion, GPT5_NANO
        
        return await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=GPT5_NANO,
            max_tokens=1024
        )

_discovery_service = None

def get_context_discovery_service() -> ContextDiscoveryService:
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = ContextDiscoveryService()
    return _discovery_service
