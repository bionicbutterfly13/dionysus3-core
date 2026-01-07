"""
Unit tests for Beautiful Loop Pydantic models.

TDD: These tests should be written BEFORE implementing api/models/beautiful_loop.py
Per SC-008: >90% test coverage with TDD methodology

Models to test:
- PrecisionProfile (FR-009, FR-010, FR-011, FR-012)
- EpistemicState (FR-017, FR-018, FR-019)
- PrecisionError (FR-013, FR-014)
- BoundInference (FR-005, FR-006)
- BindingConfig (FR-007)
- HyperModelConfig
- Event types (FR-027)
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestPrecisionProfile:
    """Tests for PrecisionProfile model (FR-009 through FR-012)."""

    def test_precision_profile_creation(self):
        """PrecisionProfile can be created with default values."""
        from api.models.beautiful_loop import PrecisionProfile

        profile = PrecisionProfile()

        # Check defaults exist
        assert profile.layer_precisions == {}
        assert profile.modality_precisions == {}
        assert profile.temporal_depth == 0.5
        assert profile.meta_precision == 0.5
        assert profile.context_embedding == []
        assert isinstance(profile.timestamp, datetime)
        assert profile.cycle_id is None

    def test_precision_profile_with_layer_precisions(self):
        """PrecisionProfile accepts per-layer precision weights (FR-010)."""
        from api.models.beautiful_loop import PrecisionProfile

        layer_precisions = {
            "perception": 0.8,
            "reasoning": 0.6,
            "metacognition": 0.9,
            "action": 0.7
        }
        profile = PrecisionProfile(layer_precisions=layer_precisions)

        assert profile.layer_precisions == layer_precisions
        assert profile.layer_precisions["perception"] == 0.8

    def test_precision_profile_with_modality_precisions(self):
        """PrecisionProfile accepts per-modality precision weights (FR-011)."""
        from api.models.beautiful_loop import PrecisionProfile

        modality_precisions = {
            "visual": 0.9,
            "semantic": 0.7,
            "procedural": 0.5,
            "episodic": 0.6
        }
        profile = PrecisionProfile(modality_precisions=modality_precisions)

        assert profile.modality_precisions == modality_precisions
        assert profile.modality_precisions["visual"] == 0.9

    def test_layer_precisions_validation_max(self):
        """Layer precisions must be <= 1.0."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(layer_precisions={"perception": 1.5})

        assert "layer_precisions" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_layer_precisions_validation_min(self):
        """Layer precisions must be >= 0.0."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(layer_precisions={"perception": -0.1})

        assert "layer_precisions" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_modality_precisions_validation_max(self):
        """Modality precisions must be <= 1.0."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(modality_precisions={"visual": 1.1})

        assert "modality_precisions" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_modality_precisions_validation_min(self):
        """Modality precisions must be >= 0.0."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(modality_precisions={"visual": -0.5})

        assert "modality_precisions" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_temporal_depth_bounds_max(self):
        """Temporal depth must be <= 1.0."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(temporal_depth=1.5)

        assert "temporal_depth" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_temporal_depth_bounds_min(self):
        """Temporal depth must be >= 0.0."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(temporal_depth=-0.1)

        assert "temporal_depth" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_temporal_depth_valid_range(self):
        """Temporal depth accepts values in [0, 1] range."""
        from api.models.beautiful_loop import PrecisionProfile

        # Test boundary values
        profile_zero = PrecisionProfile(temporal_depth=0.0)
        assert profile_zero.temporal_depth == 0.0

        profile_one = PrecisionProfile(temporal_depth=1.0)
        assert profile_one.temporal_depth == 1.0

        profile_mid = PrecisionProfile(temporal_depth=0.75)
        assert profile_mid.temporal_depth == 0.75

    def test_meta_precision_bounds_max(self):
        """Meta precision must be <= 1.0 (FR-012)."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(meta_precision=1.2)

        assert "meta_precision" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_meta_precision_bounds_min(self):
        """Meta precision must be >= 0.0 (FR-012)."""
        from api.models.beautiful_loop import PrecisionProfile

        with pytest.raises(ValidationError) as exc_info:
            PrecisionProfile(meta_precision=-0.3)

        assert "meta_precision" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_meta_precision_valid_range(self):
        """Meta precision accepts values in [0, 1] range (FR-012)."""
        from api.models.beautiful_loop import PrecisionProfile

        profile = PrecisionProfile(meta_precision=0.85)
        assert profile.meta_precision == 0.85

    def test_context_embedding_accepts_list_of_floats(self):
        """Context embedding must be a list of floats."""
        from api.models.beautiful_loop import PrecisionProfile

        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        profile = PrecisionProfile(context_embedding=embedding)

        assert profile.context_embedding == embedding
        assert all(isinstance(v, float) for v in profile.context_embedding)

    def test_context_embedding_empty_by_default(self):
        """Context embedding defaults to empty list."""
        from api.models.beautiful_loop import PrecisionProfile

        profile = PrecisionProfile()
        assert profile.context_embedding == []

    def test_precision_profile_with_cycle_id(self):
        """PrecisionProfile can track OODA cycle ID."""
        from api.models.beautiful_loop import PrecisionProfile

        profile = PrecisionProfile(cycle_id="cycle-001")
        assert profile.cycle_id == "cycle-001"

    def test_precision_profile_full_instantiation(self):
        """PrecisionProfile can be created with all fields (FR-009)."""
        from api.models.beautiful_loop import PrecisionProfile

        profile = PrecisionProfile(
            layer_precisions={"perception": 0.8, "reasoning": 0.7},
            modality_precisions={"visual": 0.9, "semantic": 0.6},
            temporal_depth=0.6,
            meta_precision=0.75,
            context_embedding=[0.1, 0.2, 0.3],
            cycle_id="test-cycle"
        )

        assert profile.layer_precisions["perception"] == 0.8
        assert profile.modality_precisions["visual"] == 0.9
        assert profile.temporal_depth == 0.6
        assert profile.meta_precision == 0.75
        assert len(profile.context_embedding) == 3
        assert profile.cycle_id == "test-cycle"


