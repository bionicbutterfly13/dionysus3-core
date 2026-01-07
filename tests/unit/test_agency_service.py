"""
Unit Tests for AgencyService

Feature: 040-metacognitive-particles
Tasks: T031

Tests sense of agency computation using KL divergence.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
import numpy as np
from api.services.agency_service import AgencyService, AGENCY_THRESHOLD
from api.models.belief_state import BeliefState
from api.models.metacognitive_particle import ParticleType


class TestAgencyService:
    """Test suite for AgencyService."""

    @pytest.fixture
    def service(self):
        """Create AgencyService instance."""
        return AgencyService()

    @pytest.mark.asyncio
    async def test_compute_agency_strength_independent(self, service):
        """Test agency strength when paths are independent (should be ~0)."""
        # Create distributions that are nearly independent
        joint = np.array([[0.25, 0.25], [0.25, 0.25]])  # Uniform
        marginal_mu = np.array([0.5, 0.5])
        marginal_a = np.array([0.5, 0.5])

        strength = await service.compute_agency_strength(
            joint, marginal_mu, marginal_a
        )

        # Should be close to 0 for independent distributions
        assert strength < 0.1

    @pytest.mark.asyncio
    async def test_compute_agency_strength_correlated(self, service):
        """Test agency strength when paths are correlated (should be > 0)."""
        # Create correlated joint distribution
        joint = np.array([[0.4, 0.1], [0.1, 0.4]])  # Diagonal correlation
        marginal_mu = np.array([0.5, 0.5])
        marginal_a = np.array([0.5, 0.5])

        strength = await service.compute_agency_strength(
            joint, marginal_mu, marginal_a
        )

        # Should be positive for correlated distributions
        assert strength > 0.0

    @pytest.mark.asyncio
    async def test_has_agency_above_threshold(self, service):
        """Test has_agency returns True above threshold."""
        result = await service.has_agency(0.001)  # Above default threshold
        assert result is True

    @pytest.mark.asyncio
    async def test_has_agency_below_threshold(self, service):
        """Test has_agency returns False below threshold."""
        result = await service.has_agency(1e-8)  # Below default threshold
        assert result is False

    @pytest.mark.asyncio
    async def test_has_agency_custom_threshold(self, service):
        """Test has_agency with custom threshold."""
        strength = 0.05

        # Below custom threshold
        result = await service.has_agency(strength, threshold=0.1)
        assert result is False

        # Above custom threshold
        result = await service.has_agency(strength, threshold=0.01)
        assert result is True

    @pytest.mark.asyncio
    async def test_compute_agency_strength_gaussian(self, service):
        """Test Gaussian agency strength computation."""
        d = 2

        # Joint distribution parameters
        joint_mean = np.array([0.0, 0.0])
        joint_precision = np.array([[2.0, 0.5], [0.5, 2.0]])  # Correlated

        # Marginal parameters (independent)
        marginal_mu_mean = np.array([0.0])
        marginal_mu_precision = np.array([[1.0]])
        marginal_a_mean = np.array([0.0])
        marginal_a_precision = np.array([[1.0]])

        strength = await service.compute_agency_strength_gaussian(
            joint_mean=joint_mean,
            joint_precision=joint_precision,
            marginal_mu_mean=marginal_mu_mean,
            marginal_mu_precision=marginal_mu_precision,
            marginal_a_mean=marginal_a_mean,
            marginal_a_precision=marginal_a_precision
        )

        # Should be non-negative
        assert strength >= 0.0

    @pytest.mark.asyncio
    async def test_kl_divergence_gaussian_same_distributions(self, service):
        """Test KL divergence is 0 for identical distributions."""
        mean = np.array([0.0, 0.0])
        precision = np.array([[1.0, 0.0], [0.0, 1.0]])

        kl = service._kl_divergence_gaussian(
            p_mean=mean,
            p_precision=precision,
            q_mean=mean,
            q_precision=precision
        )

        assert abs(kl) < 1e-6  # Should be approximately 0

    @pytest.mark.asyncio
    async def test_get_agent_agency_placeholder(self, service):
        """Test get_agent_agency returns placeholder values."""
        strength, has_agency, particle_type = await service.get_agent_agency("test_agent")

        assert strength == 0.0
        assert has_agency is False
        assert particle_type == ParticleType.COGNITIVE

    @pytest.mark.asyncio
    async def test_compute_from_beliefs(self, service):
        """Test computing agency from BeliefState objects."""
        # Create belief states
        joint_belief = BeliefState(
            mean=[0.0, 0.0],
            precision=[[2.0, 0.5], [0.5, 2.0]]
        )
        marginal_mu = BeliefState(
            mean=[0.0],
            precision=[[1.0]]
        )
        marginal_a = BeliefState(
            mean=[0.0],
            precision=[[1.0]]
        )

        strength = await service.compute_from_beliefs(
            joint_belief, marginal_mu, marginal_a
        )

        assert strength >= 0.0


class TestAgencyThreshold:
    """Test default agency threshold."""

    def test_default_threshold_value(self):
        """Test default AGENCY_THRESHOLD constant."""
        assert AGENCY_THRESHOLD == 1e-6

    def test_service_uses_default_threshold(self):
        """Test service initializes with default threshold."""
        service = AgencyService()
        assert service.threshold == AGENCY_THRESHOLD

    def test_service_custom_threshold(self):
        """Test service with custom threshold."""
        custom_threshold = 0.001
        service = AgencyService(threshold=custom_threshold)
        assert service.threshold == custom_threshold
