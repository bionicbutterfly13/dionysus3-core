"""
Unit tests for Archetype Resonance Protocol (Track 002: Jungian Cognitive Archetypes)

Tests allostatic load calculation and resonance rebalancing under high load.
"""

import pytest
from datetime import datetime

from api.models.biological_agency import SubcorticalState
from api.models.priors import (
    ArchetypePrior,
    get_default_archetype_priors,
    RESONANCE_THRESHOLD,
    RESONANCE_ACTIVATION_EFE,
)
from api.services.arousal_system_service import ArousalSystemService
from api.services.shadow_log_service import (
    ArchetypeShadowLog,
    ShadowEntry,
    get_archetype_shadow_log,
    reset_archetype_shadow_log,
)


class TestAllostasticLoadCalculation:
    """Tests for allostatic load calculation in ArousalSystemService."""

    @pytest.fixture
    def service(self):
        return ArousalSystemService()

    @pytest.fixture
    def low_stress_state(self):
        """Low stress state: low NE, high DA, good gain."""
        return SubcorticalState(
            ne_phasic=0.1,
            ne_tonic=0.2,
            da_phasic=0.6,
            da_tonic=0.8,
            synaptic_gain=3.0,
        )

    @pytest.fixture
    def high_stress_state(self):
        """High stress state: high NE, low DA, poor gain."""
        return SubcorticalState(
            ne_phasic=0.9,
            ne_tonic=0.85,
            da_phasic=0.1,
            da_tonic=0.15,
            synaptic_gain=0.5,
        )

    @pytest.fixture
    def moderate_state(self):
        """Moderate stress state."""
        return SubcorticalState(
            ne_phasic=0.5,
            ne_tonic=0.5,
            da_phasic=0.4,
            da_tonic=0.5,
            synaptic_gain=1.5,
        )

    def test_low_stress_low_load(self, service, low_stress_state):
        """Low stress should produce low allostatic load."""
        load = service.get_allostatic_load(low_stress_state)
        assert 0.0 <= load < 0.4  # Well below resonance threshold
        assert load < RESONANCE_THRESHOLD

    def test_high_stress_high_load(self, service, high_stress_state):
        """High stress should produce high allostatic load."""
        load = service.get_allostatic_load(high_stress_state)
        assert load > RESONANCE_THRESHOLD  # Should trigger resonance
        assert load <= 1.0

    def test_moderate_stress_moderate_load(self, service, moderate_state):
        """Moderate stress should produce moderate load."""
        load = service.get_allostatic_load(moderate_state)
        assert 0.3 <= load <= 0.7

    def test_load_bounded_zero_to_one(self, service):
        """Allostatic load should always be in [0, 1]."""
        # Test extreme low state
        extreme_low = SubcorticalState(
            ne_phasic=0.0,
            ne_tonic=0.0,
            da_phasic=1.0,
            da_tonic=1.0,
            synaptic_gain=5.0,
        )
        load_low = service.get_allostatic_load(extreme_low)
        assert 0.0 <= load_low <= 1.0

        # Test extreme high state
        extreme_high = SubcorticalState(
            ne_phasic=1.0,
            ne_tonic=1.0,
            da_phasic=0.0,
            da_tonic=0.1,  # Min DA
            synaptic_gain=0.1,
        )
        load_high = service.get_allostatic_load(extreme_high)
        assert 0.0 <= load_high <= 1.0

    def test_ne_tonic_dominates_uncertainty(self, service):
        """NE tonic (sustained uncertainty) should increase load."""
        low_ne = SubcorticalState(
            ne_phasic=0.3, ne_tonic=0.1, da_phasic=0.5, da_tonic=0.5, synaptic_gain=2.0
        )
        high_ne = SubcorticalState(
            ne_phasic=0.3, ne_tonic=0.9, da_phasic=0.5, da_tonic=0.5, synaptic_gain=2.0
        )

        load_low = service.get_allostatic_load(low_ne)
        load_high = service.get_allostatic_load(high_ne)

        assert load_high > load_low

    def test_da_tonic_reduces_load(self, service):
        """High DA tonic (goal progress) should reduce load."""
        low_da = SubcorticalState(
            ne_phasic=0.3, ne_tonic=0.3, da_phasic=0.5, da_tonic=0.2, synaptic_gain=2.0
        )
        high_da = SubcorticalState(
            ne_phasic=0.3, ne_tonic=0.3, da_phasic=0.5, da_tonic=0.9, synaptic_gain=2.0
        )

        load_low_da = service.get_allostatic_load(low_da)
        load_high_da = service.get_allostatic_load(high_da)

        assert load_low_da > load_high_da


