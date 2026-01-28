"""
Unit tests for Archetype Priors (Track 002: Jungian Cognitive Archetypes)

Tests the JungianArchetype enum, ArchetypePrior model, and PriorHierarchy
archetype integration.
"""

import pytest
from api.models.autobiographical import (
    JungianArchetype,
    DevelopmentArchetype,
    ARCHETYPE_SHADOW_MAP,
    is_primary_archetype,
    get_shadow,
)
from api.models.priors import (
    ArchetypePrior,
    PriorHierarchy,
    ARCHETYPE_DEFINITIONS,
    RESONANCE_THRESHOLD,
    RESONANCE_ACTIVATION_EFE,
    SHADOW_WINDOW_SIZE,
    get_default_archetype_priors,
    get_archetype_prior,
)


class TestJungianArchetypeEnum:
    """Tests for JungianArchetype enum."""

    def test_primary_archetypes_exist(self):
        """Verify all 12 primary archetypes are defined."""
        primary_archetypes = [
            "innocent", "orphan", "warrior", "caregiver",
            "explorer", "rebel", "lover", "creator",
            "jester", "sage", "magician", "ruler"
        ]
        for archetype in primary_archetypes:
            assert hasattr(JungianArchetype, archetype.upper())
            assert JungianArchetype[archetype.upper()].value == archetype

    def test_shadow_archetypes_exist(self):
        """Verify all 12 shadow archetypes are defined."""
        shadow_archetypes = [
            "naive", "cynic", "victim", "martyr",
            "wanderer", "outlaw", "obsessive", "destroyer",
            "trickster", "fool", "manipulator", "tyrant"
        ]
        for shadow in shadow_archetypes:
            assert hasattr(JungianArchetype, shadow.upper())
            assert JungianArchetype[shadow.upper()].value == shadow

    def test_backward_compatibility_alias(self):
        """DevelopmentArchetype should alias JungianArchetype."""
        assert DevelopmentArchetype is JungianArchetype
        assert DevelopmentArchetype.SAGE == JungianArchetype.SAGE
        assert DevelopmentArchetype.WARRIOR.value == "warrior"


class TestArchetypeShadowMapping:
    """Tests for archetype-shadow relationships."""

    def test_shadow_map_has_all_primaries(self):
        """All 12 primary archetypes should have shadow mappings."""
        assert len(ARCHETYPE_SHADOW_MAP) == 12

    def test_shadow_map_correct_pairings(self):
        """Verify correct shadow pairings."""
        assert ARCHETYPE_SHADOW_MAP[JungianArchetype.SAGE] == JungianArchetype.FOOL
        assert ARCHETYPE_SHADOW_MAP[JungianArchetype.WARRIOR] == JungianArchetype.VICTIM
        assert ARCHETYPE_SHADOW_MAP[JungianArchetype.CREATOR] == JungianArchetype.DESTROYER
        assert ARCHETYPE_SHADOW_MAP[JungianArchetype.RULER] == JungianArchetype.TYRANT

    def test_is_primary_archetype(self):
        """is_primary_archetype should identify primary vs shadow."""
        assert is_primary_archetype(JungianArchetype.SAGE) is True
        assert is_primary_archetype(JungianArchetype.WARRIOR) is True
        assert is_primary_archetype(JungianArchetype.FOOL) is False
        assert is_primary_archetype(JungianArchetype.VICTIM) is False

    def test_get_shadow(self):
        """get_shadow should return correct shadow or None."""
        assert get_shadow(JungianArchetype.SAGE) == JungianArchetype.FOOL
        assert get_shadow(JungianArchetype.WARRIOR) == JungianArchetype.VICTIM
        assert get_shadow(JungianArchetype.FOOL) is None  # Shadow has no shadow


