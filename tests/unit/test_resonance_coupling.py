"""
Unit tests for ResonanceCoupling in MemoryBasinRouter.
Track: 057-memory-systems-integration
Task: 6.4 - TDD tests for resonance coupling in attractor basins

Tests verify:
1. calculate_resonance computes semantic similarity
2. apply_resonance_coupling modulates extraction confidence
3. explore_basin_transitions finds better-fitting basins
4. route_memory_with_resonance integrates full workflow
5. _update_basin_from_resonance implements Hebbian learning
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from api.models.sync import MemoryType
from api.services.memory_basin_router import (
    MemoryBasinRouter,
    BASIN_MAPPING,
)


class TestCalculateResonance:
    """Tests for calculate_resonance method."""

    @pytest.mark.asyncio
    async def test_high_resonance_aligned_content(self):
        """Verify high resonance score for aligned content."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        with patch("api.services.memory_basin_router.chat_completion") as mock_chat:
            mock_chat.return_value = "0.85"

            score = await router.calculate_resonance(
                content="Python is a programming language that supports multiple paradigms",
                basin_config=basin_config,
            )

        assert score == 0.85
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_low_resonance_misaligned_content(self):
        """Verify low resonance score for misaligned content."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.PROCEDURAL]

        with patch("api.services.memory_basin_router.chat_completion") as mock_chat:
            mock_chat.return_value = "0.25"

            score = await router.calculate_resonance(
                content="The meeting yesterday was about quarterly reports",
                basin_config=basin_config,
            )

        assert score == 0.25

    @pytest.mark.asyncio
    async def test_resonance_clamps_to_valid_range(self):
        """Verify resonance score clamped to [0, 1]."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        with patch("api.services.memory_basin_router.chat_completion") as mock_chat:
            mock_chat.return_value = "1.5"  # Invalid, should clamp

            score = await router.calculate_resonance(
                content="Test content",
                basin_config=basin_config,
            )

        assert score == 1.0

    @pytest.mark.asyncio
    async def test_resonance_handles_parse_error(self):
        """Verify resonance defaults to 0.5 on parse error."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        with patch("api.services.memory_basin_router.chat_completion") as mock_chat:
            mock_chat.return_value = "invalid response"

            score = await router.calculate_resonance(
                content="Test content",
                basin_config=basin_config,
            )

        assert score == 0.5

    @pytest.mark.asyncio
    async def test_resonance_handles_api_error(self):
        """Verify resonance defaults to 0.5 on API error."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        with patch("api.services.memory_basin_router.chat_completion") as mock_chat:
            mock_chat.side_effect = Exception("API Error")

            score = await router.calculate_resonance(
                content="Test content",
                basin_config=basin_config,
            )

        assert score == 0.5


class TestApplyResonanceCoupling:
    """Tests for apply_resonance_coupling method."""

    @pytest.mark.asyncio
    async def test_high_resonance_amplifies_confidence(self):
        """Verify high resonance boosts entity/relationship confidence."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        extraction = {
            "entities": [{"name": "Python", "confidence": 0.7}],
            "relationships": [{"subject": "Python", "predicate": "is_a", "confidence": 0.7}],
        }

        result = await router.apply_resonance_coupling(
            content="Python is a language",
            primary_basin=basin_config,
            extraction=extraction,
            resonance_score=0.9,
        )

        # High resonance (0.9) should amplify confidence
        # multiplier = 0.7 + (1.3 - 0.7) * 0.9 = 0.7 + 0.54 = 1.24
        assert result["entities"][0]["confidence"] > 0.7
        assert result["relationships"][0]["confidence"] > 0.7
        assert result["entities"][0]["resonance_applied"] is True
        assert result["resonance"]["score"] == 0.9

    @pytest.mark.asyncio
    async def test_low_resonance_dampens_confidence(self):
        """Verify low resonance reduces entity/relationship confidence."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        extraction = {
            "entities": [{"name": "Meeting", "confidence": 0.8}],
            "relationships": [],
        }

        result = await router.apply_resonance_coupling(
            content="Meeting was productive",
            primary_basin=basin_config,
            extraction=extraction,
            resonance_score=0.1,
        )

        # Low resonance (0.1) should dampen confidence
        # multiplier = 0.7 + (1.3 - 0.7) * 0.1 = 0.7 + 0.06 = 0.76
        assert result["entities"][0]["confidence"] < 0.8

    @pytest.mark.asyncio
    async def test_very_low_resonance_triggers_transition_suggestion(self):
        """Verify very low resonance suggests basin transition."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.PROCEDURAL]

        extraction = {"entities": [], "relationships": []}

        result = await router.apply_resonance_coupling(
            content="I remember the party last year",
            primary_basin=basin_config,
            extraction=extraction,
            resonance_score=0.2,  # Below 0.35 threshold
        )

        assert result.get("transition_suggested") is True
        assert "transition_reason" in result

    @pytest.mark.asyncio
    async def test_confidence_caps_at_1(self):
        """Verify confidence doesn't exceed 1.0 after amplification."""
        router = MemoryBasinRouter()
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        extraction = {
            "entities": [{"name": "Test", "confidence": 0.95}],
            "relationships": [],
        }

        result = await router.apply_resonance_coupling(
            content="Test",
            primary_basin=basin_config,
            extraction=extraction,
            resonance_score=1.0,
        )

        assert result["entities"][0]["confidence"] <= 1.0


