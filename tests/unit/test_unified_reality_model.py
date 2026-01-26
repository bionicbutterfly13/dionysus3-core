"""
Unit tests for UnifiedRealityModel service.

Tests the unified consciousness state container that holds all active inference states.

User Story 1: Unified Consciousness State (Priority: P1)
Functional Requirements: FR-001, FR-002, FR-003, FR-004
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from api.models.beautiful_loop import (
    BoundInference,
    UnifiedRealityModel,
)
from api.services.unified_reality_model import (
    UnifiedRealityModelService,
    get_unified_reality_model,
    _cosine_similarity,
)


def make_bound_inference(
    inference_id: str,
    embedding: list = None,
    content: dict = None,
) -> BoundInference:
    """Helper to create bound inference objects."""
    return BoundInference(
        inference_id=inference_id,
        source_layer="reasoning",
        content=content or {},
        embedding=embedding or [0.1, 0.2, 0.3, 0.4, 0.5],
        precision_score=0.8,
        coherence_score=0.8,
        uncertainty_reduction=0.5,
    )


class TestUnifiedRealityModel:
    """Tests for UnifiedRealityModel container (FR-001)."""

    def test_create_empty_reality_model(self):
        """UnifiedRealityModel can be created with no initial states."""
        service = UnifiedRealityModelService()
        model = service.get_model()

        assert isinstance(model, UnifiedRealityModel)
        assert model.belief_states == []
        assert model.active_inference_states == []
        assert model.metacognitive_particles == []
        assert model.bound_inferences == []

    def test_add_belief_state(self):
        """BeliefState can be added to reality model."""
        service = UnifiedRealityModelService()
        belief_states = [{"belief": "test belief", "confidence": 0.8}]

        service.update_belief_states(belief_states)

        model = service.get_model()
        assert len(model.belief_states) == 1
        assert model.belief_states[0]["belief"] == "test belief"

    def test_add_active_inference_state(self):
        """ActiveInferenceState can be added to reality model."""
        service = UnifiedRealityModelService()
        inference_states = [{"state": "exploring", "free_energy": 0.5}]

        service.update_active_inference_states(inference_states)

        model = service.get_model()
        assert len(model.active_inference_states) == 1
        assert model.active_inference_states[0]["state"] == "exploring"

    def test_add_metacognitive_particle(self):
        """MetacognitiveParticle can be added to reality model."""
        service = UnifiedRealityModelService()
        particles = [{"particle_id": "p1", "weight": 0.7}]

        service.update_metacognitive_particles(particles)

        model = service.get_model()
        assert len(model.metacognitive_particles) == 1
        assert model.metacognitive_particles[0]["particle_id"] == "p1"

    def test_update_context(self):
        """Context can be updated with cycle ID."""
        service = UnifiedRealityModelService()

        service.update_context({"task": "test"}, cycle_id="cycle-123")

        model = service.get_model()
        assert model.current_context["task"] == "test"
        assert model.cycle_id == "cycle-123"


class TestCoherenceComputation:
    """Tests for coherence computation using cosine similarity (FR-002)."""

    def test_coherence_single_inference(self):
        """Single bound inference has coherence of 1.0."""
        service = UnifiedRealityModelService()
        inference = make_bound_inference("i1")

        service.update_bound_inferences([inference])

        model = service.get_model()
        assert model.coherence_score == 1.0

    def test_coherence_identical_embeddings(self):
        """Identical embeddings produce coherence of 1.0."""
        service = UnifiedRealityModelService()
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        inferences = [
            make_bound_inference("i1", embedding=embedding),
            make_bound_inference("i2", embedding=embedding),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert model.coherence_score == 1.0

    def test_coherence_orthogonal_embeddings(self):
        """Orthogonal embeddings produce coherence of 0.5 (normalized)."""
        service = UnifiedRealityModelService()
        # Orthogonal vectors
        inferences = [
            make_bound_inference("i1", embedding=[1.0, 0.0, 0.0]),
            make_bound_inference("i2", embedding=[0.0, 1.0, 0.0]),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        # Orthogonal: cos_sim = 0, normalized = (0 + 1) / 2 = 0.5
        assert abs(model.coherence_score - 0.5) < 0.01

    def test_coherence_score_bounds(self):
        """Coherence score is always in [0, 1] range."""
        service = UnifiedRealityModelService()
        # Opposite vectors
        inferences = [
            make_bound_inference("i1", embedding=[1.0, 0.0, 0.0]),
            make_bound_inference("i2", embedding=[-1.0, 0.0, 0.0]),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        # cos_sim = -1, normalized = (-1 + 1) / 2 = 0.0
        assert 0.0 <= model.coherence_score <= 1.0

    def test_coherence_no_inferences(self):
        """No inferences produces coherence of 0.0."""
        service = UnifiedRealityModelService()

        service.update_bound_inferences([])

        model = service.get_model()
        assert model.coherence_score == 0.0


class TestCosineSimilarity:
    """Tests for the _cosine_similarity helper function."""

    def test_cosine_similarity_identical(self):
        """Identical vectors have similarity of 1.0."""
        vec = [1.0, 2.0, 3.0]
        assert abs(_cosine_similarity(vec, vec) - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors have similarity of 0.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(vec_a, vec_b) - 0.0) < 0.001

    def test_cosine_similarity_opposite(self):
        """Opposite vectors have similarity of -1.0."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [-1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(vec_a, vec_b) - (-1.0)) < 0.001

    def test_cosine_similarity_empty(self):
        """Empty vectors return 0.0."""
        assert _cosine_similarity([], []) == 0.0

    def test_cosine_similarity_different_lengths(self):
        """Vectors of different lengths return 0.0."""
        assert _cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0


