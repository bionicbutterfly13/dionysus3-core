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

# Re-export for backward compatibility
BeliefState = CanonicalBeliefState

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
@dataclass
class GenerativeModel:
    """
    POMDP Generative Model (Active Inference)

    Supports both Atomic (single matrix) and Factorized (list of matrices) models.
    Maps to Thoughtseeds Eq 6 (KD Generative Model).
    """
    A: Any  # np.ndarray or List[np.ndarray] - Observation likelihood(s)
    B: Any  # np.ndarray or List[np.ndarray] - Transition dynamics
    C: Any  # np.ndarray or List[np.ndarray] - Preferences/Prior over outcomes
    D: Any  # np.ndarray or List[np.ndarray] - Initial state prior(s)
    E: Optional[np.ndarray] = None  # Policy prior
    a: Optional[Any] = None  # Dirichlet parameters for A (likelihood learning)
    b: Optional[Any] = None  # Dirichlet parameters for B (transition learning)
    A_factor_list: Optional[List[List[int]]] = None # Multi-factor mapping for observations
    B_factor_list: Optional[List[List[int]]] = None # Multi-factor mapping for transitions

    def __post_init__(self):
        """Ensure matrices are consistently formatted as lists for internal logic."""
        if not isinstance(self.A, list): self.A = [self.A]
        if not isinstance(self.B, list): self.B = [self.B]
        if not isinstance(self.C, list): self.C = [self.C]
        if not isinstance(self.D, list): self.D = [self.D]

    def to_julia(self) -> Dict[str, Any]:
        """Convert to Julia-compatible list structures."""
        def to_list(obj):
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, list): return [to_list(i) for i in obj]
            return obj

        return {
            'A': to_list(self.A),
            'B': to_list(self.B),
            'C': to_list(self.C),
            'D': to_list(self.D),
            'E': to_list(self.E) if self.E is not None else None
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

    def __init__(self, lazy_load: bool = True) -> None:
        """
        Initialize Active Inference Service.

        Args:
            lazy_load: If True, only load Julia when first needed (default).
                      If False, load Julia immediately.
        """
        self.lazy_load = lazy_load
        
        # Feature 062: Blackglass Threshold (Ambiguity Tolerance)
        # If policy entropy > 1.5 nats, refuse to act.
        self.blackglass_threshold: float = 1.5 
        
        # Initialize Adapter Registry (Simple functional mapping for now)
        self._pydantic_to_numpy_map: Dict = {} 

        if not lazy_load:
            _initialize_julia()

    def _ensure_julia(self) -> Any:
        """Ensure Julia is loaded before operation."""
        if not _julia_initialized:
            _initialize_julia()
        return _julia_main

    # ========================================================================
    # MATH UTILITIES (NumPy Native)
    # ========================================================================

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Stable Softmax implementation."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

    def _spm_log(self, x: np.ndarray) -> np.ndarray:
        """Natural log with small epsilon to avoid inf."""
        return np.log(x + 1e-16)

    def _entropy(self, p: np.ndarray) -> float:
        """Calculate Shannon entropy H[p]."""
        return -np.sum(p * self._spm_log(p))

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate KL divergence D_KL[p || q]."""
        return np.sum(p * (self._spm_log(p) - self._spm_log(q)))

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
                model.to_julia()['A'],
                prior_belief.tolist() if prior_belief is not None else [],
                num_iterations
            )
            
            # Convert back to numpy
            qs_array = [np.array(f) for f in qs] if isinstance(qs, list) else np.array(qs)
            
        except Exception as e:
            logger.warning(f"Julia backend failed, using factorized NumPy fallback: {e}")
            qs_array = self._infer_states_vfe(observation, model, prior_belief, num_iterations)

        # Convert to Canonical Pydantic Model
        if isinstance(qs_array, list):
             mean = np.concatenate([f.flatten() for f in qs_array]).tolist()
        else:
             mean = qs_array.flatten().tolist()
             
        return CanonicalBeliefState(mean=mean, precision=[[1.0]])

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

    def calculate_uncertainty(self, belief: CanonicalBeliefState) -> float:
        """
        Calculate Shannon Entropy (Uncertainty) of the belief state.
        
        H(p) = - sum(p * log(p))
        
        Args:
            belief: CanonicalBeliefState
            
        Returns:
            float: Uncertainty value (in nats)
        """
        return float(self._entropy(np.array(belief.mean)))

    def calculate_surprisal(
        self,
        observation: np.ndarray,
        belief: CanonicalBeliefState,
        model: GenerativeModel
    ) -> float:
        """
        Calculate Surprisal (Self-Information) of an observation given beliefs.
        
        I(o) = - log p(o)
        Approximated as the Accuracy term of VFE: - E_q[log p(o|s)]
        
        Args:
            observation: Observed outcome vector or index
            belief: Current belief state
            model: Generative model
            
        Returns:
            float: Surprisal value (in nats)
        """
        qs = np.array(belief.mean)
        # Handle index vs vector observation
        obs_idx = np.argmax(observation) if observation.ndim > 0 else int(observation)
        
        likelihood = model.A[0][obs_idx, :] # Use first modality for now
        accuracy = np.dot(qs, self._spm_log(likelihood))
        
        return float(-accuracy)

    def calculate_vfe(
        self,
        belief: CanonicalBeliefState,
        observation: np.ndarray,
        model: GenerativeModel
    ) -> VFEDetail:
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
        horizon: int = 1
    ) -> float:
        """
        Calculate Expected Free Energy for a policy (Factorized).

        G(pi) = Pragmatic value - Epistemic value
        """
        efe = 0.0
        
        # Ensure policy is iterable
        if not hasattr(policy, "__iter__"):
            policy = [policy]
            horizon = 1

        # Reshape mean back to factors if needed
        # We start from current belief. 
        # If model is factorized, mean represents concatenated factors.
        qs = []
        start_idx = 0
        mean_arr = np.array(belief.mean)
        for D_f in model.D:
            f_size = len(D_f.flatten())
            qs.append(mean_arr[start_idx:start_idx+f_size])
            start_idx += f_size
        
        if not qs:
            qs = [np.copy(D).flatten() for D in model.D]

        for t in range(min(horizon, len(policy))):
            action = int(policy[t])
            
            # 1. Predict next state: q(s') = B_f[action] @ q_f
            qs_next = []
            for f, B_f in enumerate(model.B):
                qs_next.append(B_f[:, :, action] @ qs[f])
            
            # 2. Predict observations across all modalities
            qo_next = []
            mod_to_factor = []
            for m, A_m in enumerate(model.A):
                factor_list = model.A_factor_list[m] if model.A_factor_list else [m % len(qs_next)]
                f_idx = factor_list[0]
                mod_to_factor.append(f_idx)
                qo_next.append(A_m @ qs_next[f_idx])
            
            # 3. Calculate components
            for m, qo in enumerate(qo_next):
                C_m = model.C[m] if m < len(model.C) else model.C[0]
                A_m = model.A[m] if m < len(model.A) else model.A[0]
                
                efe += self._kl_divergence(qo, C_m.flatten())
                
                f_idx = mod_to_factor[m]
                h_qo = self._entropy(qo)
                h_cond = np.dot(qs_next[f_idx], [self._entropy(A_m[:, s]) for s in range(A_m.shape[1])])
                efe -= (h_qo - h_cond)
                
            qs = qs_next # Proceed to next timestep
            
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
        num_obs = num_states
        num_actions = 2
        
        A = np.eye(num_obs)
        B = np.zeros((num_states, num_states, num_actions))
        B[:, :, 0] = np.eye(num_states)
        B[:, :, 1] = np.eye(num_states)
        
        C = np.ones(num_obs) / num_obs
        D = np.ones(num_states) / num_states
        
        return GenerativeModel(A=[A], B=[B], C=[C], D=[D])

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

    def _infer_states_vfe(
        self,
        observation: Any,
        model: GenerativeModel,
        prior: Optional[np.ndarray] = None,
        num_iterations: int = 16
    ) -> List[np.ndarray]:
        """
        NumPy Native: Factorized Variational Free Energy Minimization.
        """
        qs = [np.copy(D).flatten() for D in model.D]
        
        for _ in range(num_iterations):
            for f in range(len(qs)):
                ln_likelihood = np.zeros_like(qs[f])
                for m, A in enumerate(model.A):
                    factor_list = model.A_factor_list[m] if model.A_factor_list else [m]
                    if f not in factor_list: continue
                    obs_m = observation[m] if isinstance(observation, (list, np.ndarray)) and len(observation) == len(model.A) else observation
                    obs_idx = np.argmax(obs_m) if hasattr(obs_m, "ndim") and obs_m.ndim > 0 else int(obs_m)
                    ln_likelihood += self._spm_log(A[obs_idx, :])
                
                v = self._spm_log(model.D[f].flatten()) + ln_likelihood
                qs[f] = self._softmax(v)
        return qs

    def update_dirichlet_params(
        self,
        model: GenerativeModel,
        observation: Any,
        qs: List[np.ndarray],
        qs_prev: Optional[List[np.ndarray]] = None,
        action: Optional[int] = None,
        learning_rate: float = 1.0
    ) -> None:
        """
        Structural Learning: Update Dirichlet parameters (a, b) from experience.
        """
        if model.a is None:
            model.a = [np.ones_like(A_m) for A_m in model.A]
        if model.b is None and qs_prev is not None:
             model.b = [np.ones_like(B_f) for B_f in model.B]

        for m, a_m in enumerate(model.a):
            f_list = model.A_factor_list[m] if model.A_factor_list else [0]
            f_idx = f_list[0]
            obs_m = observation[m] if isinstance(observation, (list, np.ndarray)) and len(observation) == len(model.A) else observation
            if not hasattr(obs_m, "ndim"):
                oh = np.zeros(a_m.shape[0]); oh[int(obs_m)] = 1.0; obs_m = oh
            model.a[m] += learning_rate * np.outer(obs_m, qs[f_idx])
            model.A[m] = model.a[m] / (np.sum(model.a[m], axis=0) + 1e-16)

        if qs_prev and action is not None and model.b:
            for f, b_f in enumerate(model.b):
                model.b[f][:, :, action] += learning_rate * np.outer(qs[f], qs_prev[f])
                model.B[f][:, :, action] = model.b[f][:, :, action] / (np.sum(model.b[f][:, :, action], axis=0) + 1e-16)

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
        qs: List[np.ndarray],
        model: GenerativeModel,
        horizon: int
    ) -> np.ndarray:
        """Greedy selection fallback."""
        num_actions = model.B[0].shape[2]
        action_scores = np.zeros(num_actions)
        for a in range(num_actions):
            action_scores[a] = -self.calculate_efe(CanonicalBeliefState(mean=[], precision=[]), model, np.array([a]), horizon=1)
        return self._softmax(action_scores)
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
