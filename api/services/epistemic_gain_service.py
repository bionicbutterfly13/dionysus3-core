"""
Epistemic Gain Service - "Aha!" Moment Detection

Feature: 040-metacognitive-particles
Based on: Seragnoli et al. (2025) - Metacognitive Feelings of Epistemic Gain

Detects significant learning events by measuring uncertainty reduction
between prior and posterior belief states.

Key concepts:
- Epistemic gain: Reduction in uncertainty/entropy
- Magnitude: (H_prior - H_posterior) / H_prior
- Noetic quality: Certainty without proportional evidence
- Adaptive threshold: Adjusts based on historical gains

AUTHOR: Mani Saint-Victor, MD
"""

import logging
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

import numpy as np

from api.models.belief_state import BeliefState

logger = logging.getLogger("dionysus.services.epistemic_gain")

# Configuration from environment
EPISTEMIC_GAIN_THRESHOLD = float(os.getenv("EPISTEMIC_GAIN_THRESHOLD", "0.3"))
EPISTEMIC_GAIN_ADAPTIVE = os.getenv("EPISTEMIC_GAIN_ADAPTIVE", "false").lower() == "true"


@dataclass
class EpistemicGainEvent:
    """
    Record of a significant learning moment.

    Captures the "Aha!" or "Eureka" experience when uncertainty
    significantly reduces after a belief update.
    """
    id: str
    magnitude: float  # Fractional entropy reduction (0.0 to 1.0)
    prior_entropy: float
    posterior_entropy: float
    noetic_quality: bool  # True if certainty without proportional evidence
    particle_id: Optional[str] = None
    detected_at: datetime = None

    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.utcnow()