class TestArchetypePriorModel:
    """Tests for ArchetypePrior model."""

    def test_archetype_prior_creation(self):
        """ArchetypePrior should create with required fields."""
        prior = ArchetypePrior(
            archetype="sage",
            dominant_attractor="cognitive_science",
            shadow="fool",
        )
        assert prior.archetype == "sage"
        assert prior.dominant_attractor == "cognitive_science"
        assert prior.shadow == "fool"
        assert prior.precision == 0.5  # default
        assert prior.activation_threshold == 0.3  # default

    def test_archetype_prior_full_creation(self):
        """ArchetypePrior should accept all fields."""
        prior = ArchetypePrior(
            archetype="warrior",
            dominant_attractor="systems_theory",
            subordinate_attractors=["machine_learning"],
            preferred_actions=["fix", "refactor"],
            avoided_actions=["delay"],
            shadow="victim",
            precision=0.8,
            activation_threshold=0.4,
            trigger_patterns=["urgent", "critical"],
            description="Test warrior",
        )
        assert prior.archetype == "warrior"
        assert prior.precision == 0.8
        assert "fix" in prior.preferred_actions
        assert "delay" in prior.avoided_actions
        assert "urgent" in prior.trigger_patterns

    def test_archetype_prior_precision_bounds(self):
        """Precision should be bounded 0-1."""
        prior = ArchetypePrior(
            archetype="sage",
            dominant_attractor="cognitive_science",
            shadow="fool",
            precision=0.0,
        )
        assert prior.precision == 0.0

        prior2 = ArchetypePrior(
            archetype="sage",
            dominant_attractor="cognitive_science",
            shadow="fool",
            precision=1.0,
        )
        assert prior2.precision == 1.0


class TestArchetypeDefinitions:
    """Tests for ARCHETYPE_DEFINITIONS constant."""

    def test_all_12_archetypes_defined(self):
        """All 12 primary archetypes should have definitions."""
        assert len(ARCHETYPE_DEFINITIONS) == 12
        expected_archetypes = [
            "sage", "warrior", "creator", "ruler",
            "explorer", "magician", "caregiver", "rebel",
            "innocent", "orphan", "lover", "jester"
        ]
        for archetype in expected_archetypes:
            assert archetype in ARCHETYPE_DEFINITIONS

    def test_archetype_definitions_have_required_fields(self):
        """Each definition should have all required fields."""
        for name, prior in ARCHETYPE_DEFINITIONS.items():
            assert prior.archetype == name
            assert prior.dominant_attractor  # non-empty
            assert prior.shadow  # non-empty
            assert len(prior.preferred_actions) > 0
            assert len(prior.avoided_actions) > 0
            assert len(prior.trigger_patterns) > 0

    def test_archetype_basin_affinities(self):
        """Verify specific basin affinities."""
        assert ARCHETYPE_DEFINITIONS["sage"].dominant_attractor == "cognitive_science"
        assert ARCHETYPE_DEFINITIONS["warrior"].dominant_attractor == "systems_theory"
        assert ARCHETYPE_DEFINITIONS["creator"].dominant_attractor == "machine_learning"
        assert ARCHETYPE_DEFINITIONS["magician"].dominant_attractor == "neuroscience"

    def test_get_archetype_prior_function(self):
        """get_archetype_prior should return correct prior."""
        sage = get_archetype_prior("sage")
        assert sage is not None
        assert sage.archetype == "sage"
        assert sage.shadow == "fool"

        # Case insensitive
        warrior = get_archetype_prior("WARRIOR")
        assert warrior is not None
        assert warrior.archetype == "warrior"

        # Non-existent
        assert get_archetype_prior("nonexistent") is None

    def test_get_default_archetype_priors(self):
        """get_default_archetype_priors should return all 12."""
        priors = get_default_archetype_priors()
        assert len(priors) == 12
        archetype_names = {p.archetype for p in priors}
        assert "sage" in archetype_names
        assert "warrior" in archetype_names


