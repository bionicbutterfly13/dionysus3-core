"""
Unit tests for Archetype EFE Competition (Track 002: Jungian Cognitive Archetypes)

Tests EFE-based archetype competition and Shadow Log functionality.
"""

import pytest
from datetime import datetime, timedelta

from api.models.priors import (
    ArchetypePrior,
    get_default_archetype_priors,
    RESONANCE_THRESHOLD,
    RESONANCE_ACTIVATION_EFE,
)
from api.services.efe_engine import EFEEngine, get_efe_engine
from api.services.shadow_log_service import (
    ShadowEntry,
    ArchetypeShadowLog,
    get_archetype_shadow_log,
    reset_archetype_shadow_log,
)


class TestArchetypeEFECalculation:
    """Tests for archetype EFE calculation."""

    @pytest.fixture
    def engine(self):
        return EFEEngine()

    @pytest.fixture
    def sage_prior(self):
        return ArchetypePrior(
            archetype="sage",
            dominant_attractor="cognitive_science",
            subordinate_attractors=["philosophy"],
            preferred_actions=["analyze", "debug", "research"],
            avoided_actions=["rush", "guess"],
            shadow="fool",
            precision=0.5,
            activation_threshold=0.3,
            trigger_patterns=["understand", "analyze", "why", "debug"],
        )

    @pytest.fixture
    def warrior_prior(self):
        return ArchetypePrior(
            archetype="warrior",
            dominant_attractor="systems_theory",
            subordinate_attractors=["machine_learning"],
            preferred_actions=["fix", "delete", "refactor"],
            avoided_actions=["delay", "hesitate"],
            shadow="victim",
            precision=0.5,
            activation_threshold=0.3,
            trigger_patterns=["fix", "urgent", "critical", "bug"],
        )

    def test_archetype_efe_basic(self, engine, sage_prior):
        """Basic archetype EFE calculation."""
        efe = engine.calculate_archetype_efe("some content", sage_prior)
        assert 0.0 <= efe <= 2.0

    def test_archetype_efe_trigger_reduces_score(self, engine, sage_prior):
        """Matching trigger patterns should reduce EFE."""
        efe_no_trigger = engine.calculate_archetype_efe("random content", sage_prior)
        efe_with_trigger = engine.calculate_archetype_efe("I need to analyze this", sage_prior)

        assert efe_with_trigger < efe_no_trigger

    def test_archetype_efe_preferred_action_reduces_score(self, engine, sage_prior):
        """Preferred actions should reduce EFE."""
        efe_no_action = engine.calculate_archetype_efe("random content", sage_prior)
        efe_with_action = engine.calculate_archetype_efe("let me debug this", sage_prior)

        assert efe_with_action < efe_no_action

    def test_archetype_efe_avoided_action_increases_score(self, engine, sage_prior):
        """Avoided actions should increase EFE."""
        efe_neutral = engine.calculate_archetype_efe("random content", sage_prior)
        efe_with_avoided = engine.calculate_archetype_efe("let me rush through this", sage_prior)

        assert efe_with_avoided > efe_neutral

    def test_archetype_efe_precision_affects_score(self, engine):
        """Higher precision should lower EFE."""
        low_prec = ArchetypePrior(
            archetype="test",
            dominant_attractor="test",
            shadow="test_shadow",
            precision=0.2,
        )
        high_prec = ArchetypePrior(
            archetype="test",
            dominant_attractor="test",
            shadow="test_shadow",
            precision=0.8,
        )

        efe_low = engine.calculate_archetype_efe("content", low_prec)
        efe_high = engine.calculate_archetype_efe("content", high_prec)

        assert efe_high < efe_low


