from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from api.services.efe_engine import get_efe_engine, EFEEngine
from api.core.engine.models import ThoughtNode, ActiveInferenceScore

class ActiveInferenceWrapper:
    """
    Wraps the core EFEEngine to provide specific services for the Meta-ToT system.
    Handles the translation between ThoughtNodes and the raw vectors/probabilities required by EFE.
    """
    def __init__(self):
        self.engine: EFEEngine = get_efe_engine()
        
    async def score_thought(
        self, 
        thought: ThoughtNode, 
        goal_vector: List[float], 
        context_probs: List[float] = [0.5, 0.5],
        thought_vector: Optional[List[float]] = None
    ) -> ActiveInferenceScore:
        """
        Calculates the Active Inference metrics for a single thought node.
        
        Args:
            thought: The ThoughtNode to score.
            goal_vector: The embedding of the current active goal.
            context_probs: Prediction probabilities from the LLM (uncertainty source).
            thought_vector: Embedding of the thought content (if not provided, should be generated).
            
        Returns:
            ActiveInferenceScore object attached to the thought.
        """
        
        # TODO: Integrate with EmbeddingService if thought_vector is None
        # For now, we assume vector is provided or use zero-vector placeholder for skeleton
        if thought_vector is None:
            # Placeholder: In production, call embedding service here
            thought_vector = [0.0] * len(goal_vector)
            
        thought_np = np.array(thought_vector)
        goal_np = np.array(goal_vector)
        
        # Calculate Base Metrics
        entropy = self.engine.calculate_entropy(context_probs)
        divergence = self.engine.calculate_goal_divergence(thought_np, goal_np)
        
        # Calculate EFE
        # We assume default precision of 1.0 for now, can be modulated by MetaPlasticity later
        efe = self.engine.calculate_efe(context_probs, thought_np, goal_np)
        
        # Calculate Prediction Error (Simplified as Divergence for now, valid in some active inference formulations)
        prediction_error = divergence 
        
        # Create Score Object
        score = ActiveInferenceScore(
            expected_free_energy=efe,
            surprise=entropy, # Using entropy as proxy for surprise in this context
            prediction_error=prediction_error,
            precision=1.0
        )
        
        return score

_ai_wrapper: Optional[ActiveInferenceWrapper] = None

def get_active_inference_wrapper() -> ActiveInferenceWrapper:
    global _ai_wrapper
    if _ai_wrapper is None:
        _ai_wrapper = ActiveInferenceWrapper()
    return _ai_wrapper
