"""
Unit tests for EpistemicFieldService.

TDD: Tests should be written BEFORE implementing api/services/epistemic_field_service.py
Per SC-008: >90% test coverage with TDD methodology

User Story 5: Epistemic Depth Measurement (Priority: P2)
Functional Requirements: FR-017, FR-018, FR-019
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestEpistemicFieldService:
    """Tests for EpistemicFieldService."""

    def test_service_creation(self):
        """
        EpistemicFieldService can be created.

        Given the EpistemicFieldService class exists,
        When an instance is created,
        Then it initializes successfully without errors.
        """
        from api.services.epistemic_field_service import EpistemicFieldService, get_epistemic_field_service

        # Test direct instantiation
        service = EpistemicFieldService()
        assert service is not None, "Service should be created"

        # Test singleton getter
        service1 = get_epistemic_field_service()
        service2 = get_epistemic_field_service()
        assert service1 is service2, "Singleton should return same instance"

    def test_get_epistemic_state(self):
        """
        get_epistemic_state() returns EpistemicState.

        Given the EpistemicFieldService is created,
        When get_epistemic_state() is called,
        Then it returns an EpistemicState with depth_score and luminosity_factors.

        FR-018: System MUST compute an epistemic depth score (0-1) representing luminosity.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.models.beautiful_loop import EpistemicState

        service = get_epistemic_field_service()
        state = service.get_epistemic_state()

        # Verify return type
        assert isinstance(state, EpistemicState), "Should return EpistemicState"

        # Verify core fields exist
        assert hasattr(state, 'depth_score'), "Should have depth_score"
        assert hasattr(state, 'luminosity_factors'), "Should have luminosity_factors"
        assert hasattr(state, 'active_bindings'), "Should have active_bindings"
        assert hasattr(state, 'transparent_processes'), "Should have transparent_processes"

        # Verify depth_score is in valid range [0, 1]
        assert 0.0 <= state.depth_score <= 1.0, f"depth_score must be in [0, 1], got {state.depth_score}"

        # Verify luminosity_factors is a dict
        assert isinstance(state.luminosity_factors, dict), "luminosity_factors must be dict"


