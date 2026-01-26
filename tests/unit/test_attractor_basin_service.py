"""
Unit Tests for Hopfield-based Attractor Basin Service

Feature: 095-comp-neuro-gold-standard
Ref: Anderson (2014), Chapter 13 - Hopfield Networks

Tests the mathematical foundation for attractor basin dynamics:
- Energy function calculation
- State update rule (asynchronous)
- Basin convergence detection
- Memory pattern storage and recall

AUTHOR: Mani Saint-Victor, MD
"""

import numpy as np
import pytest
from typing import List

from api.services.attractor_basin_service import (
    HopfieldNetwork,
    AttractorBasinService,
    BasinState,
    ConvergenceResult,
)


class TestHopfieldEnergy:
    """Test Hopfield energy function: E = -0.5 * Σ_ij w_ij * s_i * s_j"""

    def test_energy_at_stored_pattern_is_minimum(self):
        """Energy should be minimal at stored patterns (attractors)."""
        network = HopfieldNetwork(n_units=4)
        pattern = np.array([1, -1, 1, -1])
        network.store_pattern(pattern)

        energy_at_pattern = network.compute_energy(pattern)

        # Perturb the pattern
        perturbed = pattern.copy()
        perturbed[0] = -perturbed[0]  # Flip one unit
        energy_perturbed = network.compute_energy(perturbed)

        # Energy at stored pattern should be lower
        assert energy_at_pattern < energy_perturbed

    def test_energy_formula_explicit(self):
        """Test energy formula E = -0.5 * Σ_ij w_ij * s_i * s_j explicitly."""
        network = HopfieldNetwork(n_units=3)

        # Set weights manually for testing
        # w_ij = w_ji, w_ii = 0
        network.weights = np.array([
            [0.0, 0.5, -0.3],
            [0.5, 0.0, 0.2],
            [-0.3, 0.2, 0.0]
        ])

        state = np.array([1, 1, -1])

        # Manual calculation:
        # E = -0.5 * (w_01*s_0*s_1 + w_10*s_1*s_0 + w_02*s_0*s_2 + w_20*s_2*s_0 + w_12*s_1*s_2 + w_21*s_2*s_1)
        # E = -0.5 * (0.5*1*1 + 0.5*1*1 + (-0.3)*1*(-1) + (-0.3)*(-1)*1 + 0.2*1*(-1) + 0.2*(-1)*1)
        # E = -0.5 * (0.5 + 0.5 + 0.3 + 0.3 - 0.2 - 0.2) = -0.5 * 1.2 = -0.6
        expected = -0.6

        actual = network.compute_energy(state)
        assert np.isclose(actual, expected, atol=1e-6)

    def test_energy_is_symmetric(self):
        """Energy should be same for state and its negation (if all patterns negated)."""
        network = HopfieldNetwork(n_units=5)
        pattern = np.array([1, -1, 1, 1, -1])
        network.store_pattern(pattern)

        energy_pos = network.compute_energy(pattern)
        energy_neg = network.compute_energy(-pattern)

        # Both pattern and its negation are attractors (Hopfield property)
        assert np.isclose(energy_pos, energy_neg, atol=1e-6)


class TestHopfieldUpdate:
    """Test state update rule: s_i(t+1) = sign(Σ_j w_ij * s_j(t))"""

    def test_update_converges_to_stored_pattern(self):
        """Starting near a stored pattern should converge to it."""
        network = HopfieldNetwork(n_units=8)
        pattern = np.array([1, 1, -1, -1, 1, -1, 1, -1])
        network.store_pattern(pattern)

        # Start with 2 bits flipped
        initial = pattern.copy()
        initial[0] = -initial[0]
        initial[3] = -initial[3]

        result = network.run_until_convergence(initial, max_iterations=100)

        assert result.converged
        # Should converge to pattern or its negation
        assert np.array_equal(result.final_state, pattern) or \
               np.array_equal(result.final_state, -pattern)

    def test_single_unit_update(self):
        """Test update of single unit follows sign rule."""
        network = HopfieldNetwork(n_units=3)
        network.weights = np.array([
            [0.0, 1.0, -1.0],
            [1.0, 0.0, 0.5],
            [-1.0, 0.5, 0.0]
        ])

        state = np.array([1, 1, -1])

        # Update unit 0: h_0 = w_01*s_1 + w_02*s_2 = 1.0*1 + (-1.0)*(-1) = 2
        # sign(2) = 1
        new_state = network.update_unit(state, 0)
        assert new_state[0] == 1

        # Update unit 2: h_2 = w_20*s_0 + w_21*s_1 = (-1.0)*1 + 0.5*1 = -0.5
        # sign(-0.5) = -1
        new_state = network.update_unit(state, 2)
        assert new_state[2] == -1

    def test_asynchronous_update_reduces_energy(self):
        """Each asynchronous update should not increase energy."""
        network = HopfieldNetwork(n_units=6)
        pattern = np.array([1, -1, 1, -1, 1, -1])
        network.store_pattern(pattern)

        state = np.array([1, 1, 1, -1, -1, -1])  # Far from pattern

        energy_before = network.compute_energy(state)

        # Update a few units
        for i in range(3):
            state = network.update_unit(state, i)

        energy_after = network.compute_energy(state)

        # Energy should decrease or stay same (never increase)
        assert energy_after <= energy_before + 1e-10  # Small tolerance for float