class TestArchetypeDominantSelection:
    """Tests for dominant archetype selection."""

    @pytest.fixture
    def engine(self):
        return EFEEngine()

    @pytest.fixture
    def archetypes(self):
        return get_default_archetype_priors()

    def test_select_dominant_empty_list(self, engine):
        """Empty archetype list should return None."""
        dominant, suppressed, scores = engine.select_dominant_archetype("content", [])
        assert dominant is None
        assert suppressed == []
        assert scores == {}

    def test_select_dominant_returns_archetype(self, engine, archetypes):
        """Should return a dominant archetype."""
        dominant, suppressed, scores = engine.select_dominant_archetype(
            "I need to analyze this bug",
            archetypes
        )
        assert dominant is not None
        assert dominant.archetype in [a.archetype for a in archetypes]

    def test_select_dominant_returns_all_scores(self, engine, archetypes):
        """Should return EFE scores for all archetypes."""
        dominant, suppressed, scores = engine.select_dominant_archetype(
            "content",
            archetypes
        )
        assert len(scores) == len(archetypes)
        for archetype in archetypes:
            assert archetype.archetype in scores

    def test_select_dominant_suppressed_excludes_winner(self, engine, archetypes):
        """Suppressed list should not include the winner."""
        dominant, suppressed, scores = engine.select_dominant_archetype(
            "content",
            archetypes
        )
        suppressed_names = [a.archetype for a in suppressed]
        assert dominant.archetype not in suppressed_names
        assert len(suppressed) == len(archetypes) - 1

    def test_select_dominant_warrior_wins_for_urgent(self, engine, archetypes):
        """WARRIOR should win for urgent/critical content."""
        dominant, _, _ = engine.select_dominant_archetype(
            "urgent critical fix needed for this bug error",
            archetypes
        )
        # WARRIOR triggers: fix, urgent, critical, bug, error
        assert dominant.archetype == "warrior"

    def test_select_dominant_sage_wins_for_analysis(self, engine, archetypes):
        """SAGE should win for analysis content."""
        dominant, _, _ = engine.select_dominant_archetype(
            "I need to understand and analyze why this happens",
            archetypes
        )
        # SAGE triggers: understand, analyze, why
        assert dominant.archetype == "sage"

    def test_select_dominant_creator_wins_for_build(self, engine, archetypes):
        """CREATOR should win for build/create content."""
        dominant, _, _ = engine.select_dominant_archetype(
            "let me build and create a new implementation design",
            archetypes
        )
        # CREATOR triggers: build, create, implement, new, design
        assert dominant.archetype == "creator"


class TestBayesianPrecisionUpdate:
    """Tests for Bayesian precision updates."""

    @pytest.fixture
    def engine(self):
        return EFEEngine()

    @pytest.fixture
    def prior(self):
        return ArchetypePrior(
            archetype="test",
            dominant_attractor="test",
            shadow="test_shadow",
            precision=0.5,
        )

    def test_precision_increase(self, engine, prior):
        """Positive evidence should increase precision."""
        old_precision = prior.precision
        new_precision = engine.update_archetype_precision_bayesian(
            prior, evidence_weight=0.5, direction="increase"
        )
        assert new_precision > old_precision
        assert prior.precision == new_precision

    def test_precision_decrease(self, engine, prior):
        """Negative evidence should decrease precision."""
        old_precision = prior.precision
        new_precision = engine.update_archetype_precision_bayesian(
            prior, evidence_weight=0.5, direction="decrease"
        )
        assert new_precision < old_precision
        assert prior.precision == new_precision

    def test_precision_clamped_to_max(self, engine, prior):
        """Precision should not exceed 1.0."""
        prior.precision = 0.95
        new_precision = engine.update_archetype_precision_bayesian(
            prior, evidence_weight=1.0, direction="increase"
        )
        assert new_precision <= 1.0

    def test_precision_clamped_to_min(self, engine, prior):
        """Precision should not go below 0.0."""
        prior.precision = 0.05
        new_precision = engine.update_archetype_precision_bayesian(
            prior, evidence_weight=1.0, direction="decrease"
        )
        assert new_precision >= 0.0


class TestShadowEntry:
    """Tests for ShadowEntry model."""

    def test_shadow_entry_creation(self):
        """ShadowEntry should create with required fields."""
        entry = ShadowEntry(
            archetype="sage",
            efe_score=0.35,
        )
        assert entry.archetype == "sage"
        assert entry.efe_score == 0.35
        assert entry.timestamp is not None

    def test_shadow_entry_full_creation(self):
        """ShadowEntry should accept all fields."""
        entry = ShadowEntry(
            archetype="warrior",
            efe_score=0.42,
            context="testing context",
            basin="cognitive_science",
            dominant_archetype="sage",
        )
        assert entry.archetype == "warrior"
        assert entry.context == "testing context"
        assert entry.dominant_archetype == "sage"