class TestEpistemicState:
    """Tests for EpistemicState model (FR-017 through FR-019)."""

    def test_epistemic_state_creation(self):
        """EpistemicState can be created with default values."""
        from api.models.beautiful_loop import EpistemicState

        state = EpistemicState()

        assert state.depth_score == 0.0
        assert state.reality_model_coherence == 0.0
        assert state.active_bindings == []
        assert state.transparent_processes == []
        assert state.luminosity_factors == {}
        assert isinstance(state.timestamp, datetime)

    def test_depth_score_bounds_max(self):
        """Depth score must be <= 1.0."""
        from api.models.beautiful_loop import EpistemicState

        with pytest.raises(ValidationError) as exc_info:
            EpistemicState(depth_score=1.5)

        assert "depth_score" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_depth_score_bounds_min(self):
        """Depth score must be >= 0.0."""
        from api.models.beautiful_loop import EpistemicState

        with pytest.raises(ValidationError) as exc_info:
            EpistemicState(depth_score=-0.1)

        assert "depth_score" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_depth_score_valid_range(self):
        """Depth score accepts values in [0, 1] range (FR-017, FR-018)."""
        from api.models.beautiful_loop import EpistemicState

        state = EpistemicState(depth_score=0.75)
        assert state.depth_score == 0.75

    def test_reality_model_coherence_bounds_max(self):
        """Reality model coherence must be <= 1.0."""
        from api.models.beautiful_loop import EpistemicState

        with pytest.raises(ValidationError) as exc_info:
            EpistemicState(reality_model_coherence=1.2)

        assert "reality_model_coherence" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_reality_model_coherence_bounds_min(self):
        """Reality model coherence must be >= 0.0."""
        from api.models.beautiful_loop import EpistemicState

        with pytest.raises(ValidationError) as exc_info:
            EpistemicState(reality_model_coherence=-0.5)

        assert "reality_model_coherence" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_reality_model_coherence_valid(self):
        """Reality model coherence accepts values in [0, 1] range."""
        from api.models.beautiful_loop import EpistemicState

        state = EpistemicState(reality_model_coherence=0.85)
        assert state.reality_model_coherence == 0.85

    def test_active_bindings_list(self):
        """Active bindings must be a list of strings (FR-019)."""
        from api.models.beautiful_loop import EpistemicState

        bindings = ["inference-001", "inference-002", "inference-003"]
        state = EpistemicState(active_bindings=bindings)

        assert state.active_bindings == bindings
        assert all(isinstance(b, str) for b in state.active_bindings)

    def test_transparent_processes_list(self):
        """Transparent processes must be a list of strings (FR-019)."""
        from api.models.beautiful_loop import EpistemicState

        processes = ["process-001", "process-002"]
        state = EpistemicState(transparent_processes=processes)

        assert state.transparent_processes == processes
        assert all(isinstance(p, str) for p in state.transparent_processes)

    def test_luminosity_factors_dict(self):
        """Luminosity factors accepts dict of string to float."""
        from api.models.beautiful_loop import EpistemicState

        factors = {
            "hyper_model_active": 1.0,
            "bidirectional_sharing": 0.75,
            "meta_precision_level": 0.6,
            "binding_coherence": 0.8
        }
        state = EpistemicState(luminosity_factors=factors)

        assert state.luminosity_factors == factors
        assert state.luminosity_factors["hyper_model_active"] == 1.0

    def test_epistemic_state_full_instantiation(self):
        """EpistemicState can be created with all fields."""
        from api.models.beautiful_loop import EpistemicState

        state = EpistemicState(
            depth_score=0.7,
            reality_model_coherence=0.85,
            active_bindings=["binding-1", "binding-2"],
            transparent_processes=["process-1"],
            luminosity_factors={
                "hyper_model_active": 1.0,
                "bidirectional_sharing": 0.5
            }
        )

        assert state.depth_score == 0.7
        assert state.reality_model_coherence == 0.85
        assert len(state.active_bindings) == 2
        assert len(state.transparent_processes) == 1
        assert len(state.luminosity_factors) == 2


