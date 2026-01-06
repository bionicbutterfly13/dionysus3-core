"""
Unit tests for MetaEvolutionService.

Feature: 057-complete-placeholder-implementations
User Story 1: Accurate System Health Metrics (Priority: P1)
Functional Requirements: FR-001, FR-002

TDD: Tests written BEFORE modifying api/services/meta_evolution_service.py
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from api.services.meta_evolution_service import MetaEvolutionService, get_meta_evolution_service
from api.models.evolution import SystemMoment


class TestCaptureSystemMomentRealMetrics:
    """
    Tests for capture_system_moment() with REAL metric computation.

    Replaces placeholder values (energy_level=100.0, active_basins_count=5)
    with actual computation from basin service.
    """

    @pytest.mark.asyncio
    async def test_energy_level_computed_from_basin_strengths(self):
        """
        US1-AS1: energy_level reflects computed free energy across active basins.

        Given the system has basins with known strengths,
        When capture_system_moment() is called,
        Then energy_level is the sum of active basin strengths (NOT 100.0 placeholder).

        FR-001: energy_level MUST be computed from real free energy distribution.
        """
        service = MetaEvolutionService()

        # Mock basin service to return basins with known strengths
        mock_basin_stats = {
            "basins": [
                {"name": "cognitive_science", "strength": 0.85, "stability": 0.7, "activation_count": 10},
                {"name": "consciousness", "strength": 0.65, "stability": 0.6, "activation_count": 8},
                {"name": "systems_theory", "strength": 0.50, "stability": 0.5, "activation_count": 5},
                {"name": "dormant_basin", "strength": 0.25, "stability": 0.3, "activation_count": 1},  # Below threshold
            ]
        }

        # Expected: sum of active basins (strength > 0.3)
        # cognitive_science (0.85) + consciousness (0.65) + systems_theory (0.50) = 2.00
        expected_energy = 2.00

        with patch('api.services.meta_evolution_service.get_memory_basin_router') as mock_router:
            mock_router_instance = AsyncMock()
            mock_router_instance.get_basin_stats = AsyncMock(return_value=mock_basin_stats)
            mock_router.return_value = mock_router_instance

            # Also mock Neo4j driver for total_memories_count
            with patch('api.services.meta_evolution_service.get_neo4j_driver') as mock_driver:
                mock_driver_instance = AsyncMock()
                mock_driver_instance.execute_query = AsyncMock(return_value=[
                    {"l": ["Entity"], "c": 100},
                    {"l": ["Relationship"], "c": 50},
                ])
                mock_driver.return_value = mock_driver_instance

                moment = await service.capture_system_moment()

        # Verify energy_level is computed (not placeholder)
        assert moment.energy_level != 100.0, "energy_level must NOT be placeholder value 100.0"
        assert moment.energy_level == pytest.approx(expected_energy, rel=0.01), \
            f"energy_level should be sum of active basin strengths: {expected_energy}"

    @pytest.mark.asyncio
    async def test_energy_level_excludes_weak_basins(self):
        """
        US1-AS3: Only basins with strength > threshold contribute to energy.

        Given some basins have strength < 0.3 (below active threshold),
        When system moment is captured,
        Then energy_level excludes weak basins from calculation.
        """
        service = MetaEvolutionService()

        mock_basin_stats = {
            "basins": [
                {"name": "strong_basin", "strength": 0.90, "stability": 0.8, "activation_count": 15},
                {"name": "weak_basin_1", "strength": 0.15, "stability": 0.2, "activation_count": 1},
                {"name": "weak_basin_2", "strength": 0.28, "stability": 0.25, "activation_count": 2},
            ]
        }

        # Expected: only strong_basin (0.90) contributes
        expected_energy = 0.90

        with patch('api.services.meta_evolution_service.get_memory_basin_router') as mock_router:
            mock_router_instance = AsyncMock()
            mock_router_instance.get_basin_stats = AsyncMock(return_value=mock_basin_stats)
            mock_router.return_value = mock_router_instance

            with patch('api.services.meta_evolution_service.get_neo4j_driver') as mock_driver:
                mock_driver_instance = AsyncMock()
                mock_driver_instance.execute_query = AsyncMock(return_value=[{"l": ["Entity"], "c": 50}])
                mock_driver.return_value = mock_driver_instance

                moment = await service.capture_system_moment()

        assert moment.energy_level == pytest.approx(expected_energy, rel=0.01), \
            "energy_level should exclude basins below threshold"

    @pytest.mark.asyncio
    async def test_active_basins_count_computed_from_threshold(self):
        """
        US1-AS2: active_basins_count reflects actual active basins (depth > 0.3).

        Given three basins with strength > 0.3,
        When system moment is captured,
        Then active_basins_count = 3 (NOT hardcoded 5).

        FR-002: active_basins_count MUST be computed by querying basin depths.
        """
        service = MetaEvolutionService()

        mock_basin_stats = {
            "basins": [
                {"name": "basin_1", "strength": 0.85, "stability": 0.7, "activation_count": 10},
                {"name": "basin_2", "strength": 0.65, "stability": 0.6, "activation_count": 8},
                {"name": "basin_3", "strength": 0.50, "stability": 0.5, "activation_count": 5},
                {"name": "basin_4", "strength": 0.25, "stability": 0.3, "activation_count": 1},  # Inactive
            ]
        }

        expected_count = 3  # Three basins above 0.3 threshold

        with patch('api.services.meta_evolution_service.get_memory_basin_router') as mock_router:
            mock_router_instance = AsyncMock()
            mock_router_instance.get_basin_stats = AsyncMock(return_value=mock_basin_stats)
            mock_router.return_value = mock_router_instance

            with patch('api.services.meta_evolution_service.get_neo4j_driver') as mock_driver:
                mock_driver_instance = AsyncMock()
                mock_driver_instance.execute_query = AsyncMock(return_value=[{"l": ["Entity"], "c": 75}])
                mock_driver.return_value = mock_driver_instance

                moment = await service.capture_system_moment()

        assert moment.active_basins_count != 5, "active_basins_count must NOT be placeholder value 5"
        assert moment.active_basins_count == expected_count, \
            f"active_basins_count should be number of basins above threshold: {expected_count}"

    @pytest.mark.asyncio
    async def test_zero_active_basins_cold_start(self):
        """
        US1-AS3 (Edge Case): Handle zero active basins (cold start/amnesia scenario).

        Given no basins exist or all are below threshold,
        When system moment is captured,
        Then active_basins_count = 0 and energy_level reflects high uncertainty state.
        """
        service = MetaEvolutionService()

        # No basins returned
        mock_basin_stats = {"basins": []}

        with patch('api.services.meta_evolution_service.get_memory_basin_router') as mock_router:
            mock_router_instance = AsyncMock()
            mock_router_instance.get_basin_stats = AsyncMock(return_value=mock_basin_stats)
            mock_router.return_value = mock_router_instance

            with patch('api.services.meta_evolution_service.get_neo4j_driver') as mock_driver:
                mock_driver_instance = AsyncMock()
                mock_driver_instance.execute_query = AsyncMock(return_value=[{"l": ["Entity"], "c": 0}])
                mock_driver.return_value = mock_driver_instance

                moment = await service.capture_system_moment()

        assert moment.active_basins_count == 0, "Should handle zero active basins"
        assert moment.energy_level == 0.0, "Energy level should be 0 when no basins active"

    @pytest.mark.asyncio
    async def test_energy_level_validation_in_range(self):
        """
        FR-011: System MUST validate energy_level is in reasonable range [0, 10].

        Given energy computation produces value outside bounds,
        When validation occurs,
        Then warning is logged and value is clamped.
        """
        service = MetaEvolutionService()

        # Abnormally high basin strengths (simulating error condition)
        mock_basin_stats = {
            "basins": [
                {"name": "anomaly_basin", "strength": 15.0, "stability": 0.9, "activation_count": 100},
            ]
        }

        with patch('api.services.meta_evolution_service.get_memory_basin_router') as mock_router:
            mock_router_instance = AsyncMock()
            mock_router_instance.get_basin_stats = AsyncMock(return_value=mock_basin_stats)
            mock_router.return_value = mock_router_instance

            with patch('api.services.meta_evolution_service.get_neo4j_driver') as mock_driver:
                mock_driver_instance = AsyncMock()
                mock_driver_instance.execute_query = AsyncMock(return_value=[{"l": ["Entity"], "c": 50}])
                mock_driver.return_value = mock_driver_instance

                with patch('api.services.meta_evolution_service.logger') as mock_logger:
                    moment = await service.capture_system_moment()

                    # Should log warning for out-of-range value
                    assert any("out of expected range" in str(call) for call in mock_logger.warning.call_args_list), \
                        "Should warn when energy_level outside [0, 10] range"

        # Value should be clamped to valid range
        assert 0.0 <= moment.energy_level <= 10.0, "energy_level must be clamped to [0, 10] range"


class TestMetaEvolutionServiceSingleton:
    """Test singleton pattern for service."""

    def test_get_meta_evolution_service_returns_singleton(self):
        """Verify get_meta_evolution_service() returns same instance."""
        service1 = get_meta_evolution_service()
        service2 = get_meta_evolution_service()
        assert service1 is service2, "Should return singleton instance"
