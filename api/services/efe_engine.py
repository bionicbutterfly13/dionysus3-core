import numpy as np
from scipy.stats import entropy
from scipy.spatial.distance import cosine
from typing import List, Dict, Any, Optional
import logging
from api.models.cognitive import EFEResult, EFEResponse

logger = logging.getLogger("dionysus.efe_engine")


# Global precision registry for agent-level precision modulation
# Keys: agent_name -> precision_value (default 1.0)
# Per Metacognitive Particles paper: mental actions modulate precision, not content
_agent_precision_registry: Dict[str, float] = {}


def get_agent_precision(agent_name: str) -> float:
    """Get current precision for an agent. Default is 1.0."""
    return _agent_precision_registry.get(agent_name, 1.0)


def set_agent_precision(agent_name: str, precision: float) -> None:
    """Set precision for an agent. Clamped to [0.01, 10.0]."""
    clamped = max(0.01, min(10.0, precision))
    _agent_precision_registry[agent_name] = clamped
    logger.info(f"Agent '{agent_name}' precision set to {clamped:.4f}")


def adjust_agent_precision(agent_name: str, delta: float) -> float:
    """Adjust precision by delta. Returns new precision."""
    current = get_agent_precision(agent_name)
    new_precision = max(0.01, min(10.0, current + delta))
    _agent_precision_registry[agent_name] = new_precision
    logger.info(f"Agent '{agent_name}' precision adjusted: {current:.4f} -> {new_precision:.4f} (delta={delta:+.4f})")
    return new_precision


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

    def calculate_precision_weighted_efe(
        self,
        prediction_probs: List[float],
        thought_vector: np.ndarray,
        goal_vector: np.ndarray,
        precision: float = 1.0,
        agent_name: Optional[str] = None
    ) -> float:
        """
        Calculates precision-weighted Expected Free Energy.

        Per Metacognitive Particles paper: mental actions modulate precision (inverse variance),
        not belief content directly. Higher precision = more confident = less exploratory.

        Formula: EFE_precision = (1/precision) * uncertainty + precision * divergence

        Rationale:
        - High precision (attention focused): Downweight uncertainty (less exploration),
          upweight divergence penalty (stay focused on goal)
        - Low precision (attention diffuse): Upweight uncertainty (more exploration),
          downweight divergence penalty (allow wandering)

        Args:
            prediction_probs: Probability distribution for uncertainty calculation
            thought_vector: Embedding of candidate thought
            goal_vector: Embedding of current goal
            precision: Precision weight (inverse variance). Default 1.0.
            agent_name: Optional agent name to use agent-specific precision from registry

        Returns:
            Precision-weighted EFE score (lower = better)
        """
        # Use agent-specific precision if agent_name provided and no explicit precision
        if agent_name and precision == 1.0:
            precision = get_agent_precision(agent_name)

        # Clamp precision to reasonable bounds
        precision = max(0.01, min(10.0, precision))

        uncertainty = self.calculate_entropy(prediction_probs)
        divergence = self.calculate_goal_divergence(thought_vector, goal_vector)

        # Precision-weighted formula
        # High precision -> less weight on uncertainty, more on goal adherence
        # Low precision -> more weight on uncertainty (exploration), less on goal
        efe_precision = (1.0 / precision) * uncertainty + precision * divergence

        logger.debug(
            f"Precision-Weighted EFE: precision={precision:.4f}, "
            f"uncertainty={uncertainty:.4f}, divergence={divergence:.4f}, "
            f"total={efe_precision:.4f}"
        )
        return efe_precision

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

    def agency_weighted_efe(
        self,
        prediction_probs: List[float],
        thought_vector: np.ndarray,
        goal_vector: np.ndarray,
        agency_score: float,
        agency_weight: float = 0.3
    ) -> float:
        """
        Calculate EFE weighted by agency score.
        
        Higher agency → more confidence in predicted outcomes → lower effective uncertainty
        Lower agency → less confidence → higher effective uncertainty
        
        Formula: weighted_EFE = base_EFE * (1 - agency_weight * normalized_agency)
        
        Args:
            prediction_probs: Probability distribution for uncertainty calculation
            thought_vector: Embedding of the candidate thought
            goal_vector: Embedding of the goal state
            agency_score: KL divergence from agency detector (0 = no agency)
            agency_weight: How much agency affects EFE (0-1, default 0.3)
            
        Returns:
            Agency-weighted EFE score (lower = better)
        """
        
        base_efe = self.calculate_efe(prediction_probs, thought_vector, goal_vector)
        
        # Normalize agency score to 0-1 range using sigmoid-like transformation
        # Typical KL values are 0-2, so we use tanh for smooth normalization
        normalized_agency = float(np.tanh(agency_score))
        
        # Higher agency reduces effective EFE (more confidence in outcomes)
        # agency_modifier is between (1 - agency_weight) and 1
        agency_modifier = 1.0 - (agency_weight * normalized_agency)
        
        weighted_efe = base_efe * agency_modifier
        
        logger.debug(
            f"Agency-weighted EFE: base={base_efe:.4f}, agency={agency_score:.4f}, "
            f"modifier={agency_modifier:.4f}, weighted={weighted_efe:.4f}"
        )
        
        return weighted_efe

    def select_dominant_thought_with_agency(
        self,
        candidates: List[Dict[str, Any]],
        goal_vector: List[float],
        internal_states: np.ndarray,
        active_states: np.ndarray,
        agency_weight: float = 0.3
    ) -> "EFEResponse":
        """
        Winner-take-all selection with agency-weighted EFE.
        
        Uses agency score to modulate confidence in predictions:
        - High agency: Trust predictions more (lower effective uncertainty)
        - Low agency: Trust predictions less (higher effective uncertainty)
        
        Args:
            candidates: ThoughtSeed candidates with 'id', 'vector', 'probabilities'
            goal_vector: Goal state embedding
            internal_states: Internal state samples for agency calculation
            active_states: Active state samples for agency calculation
            agency_weight: How much agency affects EFE (0-1)
            
        Returns:
            EFEResponse with agency-weighted rankings
        """
        from api.services.agency_detector import get_agency_detector
        
        if not candidates:
            return EFEResponse(dominant_seed_id="none", scores={})
        
        # Calculate agency score once for all candidates
        detector = get_agency_detector()
        agency_score = detector.calculate_agency_score(internal_states, active_states)
        
        results = {}
        goal_vec = np.array(goal_vector)
        
        for candidate in candidates:
            seed_id = candidate.get("id")
            probs = candidate.get("probabilities", [0.5, 0.5])
            thought_vec = np.array(candidate.get("vector", [0.0] * len(goal_vector)))
            
            # Calculate agency-weighted EFE
            weighted_efe = self.agency_weighted_efe(
                probs, thought_vec, goal_vec, agency_score, agency_weight
            )
            
            # Store with base metrics for transparency
            uncertainty = self.calculate_entropy(probs)
            divergence = self.calculate_goal_divergence(thought_vec, goal_vec)
            
            results[seed_id] = EFEResult(
                seed_id=seed_id,
                efe_score=weighted_efe,  # Use weighted score for ranking
                uncertainty=uncertainty,
                goal_divergence=divergence
            )
        
        # Select dominant seed (minimum weighted EFE)
        dominant_seed_id = min(results, key=lambda k: results[k].efe_score)
        
        logger.info(
            f"Agency-weighted selection: dominant={dominant_seed_id}, "
            f"agency_score={agency_score:.4f}"
        )
        
        return EFEResponse(
            dominant_seed_id=dominant_seed_id,
            scores=results
        )

_efe_engine: Optional[EFEEngine] = None

def get_efe_engine() -> EFEEngine:
    global _efe_engine
    if _efe_engine is None:
        _efe_engine = EFEEngine()
    return _efe_engine