class TestResonanceThresholdTrigger:
    """Tests for resonance threshold triggering."""

    @pytest.fixture
    def shadow_log(self):
        log = ArchetypeShadowLog(max_size=50, window_size=10)
        # Pre-populate with suppressions
        log.log_suppression("sage", efe_score=0.30, dominant_archetype="warrior")
        log.log_suppression("creator", efe_score=0.35, dominant_archetype="warrior")
        log.log_suppression("explorer", efe_score=0.50, dominant_archetype="sage")
        return log

    def test_resonance_not_triggered_below_threshold(self, shadow_log):
        """Resonance should not trigger when load is below threshold."""
        # Load below RESONANCE_THRESHOLD (0.75)
        result = shadow_log.check_resonance(allostatic_load=0.5)
        assert result is None
        assert not shadow_log.is_resonance_active

    def test_resonance_triggered_above_threshold(self, shadow_log):
        """Resonance should trigger when load is above threshold."""
        # Load above RESONANCE_THRESHOLD (0.75)
        result = shadow_log.check_resonance(allostatic_load=0.8)
        assert result is not None
        assert shadow_log.is_resonance_active
        # Should pick lowest EFE (sage at 0.30)
        assert result.archetype == "sage"

    def test_resonance_at_threshold_triggers(self, shadow_log):
        """Resonance triggers at or above threshold (>= not just >)."""
        result = shadow_log.check_resonance(allostatic_load=RESONANCE_THRESHOLD)
        # At exactly threshold, resonance is triggered (>= semantic)
        assert result is not None
        assert result.archetype == "sage"

    def test_resonance_requires_candidates_below_efe_threshold(self):
        """Resonance needs candidates with EFE below RESONANCE_ACTIVATION_EFE."""
        shadow_log = ArchetypeShadowLog(max_size=50, window_size=10)
        # Only add suppressions with high EFE (above activation threshold)
        shadow_log.log_suppression("sage", efe_score=0.50)
        shadow_log.log_suppression("warrior", efe_score=0.60)

        result = shadow_log.check_resonance(allostatic_load=0.9)
        assert result is None  # No valid candidates

    def test_custom_threshold_override(self, shadow_log):
        """Should support custom threshold override."""
        # Use lower threshold
        result = shadow_log.check_resonance(allostatic_load=0.5, threshold=0.4)
        assert result is not None
        assert result.archetype == "sage"


class TestShadowCandidateSelection:
    """Tests for shadow candidate selection."""

    @pytest.fixture
    def shadow_log(self):
        return ArchetypeShadowLog(max_size=100, window_size=10)

    def test_candidates_sorted_by_efe(self, shadow_log):
        """Candidates should be sorted by EFE (lowest first)."""
        shadow_log.log_suppression("sage", efe_score=0.35)
        shadow_log.log_suppression("warrior", efe_score=0.20)
        shadow_log.log_suppression("creator", efe_score=0.30)
        shadow_log.log_suppression("explorer", efe_score=0.50)  # Above threshold

        candidates = shadow_log.get_resonance_candidates(max_candidates=3)

        assert len(candidates) == 3
        assert candidates[0].archetype == "warrior"  # Lowest EFE
        assert candidates[1].archetype == "creator"
        assert candidates[2].archetype == "sage"

    def test_candidates_exclude_high_efe(self, shadow_log):
        """Candidates with EFE >= RESONANCE_ACTIVATION_EFE should be excluded."""
        shadow_log.log_suppression("sage", efe_score=0.30)
        shadow_log.log_suppression("warrior", efe_score=0.45)  # Above threshold
        shadow_log.log_suppression("creator", efe_score=0.60)  # Above threshold

        candidates = shadow_log.get_resonance_candidates()

        assert len(candidates) == 1
        assert candidates[0].archetype == "sage"

    def test_max_candidates_limit(self, shadow_log):
        """Should respect max_candidates limit."""
        for i, archetype in enumerate(["sage", "warrior", "creator", "explorer", "magician"]):
            shadow_log.log_suppression(archetype, efe_score=0.20 + i * 0.03)

        candidates = shadow_log.get_resonance_candidates(max_candidates=2)
        assert len(candidates) == 2

    def test_empty_log_no_candidates(self, shadow_log):
        """Empty log should return no candidates."""
        candidates = shadow_log.get_resonance_candidates()
        assert len(candidates) == 0


