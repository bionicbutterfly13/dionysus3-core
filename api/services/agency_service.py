"""
Agency Service - Sense of Agency Computation

Feature: 040-metacognitive-particles
Based on: Sandved-Smith & Da Costa (2024) Eq.20

Computes sense of agency as KL divergence:
D_KL[Q(μ¹,a¹) | Q(μ¹)Q(a¹)]

- 0.0 = no agency (internal and active paths are independent)
- Higher values = stronger sense of agency

AUTHOR: Mani Saint-Victor, MD
"""

import logging
from typing import Optional, Tuple

import numpy as np
from scipy.stats import entropy

from api.models.metacognitive_particle import ParticleType
from api.models.belief_state import BeliefState

logger = logging.getLogger("dionysus.services.agency")

# Default threshold for agency detection
AGENCY_THRESHOLD = 1e-6


class AgencyService:
    """
    Computes sense of agency strength using KL divergence.

    Per Eq.20 from Sandved-Smith & Da Costa (2024):
    Agency strength = D_KL[Q(μ¹,a¹) | Q(μ¹)Q(a¹)]

    Where:
    - Q(μ¹,a¹) is the joint distribution over internal and active paths
    - Q(μ¹)Q(a¹) is the product of marginals

    When these are equal (KL = 0), there is no sense of agency.
    Higher KL divergence indicates stronger agency.
    """

    def __init__(self, threshold: float = AGENCY_THRESHOLD):
        self.threshold = threshold

    async def compute_agency_strength(
        self,
        joint_distribution: np.ndarray,
        marginal_mu: np.ndarray,
        marginal_a: np.ndarray
    ) -> float:
        """
        Compute agency strength using KL divergence.

        Args:
            joint_distribution: Q(μ,a) joint probability over internal and active
            marginal_mu: Q(μ) marginal over internal paths
            marginal_a: Q(a) marginal over active paths

        Returns:
            KL divergence value (0 = no agency, higher = stronger agency)
        """
        # Compute independent distribution as outer product of marginals
        independent = np.outer(marginal_mu, marginal_a).flatten()

        # Normalize to ensure valid probability distributions
        joint_flat = joint_distribution.flatten()
        joint_flat = joint_flat / joint_flat.sum()
        independent = independent / independent.sum()

        # Add small epsilon to avoid log(0)
        eps = 1e-10
        joint_flat = joint_flat + eps
        independent = independent + eps

        # Renormalize
        joint_flat = joint_flat / joint_flat.sum()
        independent = independent / independent.sum()

        # Compute KL divergence using scipy
        kl_div = entropy(joint_flat, independent)

        logger.debug(f"Computed agency strength: {kl_div:.6f}")
        return float(kl_div)

    async def compute_agency_strength_gaussian(
        self,
        joint_mean: np.ndarray,
        joint_precision: np.ndarray,
        marginal_mu_mean: np.ndarray,
        marginal_mu_precision: np.ndarray,
        marginal_a_mean: np.ndarray,
        marginal_a_precision: np.ndarray
    ) -> float:
        """
        Compute agency strength for Gaussian distributions (closed-form).

        Uses the analytical KL divergence formula for multivariate Gaussians.

        Args:
            joint_mean: Mean of joint distribution
            joint_precision: Precision matrix of joint distribution
            marginal_mu_mean: Mean of marginal over internal paths
            marginal_mu_precision: Precision of marginal over internal paths
            marginal_a_mean: Mean of marginal over active paths
            marginal_a_precision: Precision of marginal over active paths

        Returns:
            KL divergence value
        """
        # Construct independent distribution parameters
        # The independent distribution is product of marginals
        # For Gaussians: block diagonal precision matrix
        d_mu = len(marginal_mu_mean)
        d_a = len(marginal_a_mean)
        d_total = d_mu + d_a

        # Independent mean is concatenation of marginal means
        independent_mean = np.concatenate([marginal_mu_mean, marginal_a_mean])

        # Independent precision is block diagonal
        independent_precision = np.zeros((d_total, d_total))
        independent_precision[:d_mu, :d_mu] = marginal_mu_precision
        independent_precision[d_mu:, d_mu:] = marginal_a_precision

        # Compute KL divergence: D_KL(P || Q)
        # where P is joint and Q is independent
        kl = self._kl_divergence_gaussian(
            p_mean=joint_mean,
            p_precision=joint_precision,
            q_mean=independent_mean,
            q_precision=independent_precision
        )

        logger.debug(f"Computed Gaussian agency strength: {kl:.6f}")
        return kl

    def _kl_divergence_gaussian(
        self,
        p_mean: np.ndarray,
        p_precision: np.ndarray,
        q_mean: np.ndarray,
        q_precision: np.ndarray
    ) -> float:
        """
        Compute KL divergence between two multivariate Gaussians.

        D_KL(P || Q) = 0.5 * [
            tr(Σ_Q^{-1} Σ_P) +
            (μ_Q - μ_P)^T Σ_Q^{-1} (μ_Q - μ_P) -
            d +
            ln(det(Σ_Q) / det(Σ_P))
        ]

        Using precision matrices (Σ^{-1}):
        D_KL(P || Q) = 0.5 * [
            tr(Π_Q Σ_P) +
            (μ_Q - μ_P)^T Π_Q (μ_Q - μ_P) -
            d +
            ln(det(Π_P) / det(Π_Q))
        ]
        """
        d = len(p_mean)

        # Compute covariance from precision
        try:
            p_cov = np.linalg.inv(p_precision)
        except np.linalg.LinAlgError:
            p_cov = np.linalg.pinv(p_precision)

        # Compute trace term
        trace_term = np.trace(q_precision @ p_cov)

        # Compute quadratic term
        diff = q_mean - p_mean
        quad_term = diff @ q_precision @ diff

        # Compute log determinant ratio
        try:
            det_p = np.linalg.det(p_precision)
            det_q = np.linalg.det(q_precision)
            if det_p <= 0 or det_q <= 0:
                log_det_ratio = 0.0
            else:
                log_det_ratio = np.log(det_p / det_q)
        except (ValueError, FloatingPointError):
            log_det_ratio = 0.0

        kl = 0.5 * (trace_term + quad_term - d + log_det_ratio)
        return max(0.0, float(kl))  # KL should be non-negative

    async def has_agency(
        self,
        agency_strength: float,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Determine if agent has sense of agency.

        FR-009: Threshold check for agency detection.

        Args:
            agency_strength: Computed KL divergence value
            threshold: Optional custom threshold (default AGENCY_THRESHOLD)

        Returns:
            True if agency strength exceeds threshold
        """
        thresh = threshold if threshold is not None else self.threshold
        return agency_strength > thresh

    async def get_agent_agency(
        self,
        agent_id: str
    ) -> Tuple[float, bool, Optional[ParticleType]]:
        """
        Get agency information for an agent.

        This is a high-level method that retrieves the agent's state
        and computes agency strength.

        Args:
            agent_id: Agent identifier

        Returns:
            Tuple of (agency_strength, has_agency, particle_type)
        """
        from api.services.network_state_service import get_network_state_service
        from api.services.agency_detector import AgencyDetector

        logger.info(f"Computing agency for agent {agent_id}")

        network_state_service = get_network_state_service()
        state = await network_state_service.get_current(agent_id)
        if state is None:
            raise LookupError(f"No network state available for agent {agent_id}")

        internal_values = list(state.connection_weights.values())
        active_values = list(state.speed_factors.values())
        sample_count = min(len(internal_values), len(active_values))
        if sample_count < 2:
            raise LookupError(f"Insufficient network state samples for agent {agent_id}")

        mu_samples = np.array([[v] for v in internal_values[:sample_count]], dtype=float)
        a_samples = np.array([[v] for v in active_values[:sample_count]], dtype=float)

        detector = AgencyDetector()
        agency_strength = detector.calculate_agency_score(mu_samples, a_samples)
        has_agency = await self.has_agency(agency_strength)
        particle_type = ParticleType.ACTIVE_METACOGNITIVE if has_agency else ParticleType.COGNITIVE

        return agency_strength, has_agency, particle_type

    async def compute_from_beliefs(
        self,
        joint_belief: BeliefState,
        marginal_mu: BeliefState,
        marginal_a: BeliefState
    ) -> float:
        """
        Compute agency strength from BeliefState objects.

        Convenience method that extracts parameters and calls
        compute_agency_strength_gaussian.

        Args:
            joint_belief: Joint belief state Q(μ,a)
            marginal_mu: Marginal belief over internal paths
            marginal_a: Marginal belief over active paths

        Returns:
            Agency strength (KL divergence)
        """
        return await self.compute_agency_strength_gaussian(
            joint_mean=joint_belief.mean_array,
            joint_precision=joint_belief.precision_array,
            marginal_mu_mean=marginal_mu.mean_array,
            marginal_mu_precision=marginal_mu.precision_array,
            marginal_a_mean=marginal_a.mean_array,
            marginal_a_precision=marginal_a.precision_array
        )
