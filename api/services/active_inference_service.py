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
import numpy as np

from api.models.belief_state import BeliefState as CanonicalBeliefState

logger = logging.getLogger("dionysus.services.active_inference")


@dataclass
class VFEDetail:
    """Breakdown of Variational Free Energy components."""
    total: float
    complexity: float  # D_KL[q(s)||p(s)]
    accuracy: float    # E_q[log p(o|s)]

# ============================================================================
# LAZY JULIA IMPORT (only load when needed)
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


# Removed local BeliefState dataclass to use CanonicalBeliefState
# The Adapter logic will handle conversion between Canonical (Pydantic) and Internal (NumPy)


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
        
        # Feature 062: Blackglass Threshold (Ambiguity Tolerance)
        # If policy entropy > 1.5 nats, refuse to act.
        self.blackglass_threshold = 1.5 
        
        # Initialize Adapter Registry (Simple functional mapping for now)
        self._pydantic_to_numpy_map = {} 

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
    ) -> CanonicalBeliefState:
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
            CanonicalBeliefState with posterior over states (mean=qs)
        """
        try:
            Main = self._ensure_julia()

            # Call Julia function
            qs = Main.infer_states(
                observation.tolist(),
                model.A.tolist(),
                prior_belief.tolist(),
                num_iterations
            )
            
            # Convert back to numpy
            qs_array = np.array(qs)
            
        except Exception as e:
            logger.warning(f"Julia backend failed for infer_states, using Lizard Brain fallback: {e}")
            qs_array = self._infer_states_fallback(observation, model, prior_belief)

        # Convert to Canonical Pydantic Model
        return self._numpy_to_belief_state(qs_array)

    async def infer_policies(
        self,
        current_belief: CanonicalBeliefState,
        model: GenerativeModel,
        horizon: int = 3,
        gamma: float = 16.0
    ) -> Tuple[CanonicalBeliefState, Optional[np.ndarray]]:
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
        # Adapter: Extract qs from Pydantic Mean
        qs_input = np.array(current_belief.mean)

        try:
            Main = self._ensure_julia()
        
            # Call Julia function
            qπ = Main.infer_policies(
                qs_input.tolist(),
                model.A.tolist(),
                model.B.tolist(),
                model.C.tolist(),
                horizon,
                gamma
            )
            qπ_array = np.array(qπ)
            
        except Exception as e:
            logger.warning(f"Julia backend failed for infer_policies, using Lizard Brain fallback: {e}")
            qπ_array = self._infer_policies_fallback(qs_input, model, horizon)

            qπ_array = self._infer_policies_fallback(qs_input, model, horizon)

        # Feature 062: The Blackglass Protocol (Ambiguity Check)
        # Calculate Entropy (Self-Friction)
        entropy = self._entropy(qπ_array)
        
        if entropy > self.blackglass_threshold:
            logger.warning(
                f"BLACKGLASS PROTOCOL: Ambiguity {entropy:.2f} > {self.blackglass_threshold}. "
                "Refusing to collapse uncertainty."
            )
            return current_belief, None  # Refusal Signal

        # Return updated belief (same state, just policy inferred)
        return current_belief, qπ_array

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
        try:
            Main = self._ensure_julia()
            
            # Use Julia sampling if available (better RNG)
            # But converting potentially complex Julia objects back might be overhead
            # Logic: If we are here, we likely have policies from Julia.
             # Call Julia function
            action = Main.sample_action(
                policy_distribution.tolist(),
                policies.tolist(), # Careful with 3D arrays
                timestep
            )
            return int(action)
            
        except Exception:
            # Simple NumPy sampling
            policy_idx = np.random.choice(
                len(policy_distribution),
                p=policy_distribution
            )
            return int(policies[policy_idx, timestep])

        # Get action at current timestep
        action = policies[policy_idx, timestep]

        logger.debug(f"Sampled action {action} from policy {policy_idx}")

        return int(action)

    # ========================================================================
    # FREE ENERGY CALCULATIONS
    # ========================================================================

    def calculate_vfe(
        self,
        belief: CanonicalBeliefState,
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
            VFEDetail object with total, complexity, and accuracy components
        """
        # Complexity term: KL divergence from prior
        qs = np.array(belief.mean)
        complexity = self._kl_divergence(qs, model.D)

        # Accuracy term: Expected log-likelihood
        likelihood = model.A[observation, :]  # P(o|s)
        accuracy = np.dot(qs, np.log(likelihood + 1e-16))

        vfe = complexity - accuracy


        logger.debug(f"VFE = {vfe:.4f} (complexity={complexity:.4f}, accuracy={accuracy:.4f})")

        return VFEDetail(
            total=float(vfe),
            complexity=float(complexity),
            accuracy=float(accuracy)
        )

    def calculate_semantic_vfe(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate VFE for Semantic Retrieval (Surprisal).
        
        Approximation:
        VFE = 1.0 - Resonance
        Resonance = Average Similarity of Top Results
        
        If the system is "surprised" (High VFE), it means the
        internal model (search strategy) failed to predict (retrieve)
        highly consonant information.
        
        Args:
            query: The user query
            results: List of memory dicts with 'similarity' or 'score'
            
        Returns:
            float: VFE score (0.0 to 1.0)
        """
        if not results:
            return 1.0 # Maximum surprisal (found nothing)
            
        similarities = []
        for res in results:
            score = res.get('similarity', 0.0) or res.get('score', 0.0) or 0.0
            similarities.append(float(score))
            
        if not similarities:
            return 1.0
            
        avg_resonance = sum(similarities) / len(similarities)
        
        # VFE is minimizing free energy (maximizing resonance)
        vfe = 1.0 - avg_resonance
        
        logger.debug(f"Semantic VFE: {vfe:.4f} (Avg Resonance: {avg_resonance:.4f})")
        return max(0.0, min(1.0, vfe))

    def calculate_efe(
        self,
        belief: CanonicalBeliefState,
        model: GenerativeModel,
        policy: np.ndarray,
        horizon: int = 3
    ) -> float:
        """
        Calculate Expected Free Energy for a policy.

        Implements Thoughtseeds Eq 17.3 (Agent-Level EFE):
        EFE_agent = Sum_{TS_m in A_pool} (alpha_m * EFE_m)

        Maps to ActiveInference.jl Eq 17-18 (Nehrer et al., 2025):
        G(pi) = E_q[D_{KL}[q(o|pi) || p(o)]] - E_q[D_{KL}[q(s|pi) || q(s)]]
              L_ Pragmatic value _J  L___ Epistemic value ___J

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
        current_qs = np.array(belief.mean)

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

    async def evaluate_efe(
        self,
        agent_state: "BiologicalAgentState",
        hypothetical_policy: str
    ) -> float:
        """
        Grounded Counterfactual Evaluation (Feature 064.5).
        
        Calculates the Expected Free Energy (EFE) for a hypothetical action
        given the agent's current belief and internal generative model.
        """
        # 1. Prepare Belief
        # Use the mean from the agent's metacognitive belief state
        mean = agent_state.metacognitive.belief_state.mean if agent_state.metacognitive.belief_state else None
        if not mean:
            # Fallback to perception
             mean = agent_state.perception.state_probabilities or [0.5, 0.5]
             
        belief = CanonicalBeliefState.from_mean_and_variance(mean=mean, variance=[0.1] * len(mean))

        # 2. Retrieve Model
        model = self._get_default_model(len(mean))
        
        # 3. Map Policy String to Action Index
        # In a real implementation, this would query a domain-specific Action Space.
        action_map = {"obey_command": 0, "resist_coercion": 1, "refuse_to_choose": 1}
        action_idx = action_map.get(hypothetical_policy, 0)
        policy = np.array([action_idx]) # 1-step policy
        
        return self.calculate_efe(belief, model, policy, horizon=1)

    def _get_default_model(self, num_states: int) -> GenerativeModel:
        """Construct a default normative GenerativeModel for simulation."""
        # Simplified Identity Model
        # Action 0 (Obey): high probability of state transition, potentially high complexity cost
        # Action 1 (Resist): maintains state, prevents coercion impact
        num_obs = num_states
        num_actions = 2
        
        A = np.eye(num_obs) # Identity observation model
        B = np.zeros((num_states, num_states, num_actions))
        B[:, :, 0] = np.eye(num_states) # Transition for Action 0
        B[:, :, 1] = np.eye(num_states) # Transition for Action 1
        
        # C (Preferences): Uniform or slightly biased toward internal state
        C = np.ones((num_obs, 1)) / num_obs
        D = np.ones((num_states, 1)) / num_states
        
        return GenerativeModel(A=A, B=B, C=C, D=D)

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
           A_pool(t) = {TS_m | alpha_m(t) >= tau_activation}

        2. Winner-Take-All (Eq 13):
           TS_dominant = argmin_{TS_m in A_pool} F_m

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

            vfe_detail = VFEDetail(0.0, 0.0, 0.0)
            if belief and observation is not None and model:
                vfe_detail = self.calculate_vfe(belief, observation, model)
                vfe = vfe_detail.total
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

    async def expand_query(
        self, 
        query: str, 
        context: Optional[str] = None
    ) -> List[str]:
        """
        Expand a query with latent concepts (Active Priors).
        
        Uses the Generative Model (LLM) to predict:
        "Given this query and context, what other concepts are likely relevant?"
        
        This implements the "Active Inquiry" principle:
        Searching not just for what was asked, but for what *should* be there.
        
        Args:
            query: The raw user query.
            context: Optional context (e.g., "Marketing", "Coding").
            
        Returns:
            List[str]: A list of expanded concepts/terms.
        """
        from api.services.llm_service import chat_completion, GPT5_NANO
        
        system_prompt = (
            "You are the Active Inference Prior Generator for a semantic memory system.\n"
            "Your task is to predict LATENT CONCEPTS that are semantically necessary "
            "to answer the user's query, even if not explicitly stated.\n"
            "Think: 'If I were an expert, what related concepts would I check?'\n"
            "Return ONLY a comma-separated list of 3-5 key concepts."
        )
        
        user_prompt = f"Query: {query}"
        if context:
            user_prompt += f"\nContext: {context}"
            
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                model=GPT5_NANO
            )
            
            content = response.strip()
            # Clean and split
            concepts = [c.strip() for c in content.split(',') if c.strip()]
            
            logger.info(f"Expanded query '{query}' -> {concepts}")
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to expand query: {e}")
            return [query] # Fallback to original query

    async def expand_state_space(self, suggestion: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Structure Learning: Expand the state space by adding a new Concept.
        
        Triggered when VFE > ExpansionThreshold (e.g. 0.7).
        The system "hallucinates" a new hidden state (Concept) to explain the surprisal.
        
        Args:
            suggestion: The proposed concept name/description.
            context: Context for where to attach this concept.
            
        Returns:
            Dict with creation details.
        """
        from api.services.graphiti_service import get_graphiti_service
        graphiti = await get_graphiti_service()
        
        try:
             # Create new Concept Node
            result = await graphiti.execute_cypher(
                """
                CREATE (c:Concept {
                    uuid: randomUUID(),
                    name: $name,
                    origin: 'ActiveInference_Expansion',
                    created_at: datetime(),
                    context: $context,
                    status: 'experimental'
                })
                RETURN c
                """,
                {"name": suggestion, "context": context or "Universal"}
            )
            logger.info(f"Structure Expansion: Created Concept '{suggestion}'")
            return {"success": True, "concept": result[0]['c']}
        except Exception as e:
            logger.error(f"Failed to expand state space: {e}")
            return {"success": False, "error": str(e)}

    async def reduce_model(self, threshold: float = 0.1) -> Dict[str, Any]:
        """
        Bayesian Model Reduction: Prune states with low evidence.
        
        Removes "experimental" Concepts that have not gained traction (relationships).
        
        Args:
            threshold: Minimum evidence required to keep.
            
        Returns:
            Dict with pruned count.
        """
        from api.services.graphiti_service import get_graphiti_service
        graphiti = await get_graphiti_service()
        
        try:
            # Find and Archive unused experimental concepts (> 1 day old, no rels)
            result = await graphiti.execute_cypher(
                """
                MATCH (c:Concept {status: 'experimental'})
                WHERE c.created_at < datetime() - duration('P1D')
                AND NOT (c)-[:RELATES_TO]-()
                SET c.status = 'archived', c.archived_at = datetime()
                RETURN count(c) as pruned
                """
            )
            count = result[0]['pruned']
            logger.info(f"Model Reduction: Pruned {count} concepts.")
            return {"success": True, "pruned": count}
        except Exception as e:
            logger.error(f"Failed to reduce model: {e}")
            return {"success": False, "error": str(e)}

            
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

    # ========================================================================
    # ADAPTERS (Phase 2: Unification)
    # ========================================================================

    def _numpy_to_belief_state(self, qs: np.ndarray) -> CanonicalBeliefState:
        """
        Convert internal NumPy belief (qs) to Canonical Pydantic CanonicalBeliefState.
        
        Args:
            qs: Probability distribution over states (Categorical).
            
        Returns:
            CanonicalBeliefState with mean=qs and calculated precision.
        """
        # 1. Mean is just the probability vector
        mean = qs.tolist()
        
        # 2. Precision (Inverse Variance)
        # For Categorical, variance of each element i is p_i * (1 - p_i).
        # We'll approximate a diagonal precision matrix.
        d = len(mean)
        variance = [(p * (1 - p)) + 1e-6 for p in mean] # Add epsilon to avoid divide by zero
        
        return CanonicalBeliefState.from_mean_and_variance(
            mean=mean,
            variance=variance
        )

    def _infer_states_fallback(
        self,
        observation: np.ndarray,
        model: GenerativeModel,
        prior: np.ndarray
    ) -> np.ndarray:
        """
        Lizard Brain: Simple Bayesian Update (No Iterative VFE).
        qs = softmax(ln A[o] + ln prior)
        """
        # 1. Likelihood: P(o|s)
        # Handle if observation is one-hot or index
        if observation.size == 1:
            likelihood = model.A[int(observation), :]
        else:
            # Dot product for probabilistic observation? Assuming index for now.
            likelihood = model.A[np.argmax(observation), :]

        # 2. Posterior ~ Likelihood * Prior
        posterior_unnormalized = likelihood * prior.flatten()
        
        # 3. Normalize
        norm = np.sum(posterior_unnormalized) + 1e-16
        qs = posterior_unnormalized / norm
        
        return qs

    def _infer_policies_fallback(
        self,
        qs: np.ndarray,
        model: GenerativeModel,
        horizon: int
    ) -> np.ndarray:
        """
        Lizard Brain: Greedy Action Selection (No Deep Tree Search).
        Evaluate immediate expected utility (alignment with C).
        """
        num_actions = model.B.shape[2]
        action_scores = np.zeros(num_actions)
        
        # Evaluate each action's immediate consequence
        for a in range(num_actions):
            # Predicted next state
            qs_next = model.B[:, :, a] @ qs
            
            # Predicted observation
            qo_next = model.A @ qs_next
            
            # Utility (Preference matching) - Simplified negative Divergence or just dot product
            # C is usually ln P(o_desired). 
            # If C is probs: utility = dot(qo, C)
            # If C is log-probs: utility = dot(qo, C)
            # Assuming C is log-probs in some implementations, but here likely probs.
            # Let's assume C is target distribution P(o). Minimizing KL[Q(o)||P(o)] maximize dot(Q, log P)
            utility = np.dot(qo_next.flatten(), np.log(model.C.flatten() + 1e-16))
            action_scores[a] = utility
            
        # Softmax over actions (Simple policy)
        # Note: This returns action probabilities, but infer_policies usually returns POLICY probabilities.
        # Fallback approximation: Each action is a "policy" of length 1 (or repeated).
        
        # Softmax
        exps = np.exp(action_scores - np.max(action_scores))
        policy_probs = exps / np.sum(exps)
        
        # Map back to whatever shape implied by 'num_policies'. 
        # For simplicity, if E (policy prior) exists, match it. 
        # If not, we just return logical distribution over actions as if they were policies.
        # REAL FALLBACK: Just return uniform if too complex.
        
        return policy_probs
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