class TestPrecisionError:
    """Tests for PrecisionError model (FR-013, FR-014)."""

    def test_precision_error_creation(self):
        """PrecisionError can be created with required fields (FR-013)."""
        from api.models.beautiful_loop import PrecisionError

        error = PrecisionError(
            layer_id="perception",
            predicted_precision=0.8,
            actual_precision_needed=0.6
        )

        assert error.layer_id == "perception"
        assert error.predicted_precision == 0.8
        assert error.actual_precision_needed == 0.6
        assert isinstance(error.timestamp, datetime)

    def test_error_magnitude_computed(self):
        """Error magnitude is computed as |predicted - actual| (FR-013)."""
        from api.models.beautiful_loop import PrecisionError

        # Over-confident case
        error1 = PrecisionError(
            layer_id="perception",
            predicted_precision=0.8,
            actual_precision_needed=0.5
        )
        assert error1.error_magnitude == pytest.approx(0.3)

        # Under-confident case
        error2 = PrecisionError(
            layer_id="reasoning",
            predicted_precision=0.3,
            actual_precision_needed=0.7
        )
        assert error2.error_magnitude == pytest.approx(0.4)

    def test_error_direction_over_confident(self):
        """Error direction is 'over_confident' when predicted > actual (FR-014)."""
        from api.models.beautiful_loop import PrecisionError

        error = PrecisionError(
            layer_id="perception",
            predicted_precision=0.9,
            actual_precision_needed=0.6
        )

        assert error.error_direction == "over_confident"

    def test_error_direction_under_confident(self):
        """Error direction is 'under_confident' when predicted < actual (FR-014)."""
        from api.models.beautiful_loop import PrecisionError

        error = PrecisionError(
            layer_id="reasoning",
            predicted_precision=0.4,
            actual_precision_needed=0.8
        )

        assert error.error_direction == "under_confident"

    def test_predicted_precision_bounds_max(self):
        """Predicted precision must be <= 1.0."""
        from api.models.beautiful_loop import PrecisionError

        with pytest.raises(ValidationError) as exc_info:
            PrecisionError(
                layer_id="test",
                predicted_precision=1.5,
                actual_precision_needed=0.5
            )

        assert "predicted_precision" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_predicted_precision_bounds_min(self):
        """Predicted precision must be >= 0.0."""
        from api.models.beautiful_loop import PrecisionError

        with pytest.raises(ValidationError) as exc_info:
            PrecisionError(
                layer_id="test",
                predicted_precision=-0.1,
                actual_precision_needed=0.5
            )

        assert "predicted_precision" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_actual_precision_bounds_max(self):
        """Actual precision must be <= 1.0."""
        from api.models.beautiful_loop import PrecisionError

        with pytest.raises(ValidationError) as exc_info:
            PrecisionError(
                layer_id="test",
                predicted_precision=0.5,
                actual_precision_needed=1.2
            )

        assert "actual_precision_needed" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_actual_precision_bounds_min(self):
        """Actual precision must be >= 0.0."""
        from api.models.beautiful_loop import PrecisionError

        with pytest.raises(ValidationError) as exc_info:
            PrecisionError(
                layer_id="test",
                predicted_precision=0.5,
                actual_precision_needed=-0.3
            )

        assert "actual_precision_needed" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_context_hash_optional(self):
        """Context hash is optional and defaults to empty string."""
        from api.models.beautiful_loop import PrecisionError

        error = PrecisionError(
            layer_id="test",
            predicted_precision=0.5,
            actual_precision_needed=0.5
        )

        assert error.context_hash == ""

    def test_context_hash_provided(self):
        """Context hash can be provided for grouping similar errors."""
        from api.models.beautiful_loop import PrecisionError

        error = PrecisionError(
            layer_id="test",
            predicted_precision=0.5,
            actual_precision_needed=0.5,
            context_hash="abc123"
        )

        assert error.context_hash == "abc123"

    def test_equal_precision_under_confident(self):
        """When predicted == actual, direction is under_confident (edge case)."""
        from api.models.beautiful_loop import PrecisionError

        error = PrecisionError(
            layer_id="test",
            predicted_precision=0.5,
            actual_precision_needed=0.5
        )

        # When equal, predicted is NOT > actual, so under_confident
        assert error.error_magnitude == pytest.approx(0.0)
        assert error.error_direction == "under_confident"


