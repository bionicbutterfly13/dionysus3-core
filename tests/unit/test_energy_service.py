"""
Unit Tests for EnergyService
Feature: 004-heartbeat-system
Task: T027

Tests energy regeneration, action costs, and budget validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.energy_service import (
    ActionType,
    DEFAULT_ACTION_COSTS,
    EnergyConfig,
    EnergyService,
    EnergyState,
)


class TestEnergyConfig:
    """Tests for EnergyConfig defaults."""

    def test_default_config(self):
        """Default config has expected values."""
        config = EnergyConfig()

        assert config.base_regeneration == 10.0
        assert config.max_energy == 20.0
        assert config.min_energy == 0.0
        assert config.carry_over_rate == 1.0

    def test_custom_config(self):
        """Custom config values are applied."""
        config = EnergyConfig(
            base_regeneration=5.0,
            max_energy=15.0,
            min_energy=1.0,
        )

        assert config.base_regeneration == 5.0
        assert config.max_energy == 15.0
        assert config.min_energy == 1.0


class TestActionCosts:
    """Tests for action cost definitions."""

    def test_free_actions_cost_zero(self):
        """Free actions have zero cost."""
        free_actions = [
            ActionType.OBSERVE,
            ActionType.REVIEW_GOALS,
            ActionType.REMEMBER,
            ActionType.REST,
        ]

        for action in free_actions:
            assert DEFAULT_ACTION_COSTS[action] == 0.0, f"{action} should be free"

    def test_all_actions_have_costs(self):
        """All action types have defined costs."""
        for action in ActionType:
            assert action in DEFAULT_ACTION_COSTS, f"{action} missing cost definition"

    def test_cost_hierarchy(self):
        """More complex actions cost more."""
        assert DEFAULT_ACTION_COSTS[ActionType.RECALL] < DEFAULT_ACTION_COSTS[ActionType.REFLECT]
        assert DEFAULT_ACTION_COSTS[ActionType.REFLECT] < DEFAULT_ACTION_COSTS[ActionType.SYNTHESIZE]
        assert DEFAULT_ACTION_COSTS[ActionType.SYNTHESIZE] < DEFAULT_ACTION_COSTS[ActionType.INQUIRE_DEEP]


class TestEnergyService:
    """Tests for EnergyService operations."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        driver = MagicMock()
        session = AsyncMock()
        driver.session.return_value.__aenter__ = AsyncMock(return_value=session)
        driver.session.return_value.__aexit__ = AsyncMock(return_value=None)
        return driver, session

    @pytest.fixture
    def service(self, mock_driver):
        """Create EnergyService with mock driver."""
        driver, _ = mock_driver
        return EnergyService(driver=driver)

    def test_get_action_cost(self, service):
        """get_action_cost returns correct costs."""
        assert service.get_action_cost(ActionType.OBSERVE) == 0.0
        assert service.get_action_cost(ActionType.RECALL) == 1.0
        assert service.get_action_cost(ActionType.REFLECT) == 2.0

    def test_get_all_costs(self, service):
        """get_all_costs returns dictionary of costs."""
        costs = service.get_all_costs()

        assert isinstance(costs, dict)
        assert "observe" in costs
        assert costs["observe"] == 0.0
        assert costs["recall"] == 1.0

    def test_estimate_turn_cost(self, service):
        """estimate_turn_cost sums action costs."""
        actions = [ActionType.RECALL, ActionType.REFLECT, ActionType.CONNECT]
        cost = service.estimate_turn_cost(actions)

        # 1.0 + 2.0 + 1.0 = 4.0
        assert cost == 4.0

    def test_estimate_turn_cost_free_actions(self, service):
        """Free actions don't add to cost."""
        actions = [ActionType.OBSERVE, ActionType.REVIEW_GOALS, ActionType.REST]
        cost = service.estimate_turn_cost(actions)

        assert cost == 0.0

    def test_trim_actions_to_budget(self, service):
        """trim_actions_to_budget removes actions exceeding budget."""
        actions = [
            ActionType.RECALL,      # 1.0
            ActionType.REFLECT,     # 2.0
            ActionType.SYNTHESIZE,  # 4.0
            ActionType.INQUIRE_DEEP,  # 6.0
        ]

        # Budget of 5 should include RECALL (1) and REFLECT (2), but not SYNTHESIZE (4)
        trimmed = service.trim_actions_to_budget(actions, 5.0)

        assert len(trimmed) == 2
        assert ActionType.RECALL in trimmed
        assert ActionType.REFLECT in trimmed
        assert ActionType.SYNTHESIZE not in trimmed

    def test_trim_actions_to_budget_free_actions(self, service):
        """Free actions always fit in budget."""
        actions = [ActionType.OBSERVE, ActionType.REST]
        trimmed = service.trim_actions_to_budget(actions, 0.0)

        assert len(trimmed) == 2

    @pytest.mark.asyncio
    async def test_get_state(self, service, mock_driver):
        """get_state returns EnergyState from database."""
        _, session = mock_driver

        # Mock database response
        mock_result = AsyncMock()
        mock_record = {
            "s": {
                "current_energy": 15.0,
                "last_heartbeat_at": None,
                "heartbeat_count": 5,
                "paused": False,
                "pause_reason": None,
            }
        }
        mock_result.single = AsyncMock(return_value=mock_record)
        session.run = AsyncMock(return_value=mock_result)

        state = await service.get_state()

        assert state.current_energy == 15.0
        assert state.heartbeat_count == 5
        assert state.paused is False

    @pytest.mark.asyncio
    async def test_can_afford_action(self, service, mock_driver):
        """can_afford_action checks energy budget."""
        _, session = mock_driver

        # Mock state with 5 energy
        mock_result = AsyncMock()
        mock_record = {
            "s": {
                "current_energy": 5.0,
                "last_heartbeat_at": None,
                "heartbeat_count": 1,
                "paused": False,
                "pause_reason": None,
            }
        }
        mock_result.single = AsyncMock(return_value=mock_record)
        session.run = AsyncMock(return_value=mock_result)

        # Can afford REFLECT (cost 2)
        can_afford = await service.can_afford_action(ActionType.REFLECT)
        assert can_afford is True

        # Cannot afford INQUIRE_DEEP (cost 6)
        can_afford = await service.can_afford_action(ActionType.INQUIRE_DEEP)
        assert can_afford is False

    @pytest.mark.asyncio
    async def test_can_afford_actions_list(self, service, mock_driver):
        """can_afford_actions checks total cost of action list."""
        _, session = mock_driver

        # Mock state with 5 energy
        mock_result = AsyncMock()
        mock_record = {
            "s": {
                "current_energy": 5.0,
                "last_heartbeat_at": None,
                "heartbeat_count": 1,
                "paused": False,
                "pause_reason": None,
            }
        }
        mock_result.single = AsyncMock(return_value=mock_record)
        session.run = AsyncMock(return_value=mock_result)

        # Can afford RECALL (1) + REFLECT (2) = 3
        can_afford, total = await service.can_afford_actions([
            ActionType.RECALL,
            ActionType.REFLECT,
        ])
        assert can_afford is True
        assert total == 3.0

        # Cannot afford RECALL (1) + SYNTHESIZE (4) = 5 with REFLECT (2) = 8
        can_afford, total = await service.can_afford_actions([
            ActionType.RECALL,
            ActionType.SYNTHESIZE,
            ActionType.REFLECT,
        ])
        assert can_afford is False
        assert total == 7.0