class TestResonanceConstants:
    """Tests for resonance protocol constants."""

    def test_resonance_threshold(self):
        """RESONANCE_THRESHOLD should be reasonable."""
        assert 0.0 < RESONANCE_THRESHOLD <= 1.0
        assert RESONANCE_THRESHOLD == 0.75

    def test_resonance_activation_efe(self):
        """RESONANCE_ACTIVATION_EFE should be reasonable."""
        assert 0.0 < RESONANCE_ACTIVATION_EFE <= 1.0
        assert RESONANCE_ACTIVATION_EFE == 0.4

    def test_shadow_window_size(self):
        """SHADOW_WINDOW_SIZE should be positive."""
        assert SHADOW_WINDOW_SIZE > 0
        assert SHADOW_WINDOW_SIZE == 10


class TestPriorHierarchyArchetypes:
    """Tests for PriorHierarchy archetype integration."""

    def test_hierarchy_has_archetype_fields(self):
        """PriorHierarchy should have archetype-related fields."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        assert hasattr(hierarchy, "dispositional_archetypes")
        assert hasattr(hierarchy, "current_archetype")
        assert hierarchy.dispositional_archetypes == []
        assert hierarchy.current_archetype is None

    def test_initialize_archetypes_default(self):
        """initialize_archetypes should load defaults."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        count = hierarchy.initialize_archetypes()
        assert count == 12
        assert len(hierarchy.dispositional_archetypes) == 12

    def test_initialize_archetypes_custom(self):
        """initialize_archetypes should accept custom list."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        custom_priors = [
            ArchetypePrior(
                archetype="sage",
                dominant_attractor="cognitive_science",
                shadow="fool",
            ),
        ]
        count = hierarchy.initialize_archetypes(custom_priors)
        assert count == 1
        assert len(hierarchy.dispositional_archetypes) == 1

    def test_get_archetype_by_name(self):
        """get_archetype_by_name should find archetypes."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        hierarchy.initialize_archetypes()

        sage = hierarchy.get_archetype_by_name("sage")
        assert sage is not None
        assert sage.archetype == "sage"

        # Case insensitive
        warrior = hierarchy.get_archetype_by_name("WARRIOR")
        assert warrior is not None

        # Non-existent
        assert hierarchy.get_archetype_by_name("nonexistent") is None

    def test_update_archetype_precision(self):
        """update_archetype_precision should update precision."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        hierarchy.initialize_archetypes()

        # Update
        result = hierarchy.update_archetype_precision("sage", 0.9)
        assert result is True
        sage = hierarchy.get_archetype_by_name("sage")
        assert sage.precision == 0.9

        # Clamp to bounds
        hierarchy.update_archetype_precision("sage", 1.5)
        assert sage.precision == 1.0

        hierarchy.update_archetype_precision("sage", -0.5)
        assert sage.precision == 0.0

        # Non-existent
        result = hierarchy.update_archetype_precision("nonexistent", 0.5)
        assert result is False

    def test_set_dominant_archetype(self):
        """set_dominant_archetype should set current_archetype."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        hierarchy.initialize_archetypes()

        result = hierarchy.set_dominant_archetype("warrior")
        assert result is True
        assert hierarchy.current_archetype == "warrior"

        # Non-existent
        result = hierarchy.set_dominant_archetype("nonexistent")
        assert result is False
        assert hierarchy.current_archetype == "warrior"  # unchanged

    def test_get_active_archetypes(self):
        """get_active_archetypes should filter by threshold."""
        hierarchy = PriorHierarchy(agent_id="test-agent")
        hierarchy.initialize_archetypes()

        # Default threshold 0.3, all have 0.5 precision
        active = hierarchy.get_active_archetypes()
        assert len(active) == 12

        # Higher threshold
        active = hierarchy.get_active_archetypes(threshold=0.6)
        assert len(active) == 0

        # Boost one archetype
        hierarchy.update_archetype_precision("sage", 0.8)
        active = hierarchy.get_active_archetypes(threshold=0.6)
        assert len(active) == 1
        assert active[0].archetype == "sage"