class TestBoundInference:
    """Tests for BoundInference model (FR-005, FR-006)."""

    def test_bound_inference_creation(self):
        """BoundInference can be created with required fields (FR-005)."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="inf-001",
            source_layer="perception",
            precision_score=0.8,
            coherence_score=0.7,
            uncertainty_reduction=0.5
        )

        assert inference.inference_id == "inf-001"
        assert inference.source_layer == "perception"
        assert inference.precision_score == 0.8
        assert inference.coherence_score == 0.7
        assert inference.uncertainty_reduction == 0.5
        assert isinstance(inference.bound_at, datetime)

    def test_binding_strength_computed(self):
        """Binding strength = precision * coherence * max(0, uncertainty_reduction) (FR-006)."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="inf-001",
            source_layer="perception",
            precision_score=0.8,
            coherence_score=0.5,
            uncertainty_reduction=0.4
        )

        # Expected: 0.8 * 0.5 * 0.4 = 0.16
        assert inference.binding_strength == pytest.approx(0.16)

    def test_binding_strength_zero_when_negative_uncertainty(self):
        """Binding strength is 0 when uncertainty_reduction < 0 (FR-008)."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="inf-001",
            source_layer="perception",
            precision_score=0.9,
            coherence_score=0.8,
            uncertainty_reduction=-0.3  # Negative - increases uncertainty
        )

        # max(0, -0.3) = 0, so binding_strength = 0
        assert inference.binding_strength == pytest.approx(0.0)

    def test_binding_strength_zero_when_zero_uncertainty(self):
        """Binding strength uses max(0, uncertainty_reduction) = 0 when ur=0."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="inf-001",
            source_layer="perception",
            precision_score=0.9,
            coherence_score=0.8,
            uncertainty_reduction=0.0
        )

        # 0.9 * 0.8 * max(0, 0) = 0
        assert inference.binding_strength == pytest.approx(0.0)

    def test_precision_score_bounds_max(self):
        """Precision score must be <= 1.0."""
        from api.models.beautiful_loop import BoundInference

        with pytest.raises(ValidationError) as exc_info:
            BoundInference(
                inference_id="test",
                source_layer="test",
                precision_score=1.5,
                coherence_score=0.5,
                uncertainty_reduction=0.5
            )

        assert "precision_score" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_precision_score_bounds_min(self):
        """Precision score must be >= 0.0."""
        from api.models.beautiful_loop import BoundInference

        with pytest.raises(ValidationError) as exc_info:
            BoundInference(
                inference_id="test",
                source_layer="test",
                precision_score=-0.1,
                coherence_score=0.5,
                uncertainty_reduction=0.5
            )

        assert "precision_score" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_coherence_score_bounds_max(self):
        """Coherence score must be <= 1.0."""
        from api.models.beautiful_loop import BoundInference

        with pytest.raises(ValidationError) as exc_info:
            BoundInference(
                inference_id="test",
                source_layer="test",
                precision_score=0.5,
                coherence_score=1.2,
                uncertainty_reduction=0.5
            )

        assert "coherence_score" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_coherence_score_bounds_min(self):
        """Coherence score must be >= 0.0."""
        from api.models.beautiful_loop import BoundInference

        with pytest.raises(ValidationError) as exc_info:
            BoundInference(
                inference_id="test",
                source_layer="test",
                precision_score=0.5,
                coherence_score=-0.3,
                uncertainty_reduction=0.5
            )

        assert "coherence_score" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_content_dict_default(self):
        """Content defaults to empty dict."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="test",
            source_layer="test",
            precision_score=0.5,
            coherence_score=0.5,
            uncertainty_reduction=0.5
        )

        assert inference.content == {}

    def test_content_dict_provided(self):
        """Content can hold layer-specific payload."""
        from api.models.beautiful_loop import BoundInference

        content = {"belief": "sky is blue", "confidence": 0.9}
        inference = BoundInference(
            inference_id="test",
            source_layer="perception",
            content=content,
            precision_score=0.5,
            coherence_score=0.5,
            uncertainty_reduction=0.5
        )

        assert inference.content == content

    def test_embedding_list_default(self):
        """Embedding defaults to empty list."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="test",
            source_layer="test",
            precision_score=0.5,
            coherence_score=0.5,
            uncertainty_reduction=0.5
        )

        assert inference.embedding == []

    def test_embedding_list_provided(self):
        """Embedding can be provided for coherence computation."""
        from api.models.beautiful_loop import BoundInference

        embedding = [0.1, 0.2, 0.3, 0.4]
        inference = BoundInference(
            inference_id="test",
            source_layer="test",
            embedding=embedding,
            precision_score=0.5,
            coherence_score=0.5,
            uncertainty_reduction=0.5
        )

        assert inference.embedding == embedding

    def test_cycle_id_optional(self):
        """Cycle ID is optional."""
        from api.models.beautiful_loop import BoundInference

        inference = BoundInference(
            inference_id="test",
            source_layer="test",
            precision_score=0.5,
            coherence_score=0.5,
            uncertainty_reduction=0.5,
            cycle_id="cycle-001"
        )

        assert inference.cycle_id == "cycle-001"