class TestResonanceArchetypeBoost:
    """Tests for resonance archetype boost mechanism."""

    @pytest.fixture
    def archetypes(self):
        return get_default_archetype_priors()

    def test_resonance_returns_suppressed_archetype(self):
        """Resonance should return the best suppressed archetype for boost."""
        shadow_log = ArchetypeShadowLog()
        shadow_log.log_suppression("sage", efe_score=0.25, context="analysis needed")

        result = shadow_log.check_resonance(allostatic_load=0.85)

        assert result is not None
        assert result.archetype == "sage"
        assert result.efe_score == 0.25

    def test_resonance_deactivation(self):
        """Should be able to deactivate resonance mode."""
        shadow_log = ArchetypeShadowLog()
        shadow_log.log_suppression("sage", efe_score=0.25)
        shadow_log.check_resonance(allostatic_load=0.85)

        assert shadow_log.is_resonance_active

        shadow_log.deactivate_resonance()

        assert not shadow_log.is_resonance_active

    def test_multiple_resonance_cycles(self):
        """Should support multiple resonance trigger cycles."""
        shadow_log = ArchetypeShadowLog()

        # First cycle
        shadow_log.log_suppression("sage", efe_score=0.25)
        result1 = shadow_log.check_resonance(allostatic_load=0.85)
        assert result1.archetype == "sage"

        shadow_log.deactivate_resonance()

        # Add more suppressions
        shadow_log.log_suppression("warrior", efe_score=0.20)

        # Second cycle
        result2 = shadow_log.check_resonance(allostatic_load=0.85)
        assert result2.archetype == "warrior"  # Lowest EFE now


class TestIntegrationWithArousalService:
    """Integration tests between ArousalSystemService and ShadowLog."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_archetype_shadow_log()

    @pytest.fixture
    def arousal_service(self):
        return ArousalSystemService()

    @pytest.fixture
    def shadow_log(self):
        log = get_archetype_shadow_log()
        log.log_suppression("sage", efe_score=0.25)
        log.log_suppression("creator", efe_score=0.30)
        return log

    def test_full_resonance_flow(self, arousal_service, shadow_log):
        """Test full flow: high stress → high load → resonance trigger."""
        # Create high stress state
        high_stress = SubcorticalState(
            ne_phasic=0.85,
            ne_tonic=0.80,
            da_phasic=0.15,
            da_tonic=0.2,
            synaptic_gain=0.6,
        )

        # Calculate allostatic load
        load = arousal_service.get_allostatic_load(high_stress)
        assert load > RESONANCE_THRESHOLD

        # Check resonance
        result = shadow_log.check_resonance(allostatic_load=load)
        assert result is not None
        assert result.archetype == "sage"  # Lowest EFE

    def test_low_stress_no_resonance(self, arousal_service, shadow_log):
        """Test that low stress doesn't trigger resonance."""
        low_stress = SubcorticalState(
            ne_phasic=0.1,
            ne_tonic=0.15,
            da_phasic=0.7,
            da_tonic=0.85,
            synaptic_gain=3.5,
        )

        load = arousal_service.get_allostatic_load(low_stress)
        assert load < RESONANCE_THRESHOLD

        result = shadow_log.check_resonance(allostatic_load=load)
        assert result is None


class TestResonanceConstants:
    """Tests for resonance-related constants."""

    def test_resonance_threshold_value(self):
        """RESONANCE_THRESHOLD should be 0.75."""
        assert RESONANCE_THRESHOLD == 0.75

    def test_resonance_activation_efe_value(self):
        """RESONANCE_ACTIVATION_EFE should be 0.4."""
        assert RESONANCE_ACTIVATION_EFE == 0.4

    def test_thresholds_relationship(self):
        """EFE threshold should be lower than load threshold."""
        # This ensures candidates are reasonably good (low EFE)
        # before resonance can trigger (high load)
        assert RESONANCE_ACTIVATION_EFE < RESONANCE_THRESHOLD
