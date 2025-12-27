import numpy as np
from typing import List, Dict, Any
from api.models.cognitive import EFEResult, EFEResponse

class EFEEngine:
    """
    Engine for calculating Expected Free Energy (EFE) for ThoughtSeeds.
    EFE = Uncertainty (Entropy) + Goal Divergence
    """

    def calculate_efe(self, query: str, goal_vector: List[float], thoughtseeds: List[Dict[str, Any]]) -> EFEResponse:
        """
        Rank a set of candidate ThoughtSeeds by their EFE scores.
        """
        results = {}
        goal_vec = np.array(goal_vector)

        for seed in thoughtseeds:
            seed_id = seed.get("id")
            # 1. Calculate Uncertainty (Shannon Entropy of prediction probabilities)
            probs = np.array(seed.get("prediction_probabilities", [0.5, 0.5]))
            uncertainty = -np.sum(probs * np.log2(probs + 1e-12))

            # 2. Calculate Goal Divergence (Cosine Distance)
            seed_vec = np.array(seed.get("response_vector", [0.0] * len(goal_vector)))
            
            if np.linalg.norm(seed_vec) == 0 or np.linalg.norm(goal_vec) == 0:
                goal_divergence = 1.0 # Max divergence if vectors are null
            else:
                cosine_sim = np.dot(seed_vec, goal_vec) / (np.linalg.norm(seed_vec) * np.linalg.norm(goal_vec))
                goal_divergence = 1.0 - float(cosine_sim)

            efe_score = uncertainty + goal_divergence
            
            results[seed_id] = EFEResult(
                seed_id=seed_id,
                efe_score=efe_score,
                uncertainty=uncertainty,
                goal_divergence=goal_divergence
            )

        # Select dominant seed (minimum EFE)
        dominant_seed_id = min(results, key=lambda k: results[k].efe_score) if results else "none"

        return EFEResponse(
            dominant_seed_id=dominant_seed_id,
            scores=results
        )

_efe_engine: Any = None

def get_efe_engine() -> EFEEngine:
    global _efe_engine
    if _efe_engine is None:
        _efe_engine = EFEEngine()
    return _efe_engine