class TestBindingConfig:
    """Tests for BindingConfig model (FR-007)."""

    def test_binding_config_defaults(self):
        """BindingConfig has sensible defaults (7 +/- 2) (FR-007)."""
        from api.models.beautiful_loop import BindingConfig

        config = BindingConfig()

        assert config.min_capacity == 5
        assert config.max_capacity == 9
        assert config.default_capacity == 7
        assert config.precision_threshold == 0.3
        assert config.coherence_threshold == 0.4

    def test_get_capacity_high_complexity(self):
        """Higher complexity returns lower capacity (FR-007)."""
        from api.models.beautiful_loop import BindingConfig

        config = BindingConfig()

        # High complexity (1.0) should return min_capacity
        capacity = config.get_capacity(task_complexity=1.0)
        assert capacity == config.min_capacity  # 5

    def test_get_capacity_low_complexity(self):
        """Lower complexity returns higher capacity (FR-007)."""
        from api.models.beautiful_loop import BindingConfig

        config = BindingConfig()

        # Low complexity (0.0) should return max_capacity
        capacity = config.get_capacity(task_complexity=0.0)
        assert capacity == config.max_capacity  # 9

    def test_get_capacity_mid_complexity(self):
        """Mid complexity returns intermediate capacity."""
        from api.models.beautiful_loop import BindingConfig

        config = BindingConfig()

        # Mid complexity (0.5) should return value between min and max
        capacity = config.get_capacity(task_complexity=0.5)
        assert config.min_capacity <= capacity <= config.max_capacity
        # Expected: 9 - (0.5 * 4) = 9 - 2 = 7
        assert capacity == 7

    def test_min_capacity_bounds(self):
        """Min capacity must be >= 1."""
        from api.models.beautiful_loop import BindingConfig

        with pytest.raises(ValidationError) as exc_info:
            BindingConfig(min_capacity=0)

        assert "min_capacity" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_max_capacity_bounds(self):
        """Max capacity must be >= 1."""
        from api.models.beautiful_loop import BindingConfig

        with pytest.raises(ValidationError) as exc_info:
            BindingConfig(max_capacity=0)

        assert "max_capacity" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_precision_threshold_bounds_max(self):
        """Precision threshold must be <= 1.0."""
        from api.models.beautiful_loop import BindingConfig

        with pytest.raises(ValidationError) as exc_info:
            BindingConfig(precision_threshold=1.5)

        assert "precision_threshold" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_precision_threshold_bounds_min(self):
        """Precision threshold must be >= 0.0."""
        from api.models.beautiful_loop import BindingConfig

        with pytest.raises(ValidationError) as exc_info:
            BindingConfig(precision_threshold=-0.1)

        assert "precision_threshold" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_coherence_threshold_bounds_max(self):
        """Coherence threshold must be <= 1.0."""
        from api.models.beautiful_loop import BindingConfig

        with pytest.raises(ValidationError) as exc_info:
            BindingConfig(coherence_threshold=1.2)

        assert "coherence_threshold" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_coherence_threshold_bounds_min(self):
        """Coherence threshold must be >= 0.0."""
        from api.models.beautiful_loop import BindingConfig

        with pytest.raises(ValidationError) as exc_info:
            BindingConfig(coherence_threshold=-0.5)

        assert "coherence_threshold" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_custom_capacity_range(self):
        """BindingConfig can be customized for different capacity ranges."""
        from api.models.beautiful_loop import BindingConfig

        config = BindingConfig(
            min_capacity=3,
            max_capacity=15,
            default_capacity=10
        )

        assert config.min_capacity == 3
        assert config.max_capacity == 15
        assert config.default_capacity == 10


