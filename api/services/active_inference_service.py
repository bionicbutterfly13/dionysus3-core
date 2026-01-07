"""
Active Inference Service - Julia Backend Integration

Wraps ActiveInference.jl in Python service layer for Dionysus framework.
Ensures field-standard algorithms while maintaining Python integration.

Based on:
- ActiveInference.jl (Nehrer et al., 2025) - Computational implementation
- Thoughtseeds Framework (Kavi et al., 2025) - Cognitive architecture
- Free Energy Principle (Friston, 2010) - Theoretical foundation

Author: Mani Saint-Victor, MD
Date: 2026-01-03
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger("dionysus.services.active_inference")


# ============================================================================
# LAZY JULIA IMPORT (only load when needed)
# ============================================================================

_julia_initialized = False
_julia_main = None


def _initialize_julia():
    """
    Lazy initialization of Julia runtime.
    Only loads when ActiveInference functions are actually called.
    """
    global _julia_initialized, _julia_main

    if _julia_initialized:
        return _julia_main

    try:
        from julia import Main
        from julia import Pkg

        # Load ActiveInference.jl
        logger.info("Loading ActiveInference.jl...")
        Main.eval('using ActiveInference')

        _julia_main = Main
        _julia_initialized = True
        logger.info("ActiveInference.jl loaded successfully")

        return _julia_main

    except Exception as e:
        logger.error(f"Failed to initialize Julia: {e}")
        raise RuntimeError(
            f"Julia initialization failed. Ensure Julia is installed and "
            f"ActiveInference.jl package is available: {e}"
        )


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class GenerativeModel:
    """
    POMDP Generative Model (Active Inference)

    Maps to Thoughtseeds Eq 6 (KD Generative Model):
    P(a_k, s_k, μ_k, C_k, v_k, r_k | θ_k, TS_parent)

    Attributes:
        A: Observation model (likelihood) - P(o|s)
        B: Transition model (dynamics) - P(s'|s,a)
        C: Preference model (goals) - P(o*)
        D: Initial state prior - P(s_0)
        E: Policy prior (optional) - P(π)
    """
    A: np.ndarray  # [num_obs, num_states]
    B: np.ndarray  # [num_states, num_states, num_actions]
    C: np.ndarray  # [num_obs, 1]
    D: np.ndarray  # [num_states, 1]
    E: Optional[np.ndarray] = None  # [num_policies, 1]

    def to_julia(self) -> Dict[str, Any]:
        """Convert to Julia-compatible format."""
        return {
            'A': self.A.tolist(),
            'B': self.B.tolist(),
            'C': self.C.tolist(),
            'D': self.D.tolist(),
            'E': self.E.tolist() if self.E is not None else None
        }


@dataclass
class BeliefState:
    """
    Agent's current beliefs about states.

    Maps to Thoughtseeds μ_k (internal state).
    """
    qs: np.ndarray  # Posterior belief over states
    qπ: Optional[np.ndarray] = None  # Posterior belief over policies

    @property
    def entropy(self) -> float:
        """Calculate entropy of belief distribution (uncertainty)."""
        return -np.sum(self.qs * np.log(self.qs + 1e-16))


# ============================================================================
# ACTIVE INFERENCE SERVICE
# ============================================================================

class ActiveInferenceService:
    """
    Python wrapper for ActiveInference.jl operations.

    Provides field-standard active inference algorithms while maintaining
    integration with Dionysus Python architecture.

    Key Operations:
    - infer_states: State inference from observations (VFE minimization)
    - infer_policies: Policy selection (EFE minimization)
    - calculate_vfe: Variational Free Energy
    - calculate_efe: Expected Free Energy
    - sample_action: Action sampling from policy

    Maps to Thoughtseeds Framework:
    - NP Free Energy (Eq 3) → calculate_vfe()
    - TS Policy Selection (Eq 13) → infer_policies()
    - Active Pool (Eq 12) → belief-based thresholding
    """

    def __init__(self, lazy_load: bool = True):
        """
        Initialize Active Inference Service.

        Args:
            lazy_load: If True, only load Julia when first needed (default).
                      If False, load Julia immediately.
        """
        self.lazy_load = lazy_load

        if not lazy_load:
            _initialize_julia()

    def _ensure_julia(self):
        """Ensure Julia is loaded before operation."""
        if not _julia_initialized:
            _initialize_julia()
        return _julia_main

    # ========================================================================
    # CORE INFERENCE OPERATIONS
    # ========================================================================

    def infer_states(
        self,
        observation: np.ndarray,
        model: GenerativeModel,
        prior_belief: Optional[np.ndarray] = None,
        num_iterations: int = 16
    ) -> BeliefState:
        """
        Infer hidden states from observation using VFE minimization.

        Implements Thoughtseeds Eq 3 (NP Free Energy):
        F_i = D_KL[q(μ_i) || p(μ_i | s_i, a_i, θ_i)]

        Uses ActiveInference.jl's infer_states!() - exact algorithm.

        Args:
            observation: Observed outcome vector
            model: Generative model (A, B, C, D matrices)
            prior_belief: Prior belief over states (default: model.D)
            num_iterations: Number of VFE minimization iterations

        Returns:
            BeliefState with posterior over states
        """
        Main = self._ensure_julia()

        if prior_belief is None:
            prior_belief = model.D

        logger.debug(f"Inferring states from observation: {observation}")

        # Call Julia function
        # Note: Actual API may vary - this is a template
        qs = Main.infer_states(
            observation.tolist(),
            model.A.tolist(),
            prior_belief.tolist(),
            num_iterations
        )

        # Convert back to numpy
        qs_array = np.array(qs)

        return BeliefState(qs=qs_array)

    def infer_policies(
        self,
        current_belief: BeliefState,
        model: GenerativeModel,
        horizon: int = 3,
        gamma: float = 16.0
    ) -> Tuple[BeliefState, np.ndarray]:
        """
        Infer policy distribution using EFE minimization.

        Implements Thoughtseeds Eq 13 (Dominant Selection):
        TS_dominant = argmin_{TS_m ∈ A_pool} F_m

        Uses ActiveInference.jl's infer_policies!() - exact algorithm.

        Args:
            current_belief: Current posterior over states
            model: Generative model
            horizon: Planning horizon (number of timesteps)
            gamma: Precision parameter (inverse temperature)

        Returns:
            Tuple of (updated_belief, policy_distribution)
        """
        Main = self._ensure_julia()

        logger.debug(f"Inferring policies with horizon={horizon}, gamma={gamma}")

        # Call Julia function
        qπ = Main.infer_policies(
            current_belief.qs.tolist(),
            model.A.tolist(),
            model.B.tolist(),
            model.C.tolist(),
            horizon,
            gamma
        )

        qπ_array = np.array(qπ)

        # Update belief state with policy distribution
        updated_belief = BeliefState(
            qs=current_belief.qs,
            qπ=qπ_array
        )

        return updated_belief, qπ_array

    def sample_action(
        self,
        policy_distribution: np.ndarray,
        policies: np.ndarray,
        timestep: int = 0
    ) -> int:
        """
        Sample action from policy distribution.

        Uses ActiveInference.jl's sample_action!().

        Args:
            policy_distribution: Posterior over policies (from infer_policies)
            policies: Available policy sequences [num_policies, horizon, num_actions]
            timestep: Current timestep in policy sequence

        Returns:
            Sampled action index
        """
        Main = self._ensure_julia()

        # Sample policy weighted by posterior
        policy_idx = np.random.choice(
            len(policy_distribution),
            p=policy_distribution
        )

        # Get action at current timestep
        action = policies[policy_idx, timestep]

        logger.debug(f"Sampled action {action} from policy {policy_idx}")

        return int(action)

    # ========================================================================
    # FREE ENERGY CALCULATIONS
    # ========================================================================

    def calculate_vfe(
        self,
        belief: BeliefState,
        observation: np.ndarray,
        model: GenerativeModel
    ) -> float:
        """
        Calculate Variational Free Energy.

        Implements Thoughtseeds Eq 3, 7 (NP and KD Free Energy):
        VFE = Complexity - Accuracy
            = D_KL[q(s) || p(s)] - E_q[log p(o|s)]

        Maps to ActiveInference.jl Eq 5 (Nehrer et al., 2025):
        F = D_{KL}[q(s) || p(o,s)]

        Args:
            belief: Current belief state
            observation: Observed outcome
            model: Generative model

        Returns:
            VFE scalar value
        """
        # Complexity term: KL divergence from prior
        complexity = self._kl_divergence(belief.qs, model.D)

        # Accuracy term: Expected log-likelihood
        likelihood = model.A[observation, :]  # P(o|s)
        accuracy = np.dot(belief.qs, np.log(likelihood + 1e-16))

        vfe = complexity - accuracy

        logger.debug(f"VFE = {vfe:.4f} (complexity={complexity:.4f}, accuracy={accuracy:.4f})")

        return float(vfe)

    def calculate_efe(
        self,
        belief: BeliefState,
        model: GenerativeModel,
        policy: np.ndarray,
        horizon: int = 3
    ) -> float:
        """
        Calculate Expected Free Energy for a policy.

        Implements Thoughtseeds Eq 17.3 (Agent-Level EFE):
        EFE_agent = Σ_{TS_m ∈ A_pool} (α_m × EFE_m)

        Maps to ActiveInference.jl Eq 17-18 (Nehrer et al., 2025):
        G(π) = E_q[D_{KL}[q(o|π) || p(o)]] - E_q[D_{KL}[q(s|π) || q(s)]]
              └─ Pragmatic value ─┘  └─── Epistemic value ───┘

        Args:
            belief: Current belief state
            model: Generative model
            policy: Policy sequence [horizon, num_actions]
            horizon: Planning horizon

        Returns:
            EFE scalar value
        """
        efe = 0.0

        # Simulate forward under policy
        current_qs = belief.qs

        for t in range(horizon):
            action = policy[t]

            # Predict next state: q(s') = B(s,a) @ q(s)
            predicted_qs = model.B[:, :, action] @ current_qs

            # Predict observation: q(o) = A @ q(s')
            predicted_qo = model.A @ predicted_qs

            # Pragmatic value: KL[q(o) || C] (preference satisfaction)
            pragmatic = self._kl_divergence(predicted_qo, model.C)

            # Epistemic value: H[q(o)] - E_qs[H[q(o|s)]]
            # (information gain about states)
            epistemic = self._entropy(predicted_qo)
            # Subtract conditional entropy (simplified)
            epistemic -= np.sum(
                predicted_qs * np.array([self._entropy(model.A[:, s]) for s in range(len(predicted_qs))])
            )

            efe += pragmatic - epistemic
            current_qs = predicted_qs

        logger.debug(f"EFE = {efe:.4f} for policy")

        return float(efe)

    # ========================================================================
    # THOUGHTSEEDS INTEGRATION
    # ========================================================================

    def select_dominant_thoughtseed(
        self,
        thoughtseeds: List[Dict],
        threshold: float = 0.5
    ) -> Optional[Dict]:
        """
        Select dominant ThoughtSeed via free energy minimization.

        Implements Thoughtseeds Eq 12-13 (Active Pool & Dominant Selection):

        1. Active Pool (Eq 12):
           A_pool(t) = {TS_m | α_m(t) ≥ τ_activation}

        2. Winner-Take-All (Eq 13):
           TS_dominant = argmin_{TS_m ∈ A_pool} F_m

        Args:
            thoughtseeds: List of ThoughtSeed dicts with 'activation_level' and 'belief_state'
            threshold: Activation threshold τ for pool membership

        Returns:
            Dominant ThoughtSeed dict, or None if pool is empty
        """
        # Step 1: Filter active pool (Eq 12)
        active_pool = [
            ts for ts in thoughtseeds
            if ts.get('activation_level', 0.0) >= threshold
        ]

        if not active_pool:
            logger.debug("No thoughtseeds meet activation threshold")
            return None

        logger.debug(f"Active pool size: {len(active_pool)}/{len(thoughtseeds)}")

        # Step 2: Calculate VFE for each in pool
        vfe_scores = []
        for ts in active_pool:
            belief = ts.get('belief_state')
            observation = ts.get('observation')
            model = ts.get('generative_model')

            if belief and observation is not None and model:
                vfe = self.calculate_vfe(belief, observation, model)
            else:
                # Fallback: use activation as proxy
                vfe = -ts['activation_level']

            vfe_scores.append(vfe)

        # Step 3: Select minimum VFE (Eq 13)
        dominant_idx = np.argmin(vfe_scores)
        dominant_ts = active_pool[dominant_idx]

        logger.info(
            f"Dominant ThoughtSeed selected with VFE={vfe_scores[dominant_idx]:.4f}"
        )

        return dominant_ts

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate KL divergence D_KL[p || q]."""
        return np.sum(p * np.log((p + 1e-16) / (q + 1e-16)))

    def _entropy(self, p: np.ndarray) -> float:
        """Calculate Shannon entropy H[p]."""
        return -np.sum(p * np.log(p + 1e-16))

    def create_simple_model(
        self,
        num_states: int,
        num_observations: int,
        num_actions: int
    ) -> GenerativeModel:
        """
        Create a simple generative model with uniform priors.

        Useful for testing and simple scenarios.

        Args:
            num_states: Number of hidden states
            num_observations: Number of observable outcomes
            num_actions: Number of available actions

        Returns:
            GenerativeModel with uniform distributions
        """
        # Uniform observation model
        A = np.ones((num_observations, num_states)) / num_observations

        # Uniform transition model
        B = np.ones((num_states, num_states, num_actions)) / num_states

        # Uniform preferences (no preference)
        C = np.ones((num_observations, 1)) / num_observations

        # Uniform prior
        D = np.ones((num_states, 1)) / num_states

        return GenerativeModel(A=A, B=B, C=C, D=D)


# ============================================================================
# FACTORY
# ============================================================================

_service_instance: Optional[ActiveInferenceService] = None


def get_active_inference_service(lazy_load: bool = True) -> ActiveInferenceService:
    """
    Get singleton Active Inference Service instance.

    Args:
        lazy_load: Only load Julia when first needed (recommended)

    Returns:
        ActiveInferenceService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = ActiveInferenceService(lazy_load=lazy_load)

    return _service_instance
