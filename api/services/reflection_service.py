import logging
from typing import List, Dict, Any
from api.models.cognitive import CognitiveEpisode
from api.services.arbitration_service import get_arbitration_service

logger = logging.getLogger("dionysus.services.reflection")

class ReflectionService:
    """
    Implements SOFAI Reflective Metacognition (Algorithm 2).
    Analyzes past episodes to update the bias towards System 2.
    """

    async def reflect_on_episodes(self, episodes: List[CognitiveEpisode]):
        """
        Perform counterfactual replay on a set of episodes.
        """
        logger.info(f"Starting reflection on {len(episodes)} episodes...")
        
        s2_benefit_sum = 0.0
        
        for ep in episodes:
            # 1. Simulate: What would have happened with S2 (Slow Thinking)?
            # In a real implementation, we would re-run the task using ReasoningAgent.
            # Here, we compare the actual EFE/Reward to a potential S2 improvement.
            
            actual_g = ep.surprise_score # We use surprise as a proxy for EFE error
            
            # Heuristic: If surprise was high, S2 would likely have helped.
            if actual_g > 0.6:
                s2_benefit_sum += (actual_g - 0.2) # Estimated improvement
                
        # 2. Update Reflection Bias (Architecture Hunger)
        if episodes:
            avg_benefit = s2_benefit_sum / len(episodes)
            arbitration_svc = get_arbitration_service()
            
            # Gradually update the bias (Learning Rate = 0.1)
            arbitration_svc.reflection_bias = (0.9 * arbitration_svc.reflection_bias) + (0.1 * avg_benefit)
            
            logger.info(f"Reflection completed. New Reflection Bias: {arbitration_svc.reflection_bias:.4f}")

# Global singleton
_service = None

def get_reflection_service() -> ReflectionService:
    global _service
    if _service is None:
        _service = ReflectionService()
    return _service