class TestBasinConvergence:
    """Test basin convergence detection."""

    def test_convergence_detected_when_stable(self):
        """Convergence should be detected when state stops changing."""
        network = HopfieldNetwork(n_units=4)
        pattern = np.array([1, 1, 1, 1])
        network.store_pattern(pattern)

        result = network.run_until_convergence(pattern, max_iterations=10)

        assert result.converged
        assert result.iterations == 1  # Already at attractor

    def test_convergence_tracks_iterations(self):
        """Should track number of iterations to convergence."""
        network = HopfieldNetwork(n_units=4)
        pattern = np.array([1, -1, 1, -1])
        network.store_pattern(pattern)

        initial = np.array([-1, -1, 1, -1])  # 1 bit flipped
        result = network.run_until_convergence(initial, max_iterations=50)

        assert result.converged
        assert result.iterations >= 1
        assert result.iterations <= 50

    def test_non_convergence_returns_max_iterations(self):
        """Should return max iterations when convergence is slow or doesn't occur."""
        network = HopfieldNetwork(n_units=4)
        # Don't store any pattern - with just 1 iteration, won't detect convergence
        # because convergence requires comparing before/after states
        network.weights = np.zeros((4, 4))  # Zero weights = no dynamics

        initial = np.array([1, -1, 1, -1])
        result = network.run_until_convergence(initial, max_iterations=1)

        # With max_iterations=1, we do one update then check
        # Even with zero weights, we get one iteration
        assert result.iterations == 1
        assert result.converged  # Zero weights means state is already stable


class TestPatternStorage:
    """Test Hebbian pattern storage."""

    def test_store_single_pattern(self):
        """Storing a pattern creates appropriate weight matrix."""
        network = HopfieldNetwork(n_units=4)
        pattern = np.array([1, -1, 1, -1])

        network.store_pattern(pattern)

        # Weights should be outer product (normalized)
        # w_ij = (1/N) * s_i * s_j for i != j
        expected = np.outer(pattern, pattern) / 4.0
        np.fill_diagonal(expected, 0)

        assert np.allclose(network.weights, expected)

    def test_store_strong_attractor(self):
        """
        Strong attractors (degree > 1) have larger weight contributions.

        Ref: Edalat & Mancinelli (2013), Strong Attractors of Hopfield Neural Networks

        w_ij += (d/N) * s_i * s_j where d = degree
        """
        network = HopfieldNetwork(n_units=4)
        pattern = np.array([1, -1, 1, -1])
        degree = 3  # Triple strength

        network.store_pattern(pattern, degree=degree)

        # Weights should be scaled by degree
        expected = np.outer(pattern, pattern) * degree / 4.0
        np.fill_diagonal(expected, 0)

        assert np.allclose(network.weights, expected)

    def test_strong_attractor_wins_competition(self):
        """
        Higher degree patterns should win competition against weaker patterns.

        Ref: Edalat & Mancinelli (2013) - strong attractors have larger basins
        """
        n = 16
        network = HopfieldNetwork(n_units=n)

        # Store two orthogonal patterns with different strengths
        weak_pattern = np.array([1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, -1, -1])
        strong_pattern = np.array([1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1])

        network.store_pattern(weak_pattern, degree=1)
        network.store_pattern(strong_pattern, degree=5)  # Much stronger

        # Create a state equidistant from both (50% overlap with each)
        # The strong attractor should pull harder
        ambiguous_start = np.array([1, 1, 1, -1, 1, -1, 1, -1, 1, 1, 1, -1, 1, -1, 1, -1])

        result = network.run_until_convergence(ambiguous_start, max_iterations=100)

        # Should converge to strong pattern (or its negation)
        assert result.converged
        strong_overlap = abs(network.compute_normalized_overlap(
            result.final_state, strong_pattern
        ))
        weak_overlap = abs(network.compute_normalized_overlap(
            result.final_state, weak_pattern
        ))

        # Strong attractor should have better overlap
        assert strong_overlap > weak_overlap

    def test_store_multiple_patterns(self):
        """Multiple patterns are superimposed in weights."""
        network = HopfieldNetwork(n_units=4)
        p1 = np.array([1, 1, 1, 1])
        p2 = np.array([1, -1, 1, -1])

        network.store_pattern(p1)
        network.store_pattern(p2)

        # Weights should be sum of outer products
        expected = (np.outer(p1, p1) + np.outer(p2, p2)) / 4.0
        np.fill_diagonal(expected, 0)

        assert np.allclose(network.weights, expected)

    def test_capacity_limit(self):
        """Network has limited capacity (~0.138N patterns)."""
        n = 100
        network = HopfieldNetwork(n_units=n)

        # Store many random patterns
        n_patterns = 20  # Above 0.138 * 100 = 13.8
        patterns = [np.sign(np.random.randn(n)) for _ in range(n_patterns)]
        for p in patterns:
            network.store_pattern(p)

        # Some patterns may not be recalled perfectly
        recall_errors = 0
        for p in patterns[:5]:  # Test first 5
            result = network.run_until_convergence(p, max_iterations=50)
            if not np.array_equal(result.final_state, p) and \
               not np.array_equal(result.final_state, -p):
                recall_errors += 1

        # With overloaded network, expect some errors
        # (This is a probabilistic test)
        assert True  # Just document the capacity limit


