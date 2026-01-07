"""
Unit tests for Active Metacognition.

Feature: Priority 1 - Active Metacognition
Tests mental actions, precision modulation, and attentional spotlight.

Per Metacognitive Particles paper:
- Mental actions modulate precision, not content
- Higher-level active paths (a^2) modulate lower-level belief parameters
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.efe_engine import (
    get_agent_precision,
    set_agent_precision,
    adjust_agent_precision,
    _agent_precision_registry,
)

from api.agents.metacognition_agent import (
    MetacognitionAgent,
    get_attentional_spotlight,
    _attentional_spotlight_registry,
)


@pytest.fixture(autouse=True)
def reset_registries():
    """Reset both registries before each test."""
    _agent_precision_registry.clear()
    _attentional_spotlight_registry.clear()
    yield
    _agent_precision_registry.clear()
    _attentional_spotlight_registry.clear()


class TestMentalAction:
    """Tests for MetacognitionAgent.mental_action()."""

    @pytest.mark.asyncio
    async def test_mental_action_precision_delta(self):
        """Mental action should adjust precision by delta."""
        agent = MetacognitionAgent()
        set_agent_precision("perception", 1.0)

        result = await agent.mental_action(
            target_agent="perception",
            modulation={"precision_delta": -0.3}
        )

        assert result["success"] is True
        assert result["prior_state"]["precision"] == 1.0
        assert result["new_state"]["precision"] == 0.7
        assert "precision_delta=-0.3000" in result["modulations_applied"][0]

    @pytest.mark.asyncio
    async def test_mental_action_set_precision(self):
        """Mental action should set absolute precision."""
        agent = MetacognitionAgent()
        set_agent_precision("reasoning", 1.0)

        result = await agent.mental_action(
            target_agent="reasoning",
            modulation={"set_precision": 2.5}
        )

        assert result["success"] is True
        assert get_agent_precision("reasoning") == 2.5
        assert "set_precision=2.5000" in result["modulations_applied"][0]

    @pytest.mark.asyncio
    async def test_mental_action_spotlight_adjustment(self):
        """Mental action should adjust attentional spotlight."""
        agent = MetacognitionAgent()

        result = await agent.mental_action(
            target_agent="perception",
            modulation={
                "focus_target": "visual_patterns",
                "spotlight_precision": 0.8
            }
        )

        assert result["success"] is True
        spotlight = get_attentional_spotlight("perception")
        assert spotlight["focus_target"] == "visual_patterns"
        assert spotlight["spotlight_precision"] == 0.8

    @pytest.mark.asyncio
    async def test_mental_action_combined_modulation(self):
        """Mental action should handle multiple modulations."""
        agent = MetacognitionAgent()
        set_agent_precision("reasoning", 1.0)

        result = await agent.mental_action(
            target_agent="reasoning",
            modulation={
                "precision_delta": 0.5,
                "focus_target": "logical_inference",
                "spotlight_precision": 0.9
            }
        )

        assert result["success"] is True
        assert len(result["modulations_applied"]) == 2
        assert get_agent_precision("reasoning") == 1.5
        spotlight = get_attentional_spotlight("reasoning")
        assert spotlight["focus_target"] == "logical_inference"


class TestAdjustAgentPrecision:
    """Tests for MetacognitionAgent._adjust_agent_precision()."""

    @pytest.mark.asyncio
    async def test_precision_increase(self):
        """Precision should increase with positive delta."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 1.0)

        new_prec = await agent._adjust_agent_precision("test", 0.5)

        assert new_prec == 1.5
        assert get_agent_precision("test") == 1.5

    @pytest.mark.asyncio
    async def test_precision_decrease(self):
        """Precision should decrease with negative delta."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 1.0)

        new_prec = await agent._adjust_agent_precision("test", -0.4)

        assert new_prec == 0.6
        assert get_agent_precision("test") == 0.6

    @pytest.mark.asyncio
    async def test_precision_clamping(self):
        """Precision should be clamped to valid range."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 0.1)

        new_prec = await agent._adjust_agent_precision("test", -1.0)

        assert new_prec == 0.01  # Clamped to minimum