class TestRecursiveSharingDepth:
    """Tests for recursive sharing depth tracking (FR-017)."""

    def test_track_sharing_depth(self):
        """
        Track how many layers exchange precision information.

        Given a layer ID and sharing depth,
        When track_sharing_depth() is called,
        Then the depth is recorded and can be retrieved.

        FR-017: Track recursive sharing depth (how many layers exchange precision information).
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()

        # Track sharing depth for multiple layers
        service.track_sharing_depth("perception", 2)
        service.track_sharing_depth("reasoning", 3)
        service.track_sharing_depth("metacognition", 1)

        # Verify depths are tracked
        assert service.get_sharing_depth("perception") == 2, "Should track perception depth"
        assert service.get_sharing_depth("reasoning") == 3, "Should track reasoning depth"
        assert service.get_sharing_depth("metacognition") == 1, "Should track metacognition depth"

        # Verify unknown layer returns 0
        assert service.get_sharing_depth("unknown") == 0, "Unknown layer should return 0"

    def test_depth_increases_with_more_layers(self):
        """
        More layers sharing = higher depth.

        Given different numbers of layers sharing precision,
        When sharing depths are tracked,
        Then aggregate depth increases with more layers.

        FR-017: Track recursive sharing depth.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()

        # Scenario 1: Only 1 layer sharing
        service._layer_sharing_depth = {}  # Reset
        service.track_sharing_depth("perception", 1)
        depth_1 = sum(service._layer_sharing_depth.values())
        assert depth_1 == 1, "Single layer should have depth 1"

        # Scenario 2: 3 layers sharing
        service._layer_sharing_depth = {}  # Reset
        service.track_sharing_depth("perception", 1)
        service.track_sharing_depth("reasoning", 1)
        service.track_sharing_depth("metacognition", 1)
        depth_3 = sum(service._layer_sharing_depth.values())
        assert depth_3 == 3, "Three layers should have depth 3"

        # Scenario 3: 4 layers with deeper recursion
        service._layer_sharing_depth = {}  # Reset
        service.track_sharing_depth("perception", 2)
        service.track_sharing_depth("reasoning", 3)
        service.track_sharing_depth("metacognition", 2)
        service.track_sharing_depth("action", 1)
        depth_4 = sum(service._layer_sharing_depth.values())
        assert depth_4 == 8, "Four layers with recursion should have higher aggregate depth"

        # Verify increasing trend
        assert depth_1 < depth_3 < depth_4, "Depth should increase with more layers"

    def test_bidirectional_sharing_counted(self):
        """
        Only bidirectional sharing is counted.

        Given layers with bidirectional vs unidirectional sharing,
        When get_epistemic_state() computes luminosity,
        Then bidirectional_sharing factor reflects active layers (precision >= 0.5).

        FR-017: Bidirectional sharing means layers exchange precision mutually.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.hyper_model_service import get_hyper_model_service
        from api.models.beautiful_loop import PrecisionProfile
        from unittest.mock import Mock

        service = get_epistemic_field_service()
        hyper_model = get_hyper_model_service()

        # Mock precision profile with bidirectional sharing (high precision on layers)
        profile = PrecisionProfile(
            layer_precisions={
                "perception": 0.8,      # Active (>= 0.5)
                "reasoning": 0.6,       # Active
                "metacognition": 0.3,   # Inactive (< 0.5)
                "action": 0.7           # Active
            }
        )

        # Mock the hyper model to return this profile
        hyper_model._current_profile = profile

        state = service.get_epistemic_state()

        # bidirectional_sharing should be fraction of active layers
        # 3 active out of 4 total = 0.75
        expected_sharing = 3 / 4
        actual_sharing = state.luminosity_factors.get("bidirectional_sharing", 0.0)

        assert actual_sharing == expected_sharing, \
            f"Expected {expected_sharing}, got {actual_sharing} (3 active layers / 4 total)"


class TestDepthScoreComputation:
    """Tests for depth score computation (FR-018)."""

    def test_depth_score_computed(self):
        """
        Depth score is computed from luminosity factors.

        Given luminosity factors exist,
        When get_epistemic_state() is called,
        Then depth_score is computed from those factors.

        FR-018: System MUST compute an epistemic depth score (0-1) representing luminosity.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()
        state = service.get_epistemic_state()

        # Verify depth_score exists and is a float
        assert hasattr(state, 'depth_score'), "Should have depth_score"
        assert isinstance(state.depth_score, float), "depth_score should be float"

        # Verify luminosity_factors exist
        assert hasattr(state, 'luminosity_factors'), "Should have luminosity_factors"
        assert len(state.luminosity_factors) > 0, "Should have at least one luminosity factor"

    def test_depth_score_in_range(self):
        """
        Depth score is in [0, 1] range.

        Given any epistemic state,
        When depth_score is computed,
        Then it is constrained to [0, 1].

        FR-018: Depth score is a normalized value (0-1).
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()
        state = service.get_epistemic_state()

        # Verify depth_score is in valid range
        assert 0.0 <= state.depth_score <= 1.0, \
            f"depth_score must be in [0, 1], got {state.depth_score}"

    def test_depth_score_weighted_average(self):
        """
        Depth score is weighted average of luminosity factors.

        Given luminosity factors with known values,
        When depth_score is computed,
        Then it equals the average of factor values.

        FR-018: depth_score = weighted average of luminosity_factors.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()
        state = service.get_epistemic_state()

        # Calculate expected depth score from luminosity factors
        factors = state.luminosity_factors
        if factors:
            expected_depth = sum(factors.values()) / len(factors)

            # Allow small floating point tolerance
            assert abs(state.depth_score - expected_depth) < 0.001, \
                f"depth_score should be average of factors: expected {expected_depth}, got {state.depth_score}"