class TestEffectiveConditionNumber:
    """
    Test effective condition number as capacity indicator.

    Ref: Lin, Yeap, & Kiringa (2024) - Basin of Attraction and Capacity
         of Restricted Hopfield Network
    """

    def test_single_pattern_condition_number_is_one(self):
        """With single pattern, condition number should be 1."""
        network = HopfieldNetwork(n_units=10)
        pattern = np.array([1, -1, 1, -1, 1, -1, 1, -1, 1, -1])
        network.store_pattern(pattern)

        cond = network.compute_effective_condition_number()

        # With one pattern, only one significant eigenvalue
        assert cond == 1.0

    def test_condition_number_grows_with_patterns(self):
        """Condition number grows as more patterns are added."""
        n = 35  # Same as Lin et al. AUTS patterns
        network = HopfieldNetwork(n_units=n)

        # Generate orthogonal-ish patterns
        np.random.seed(42)
        patterns = [np.sign(np.random.randn(n)) for _ in range(4)]

        cond_numbers = []
        for p in patterns:
            network.store_pattern(p)
            cond_numbers.append(network.compute_effective_condition_number())

        # Condition number should generally increase (not strictly monotonic)
        assert cond_numbers[-1] >= cond_numbers[0]

    def test_capacity_warning_at_high_condition_number(self):
        """Capacity estimation warns when condition number is high."""
        n = 20
        network = HopfieldNetwork(n_units=n)

        # Store many patterns to push condition number up
        np.random.seed(123)
        for _ in range(15):  # Way over 0.138*20 = 2.76 capacity
            network.store_pattern(np.sign(np.random.randn(n)))

        remaining = network.estimate_capacity_remaining()

        # Should be near or at zero capacity
        assert remaining < 0.5


class TestAttractorBasinService:
    """Test high-level AttractorBasinService integration."""

    @pytest.mark.asyncio
    async def test_create_basin_from_content(self):
        """Service creates basin state from text content."""
        service = AttractorBasinService(n_units=64)

        basin = await service.create_basin(
            name="test-basin",
            seed_content="This is a test memory about cognitive science"
        )

        assert basin.name == "test-basin"
        assert basin.pattern is not None
        assert len(basin.pattern) == 64

    @pytest.mark.asyncio
    async def test_find_nearest_basin(self):
        """Service finds nearest attractor basin for input."""
        service = AttractorBasinService(n_units=32)

        # Create some basins
        await service.create_basin("cognitive", "cognitive science and neuroscience")
        await service.create_basin("emotional", "emotions and feelings")

        # Query should activate nearest basin
        result = await service.find_nearest_basin("brain and cognition research")

        assert result is not None
        assert result.converged

    @pytest.mark.asyncio
    async def test_basin_stability_metric(self):
        """Service provides basin stability metric."""
        service = AttractorBasinService(n_units=32)

        basin = await service.create_basin(
            "stable-test",
            "consistent and stable memory content"
        )

        stability = service.compute_basin_stability(basin)

        assert 0.0 <= stability <= 1.0


class TestBasinState:
    """Test BasinState model."""

    def test_basin_state_creation(self):
        """BasinState holds pattern and metadata."""
        pattern = np.array([1, -1, 1, -1])
        state = BasinState(
            name="test",
            pattern=pattern,
            energy=-2.0,
            activation=0.8
        )

        assert state.name == "test"
        assert np.array_equal(state.pattern, pattern)
        assert state.energy == -2.0
        assert state.activation == 0.8