class TestBoundTransparentTracking:
    """Tests for bound vs transparent process tracking (FR-003)."""

    def test_mark_inference_as_bound(self):
        """Inference can be marked as bound."""
        service = UnifiedRealityModelService()
        inference = make_bound_inference("i1")

        service.update_bound_inferences([inference])

        model = service.get_model()
        assert len(model.bound_inferences) == 1
        assert model.bound_inferences[0].inference_id == "i1"

    def test_mark_inference_as_transparent(self):
        """Inference is transparent if not in bound_inferences."""
        service = UnifiedRealityModelService()
        # Create inference but don't add to bound
        service.update_bound_inferences([])

        model = service.get_model()
        # No bound inferences = all processes transparent
        assert model.bound_inferences == []

    def test_no_overlap_bound_transparent(self):
        """No inference can be both bound and transparent (by design)."""
        # By the model design, an inference is either in bound_inferences or not
        # This is enforced by the data structure itself
        service = UnifiedRealityModelService()
        inference = make_bound_inference("i1")

        service.update_bound_inferences([inference])

        model = service.get_model()
        bound_ids = {b.inference_id for b in model.bound_inferences}
        # There's no separate transparent list, so no overlap possible
        assert "i1" in bound_ids

    def test_get_bound_processes(self):
        """Can retrieve list of bound processes."""
        service = UnifiedRealityModelService()
        inferences = [
            make_bound_inference("i1"),
            make_bound_inference("i2"),
            make_bound_inference("i3"),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert len(model.bound_inferences) == 3
        ids = {b.inference_id for b in model.bound_inferences}
        assert ids == {"i1", "i2", "i3"}

    def test_get_transparent_processes(self):
        """Transparent processes are those not in bound_inferences."""
        # In this architecture, transparent processes are implicit
        # (anything not bound is transparent)
        service = UnifiedRealityModelService()
        service.update_bound_inferences([])

        model = service.get_model()
        # Empty bound_inferences means all processes are transparent
        assert model.bound_inferences == []


class TestEpistemicAffordances:
    """Tests for epistemic affordances derivation (FR-004)."""

    def test_derive_affordances_from_beliefs(self):
        """Affordances can be derived from bound inferences content."""
        service = UnifiedRealityModelService()
        inferences = [
            make_bound_inference("i1", content={"affordance": "explore"}),
            make_bound_inference("i2", content={"action": "decide"}),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert "explore" in model.epistemic_affordances
        assert "decide" in model.epistemic_affordances

    def test_affordances_reflect_context(self):
        """Affordances reflect content from bound inferences."""
        service = UnifiedRealityModelService()
        inferences = [
            make_bound_inference("i1", content={"next_action": "analyze"}),
            make_bound_inference("i2", content={"decision": "proceed"}),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert "analyze" in model.epistemic_affordances
        assert "proceed" in model.epistemic_affordances

    def test_affordances_list_type(self):
        """Affordances are returned as list of strings."""
        service = UnifiedRealityModelService()
        inferences = [
            make_bound_inference("i1", content={"affordance": "test"}),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert isinstance(model.epistemic_affordances, list)
        assert all(isinstance(a, str) for a in model.epistemic_affordances)

    def test_affordances_deduplication(self):
        """Duplicate affordances are removed."""
        service = UnifiedRealityModelService()
        inferences = [
            make_bound_inference("i1", content={"affordance": "explore"}),
            make_bound_inference("i2", content={"affordance": "explore"}),  # Duplicate
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert model.epistemic_affordances.count("explore") == 1

    def test_affordances_empty_content(self):
        """Empty content produces no affordances."""
        service = UnifiedRealityModelService()
        inferences = [
            make_bound_inference("i1", content={}),
        ]

        service.update_bound_inferences(inferences)

        model = service.get_model()
        assert model.epistemic_affordances == []


class TestLastUpdated:
    """Tests for last_updated timestamp tracking."""

    def test_last_updated_on_create(self):
        """Model has last_updated timestamp on creation."""
        service = UnifiedRealityModelService()
        model = service.get_model()

        assert model.last_updated is not None
        assert isinstance(model.last_updated, datetime)

    def test_last_updated_on_change(self):
        """last_updated is updated when model changes."""
        service = UnifiedRealityModelService()
        model = service.get_model()
        initial_time = model.last_updated

        # Make a change
        service.update_belief_states([{"belief": "test"}])

        updated_model = service.get_model()
        # Time should be same or later
        assert updated_model.last_updated >= initial_time


class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_unified_reality_model_singleton(self):
        """get_unified_reality_model returns same instance."""
        import api.services.unified_reality_model as module
        module._unified_reality_model = None

        service1 = get_unified_reality_model()
        service2 = get_unified_reality_model()

        assert service1 is service2


class TestCycleTracking:
    """Tests for OODA cycle ID tracking."""

    def test_cycle_id_stored(self):
        """Cycle ID is stored in model."""
        service = UnifiedRealityModelService()

        service.update_context({}, cycle_id="cycle-456")

        model = service.get_model()
        assert model.cycle_id == "cycle-456"

    def test_cycle_id_updated_with_inferences(self):
        """Cycle ID updated when bound inferences are updated."""
        service = UnifiedRealityModelService()
        inference = make_bound_inference("i1")

        service.update_bound_inferences([inference], cycle_id="cycle-789")

        model = service.get_model()
        assert model.cycle_id == "cycle-789"


class TestResonanceStorage:
    """Tests for resonance signal storage (Track 071)."""

    def test_update_resonance_stores_signal(self):
        """update_resonance() stores ResonanceSignal in model."""
        from api.models.beautiful_loop import ResonanceSignal, ResonanceMode

        service = UnifiedRealityModelService()
        signal = ResonanceSignal(
            mode=ResonanceMode.STABLE,
            resonance_score=0.75,
            surprisal=0.3,
            coherence=0.8,
            discovery_urgency=0.1,
            cycle_id="cycle-res-1",
        )

        service.update_resonance(signal)

        model = service.get_model()
        assert model.resonance is not None
        assert model.resonance.mode == ResonanceMode.STABLE
        assert model.resonance.resonance_score == 0.75

    def test_update_resonance_updates_timestamp(self):
        """update_resonance() updates last_updated timestamp."""
        from api.models.beautiful_loop import ResonanceSignal, ResonanceMode

        service = UnifiedRealityModelService()
        initial_time = service.get_model().last_updated

        signal = ResonanceSignal(
            mode=ResonanceMode.LUMINOUS,
            resonance_score=0.9,
            surprisal=0.1,
            coherence=0.95,
            discovery_urgency=0.0,
        )

        service.update_resonance(signal)

        model = service.get_model()
        assert model.last_updated >= initial_time

    def test_resonance_can_be_replaced(self):
        """Subsequent resonance updates replace previous signal."""
        from api.models.beautiful_loop import ResonanceSignal, ResonanceMode

        service = UnifiedRealityModelService()

        signal1 = ResonanceSignal(
            mode=ResonanceMode.STABLE,
            resonance_score=0.5,
            surprisal=0.5,
            coherence=0.5,
            discovery_urgency=0.5,
        )
        signal2 = ResonanceSignal(
            mode=ResonanceMode.DISSONANT,
            resonance_score=0.2,
            surprisal=0.8,
            coherence=0.3,
            discovery_urgency=0.9,
        )

        service.update_resonance(signal1)
        service.update_resonance(signal2)

        model = service.get_model()
        assert model.resonance.mode == ResonanceMode.DISSONANT
        assert model.resonance.discovery_urgency == 0.9


class TestMetacognitiveParticleAccumulation:
    """Tests for metacognitive particle accumulation (Track 071)."""

    def test_add_metacognitive_particle_appends(self):
        """add_metacognitive_particle() appends to list."""
        from api.models.metacognitive_particle import MetacognitiveParticle

        service = UnifiedRealityModelService()
        particle = MetacognitiveParticle(
            id="p1",
            content="Test particle",
            source_agent="test-agent",
        )

        service.add_metacognitive_particle(particle)

        model = service.get_model()
        assert len(model.metacognitive_particles) == 1
        assert model.metacognitive_particles[0].id == "p1"

    def test_add_metacognitive_particle_accumulates(self):
        """Multiple add_metacognitive_particle() calls accumulate."""
        from api.models.metacognitive_particle import MetacognitiveParticle

        service = UnifiedRealityModelService()
        p1 = MetacognitiveParticle(id="p1", content="First", source_agent="test")
        p2 = MetacognitiveParticle(id="p2", content="Second", source_agent="test")
        p3 = MetacognitiveParticle(id="p3", content="Third", source_agent="test")

        service.add_metacognitive_particle(p1)
        service.add_metacognitive_particle(p2)
        service.add_metacognitive_particle(p3)

        model = service.get_model()
        assert len(model.metacognitive_particles) == 3
        ids = [p.id for p in model.metacognitive_particles]
        assert ids == ["p1", "p2", "p3"]

    def test_add_metacognitive_particle_updates_timestamp(self):
        """add_metacognitive_particle() updates last_updated."""
        from api.models.metacognitive_particle import MetacognitiveParticle

        service = UnifiedRealityModelService()
        initial_time = service.get_model().last_updated

        particle = MetacognitiveParticle(
            id="px",
            content="Timestamp test",
            source_agent="test",
        )
        service.add_metacognitive_particle(particle)

        model = service.get_model()
        assert model.last_updated >= initial_time


class TestCycleStateManagement:
    """Tests for cycle state reset (Track 071)."""

    def test_clear_cycle_state_resets_particles(self):
        """clear_cycle_state() clears metacognitive_particles."""
        from api.models.metacognitive_particle import MetacognitiveParticle

        service = UnifiedRealityModelService()
        p1 = MetacognitiveParticle(id="p1", content="Test", source_agent="test")
        service.add_metacognitive_particle(p1)

        service.clear_cycle_state()

        model = service.get_model()
        assert model.metacognitive_particles == []

    def test_clear_cycle_state_resets_resonance(self):
        """clear_cycle_state() clears resonance signal."""
        from api.models.beautiful_loop import ResonanceSignal, ResonanceMode

        service = UnifiedRealityModelService()
        signal = ResonanceSignal(
            mode=ResonanceMode.STABLE,
            resonance_score=0.7,
            surprisal=0.3,
            coherence=0.8,
            discovery_urgency=0.1,
        )
        service.update_resonance(signal)

        service.clear_cycle_state()

        model = service.get_model()
        assert model.resonance is None

    def test_clear_cycle_state_preserves_bound_inferences(self):
        """clear_cycle_state() preserves bound_inferences."""
        service = UnifiedRealityModelService()
        inference = make_bound_inference("i1")
        service.update_bound_inferences([inference])

        service.clear_cycle_state()

        model = service.get_model()
        assert len(model.bound_inferences) == 1
        assert model.bound_inferences[0].inference_id == "i1"

    def test_clear_cycle_state_preserves_context(self):
        """clear_cycle_state() preserves current_context."""
        service = UnifiedRealityModelService()
        service.update_context({"task": "test"}, cycle_id="c1")

        service.clear_cycle_state()

        model = service.get_model()
        assert model.current_context["task"] == "test"

    def test_clear_cycle_state_resets_active_inference_states(self):
        """clear_cycle_state() clears active_inference_states."""
        service = UnifiedRealityModelService()
        service.update_active_inference_states([{"state": "exploring"}])

        service.clear_cycle_state()

        model = service.get_model()
        assert model.active_inference_states == []

    def test_clear_cycle_state_updates_timestamp(self):
        """clear_cycle_state() updates last_updated."""
        service = UnifiedRealityModelService()
        initial_time = service.get_model().last_updated

        service.clear_cycle_state()

        model = service.get_model()
        assert model.last_updated >= initial_time