class TestHyperModelConfig:
    """Tests for HyperModelConfig model."""

    def test_hyper_model_config_defaults(self):
        """HyperModelConfig has sensible defaults."""
        from api.models.beautiful_loop import HyperModelConfig

        config = HyperModelConfig()

        assert config.base_learning_rate == 0.1
        assert config.min_learning_rate == 0.01
        assert config.max_learning_rate == 0.3
        assert config.default_layers == ["perception", "reasoning", "metacognition", "action"]
        assert config.default_modalities == ["visual", "semantic", "procedural", "episodic"]

    def test_base_learning_rate_bounds_max(self):
        """Base learning rate must be <= 1.0."""
        from api.models.beautiful_loop import HyperModelConfig

        with pytest.raises(ValidationError) as exc_info:
            HyperModelConfig(base_learning_rate=1.5)

        assert "base_learning_rate" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_base_learning_rate_bounds_min(self):
        """Base learning rate must be >= 0.0."""
        from api.models.beautiful_loop import HyperModelConfig

        with pytest.raises(ValidationError) as exc_info:
            HyperModelConfig(base_learning_rate=-0.1)

        assert "base_learning_rate" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_min_learning_rate_bounds(self):
        """Min learning rate must be >= 0.0."""
        from api.models.beautiful_loop import HyperModelConfig

        with pytest.raises(ValidationError) as exc_info:
            HyperModelConfig(min_learning_rate=-0.05)

        assert "min_learning_rate" in str(exc_info.value) or "greater than or equal to" in str(exc_info.value)

    def test_max_learning_rate_bounds(self):
        """Max learning rate must be <= 1.0."""
        from api.models.beautiful_loop import HyperModelConfig

        with pytest.raises(ValidationError) as exc_info:
            HyperModelConfig(max_learning_rate=1.5)

        assert "max_learning_rate" in str(exc_info.value) or "less than or equal to" in str(exc_info.value)

    def test_custom_layers(self):
        """HyperModelConfig can use custom layer IDs."""
        from api.models.beautiful_loop import HyperModelConfig

        config = HyperModelConfig(
            default_layers=["input", "hidden", "output"]
        )

        assert config.default_layers == ["input", "hidden", "output"]

    def test_custom_modalities(self):
        """HyperModelConfig can use custom modality IDs."""
        from api.models.beautiful_loop import HyperModelConfig

        config = HyperModelConfig(
            default_modalities=["text", "image", "audio"]
        )

        assert config.default_modalities == ["text", "image", "audio"]

    def test_learning_rate_range_valid(self):
        """Learning rates can be customized within valid bounds."""
        from api.models.beautiful_loop import HyperModelConfig

        config = HyperModelConfig(
            base_learning_rate=0.15,
            min_learning_rate=0.05,
            max_learning_rate=0.5
        )

        assert config.base_learning_rate == 0.15
        assert config.min_learning_rate == 0.05
        assert config.max_learning_rate == 0.5


