import numpy as np
from scipy.stats import entropy
from scipy.spatial.distance import cosine
from typing import List, Dict, Any, Optional
import logging
from api.models.cognitive import EFEResult, EFEResponse

logger = logging.getLogger("dionysus.efe_engine")

class EFEEngine:
    """
    Expected Free Energy (EFE) Engine for Thoughtseed selection.
    Feature: 038-thoughtseeds-framework
    
    Formula: EFE = Uncertainty (Entropy) + Goal Divergence (KL or Distance)
    Simplified for embeddings: EFE = H(p) + (1 - cos_sim(thought, goal))
    """

    def calculate_entropy(self, probabilities: List[float]) -> float:
        """Calculates Shannon entropy of a probability distribution."""
        if not probabilities:
            return 1.0
        # scipy.stats.entropy uses ln by default, we use base 2 for bits
        return float(entropy(probabilities, base=2))

    def calculate_goal_divergence(self, thought_vector: np.ndarray, goal_vector: np.ndarray) -> float:
        """Calculates divergence from goal using cosine distance."""
        # cosine distance = 1 - cosine similarity
        if np.linalg.norm(thought_vector) == 0 or np.linalg.norm(goal_vector) == 0:
            return 1.0
        return float(cosine(thought_vector, goal_vector))

    def calculate_efe(
        self, 
        prediction_probs: List[float], 
        thought_vector: np.ndarray, 
        goal_vector: np.ndarray
    ) -> float:
        """
        Calculates the cumulative Expected Free Energy for a candidate thought.
        Lower EFE = More valuable thought (balance of epistemic gain and pragmatic goal alignment).
        """
        uncertainty = self.calculate_entropy(prediction_probs)
        divergence = self.calculate_goal_divergence(thought_vector, goal_vector)
        
        # Weighted sum (could be tuned)
        # Higher uncertainty makes the agent "curious" (epistemic value)
        # Higher divergence makes the agent "unfocused" (pragmatic cost)
        efe = uncertainty + divergence
        
        logger.debug(f"EFE Calculation: Uncertainty={uncertainty:.4f}, Divergence={divergence:.4f}, Total={efe:.4f}")
        return efe

    def select_dominant_thought(self, candidates: List[Dict[str, Any]], goal_vector: List[float]) -> EFEResponse:
        """
        Winner-take-all selection of the dominant ThoughtSeed based on minimal EFE.
        """
        if not candidates:
            return EFEResponse(dominant_seed_id="none", scores={})

        results = {}
        goal_vec = np.array(goal_vector)
        
        for candidate in candidates:
            seed_id = candidate.get("id")
            uncertainty = self.calculate_entropy(candidate.get("probabilities", [0.5, 0.5]))
            divergence = self.calculate_goal_divergence(np.array(candidate.get("vector")), goal_vec)
            
            efe = uncertainty + divergence
            
            results[seed_id] = EFEResult(
                seed_id=seed_id,
                efe_score=efe,
                uncertainty=uncertainty,
                goal_divergence=divergence
            )

        # Select dominant seed (minimum EFE)
        dominant_seed_id = min(results, key=lambda k: results[k].efe_score)

        return EFEResponse(
            dominant_seed_id=dominant_seed_id,
            scores=results
        )

    def rank_candidates(self, query: str, goal_vector: List[float], candidates: List[Dict[str, Any]]) -> EFEResponse:
        """
        Legacy method for compatibility with existing service calls.
        Maps query/goal/candidates to EFE calculation.
        """
        # Adapt keys for compatibility with older code (Feature 030)
        adapted_candidates = []
        for c in candidates:
            adapted = c.copy()
            if "response_vector" in c:
                adapted["vector"] = c["response_vector"]
            if "prediction_probabilities" in c:
                adapted["probabilities"] = c["prediction_probabilities"]
            adapted_candidates.append(adapted)
            
        return self.select_dominant_thought(adapted_candidates, goal_vector)

_efe_engine: Optional[EFEEngine] = None

def get_efe_engine() -> EFEEngine:
    global _efe_engine
    if _efe_engine is None:
        _efe_engine = EFEEngine()
    return _efe_engine