class EpistemicGainService:
    """
    Detects epistemic gain events ("Aha!" moments).

    Per FR-011-FR-014:
    - check_gain(): Compare beliefs against threshold
    - Magnitude calculation: (H_prior - H_posterior) / H_prior
    - Noetic quality detection
    - Adaptive threshold support
    """

    def __init__(
        self,
        threshold: float = EPISTEMIC_GAIN_THRESHOLD,
        adaptive: bool = EPISTEMIC_GAIN_ADAPTIVE,
        history_size: int = 100
    ):
        self.base_threshold = threshold
        self.adaptive = adaptive
        self.history_size = history_size
        self.gain_history: deque = deque(maxlen=history_size)

    @property
    def current_threshold(self) -> float:
        """
        Get current threshold (may be adaptive).

        Adaptive formula: threshold = mean(historical_gains) + std(historical_gains)
        """
        if not self.adaptive or len(self.gain_history) < 10:
            return self.base_threshold

        gains = list(self.gain_history)
        mean_gain = np.mean(gains)
        std_gain = np.std(gains)

        # Adaptive threshold = mean + 1 std dev
        adaptive_threshold = mean_gain + std_gain

        # Clamp to reasonable range [0.1, 0.9]
        return max(0.1, min(0.9, adaptive_threshold))

    async def check_gain(
        self,
        prior_belief: BeliefState,
        posterior_belief: BeliefState,
        threshold: Optional[float] = None,
        particle_id: Optional[str] = None
    ) -> Optional[EpistemicGainEvent]:
        """
        Check for epistemic gain event.

        FR-011: Returns event if uncertainty reduction > threshold.

        Args:
            prior_belief: Belief state before update
            posterior_belief: Belief state after update
            threshold: Optional custom threshold
            particle_id: Optional particle identifier

        Returns:
            EpistemicGainEvent if gain exceeds threshold, None otherwise
        """
        # Compute entropies
        prior_entropy = prior_belief.entropy
        posterior_entropy = posterior_belief.entropy

        # Handle edge cases
        if prior_entropy <= 0 or prior_entropy == float('inf'):
            logger.debug("Invalid prior entropy, no gain detected")
            return None

        if posterior_entropy == float('inf'):
            logger.debug("Invalid posterior entropy, no gain detected")
            return None

        # Compute magnitude (FR-012)
        magnitude = self._compute_magnitude(prior_entropy, posterior_entropy)

        # Record in history for adaptive threshold
        if magnitude > 0:
            self.gain_history.append(magnitude)

        # Determine threshold to use
        thresh = threshold if threshold is not None else self.current_threshold

        # Check if gain exceeds threshold
        if magnitude < thresh:
            logger.debug(f"Epistemic gain {magnitude:.3f} below threshold {thresh:.3f}")
            return None

        # Detect noetic quality (FR-013)
        noetic_quality = self._detect_noetic_quality(
            prior_belief, posterior_belief, magnitude
        )

        logger.info(
            f"Epistemic gain detected: magnitude={magnitude:.3f}, "
            f"noetic={noetic_quality}"
        )

        return EpistemicGainEvent(
            id=str(uuid4()),
            magnitude=magnitude,
            prior_entropy=prior_entropy,
            posterior_entropy=posterior_entropy,
            noetic_quality=noetic_quality,
            particle_id=particle_id
        )

    def _compute_magnitude(
        self,
        prior_entropy: float,
        posterior_entropy: float
    ) -> float:
        """
        Compute epistemic gain magnitude.

        FR-012: magnitude = (H_prior - H_posterior) / H_prior

        Returns:
            Fractional reduction in entropy (0.0 to 1.0)
        """
        if prior_entropy <= 0:
            return 0.0

        reduction = (prior_entropy - posterior_entropy) / prior_entropy

        # Clamp to [0, 1] - negative reduction means increased uncertainty
        return max(0.0, min(1.0, reduction))

    def _detect_noetic_quality(
        self,
        prior_belief: BeliefState,
        posterior_belief: BeliefState,
        magnitude: float
    ) -> bool:
        """
        Detect noetic quality in epistemic gain.

        FR-013: True if certainty increases without proportional evidence.

        Noetic quality indicates an "insight" experience where the agent
        feels certain without clear justification - the hallmark of
        mystical or peak experiences.

        Heuristic: Compare precision increase to entropy reduction.
        If precision increase >> entropy reduction, it's noetic.
        """
        # Compute precision changes
        prior_precision = self._average_precision(prior_belief)
        posterior_precision = self._average_precision(posterior_belief)

        if prior_precision <= 0:
            return False

        precision_increase = (posterior_precision - prior_precision) / prior_precision

        # Noetic quality: precision increase much greater than evidence would suggest
        # Threshold: precision increases by more than 2x the magnitude
        return precision_increase > (2.0 * magnitude)

    def _average_precision(self, belief: BeliefState) -> float:
        """Compute average diagonal precision."""
        precision_array = belief.precision_array
        diagonal = np.diag(precision_array)
        return float(np.mean(diagonal))

    async def compute_kl_gain(
        self,
        prior_belief: BeliefState,
        posterior_belief: BeliefState
    ) -> float:
        """
        Compute epistemic gain as KL divergence.

        Alternative to entropy-based magnitude.
        D_KL(posterior || prior) measures information gained.

        Args:
            prior_belief: Prior belief state
            posterior_belief: Posterior belief state

        Returns:
            KL divergence value
        """
        # For Gaussian distributions, use closed-form KL
        d = prior_belief.dimension

        try:
            # KL(posterior || prior)
            prior_cov = np.linalg.inv(prior_belief.precision_array)
            posterior_cov = np.linalg.inv(posterior_belief.precision_array)

            trace_term = np.trace(prior_belief.precision_array @ posterior_cov)

            diff = prior_belief.mean_array - posterior_belief.mean_array
            quad_term = diff @ prior_belief.precision_array @ diff

            det_prior = np.linalg.det(prior_belief.precision_array)
            det_posterior = np.linalg.det(posterior_belief.precision_array)

            if det_prior <= 0 or det_posterior <= 0:
                return 0.0

            log_det = np.log(det_prior / det_posterior)

            kl = 0.5 * (trace_term + quad_term - d + log_det)
            return max(0.0, float(kl))

        except (np.linalg.LinAlgError, ValueError) as e:
            logger.warning(f"KL computation failed: {e}")
            return 0.0

    def reset_history(self):
        """Clear gain history for adaptive threshold."""
        self.gain_history.clear()

    @property
    def history_stats(self) -> dict:
        """Get statistics about gain history."""
        if not self.gain_history:
            return {"count": 0, "mean": 0, "std": 0, "threshold": self.base_threshold}

        gains = list(self.gain_history)
        return {
            "count": len(gains),
            "mean": float(np.mean(gains)),
            "std": float(np.std(gains)),
            "threshold": self.current_threshold
        }
