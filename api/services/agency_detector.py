"""
Agency Detector Service
Feature: 038-thoughtseeds-framework (Priority 3)

Detects sense of agency via statistical dependence between internal and active paths.
Based on Metacognitive Particles paper:
- Sense of agency = D_KL[p(μ,a) || p(μ)p(a)]
- High KL = strong coupling between internal states and actions = AGENCY
- Zero KL = statistical independence = NO AGENCY (mere observation)
"""

import logging
from typing import Optional, Tuple

import numpy as np
from scipy.stats import entropy

from api.models.agency import (
    AgencyAttribution,
    AgencyAttributionType,
    AgencyThresholds,
    DEFAULT_AGENCY_THRESHOLDS,
)

logger = logging.getLogger("dionysus.agency_detector")


class AgencyDetector:
    """
    Detects sense of agency via statistical dependence between internal and active paths.
    
    The core insight from Metacognitive Particles:
    - Agency manifests as statistical coupling between internal states (μ) and actions (a)
    - D_KL[p(μ,a) || p(μ)p(a)] measures this coupling
    - High KL divergence → actions are determined by internal states → AGENCY
    - Zero KL divergence → actions are independent of internal states → NO AGENCY
    """

    def __init__(self, thresholds: Optional[AgencyThresholds] = None, num_bins: int = 20):
        """
        Initialize agency detector.
        
        Args:
            thresholds: Classification thresholds for agency attribution
            num_bins: Number of bins for histogram-based density estimation
        """
        self.thresholds = thresholds or DEFAULT_AGENCY_THRESHOLDS
        self.num_bins = num_bins
        self._epsilon = 1e-10  # Small value to prevent log(0)

    def calculate_agency_score(
        self,
        internal_states: np.ndarray,
        active_states: np.ndarray
    ) -> float:
        """
        Calculate KL divergence between joint and product of marginals.
        
        D_KL[p(μ,a) || p(μ)p(a)] = sum_i sum_j p(μ_i, a_j) * log(p(μ_i, a_j) / (p(μ_i) * p(a_j)))
        
        This is equivalent to mutual information I(μ;a), which measures the
        statistical dependence between internal states and actions.
        
        Args:
            internal_states: μ path samples (N samples, D dimensions)
            active_states: a path samples (N samples, D dimensions)
            
        Returns:
            Agency score: high = self-caused, low = external causation
        """
        if len(internal_states) != len(active_states):
            raise ValueError("Internal and active state arrays must have same length")
        
        if len(internal_states) < 2:
            logger.warning("Insufficient samples for agency calculation, returning 0")
            return 0.0
        
        # Ensure 2D arrays
        mu = np.atleast_2d(internal_states)
        a = np.atleast_2d(active_states)
        
        # If 1D arrays were passed, transpose to (N, 1)
        if mu.shape[0] == 1 and len(internal_states.shape) == 1:
            mu = mu.T
        if a.shape[0] == 1 and len(active_states.shape) == 1:
            a = a.T
        
        # Calculate mutual information as KL divergence between joint and product of marginals
        # For each dimension pair, compute the KL divergence and sum
        total_kl = 0.0
        
        for d_mu in range(mu.shape[1]):
            for d_a in range(a.shape[1]):
                kl = self._compute_2d_kl_divergence(mu[:, d_mu], a[:, d_a])
                total_kl += kl
        
        # Normalize by number of dimension pairs for interpretability
        num_pairs = mu.shape[1] * a.shape[1]
        normalized_kl = total_kl / num_pairs if num_pairs > 0 else 0.0
        
        logger.debug(f"Agency score: {normalized_kl:.4f} (total KL: {total_kl:.4f}, pairs: {num_pairs})")
        return normalized_kl

    def _compute_2d_kl_divergence(self, mu_dim: np.ndarray, a_dim: np.ndarray) -> float:
        """
        Compute KL divergence between joint distribution and product of marginals
        for a single dimension pair.
        
        D_KL[p(x,y) || p(x)p(y)] = I(X;Y) (mutual information)
        
        Uses histogram-based density estimation.
        """
        # Get data range for consistent binning
        mu_range = (mu_dim.min(), mu_dim.max())
        a_range = (a_dim.min(), a_dim.max())
        
        # Handle constant arrays
        if mu_range[0] == mu_range[1]:
            mu_range = (mu_range[0] - 0.5, mu_range[1] + 0.5)
        if a_range[0] == a_range[1]:
            a_range = (a_range[0] - 0.5, a_range[1] + 0.5)
        
        # Estimate joint distribution p(μ,a)
        joint_hist, _, _ = np.histogram2d(
            mu_dim, a_dim,
            bins=self.num_bins,
            range=[mu_range, a_range]
        )
        
        # Normalize to get probability distribution
        joint_prob = joint_hist / (joint_hist.sum() + self._epsilon)
        joint_prob = joint_prob + self._epsilon  # Avoid log(0)
        joint_prob = joint_prob / joint_prob.sum()  # Renormalize
        
        # Estimate marginal distributions
        mu_hist, _ = np.histogram(mu_dim, bins=self.num_bins, range=mu_range)
        a_hist, _ = np.histogram(a_dim, bins=self.num_bins, range=a_range)
        
        # Normalize marginals
        p_mu = (mu_hist + self._epsilon) / (mu_hist.sum() + self._epsilon * self.num_bins)
        p_a = (a_hist + self._epsilon) / (a_hist.sum() + self._epsilon * self.num_bins)
        
        # Compute product of marginals p(μ)p(a)
        marginal_product = np.outer(p_mu, p_a)
        marginal_product = marginal_product / marginal_product.sum()  # Normalize
        
        # Compute KL divergence: D_KL[joint || marginal_product]
        # This equals mutual information I(μ;a)
        kl_div = np.sum(joint_prob * np.log(joint_prob / (marginal_product + self._epsilon)))
        
        return max(0.0, kl_div)  # KL divergence is always non-negative

    def _estimate_joint_distribution(
        self,
        mu: np.ndarray,
        a: np.ndarray
    ) -> np.ndarray:
        """
        Estimate p(μ,a) from samples using histogram method.
        
        Args:
            mu: Internal state samples (1D array)
            a: Active state samples (1D array)
            
        Returns:
            2D array representing joint probability distribution
        """
        mu_range = (mu.min(), mu.max())
        a_range = (a.min(), a.max())
        
        if mu_range[0] == mu_range[1]:
            mu_range = (mu_range[0] - 0.5, mu_range[1] + 0.5)
        if a_range[0] == a_range[1]:
            a_range = (a_range[0] - 0.5, a_range[1] + 0.5)
        
        joint_hist, _, _ = np.histogram2d(
            mu, a,
            bins=self.num_bins,
            range=[mu_range, a_range]
        )
        
        # Add epsilon and normalize
        joint_prob = (joint_hist + self._epsilon) / (joint_hist.sum() + self._epsilon * self.num_bins**2)
        return joint_prob / joint_prob.sum()

    def _estimate_marginal_product(
        self,
        mu: np.ndarray,
        a: np.ndarray
    ) -> np.ndarray:
        """
        Estimate p(μ)p(a) from samples.
        
        Args:
            mu: Internal state samples (1D array)
            a: Active state samples (1D array)
            
        Returns:
            2D array representing product of marginal distributions
        """
        mu_range = (mu.min(), mu.max())
        a_range = (a.min(), a.max())
        
        if mu_range[0] == mu_range[1]:
            mu_range = (mu_range[0] - 0.5, mu_range[1] + 0.5)
        if a_range[0] == a_range[1]:
            a_range = (a_range[0] - 0.5, a_range[1] + 0.5)
        
        # Estimate marginals
        mu_hist, _ = np.histogram(mu, bins=self.num_bins, range=mu_range)
        a_hist, _ = np.histogram(a, bins=self.num_bins, range=a_range)
        
        # Normalize marginals
        p_mu = (mu_hist + self._epsilon) / (mu_hist.sum() + self._epsilon * self.num_bins)
        p_a = (a_hist + self._epsilon) / (a_hist.sum() + self._epsilon * self.num_bins)
        
        # Product of marginals
        marginal_product = np.outer(p_mu, p_a)
        return marginal_product / marginal_product.sum()

    def _calculate_entropies(
        self,
        mu: np.ndarray,
        a: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Calculate entropies for internal states, active states, and joint distribution.
        
        Returns:
            (H(μ), H(a), H(μ,a))
        """
        # Estimate distributions
        joint_prob = self._estimate_joint_distribution(mu.flatten(), a.flatten())
        
        mu_hist, _ = np.histogram(mu.flatten(), bins=self.num_bins)
        a_hist, _ = np.histogram(a.flatten(), bins=self.num_bins)
        
        # Normalize
        p_mu = (mu_hist + self._epsilon) / (mu_hist.sum() + self._epsilon * self.num_bins)
        p_a = (a_hist + self._epsilon) / (a_hist.sum() + self._epsilon * self.num_bins)
        
        # Calculate entropies using scipy
        h_mu = float(entropy(p_mu, base=2))
        h_a = float(entropy(p_a, base=2))
        h_joint = float(entropy(joint_prob.flatten(), base=2))
        
        return h_mu, h_a, h_joint

    def attribute_action(
        self,
        action_result: dict,
        internal_state_before: np.ndarray,
        internal_state_after: np.ndarray
    ) -> AgencyAttribution:
        """
        Attribute action to self or external cause based on agency score.
        
        Uses the change in internal state before/after action to estimate
        the coupling between internal states and the action.
        
        Args:
            action_result: Dictionary containing action metadata
            internal_state_before: Internal state vector before action (μ_t)
            internal_state_after: Internal state vector after action (μ_{t+1})
            
        Returns:
            AgencyAttribution with score, attribution, and confidence
        """
        # Stack before/after as samples to estimate coupling
        # The idea: if internal states predict action outcomes, there's agency
        mu_samples = np.vstack([internal_state_before, internal_state_after])
        
        # Use the difference as a proxy for action effect
        action_effect = internal_state_after - internal_state_before
        a_samples = np.vstack([np.zeros_like(action_effect), action_effect])
        
        # Calculate agency score
        agency_score = self.calculate_agency_score(mu_samples, a_samples)
        
        # Calculate entropies for detailed attribution
        h_mu, h_a, h_joint = self._calculate_entropies(mu_samples, a_samples)
        
        # Mutual information I(μ;a) = H(μ) + H(a) - H(μ,a)
        mutual_info = max(0.0, h_mu + h_a - h_joint)
        
        # Classify based on thresholds
        if agency_score >= self.thresholds.high_agency_threshold:
            attribution = AgencyAttributionType.SELF
            # Confidence increases with score above threshold
            confidence = min(1.0, 0.7 + 0.3 * (
                (agency_score - self.thresholds.high_agency_threshold) /
                (2.0 - self.thresholds.high_agency_threshold + self._epsilon)
            ))
        elif agency_score <= self.thresholds.low_agency_threshold:
            attribution = AgencyAttributionType.EXTERNAL
            # Confidence increases as score approaches 0
            confidence = min(1.0, 0.7 + 0.3 * (
                (self.thresholds.low_agency_threshold - agency_score) /
                (self.thresholds.low_agency_threshold + self._epsilon)
            ))
        else:
            attribution = AgencyAttributionType.AMBIGUOUS
            # Confidence is lower in ambiguous zone
            mid_point = (self.thresholds.high_agency_threshold + self.thresholds.low_agency_threshold) / 2
            distance_from_mid = abs(agency_score - mid_point)
            zone_width = (self.thresholds.high_agency_threshold - self.thresholds.low_agency_threshold) / 2
            confidence = 0.3 + 0.4 * (distance_from_mid / (zone_width + self._epsilon))
        
        logger.info(
            f"Agency attribution: {attribution.value} (score={agency_score:.4f}, "
            f"confidence={confidence:.4f}, MI={mutual_info:.4f})"
        )
        
        return AgencyAttribution(
            score=agency_score,
            attribution=attribution,
            confidence=confidence,
            internal_entropy=h_mu,
            active_entropy=h_a,
            joint_entropy=h_joint,
            mutual_information=mutual_info
        )

    def estimate_agency_from_trajectory(
        self,
        internal_trajectory: np.ndarray,
        action_trajectory: np.ndarray
    ) -> AgencyAttribution:
        """
        Estimate agency from a trajectory of internal states and actions.
        
        More accurate than single-action attribution as it uses
        full trajectory data for density estimation.
        
        Args:
            internal_trajectory: Sequence of internal states (T x D)
            action_trajectory: Sequence of action states (T x D)
            
        Returns:
            AgencyAttribution with score, attribution, and confidence
        """
        agency_score = self.calculate_agency_score(internal_trajectory, action_trajectory)
        
        # Calculate entropies
        h_mu, h_a, h_joint = self._calculate_entropies(internal_trajectory, action_trajectory)
        mutual_info = max(0.0, h_mu + h_a - h_joint)
        
        # Classify
        if agency_score >= self.thresholds.high_agency_threshold:
            attribution = AgencyAttributionType.SELF
            base_confidence = 0.7
        elif agency_score <= self.thresholds.low_agency_threshold:
            attribution = AgencyAttributionType.EXTERNAL
            base_confidence = 0.7
        else:
            attribution = AgencyAttributionType.AMBIGUOUS
            base_confidence = 0.4
        
        # Trajectory-based estimation has higher confidence due to more samples
        sample_bonus = min(0.2, 0.01 * len(internal_trajectory))
        confidence = min(1.0, base_confidence + sample_bonus)
        
        return AgencyAttribution(
            score=agency_score,
            attribution=attribution,
            confidence=confidence,
            internal_entropy=h_mu,
            active_entropy=h_a,
            joint_entropy=h_joint,
            mutual_information=mutual_info
        )


# Singleton factory
_agency_detector: Optional[AgencyDetector] = None


def get_agency_detector(
    thresholds: Optional[AgencyThresholds] = None,
    num_bins: int = 20
) -> AgencyDetector:
    """Get or create agency detector singleton."""
    global _agency_detector
    if _agency_detector is None:
        _agency_detector = AgencyDetector(thresholds=thresholds, num_bins=num_bins)
    return _agency_detector