class TestEventTypes:
    """Tests for Beautiful Loop event types (FR-027)."""

    def test_precision_forecast_event_creation(self):
        """PrecisionForecastEvent can be created with profile and cycle_id (FR-027)."""
        from api.models.beautiful_loop import (
            PrecisionProfile,
            PrecisionForecastEvent
        )

        profile = PrecisionProfile(
            layer_precisions={"perception": 0.8},
            meta_precision=0.7
        )
        event = PrecisionForecastEvent(
            precision_profile=profile,
            cycle_id="cycle-001"
        )

        assert event.event_type == "precision_forecast"
        assert event.precision_profile == profile
        assert event.cycle_id == "cycle-001"

    def test_precision_forecast_event_type_literal(self):
        """PrecisionForecastEvent has correct event_type literal."""
        from api.models.beautiful_loop import (
            PrecisionProfile,
            PrecisionForecastEvent
        )

        profile = PrecisionProfile()
        event = PrecisionForecastEvent(
            precision_profile=profile,
            cycle_id="test"
        )

        assert event.event_type == "precision_forecast"

    def test_precision_error_event_creation(self):
        """PrecisionErrorEvent can be created with errors list and cycle_id (FR-027)."""
        from api.models.beautiful_loop import (
            PrecisionError,
            PrecisionErrorEvent
        )

        errors = [
            PrecisionError(
                layer_id="perception",
                predicted_precision=0.8,
                actual_precision_needed=0.6
            ),
            PrecisionError(
                layer_id="reasoning",
                predicted_precision=0.5,
                actual_precision_needed=0.7
            )
        ]
        event = PrecisionErrorEvent(
            errors=errors,
            cycle_id="cycle-002"
        )

        assert event.event_type == "precision_error"
        assert len(event.errors) == 2
        assert event.cycle_id == "cycle-002"

    def test_precision_error_event_empty_errors(self):
        """PrecisionErrorEvent can have empty errors list."""
        from api.models.beautiful_loop import PrecisionErrorEvent

        event = PrecisionErrorEvent(
            errors=[],
            cycle_id="cycle-003"
        )

        assert event.errors == []
        assert event.cycle_id == "cycle-003"

    def test_precision_update_event_creation(self):
        """PrecisionUpdateEvent can be created with new profile and learning delta (FR-027)."""
        from api.models.beautiful_loop import (
            PrecisionProfile,
            PrecisionUpdateEvent
        )

        new_profile = PrecisionProfile(
            layer_precisions={"perception": 0.85},
            meta_precision=0.75
        )
        event = PrecisionUpdateEvent(
            new_profile=new_profile,
            learning_delta=0.05
        )

        assert event.event_type == "precision_update"
        assert event.new_profile == new_profile
        assert event.learning_delta == 0.05

    def test_precision_update_event_learning_delta_types(self):
        """Learning delta can be positive (learned more) or negative (unlearned)."""
        from api.models.beautiful_loop import (
            PrecisionProfile,
            PrecisionUpdateEvent
        )

        profile = PrecisionProfile()

        # Positive delta
        event_pos = PrecisionUpdateEvent(
            new_profile=profile,
            learning_delta=0.1
        )
        assert event_pos.learning_delta == 0.1

        # Negative delta (correction/forgetting)
        event_neg = PrecisionUpdateEvent(
            new_profile=profile,
            learning_delta=-0.05
        )
        assert event_neg.learning_delta == -0.05

    def test_binding_completed_event_creation(self):
        """BindingCompletedEvent can be created with binding stats and cycle_id (FR-027)."""
        from api.models.beautiful_loop import BindingCompletedEvent

        event = BindingCompletedEvent(
            bound_count=5,
            rejected_count=3,
            average_binding_strength=0.65,
            cycle_id="cycle-004"
        )

        assert event.event_type == "binding_completed"
        assert event.bound_count == 5
        assert event.rejected_count == 3
        assert event.average_binding_strength == 0.65
        assert event.cycle_id == "cycle-004"

    def test_binding_completed_event_zero_bindings(self):
        """BindingCompletedEvent handles case with no bindings."""
        from api.models.beautiful_loop import BindingCompletedEvent

        event = BindingCompletedEvent(
            bound_count=0,
            rejected_count=10,
            average_binding_strength=0.0,
            cycle_id="cycle-005"
        )

        assert event.bound_count == 0
        assert event.rejected_count == 10
        assert event.average_binding_strength == 0.0

    def test_binding_completed_event_all_bound(self):
        """BindingCompletedEvent handles case where all candidates bound."""
        from api.models.beautiful_loop import BindingCompletedEvent

        event = BindingCompletedEvent(
            bound_count=7,
            rejected_count=0,
            average_binding_strength=0.8,
            cycle_id="cycle-006"
        )

        assert event.bound_count == 7
        assert event.rejected_count == 0

    def test_event_types_have_unique_identifiers(self):
        """All event types have unique event_type identifiers."""
        from api.models.beautiful_loop import (
            PrecisionProfile,
            PrecisionError,
            PrecisionForecastEvent,
            PrecisionErrorEvent,
            PrecisionUpdateEvent,
            BindingCompletedEvent
        )

        profile = PrecisionProfile()

        forecast = PrecisionForecastEvent(precision_profile=profile, cycle_id="c1")
        error = PrecisionErrorEvent(errors=[], cycle_id="c2")
        update = PrecisionUpdateEvent(new_profile=profile, learning_delta=0.1)
        binding = BindingCompletedEvent(
            bound_count=5,
            rejected_count=2,
            average_binding_strength=0.5,
            cycle_id="c3"
        )

        event_types = {forecast.event_type, error.event_type, update.event_type, binding.event_type}
        assert len(event_types) == 4  # All unique