class TestArchetypeShadowLog:
    """Tests for ArchetypeShadowLog."""

    @pytest.fixture
    def shadow_log(self):
        return ArchetypeShadowLog(max_size=50, window_size=5)

    def test_log_suppression(self, shadow_log):
        """Should log a suppressed archetype."""
        entry = shadow_log.log_suppression(
            archetype="sage",
            efe_score=0.4,
            context="test",
            dominant_archetype="warrior"
        )
        assert entry.archetype == "sage"
        assert shadow_log.size == 1

    def test_log_suppressions_batch(self, shadow_log):
        """Should log multiple suppressions."""
        archetypes = [
            ArchetypePrior(archetype="sage", dominant_attractor="test", shadow="fool"),
            ArchetypePrior(archetype="explorer", dominant_attractor="test", shadow="wanderer"),
        ]
        efe_scores = {"sage": 0.4, "explorer": 0.45}

        entries = shadow_log.log_suppressions_batch(
            archetypes, efe_scores, "context", "basin", "warrior"
        )

        assert len(entries) == 2
        assert shadow_log.size == 2

    def test_get_recent(self, shadow_log):
        """Should return recent entries."""
        for i in range(10):
            shadow_log.log_suppression(f"archetype_{i}", 0.3 + i * 0.01)

        # Window size is 5
        recent = shadow_log.get_recent()
        assert len(recent) == 5

    def test_get_archetype_frequency(self, shadow_log):
        """Should count archetype suppressions."""
        shadow_log.log_suppression("sage", 0.3)
        shadow_log.log_suppression("sage", 0.35)
        shadow_log.log_suppression("warrior", 0.4)

        freq = shadow_log.get_archetype_frequency()
        assert freq["sage"] == 2
        assert freq["warrior"] == 1

    def test_check_resonance_below_threshold(self, shadow_log):
        """Should not trigger resonance below threshold."""
        shadow_log.log_suppression("sage", 0.3)

        result = shadow_log.check_resonance(allostatic_load=0.5)  # Below 0.75
        assert result is None

    def test_check_resonance_above_threshold(self, shadow_log):
        """Should trigger resonance above threshold."""
        shadow_log.log_suppression("sage", 0.3)  # Below RESONANCE_ACTIVATION_EFE (0.4)

        result = shadow_log.check_resonance(allostatic_load=0.8)  # Above 0.75
        assert result is not None
        assert result.archetype == "sage"
        assert shadow_log.is_resonance_active

    def test_check_resonance_no_candidates(self, shadow_log):
        """Should not trigger if no candidates below EFE threshold."""
        shadow_log.log_suppression("sage", 0.6)  # Above RESONANCE_ACTIVATION_EFE (0.4)

        result = shadow_log.check_resonance(allostatic_load=0.8)
        assert result is None

    def test_get_resonance_candidates(self, shadow_log):
        """Should return candidates sorted by EFE."""
        shadow_log.log_suppression("sage", 0.35)
        shadow_log.log_suppression("warrior", 0.25)
        shadow_log.log_suppression("creator", 0.30)
        shadow_log.log_suppression("explorer", 0.50)  # Above threshold, excluded

        candidates = shadow_log.get_resonance_candidates(max_candidates=3)

        assert len(candidates) == 3
        assert candidates[0].archetype == "warrior"  # Lowest EFE
        assert candidates[1].archetype == "creator"
        assert candidates[2].archetype == "sage"

    def test_clear_all(self, shadow_log):
        """Should clear all entries."""
        shadow_log.log_suppression("sage", 0.3)
        shadow_log.log_suppression("warrior", 0.4)

        count = shadow_log.clear_all()

        assert count == 2
        assert shadow_log.size == 0
        assert not shadow_log.is_resonance_active

    def test_deactivate_resonance(self, shadow_log):
        """Should deactivate resonance mode."""
        shadow_log.log_suppression("sage", 0.3)
        shadow_log.check_resonance(allostatic_load=0.8)

        assert shadow_log.is_resonance_active

        shadow_log.deactivate_resonance()

        assert not shadow_log.is_resonance_active


class TestShadowLogSingleton:
    """Tests for shadow log singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_archetype_shadow_log()

    def test_get_shadow_log_singleton(self):
        """Should return same instance."""
        log1 = get_archetype_shadow_log()
        log2 = get_archetype_shadow_log()
        assert log1 is log2

    def test_reset_shadow_log(self):
        """Should create new instance after reset."""
        log1 = get_archetype_shadow_log()
        log1.log_suppression("sage", 0.3)

        reset_archetype_shadow_log()
        log2 = get_archetype_shadow_log()

        assert log2.size == 0