class TestAdjustAttentionalSpotlight:
    """Tests for MetacognitionAgent._adjust_attentional_spotlight()."""

    @pytest.mark.asyncio
    async def test_spotlight_creation(self):
        """Should create spotlight for new agent."""
        agent = MetacognitionAgent()

        result = await agent._adjust_attentional_spotlight(
            "new_agent",
            {"focus_target": "patterns", "spotlight_precision": 0.6}
        )

        assert result["focus_target"] == "patterns"
        assert result["spotlight_precision"] == 0.6
        assert result["updated_by"] == "metacognition"

    @pytest.mark.asyncio
    async def test_spotlight_update(self):
        """Should update existing spotlight."""
        agent = MetacognitionAgent()
        _attentional_spotlight_registry["existing"] = {
            "focus_target": "old_target",
            "spotlight_precision": 0.3
        }

        result = await agent._adjust_attentional_spotlight(
            "existing",
            {"focus_target": "new_target", "spotlight_precision": 0.9}
        )

        assert result["focus_target"] == "new_target"
        assert result["spotlight_precision"] == 0.9

    @pytest.mark.asyncio
    async def test_spotlight_partial_update(self):
        """Should preserve unspecified spotlight values."""
        agent = MetacognitionAgent()
        _attentional_spotlight_registry["partial"] = {
            "focus_target": "keep_this",
            "spotlight_precision": 0.5
        }

        result = await agent._adjust_attentional_spotlight(
            "partial",
            {"spotlight_precision": 0.8}  # Only updating precision
        )

        assert result["focus_target"] == "keep_this"
        assert result["spotlight_precision"] == 0.8


class TestActiveCorrection:
    """Tests for MetacognitionAgent.active_correction()."""

    @pytest.mark.asyncio
    async def test_no_correction_for_low_error(self):
        """Should not trigger correction for acceptable error."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 1.0)

        result = await agent.active_correction(
            agent_name="test",
            prediction_error=0.10  # Below threshold
        )

        assert result["correction_type"] == "none"
        assert len(result["actions_taken"]) == 0
        assert get_agent_precision("test") == 1.0  # Unchanged

    @pytest.mark.asyncio
    async def test_moderate_correction_for_high_error(self):
        """Should trigger moderate correction for high error."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 1.0)

        result = await agent.active_correction(
            agent_name="test",
            prediction_error=0.20  # Between 0.15 and 0.30
        )

        assert result["correction_type"] == "moderate"
        assert len(result["actions_taken"]) >= 1
        assert get_agent_precision("test") == 0.85  # 1.0 - 0.15

    @pytest.mark.asyncio
    async def test_critical_correction_for_very_high_error(self):
        """Should trigger aggressive correction for critical error."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 1.0)

        result = await agent.active_correction(
            agent_name="test",
            prediction_error=0.35  # Above 0.30
        )

        assert result["correction_type"] == "critical"
        assert len(result["actions_taken"]) >= 1
        assert get_agent_precision("test") == 0.7  # 1.0 - 0.3

    @pytest.mark.asyncio
    async def test_correction_with_focus_suggestion(self):
        """Should adjust spotlight when focus_suggestion provided."""
        agent = MetacognitionAgent()
        set_agent_precision("test", 1.0)

        result = await agent.active_correction(
            agent_name="test",
            prediction_error=0.25,
            error_context={"focus_suggestion": "memory_recall"}
        )

        assert result["correction_type"] == "moderate"
        assert len(result["actions_taken"]) == 2  # Precision + spotlight

        spotlight = get_attentional_spotlight("test")
        assert spotlight["focus_target"] == "memory_recall"


class TestGetAttentionalSpotlight:
    """Tests for module-level get_attentional_spotlight()."""

    def test_default_spotlight(self):
        """Should return default for unknown agent."""
        spotlight = get_attentional_spotlight("unknown")
        assert spotlight["focus_target"] is None
        assert spotlight["spotlight_precision"] == 0.5

    def test_registered_spotlight(self):
        """Should return registered spotlight."""
        _attentional_spotlight_registry["known"] = {
            "focus_target": "test_target",
            "spotlight_precision": 0.7
        }

        spotlight = get_attentional_spotlight("known")
        assert spotlight["focus_target"] == "test_target"
        assert spotlight["spotlight_precision"] == 0.7
