"""
Hopfield-based Attractor Basin Service

Feature: 095-comp-neuro-gold-standard
Ref: Anderson (2014), Chapter 13 - Hopfield Networks

Implements attractor basin dynamics using Hopfield network mathematics:
- Energy function: E = -0.5 * Σ_ij w_ij * s_i * s_j
- State update rule: s_i(t+1) = sign(Σ_j w_ij * s_j(t))
- Hebbian learning for pattern storage

Integration (IO Map):
- Inlets: Content strings from memory_basin_router, seed patterns from memory recall
- Outlets: BasinState objects, convergence results, stability metrics
- Attaches to: memory_basin_router.py (basin activation), basin_callback.py (Hebbian strengthening)

AUTHOR: Mani Saint-Victor, MD
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BasinState:
    """
    Represents the state of an attractor basin.

    Ref: Anderson (2014), Ch 13 - Attractors as stable states in Hopfield networks
    """
    name: str
    pattern: np.ndarray
    energy: float = 0.0
    activation: float = 0.0
    stability: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ConvergenceResult:
    """
    Result of running network dynamics until convergence.

    Ref: Anderson (2014), Ch 13.3 - Convergence properties
    """
    converged: bool
    iterations: int
    final_state: np.ndarray
    final_energy: float
    energy_trajectory: List[float] = field(default_factory=list)


class HopfieldNetwork:
    """
    Hopfield Network implementation for attractor basin dynamics.

    Ref: Anderson (2014), Chapter 13 - Hopfield Networks
    Ref: Hopfield, J.J. (1982). Neural networks and physical systems
         with emergent collective computational abilities.
    Ref: Wang, T. (2024). Bias, Basins of Attraction, and Memory Structure
         in Hopfield Networks.

    The network stores patterns as attractors in a weight matrix.
    Starting from any initial state, the network converges to the
    nearest stored pattern (attractor basin).

    Key equations:
    - Energy (with bias): E = -0.5 * Σ_ij w_ij * s_i * s_j - Σ_i θ_i * s_i
    - Update: s_i(t+1) = sign(Σ_j w_ij * s_j(t) + θ_i)
    - Learning: Δw_ij = (1/N) * s_i * s_j (Hebbian)
    - Overlap: M(s) = Σ_i ξ_i * s_i (basin membership indicator)

    Key insights from Wang (2024):
    - Zero-bias networks have paired attractors (s* and -s*) due to spin-flip symmetry
    - Adding bias breaks symmetry, enabling unique attractors
    - Basin membership determined by sign of overlap with pattern

    Capacity: ~0.138N patterns for N units (Amit et al., 1985)
    """

    def __init__(self, n_units: int, use_bias: bool = False):
        """
        Initialize Hopfield network.

        Args:
            n_units: Number of binary units (-1 or +1)
            use_bias: Whether to use bias terms (breaks spin-flip symmetry)
        """
        self.n_units = n_units
        self.weights = np.zeros((n_units, n_units))
        self.biases = np.zeros(n_units)  # θ_i bias terms
        self.use_bias = use_bias
        self.stored_patterns: List[np.ndarray] = []

    def store_pattern(self, pattern: np.ndarray, degree: int = 1) -> None:
        """
        Store a pattern using Hebbian learning rule with optional multiplicity.

        Ref: Anderson (2014), Ch 13.2 - Hebbian Learning
        Ref: Edalat & Mancinelli (2013). Strong Attractors of Hopfield Neural Networks

        w_ij += (d/N) * s_i * s_j for i != j

        Strong attractors (degree > 1):
        - More stable with larger basins of attraction
        - Model attachment types and behavioral patterns
        - Higher degree wins competition between patterns

        Args:
            pattern: Binary pattern array (-1 or +1 values)
            degree: Multiplicity of storage (d >= 1). Higher = stronger attractor.
        """
        if len(pattern) != self.n_units:
            raise ValueError(f"Pattern length {len(pattern)} != n_units {self.n_units}")
        if degree < 1:
            raise ValueError(f"Degree must be >= 1, got {degree}")

        # Ensure binary (-1, +1)
        pattern = np.sign(pattern).astype(float)
        pattern[pattern == 0] = 1  # Map 0 to 1

        # Hebbian update: outer product normalized by N, scaled by degree
        # Ref: Edalat & Mancinelli (2013), Eq for strong attractors
        # w_ij += (d/N) * s_i * s_j
        delta_w = np.outer(pattern, pattern) * degree / self.n_units
        np.fill_diagonal(delta_w, 0)  # No self-connections

        self.weights += delta_w
        self.stored_patterns.append(pattern.copy())

        # Store degree for capacity analysis
        if not hasattr(self, 'pattern_degrees'):
            self.pattern_degrees = []
        self.pattern_degrees.append(degree)

        # If using bias, align biases with pattern for unique attractor
        # Ref: Wang (2024), Proposition 2 - biases break spin-flip symmetry
        if self.use_bias:
            self.biases = pattern.copy()  # θ_i = ξ_i for unique minimum

        logger.debug(f"Stored pattern {len(self.stored_patterns)}, "
                    f"capacity ~{0.138 * self.n_units:.1f}")

    def compute_overlap(self, state: np.ndarray, pattern: np.ndarray) -> float:
        """
        Compute overlap between state and pattern.

        Ref: Wang (2024), Definition 2

        M(s) = Σ_i ξ_i * s_i

        The overlap determines basin membership:
        - M(s) > 0: state is in basin of pattern ξ
        - M(s) < 0: state is in basin of -ξ
        - M(s) = 0: state is on basin boundary

        Args:
            state: Current network state
            pattern: Reference pattern

        Returns:
            Overlap value (unnormalized)
        """
        return float(np.dot(pattern, state))

    def compute_normalized_overlap(self, state: np.ndarray, pattern: np.ndarray) -> float:
        """
        Compute normalized overlap m(s) = M(s) / N.

        Returns value in [-1, 1] where:
        - 1.0: perfect alignment with pattern
        - -1.0: perfect alignment with inverse
        - 0.0: orthogonal (on basin boundary)
        """
        return self.compute_overlap(state, pattern) / self.n_units

    def compute_energy(self, state: np.ndarray) -> float:
        """
        Compute Hopfield energy function with optional bias.

        Ref: Anderson (2014), Ch 13.1, Eq 13.1
        Ref: Wang (2024), Eq 1

        Without bias: E = -0.5 * Σ_ij w_ij * s_i * s_j
        With bias:    E = -0.5 * Σ_ij w_ij * s_i * s_j - Σ_i θ_i * s_i

        Lower energy = more stable state.
        Stored patterns are energy minima (attractors).

        Args:
            state: Current network state (-1 or +1 values)

        Returns:
            Energy value (float)
        """
        # Quadratic term: E_weights = -0.5 * s^T * W * s
        energy = -0.5 * float(state @ self.weights @ state)

        # Bias term: E_bias = -Σ_i θ_i * s_i
        if self.use_bias:
            energy -= float(np.dot(self.biases, state))

        return energy

    def update_unit(self, state: np.ndarray, unit_idx: int) -> np.ndarray:
        """
        Asynchronously update a single unit.

        Ref: Anderson (2014), Ch 13.2 - Asynchronous Update
        Ref: Wang (2024), Eq 3

        Without bias: s_i(t+1) = sign(Σ_j w_ij * s_j(t))
        With bias:    s_i(t+1) = sign(Σ_j w_ij * s_j(t) + θ_i)

        The sign function:
        - sign(x) = +1 if x > 0
        - sign(x) = -1 if x < 0
        - sign(0) = current state (no change, tie-breaking)

        Note from Wang (2024): When h_i(s) = 0, tie-breaking affects basin
        assignment but not energy monotonicity.

        Args:
            state: Current network state
            unit_idx: Index of unit to update

        Returns:
            New state with updated unit
        """
        new_state = state.copy()

        # Local field: h_i = Σ_j w_ij * s_j + θ_i
        local_field = self.weights[unit_idx] @ state
        if self.use_bias:
            local_field += self.biases[unit_idx]

        # Update rule with tie-breaking (keep current if h=0)
        if local_field > 0:
            new_state[unit_idx] = 1
        elif local_field < 0:
            new_state[unit_idx] = -1
        # else: keep current value (local_field == 0)

        return new_state

    def update_all_units(self, state: np.ndarray) -> np.ndarray:
        """
        Update all units asynchronously (random order).

        Args:
            state: Current network state

        Returns:
            State after updating all units once
        """
        new_state = state.copy()
        order = np.random.permutation(self.n_units)

        for idx in order:
            new_state = self.update_unit(new_state, idx)

        return new_state

    def run_until_convergence(
        self,
        initial_state: np.ndarray,
        max_iterations: int = 100
    ) -> ConvergenceResult:
        """
        Run network dynamics until convergence to attractor.

        Ref: Anderson (2014), Ch 13.3 - Convergence

        The network is guaranteed to converge because:
        1. Energy is bounded below
        2. Each update decreases energy (or keeps it same)
        3. State space is finite

        Args:
            initial_state: Starting state
            max_iterations: Maximum update rounds

        Returns:
            ConvergenceResult with final state and trajectory
        """
        state = np.sign(initial_state).astype(float)
        state[state == 0] = 1

        energy_trajectory = [self.compute_energy(state)]

        for iteration in range(1, max_iterations + 1):
            prev_state = state.copy()
            state = self.update_all_units(state)

            energy_trajectory.append(self.compute_energy(state))

            # Check convergence (state unchanged)
            if np.array_equal(state, prev_state):
                return ConvergenceResult(
                    converged=True,
                    iterations=iteration,
                    final_state=state,
                    final_energy=energy_trajectory[-1],
                    energy_trajectory=energy_trajectory
                )

        return ConvergenceResult(
            converged=False,
            iterations=max_iterations,
            final_state=state,
            final_energy=energy_trajectory[-1],
            energy_trajectory=energy_trajectory
        )

    def recall_pattern(self, partial: np.ndarray, max_iterations: int = 50) -> np.ndarray:
        """
        Recall stored pattern from partial or noisy input.

        This is content-addressable memory: given a corrupted version
        of a stored pattern, the network recovers the original.

        Args:
            partial: Partial or noisy pattern
            max_iterations: Max convergence iterations

        Returns:
            Recalled pattern (nearest attractor)
        """
        result = self.run_until_convergence(partial, max_iterations)
        return result.final_state

    def compute_effective_condition_number(self) -> float:
        """
        Compute effective condition number of weight matrix.

        Ref: Lin, Yeap, & Kiringa (2024), "Basin of Attraction and Capacity
             of Restricted Hopfield Network"

        N = λmax / λmin (using only positive eigenvalues)

        When effective condition number exceeds a threshold (~5-10),
        the network loses ability to memorize new patterns reliably.

        Returns:
            Effective condition number (>= 1.0)
        """
        eigenvalues = np.linalg.eigvalsh(self.weights)

        # Only consider positive eigenvalues (negative ones are trivial)
        positive_eigs = eigenvalues[eigenvalues > 1e-10]

        if len(positive_eigs) == 0:
            return 1.0

        lambda_max = np.max(positive_eigs)
        lambda_min = np.min(positive_eigs)

        if lambda_min < 1e-10:
            return float('inf')

        return lambda_max / lambda_min

    def estimate_capacity_remaining(self) -> float:
        """
        Estimate remaining pattern storage capacity.

        Ref: Lin et al. (2024) - effective condition number as capacity indicator

        Returns:
            Estimated fraction of capacity remaining [0, 1]
        """
        cond = self.compute_effective_condition_number()

        # Empirical threshold from Lin et al.: ~5-10 for HNN
        threshold = 5.0

        if cond >= threshold:
            return 0.0

        return 1.0 - (cond - 1.0) / (threshold - 1.0)


class AttractorBasinService:
    """
    High-level service for attractor basin operations.

    Provides content-based basin creation, nearest basin lookup,
    and stability metrics for integration with Dionysus memory systems.

    Integration (IO Map):
    - Inlet: Content strings, seed patterns
    - Outlet: BasinState objects, convergence results
    - Attaches to: memory_basin_router.py, basin_callback.py
    """

    def __init__(self, n_units: int = 128):
        """
        Initialize attractor basin service.

        Args:
            n_units: Dimensionality of basin patterns (default 128)
        """
        self.n_units = n_units
        self.network = HopfieldNetwork(n_units)
        self.basins: Dict[str, BasinState] = {}

    def _content_to_pattern(self, content: str) -> np.ndarray:
        """
        Convert text content to binary pattern.

        Uses deterministic hash-based encoding to create
        reproducible patterns from text.

        Args:
            content: Text content

        Returns:
            Binary pattern array (-1/+1)
        """
        # Hash content for reproducibility
        content_hash = hashlib.sha256(content.encode()).digest()

        # Expand hash to n_units using repeated hashing
        pattern_bytes = bytearray()
        seed = content_hash
        while len(pattern_bytes) < self.n_units:
            seed = hashlib.sha256(seed).digest()
            pattern_bytes.extend(seed)

        # Convert bytes to binary pattern
        pattern = np.array([
            1 if b & (1 << (i % 8)) else -1
            for i, b in enumerate(pattern_bytes[:self.n_units])
        ], dtype=float)

        return pattern

    async def create_basin(
        self,
        name: str,
        seed_content: str,
        metadata: Optional[Dict] = None
    ) -> BasinState:
        """
        Create a new attractor basin from content.

        Args:
            name: Basin identifier
            seed_content: Text content to encode
            metadata: Optional basin metadata

        Returns:
            Created BasinState
        """
        pattern = self._content_to_pattern(seed_content)
        self.network.store_pattern(pattern)

        energy = self.network.compute_energy(pattern)

        basin = BasinState(
            name=name,
            pattern=pattern,
            energy=energy,
            activation=1.0,
            stability=1.0,  # Initial stability
            metadata=metadata or {"seed_content": seed_content[:100]}
        )

        self.basins[name] = basin
        logger.info(f"Created basin '{name}' with energy {energy:.3f}")

        return basin

    async def find_nearest_basin(
        self,
        query_content: str,
        max_iterations: int = 50
    ) -> Optional[ConvergenceResult]:
        """
        Find the nearest attractor basin for query content.

        Args:
            query_content: Query text
            max_iterations: Max convergence iterations

        Returns:
            ConvergenceResult with nearest basin state
        """
        if not self.basins:
            logger.warning("No basins stored")
            return None

        query_pattern = self._content_to_pattern(query_content)
        result = self.network.run_until_convergence(query_pattern, max_iterations)

        logger.debug(f"Basin lookup converged={result.converged} "
                    f"in {result.iterations} iterations")

        return result

    def compute_basin_stability(self, basin: BasinState) -> float:
        """
        Compute stability metric for a basin.

        Stability is measured by the basin of attraction radius:
        how many bits can be flipped while still converging
        to this attractor.

        Args:
            basin: Basin to evaluate

        Returns:
            Stability score [0, 1]
        """
        if basin.pattern is None:
            return 0.0

        # Test convergence with increasing noise
        n_tests = 10
        noise_levels = np.linspace(0.05, 0.5, n_tests)
        successes = 0

        for noise in noise_levels:
            # Add noise by flipping bits
            n_flip = int(noise * self.n_units)
            test_pattern = basin.pattern.copy()
            flip_indices = np.random.choice(self.n_units, n_flip, replace=False)
            test_pattern[flip_indices] *= -1

            result = self.network.run_until_convergence(test_pattern, max_iterations=30)

            # Check if converged to original or its negation
            if np.array_equal(result.final_state, basin.pattern) or \
               np.array_equal(result.final_state, -basin.pattern):
                successes += 1

        return successes / n_tests

    def get_basin_by_name(self, name: str) -> Optional[BasinState]:
        """Get basin by name."""
        return self.basins.get(name)

    def list_basins(self) -> List[str]:
        """List all basin names."""
        return list(self.basins.keys())


# Singleton instance
_attractor_service: Optional[AttractorBasinService] = None


def get_attractor_basin_service(n_units: int = 128) -> AttractorBasinService:
    """
    Get singleton attractor basin service.

    Args:
        n_units: Pattern dimensionality (only used on first call)

    Returns:
        AttractorBasinService instance
    """
    global _attractor_service
    if _attractor_service is None:
        _attractor_service = AttractorBasinService(n_units)
    return _attractor_service
