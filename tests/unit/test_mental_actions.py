"""
Unit Tests for Mental Actions

Feature: 040-metacognitive-particles
Tasks: T022

Tests mental action execution and hierarchy validation.

AUTHOR: Mani Saint-Victor, MD
"""

import pytest
from api.routers.metacognition import (
    validate_hierarchy,
    get_agent_level,
    set_agent_level,
    _agent_level_registry
)
from api.models.metacognitive_particle import MentalActionType


class TestHierarchyValidation:
    """Test suite for hierarchy validation."""

    def setup_method(self):
        """Clear registry before each test."""
        _agent_level_registry.clear()

    def test_get_agent_level_default(self):
        """Test default agent level is 1."""
        level = get_agent_level("unknown_agent")
        assert level == 1

    def test_set_and_get_agent_level(self):
        """Test setting and getting agent levels."""
        set_agent_level("meta_agent", 3)
        set_agent_level("base_agent", 1)

        assert get_agent_level("meta_agent") == 3
        assert get_agent_level("base_agent") == 1

    def test_validate_hierarchy_valid(self):
        """Test valid hierarchy: higher source, lower target."""
        set_agent_level("metacognition", 3)
        set_agent_level("perception", 1)

        # Should not raise - higher level can target lower
        validate_hierarchy("metacognition", "perception")

    def test_validate_hierarchy_invalid_same_level(self):
        """Test invalid hierarchy: same level."""
        set_agent_level("agent_a", 2)
        set_agent_level("agent_b", 2)

        with pytest.raises(PermissionError) as exc_info:
            validate_hierarchy("agent_a", "agent_b")

        assert "Hierarchy violation" in str(exc_info.value)
        assert "level 2" in str(exc_info.value)

    def test_validate_hierarchy_invalid_lower_source(self):
        """Test invalid hierarchy: lower source targeting higher."""
        set_agent_level("low_agent", 1)
        set_agent_level("high_agent", 3)

        with pytest.raises(PermissionError) as exc_info:
            validate_hierarchy("low_agent", "high_agent")

        assert "Hierarchy violation" in str(exc_info.value)

    def test_validate_hierarchy_default_levels(self):
        """Test hierarchy with default levels (both level 1)."""
        # Both unknown agents default to level 1
        with pytest.raises(PermissionError):
            validate_hierarchy("unknown_a", "unknown_b")


class TestMentalActionTypes:
    """Test MentalActionType enum values."""

    def test_precision_modulation_type(self):
        """Test precision modulation action type."""
        action_type = MentalActionType.PRECISION_MODULATION
        assert action_type.value == "precision_modulation"

    def test_attention_control_type(self):
        """Test attention control action type."""
        action_type = MentalActionType.ATTENTION_CONTROL
        assert action_type.value == "attention_control"

    def test_belief_revision_type(self):
        """Test belief revision action type."""
        action_type = MentalActionType.BELIEF_REVISION
        assert action_type.value == "belief_revision"

    def test_policy_selection_type(self):
        """Test policy selection action type."""
        action_type = MentalActionType.POLICY_SELECTION
        assert action_type.value == "policy_selection"


class TestMentalActionModel:
    """Test MentalAction Pydantic model."""

    def test_mental_action_creation(self):
        """Test creating a MentalAction model."""
        from api.models.metacognitive_particle import MentalAction, ModulatedParameter

        action = MentalAction(
            action_type=MentalActionType.PRECISION_MODULATION,
            source_level=2,
            target_level=1,
            modulated_parameter=ModulatedParameter.PRECISION
        )

        assert action.source_level == 2
        assert action.target_level == 1
        assert action.id is not None

    def test_mental_action_target_below_source_validation(self):
        """Test that target_level must be below source_level."""
        from api.models.metacognitive_particle import MentalAction, ModulatedParameter
        from pydantic import ValidationError

        # Valid: target < source
        valid_action = MentalAction(
            action_type=MentalActionType.PRECISION_MODULATION,
            source_level=3,
            target_level=1,
            modulated_parameter=ModulatedParameter.PRECISION
        )
        assert valid_action.target_level < valid_action.source_level

        # Invalid: target >= source
        with pytest.raises(ValidationError):
            MentalAction(
                action_type=MentalActionType.PRECISION_MODULATION,
                source_level=2,
                target_level=2,  # Same as source
                modulated_parameter=ModulatedParameter.PRECISION
            )