class TestExploreBasinTransitions:
    """Tests for explore_basin_transitions method."""

    @pytest.mark.asyncio
    async def test_finds_better_basin(self):
        """Verify exploration finds better-fitting basin."""
        router = MemoryBasinRouter()
        current_basin = BASIN_MAPPING[MemoryType.PROCEDURAL]

        with patch.object(router, "calculate_resonance") as mock_resonance:
            # Current basin has low resonance, episodic has high
            def resonance_side_effect(content, basin_config):
                if basin_config["basin_name"] == "experiential-basin":
                    return 0.85
                return 0.3  # Low for others

            mock_resonance.side_effect = resonance_side_effect

            result = await router.explore_basin_transitions(
                content="Yesterday I learned something important",
                current_basin=current_basin,
                current_resonance=0.2,
            )

        assert result is not None
        assert result["basin"]["basin_name"] == "experiential-basin"
        assert result["improvement"] > 0.15

    @pytest.mark.asyncio
    async def test_no_transition_if_current_is_best(self):
        """Verify no transition suggested if current basin fits best."""
        router = MemoryBasinRouter()
        current_basin = BASIN_MAPPING[MemoryType.SEMANTIC]

        with patch.object(router, "calculate_resonance") as mock_resonance:
            # All alternatives are worse
            mock_resonance.return_value = 0.3

            result = await router.explore_basin_transitions(
                content="Python is a programming language",
                current_basin=current_basin,
                current_resonance=0.8,  # Already high
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_requires_significant_improvement(self):
        """Verify transition requires >0.15 improvement."""
        router = MemoryBasinRouter()
        current_basin = BASIN_MAPPING[MemoryType.STRATEGIC]

        with patch.object(router, "calculate_resonance") as mock_resonance:
            # Alternative is only slightly better
            mock_resonance.return_value = 0.55  # Only 0.05 improvement

            result = await router.explore_basin_transitions(
                content="Test content",
                current_basin=current_basin,
                current_resonance=0.5,
            )

        assert result is None  # 0.05 improvement not enough


class TestRouteMemoryWithResonance:
    """Tests for route_memory_with_resonance method."""

    @pytest.mark.asyncio
    async def test_full_routing_workflow(self):
        """Verify full routing with resonance coupling."""
        router = MemoryBasinRouter()

        mock_memevolve = AsyncMock()
        mock_memevolve.extract_with_context.return_value = {
            "entities": [{"name": "Python", "confidence": 0.7}],
            "relationships": [{"subject": "Python", "predicate": "is_a", "confidence": 0.7, "status": "approved"}],
        }
        mock_memevolve.ingest_relationships.return_value = {"ingested": 1}
        mock_memevolve.execute_cypher.return_value = [{"strength": 0.8}]

        with patch.object(router, "_get_memevolve_adapter", return_value=mock_memevolve):
            with patch.object(router, "classify_memory_type", return_value=MemoryType.SEMANTIC):
                with patch.object(router, "calculate_resonance", return_value=0.75):
                    with patch.object(router, "_activate_basin", return_value="Basin context"):
                        result = await router.route_memory_with_resonance(
                            content="Python is a programming language",
                            enable_transition_exploration=False,
                        )

        assert result["memory_type"] == "semantic"
        assert result["basin_name"] == "conceptual-basin"
        assert result["resonance"]["score"] == 0.75
        assert result["resonance"]["coupling_applied"] is True

    @pytest.mark.asyncio
    async def test_routing_with_basin_transition(self):
        """Verify routing transitions to better basin when resonance is low."""
        router = MemoryBasinRouter()

        mock_memevolve = AsyncMock()
        mock_memevolve.extract_with_context.return_value = {
            "entities": [],
            "relationships": [],
        }
        mock_memevolve.execute_cypher.return_value = [{"strength": 0.8}]

        with patch.object(router, "_get_memevolve_adapter", return_value=mock_memevolve):
            with patch.object(router, "classify_memory_type", return_value=MemoryType.PROCEDURAL):
                with patch.object(router, "calculate_resonance", return_value=0.2):
                    with patch.object(router, "_activate_basin", return_value="Basin context"):
                        with patch.object(router, "explore_basin_transitions") as mock_explore:
                            mock_explore.return_value = {
                                "basin": BASIN_MAPPING[MemoryType.EPISODIC],
                                "memory_type": MemoryType.EPISODIC,
                                "resonance": 0.8,
                                "improvement": 0.6,
                            }

                            result = await router.route_memory_with_resonance(
                                content="Yesterday's meeting was productive",
                                enable_transition_exploration=True,
                            )

        assert result["memory_type"] == "episodic"
        assert result["original_type"] == "procedural"
        assert result["transition"] is not None

    @pytest.mark.asyncio
    async def test_routing_without_transition_exploration(self):
        """Verify routing skips transition exploration when disabled."""
        router = MemoryBasinRouter()

        mock_memevolve = AsyncMock()
        mock_memevolve.extract_with_context.return_value = {
            "entities": [],
            "relationships": [],
        }
        mock_memevolve.execute_cypher.return_value = [{"strength": 0.8}]

        with patch.object(router, "_get_memevolve_adapter", return_value=mock_memevolve):
            with patch.object(router, "classify_memory_type", return_value=MemoryType.SEMANTIC):
                with patch.object(router, "calculate_resonance", return_value=0.2):  # Low resonance
                    with patch.object(router, "_activate_basin", return_value="Basin context"):
                        with patch.object(router, "explore_basin_transitions") as mock_explore:
                            result = await router.route_memory_with_resonance(
                                content="Test",
                                enable_transition_exploration=False,
                            )

        # Should not call explore_basin_transitions
        mock_explore.assert_not_called()
        assert result["transition"] is None


class TestUpdateBasinFromResonance:
    """Tests for _update_basin_from_resonance method (Hebbian learning)."""

    @pytest.mark.asyncio
    async def test_high_resonance_strengthens_basin(self):
        """Verify high resonance increases basin strength."""
        router = MemoryBasinRouter()

        mock_memevolve = AsyncMock()
        mock_memevolve.execute_cypher.return_value = [{"strength": 0.85, "avg_resonance": 0.75}]

        with patch.object(router, "_get_memevolve_adapter", return_value=mock_memevolve):
            await router._update_basin_from_resonance(
                basin_name="conceptual-basin",
                resonance_score=0.8,  # Above 0.5
            )

        # Should call with positive delta
        call_args = mock_memevolve.execute_cypher.call_args
        params = call_args[0][1]
        assert params["delta"] > 0  # (0.8 - 0.5) * 0.1 = 0.03

    @pytest.mark.asyncio
    async def test_low_resonance_weakens_basin(self):
        """Verify low resonance decreases basin strength."""
        router = MemoryBasinRouter()

        mock_memevolve = AsyncMock()
        mock_memevolve.execute_cypher.return_value = [{"strength": 0.75}]

        with patch.object(router, "_get_memevolve_adapter", return_value=mock_memevolve):
            await router._update_basin_from_resonance(
                basin_name="conceptual-basin",
                resonance_score=0.2,  # Below 0.5
            )

        call_args = mock_memevolve.execute_cypher.call_args
        params = call_args[0][1]
        assert params["delta"] < 0  # (0.2 - 0.5) * 0.1 = -0.03

    @pytest.mark.asyncio
    async def test_update_handles_error_gracefully(self):
        """Verify update handles errors without raising."""
        router = MemoryBasinRouter()

        mock_memevolve = AsyncMock()
        mock_memevolve.execute_cypher.side_effect = Exception("Database error")

        with patch.object(router, "_get_memevolve_adapter", return_value=mock_memevolve):
            # Should not raise
            await router._update_basin_from_resonance(
                basin_name="test-basin",
                resonance_score=0.5,
            )


class TestBasinMappingIntegration:
    """Tests for basin mapping configuration."""

    def test_all_memory_types_have_basin_mapping(self):
        """Verify all MemoryType values have basin configuration."""
        for memory_type in MemoryType:
            assert memory_type in BASIN_MAPPING
            config = BASIN_MAPPING[memory_type]
            assert "basin_name" in config
            assert "description" in config
            assert "concepts" in config
            assert "default_strength" in config
            assert "extraction_focus" in config

    def test_basin_names_are_unique(self):
        """Verify all basin names are unique."""
        basin_names = [config["basin_name"] for config in BASIN_MAPPING.values()]
        assert len(basin_names) == len(set(basin_names))

    def test_default_strengths_in_valid_range(self):
        """Verify default strengths are in valid range."""
        for config in BASIN_MAPPING.values():
            strength = config["default_strength"]
            assert 0.0 <= strength <= 2.0