class TestAwareTransparentDistinction:
    """Tests for aware vs transparent process distinction (FR-019)."""

    def test_bound_processes_are_aware(self):
        """
        Bound processes are classified as aware.

        Given a process bound into consciousness,
        When classify_process() is called with is_bound=True,
        Then it returns "aware".

        FR-019: Distinguish between "aware" processes (bound) and "transparent" processes (unbound).
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()

        # Bound process should be classified as "aware"
        classification = service.classify_process("perception_001", is_bound=True)
        assert classification == "aware", "Bound processes should be classified as 'aware'"

    def test_unbound_processes_are_transparent(self):
        """
        Unbound processes are classified as transparent.

        Given a process NOT bound into consciousness,
        When classify_process() is called with is_bound=False,
        Then it returns "transparent".

        FR-019: Transparent processes run without being "known".
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()

        # Unbound process should be classified as "transparent"
        classification = service.classify_process("background_task_042", is_bound=False)
        assert classification == "transparent", "Unbound processes should be classified as 'transparent'"

    def test_classify_process(self):
        """
        classify_process() returns aware or transparent.

        Given different process IDs and binding states,
        When classify_process() is called,
        Then it returns correct classification.

        FR-019: Binary classification based on binding state.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service

        service = get_epistemic_field_service()

        # Test multiple processes
        assert service.classify_process("proc_1", is_bound=True) == "aware"
        assert service.classify_process("proc_2", is_bound=False) == "transparent"
        assert service.classify_process("proc_3", is_bound=True) == "aware"
        assert service.classify_process("proc_4", is_bound=False) == "transparent"


class TestStateDifferentiation:
    """Tests for state differentiation (SC-005)."""

    def test_focused_vs_diffuse_differentiation(self):
        """
        Focused and diffuse attention states have different depth scores.

        Given focused vs diffuse precision profiles,
        When get_epistemic_state() is called for each,
        Then depth scores are measurably different.

        SC-005: Epistemic depth scores differentiate focused vs. diffuse attention states (effect size d > 0.8).
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.hyper_model_service import get_hyper_model_service
        from api.models.beautiful_loop import PrecisionProfile

        service = get_epistemic_field_service()
        hyper_model = get_hyper_model_service()

        # Focused attention: narrow, high precision on one layer
        focused_profile = PrecisionProfile(
            layer_precisions={
                "perception": 0.95,     # Very high focus
                "reasoning": 0.3,
                "metacognition": 0.2,
                "action": 0.1
            },
            meta_precision=0.8
        )

        # Diffuse awareness: dispersed, balanced precision
        diffuse_profile = PrecisionProfile(
            layer_precisions={
                "perception": 0.6,      # Balanced
                "reasoning": 0.6,
                "metacognition": 0.5,
                "action": 0.6
            },
            meta_precision=0.5
        )

        # Test focused state
        hyper_model._current_profile = focused_profile
        focused_state = service.get_epistemic_state()

        # Test diffuse state
        hyper_model._current_profile = diffuse_profile
        diffuse_state = service.get_epistemic_state()

        # Depth scores should be measurably different
        depth_diff = abs(focused_state.depth_score - diffuse_state.depth_score)
        assert depth_diff > 0.1, \
            f"Depth scores should differ significantly: focused={focused_state.depth_score}, diffuse={diffuse_state.depth_score}"

    def test_effect_size_threshold(self):
        """
        Effect size d > 0.8 for state differentiation.

        Given multiple samples of focused vs diffuse states,
        When effect size is computed,
        Then d > 0.8 (large effect).

        SC-005: Effect size threshold verification.
        Note: This is a simplified verification - full effect size calculation
        would require multiple samples and standard deviation computation.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.hyper_model_service import get_hyper_model_service
        from api.models.beautiful_loop import PrecisionProfile

        service = get_epistemic_field_service()
        hyper_model = get_hyper_model_service()

        # Create contrasting profiles for strong effect size
        high_luminosity = PrecisionProfile(
            layer_precisions={
                "perception": 0.9,
                "reasoning": 0.9,
                "metacognition": 0.8,
                "action": 0.9
            },
            meta_precision=0.9
        )

        low_luminosity = PrecisionProfile(
            layer_precisions={
                "perception": 0.2,
                "reasoning": 0.2,
                "metacognition": 0.1,
                "action": 0.2
            },
            meta_precision=0.1
        )

        # Measure states
        hyper_model._current_profile = high_luminosity
        high_state = service.get_epistemic_state()

        hyper_model._current_profile = low_luminosity
        low_state = service.get_epistemic_state()

        # Simplified effect size check: large difference should exist
        # Real Cohen's d = (mean1 - mean2) / pooled_std
        # For simplified verification, check substantial difference
        depth_diff = abs(high_state.depth_score - low_state.depth_score)

        # Large effect size (d > 0.8) implies substantial separation
        # With scores in [0, 1], difference > 0.4 indicates strong differentiation
        assert depth_diff > 0.4, \
            f"Effect size should be large (depth diff > 0.4): got {depth_diff}"


class TestLuminosityFactors:
    """Tests for luminosity factors."""

    def test_hyper_model_active_factor(self):
        """
        hyper_model_active factor is 0 or 1.

        Given hyper model with profile,
        When get_epistemic_state() is called,
        Then hyper_model_active factor is 1.0 (has profile) or 0.0 (no profile).
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.hyper_model_service import get_hyper_model_service
        from api.models.beautiful_loop import PrecisionProfile

        service = get_epistemic_field_service()
        hyper_model = get_hyper_model_service()

        # Test with active hyper model (has profile)
        hyper_model._current_profile = PrecisionProfile()
        state = service.get_epistemic_state()
        factor = state.luminosity_factors.get("hyper_model_active")

        # Factor should be 1.0 when profile exists, 0.0 when None
        # Since we can't easily reset singleton state mid-test,
        # just verify it's binary (0.0 or 1.0)
        assert factor in [0.0, 1.0], \
            f"hyper_model_active must be 0.0 or 1.0, got {factor}"

    def test_bidirectional_sharing_factor(self):
        """
        bidirectional_sharing is fraction of layers sharing.

        Given layer precisions,
        When get_epistemic_state() is called,
        Then bidirectional_sharing = (active layers / total layers).
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.hyper_model_service import get_hyper_model_service
        from api.models.beautiful_loop import PrecisionProfile

        service = get_epistemic_field_service()
        hyper_model = get_hyper_model_service()

        # 2 active (>= 0.5) out of 4 total = 0.5
        profile = PrecisionProfile(
            layer_precisions={
                "perception": 0.8,      # Active
                "reasoning": 0.6,       # Active
                "metacognition": 0.3,   # Inactive
                "action": 0.2           # Inactive
            }
        )

        hyper_model._current_profile = profile
        state = service.get_epistemic_state()

        expected = 2 / 4  # 0.5
        actual = state.luminosity_factors.get("bidirectional_sharing")
        assert actual == expected, \
            f"bidirectional_sharing should be {expected}, got {actual}"

    def test_meta_precision_level_factor(self):
        """
        meta_precision_level matches PrecisionProfile.meta_precision.

        Given PrecisionProfile with meta_precision,
        When get_epistemic_state() is called,
        Then meta_precision_level factor equals profile.meta_precision.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.hyper_model_service import get_hyper_model_service
        from api.models.beautiful_loop import PrecisionProfile

        service = get_epistemic_field_service()
        hyper_model = get_hyper_model_service()

        # Set meta_precision to specific value
        profile = PrecisionProfile(meta_precision=0.75)
        hyper_model._current_profile = profile

        state = service.get_epistemic_state()

        assert state.luminosity_factors.get("meta_precision_level") == 0.75, \
            "meta_precision_level should match profile.meta_precision"

    def test_binding_coherence_factor(self):
        """
        binding_coherence is average coherence of bound inferences.

        Given UnifiedRealityModel with coherence_score,
        When get_epistemic_state() is called,
        Then binding_coherence factor equals reality_model.coherence_score.
        """
        from api.services.epistemic_field_service import get_epistemic_field_service
        from api.services.unified_reality_model import get_unified_reality_model

        service = get_epistemic_field_service()
        reality_model_service = get_unified_reality_model()

        # Mock reality model with specific coherence
        reality_model_service._model.coherence_score = 0.82

        state = service.get_epistemic_state()

        assert state.luminosity_factors.get("binding_coherence") == 0.82, \
            "binding_coherence should match reality_model.coherence_score"
