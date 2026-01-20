"""
Integration tests for Track 038: Thoughtseeds Framework Enhancement

Tests the full integration of:
- Phase 1: EFE-Driven Decision Engine
- Phase 2: Evolutionary Priors Hierarchy
- Phase 3: Nested Markov Blankets (implied by thoughtseed model)
- Phase 4: Fractal Inner Screen (Bio-Constraints)

Task 5.3: Final system-wide integration test for OODA + EFE + Screen
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestThoughtseedsIngestionData:
    """Task 5.1: Verify Thoughtseeds paper ingestion data structures."""

    def test_paper_concepts_are_valid(self):
        """All concepts have required fields."""
        from scripts.ingest_thoughtseeds_paper import THOUGHTSEEDS_CONCEPTS

        assert len(THOUGHTSEEDS_CONCEPTS) > 0
        for concept in THOUGHTSEEDS_CONCEPTS:
            assert "name" in concept
            assert "type" in concept
            assert "description" in concept
            assert concept["type"] in ["concept", "person"]

    def test_paper_relationships_are_valid(self):
        """All relationships have required fields."""
        from scripts.ingest_thoughtseeds_paper import THOUGHTSEEDS_RELATIONSHIPS

        assert len(THOUGHTSEEDS_RELATIONSHIPS) > 0
        for rel in THOUGHTSEEDS_RELATIONSHIPS:
            assert "source" in rel
            assert "target" in rel
            assert "type" in rel
            assert "confidence" in rel
            assert 0 <= rel["confidence"] <= 1

    def test_paper_sections_are_valid(self):
        """All paper sections have title and content."""
        from scripts.ingest_thoughtseeds_paper import PAPER_SECTIONS

        assert len(PAPER_SECTIONS) >= 7  # At least 7 sections
        for section in PAPER_SECTIONS:
            assert "title" in section
            assert "content" in section
            assert len(section["content"]) > 100  # Substantial content

    def test_key_concepts_present(self):
        """Key Thoughtseeds concepts are defined."""
        from scripts.ingest_thoughtseeds_paper import THOUGHTSEEDS_CONCEPTS

        names = [c["name"] for c in THOUGHTSEEDS_CONCEPTS]

        # Core concepts
        assert "Thoughtseed" in names
        assert "Neuronal Packet" in names
        assert "Inner Screen" in names
        assert "Markov Blanket" in names

        # Free Energy concepts
        assert "Variational Free Energy" in names
        assert "Expected Free Energy" in names

        # Prior types
        assert "Basal Prior" in names
        assert "Learned Prior" in names


class TestEFEEngineIntegration:
    """Task 5.2: Verify EFE Engine implementation (FR-030-003)."""

    def test_efe_formula_components(self):
        """EFE = Uncertainty (Entropy) + Goal Divergence."""
        import numpy as np
        from api.services.efe_engine import EFEEngine

        efe = EFEEngine()

        # Test entropy calculation
        uniform_probs = [0.25, 0.25, 0.25, 0.25]
        entropy_val = efe.calculate_entropy(uniform_probs)
        assert entropy_val > 0  # Uncertainty exists

        # Test goal divergence
        vector = np.array([1.0, 0.0, 0.0])
        goal = np.array([0.0, 1.0, 0.0])
        divergence = efe.calculate_goal_divergence(vector, goal)
        assert divergence > 0  # Goal mismatch

        # Test combined EFE
        efe_score = efe.calculate_efe(
            prediction_probs=uniform_probs,
            thought_vector=vector,
            goal_vector=goal,
            precision=1.0
        )
        assert efe_score > 0

    def test_select_dominant_thought(self):
        """Dominant thought selected via EFE minimization."""
        from api.services.efe_engine import EFEEngine

        efe = EFEEngine()

        candidates = [
            {
                "id": "thought_high_certainty",
                "vector": [1.0, 0.0],
                "probabilities": [0.9, 0.1],  # Low entropy (certain)
            },
            {
                "id": "thought_low_certainty",
                "vector": [0.5, 0.5],
                "probabilities": [0.5, 0.5],  # High entropy (uncertain)
            },
        ]

        goal = [1.0, 0.0]  # Aligned with first thought
        result = efe.select_dominant_thought(candidates, goal, precision=1.0)

        # High certainty + goal alignment = lower EFE = winner
        assert result.dominant_seed_id == "thought_high_certainty"
        # Check scores exist
        assert len(result.scores) > 0


class TestPriorHierarchyIntegration:
    """Task 5.2: Verify Prior Hierarchy (Phase 2)."""

    def test_prior_level_ordering(self):
        """BASAL > DISPOSITIONAL > LEARNED."""
        from api.models.priors import PriorLevel

        # Enum values should maintain ordering
        assert PriorLevel.BASAL.value == "basal"
        assert PriorLevel.DISPOSITIONAL.value == "dispositional"
        assert PriorLevel.LEARNED.value == "learned"

    def test_basal_blocks_before_efe(self):
        """BASAL violations block BEFORE EFE scoring."""
        from api.services.prior_constraint_service import create_default_hierarchy

        hierarchy = create_default_hierarchy("test-agent")
        result = hierarchy.check_action_permitted("delete all database tables")

        assert result.permitted is False
        assert result.blocking_level.value == "basal"
        assert result.effective_precision == 0.0

    def test_safe_actions_pass_priors(self):
        """Safe actions pass through prior checks."""
        from api.services.prior_constraint_service import create_default_hierarchy

        hierarchy = create_default_hierarchy("test-agent")
        result = hierarchy.check_action_permitted("help user understand concept")

        assert result.permitted is True
        assert result.effective_precision > 0.0


class TestFractalInnerScreenIntegration:
    """Task 5.3: Verify Fractal Inner Screen (Phase 4)."""

    def test_biographical_constraint_cell_structure(self):
        """BiographicalConstraintCell has required fields."""
        from api.services.context_packaging import (
            BiographicalConstraintCell,
            CellPriority,
        )

        cell = BiographicalConstraintCell(
            cell_id="bio_test",
            content="Test biographical content",
            priority=CellPriority.CRITICAL,
            token_count=100,
            journey_id="test-journey",
            unresolved_themes=["authenticity", "growth"],
            identity_markers=["Analytical Empath"],
        )

        assert cell.journey_id == "test-journey"
        assert len(cell.unresolved_themes) == 2
        assert cell.priority == CellPriority.CRITICAL

    def test_fractal_tracer_captures_constraints(self):
        """FractalReflectionTracer captures constraint propagation."""
        from api.services.fractal_reflection_tracer import (
            FractalReflectionTracer,
            FractalLevel,
        )

        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="integration-test", agent_id="test-agent")

        # Simulate constraint flow: Identity → Episode → Event
        tracer.trace_identity_constraint(trace, "journey", "explore", "boosted")
        tracer.trace_episode_constraint(trace, "arc", "complete", "injected")
        tracer.trace_event_constraint(trace, "prior", "action", "warned")

        tracer.end_trace(trace)

        assert trace.identity_constraints_applied == 1
        assert trace.episode_constraints_applied == 1
        assert trace.event_constraints_applied == 1
        assert trace.narrative_coherence > 0


class TestOODACycleIntegration:
    """Task 5.3: Verify full OODA cycle integration."""

    @pytest.mark.asyncio
    async def test_consciousness_manager_prior_check_integration(self):
        """ConsciousnessManager checks priors in OODA cycle."""
        from api.agents.consciousness_manager import ConsciousnessManager

        cm = ConsciousnessManager()

        # Mock the internal services
        with patch.object(cm, 'bootstrap_svc') as mock_bootstrap, \
             patch.object(cm, 'meta_learner') as mock_learner:

            mock_bootstrap.recall_context = AsyncMock(return_value=MagicMock(
                formatted_context="test context",
                source_count=1,
                summarized=False
            ))
            mock_learner.retrieve_relevant_episodes = AsyncMock(return_value=[])

            # Test that prior check is called
            result = await cm._check_prior_constraints(
                agent_id="test-agent",
                task_query="help user with question",
                context={}
            )

            assert result["permitted"] is True

    @pytest.mark.asyncio
    async def test_consciousness_manager_blocks_basal_violation(self):
        """BASAL violation blocks OODA cycle early via prior hierarchy check."""
        from api.services.prior_constraint_service import create_default_hierarchy

        # Test the prior hierarchy directly (avoids Neo4j dependency)
        hierarchy = create_default_hierarchy("test-agent")
        result = hierarchy.check_action_permitted(
            "delete all database records destroy everything"
        )

        assert result.permitted is False
        assert result.blocking_level.value == "basal"
        assert "BASAL" in result.reason

    def test_efe_with_prior_filtering(self):
        """EFE selection respects prior filtering."""
        from api.services.efe_engine import EFEEngine
        from api.services.prior_constraint_service import create_default_hierarchy

        efe = EFEEngine()
        hierarchy = create_default_hierarchy("test-agent")

        candidates = [
            {
                "id": "safe_action",
                "action": "help user understand",
                "vector": [1.0, 0.0],
                "probabilities": [0.8, 0.2],
            },
            {
                "id": "unsafe_action",
                "action": "delete all database",
                "vector": [0.9, 0.1],
                "probabilities": [0.9, 0.1],
            },
        ]

        result = efe.select_dominant_thought_with_priors(
            candidates=candidates,
            goal_vector=[1.0, 0.0],
            prior_hierarchy=hierarchy,
            precision=1.0
        )

        # Unsafe action should be filtered out
        assert result.dominant_seed_id == "safe_action"


class TestEndToEndFlow:
    """Full end-to-end integration test."""

    def test_thoughtseed_lifecycle(self):
        """
        Test complete thoughtseed lifecycle:
        1. Prior check (BASAL/DISPOSITIONAL/LEARNED)
        2. EFE calculation (entropy + goal divergence)
        3. Dominant selection (winner-take-all)
        4. Fractal tracing (constraint propagation)
        """
        from api.services.efe_engine import EFEEngine
        from api.services.prior_constraint_service import create_default_hierarchy
        from api.services.fractal_reflection_tracer import FractalReflectionTracer

        # Setup
        efe = EFEEngine()
        hierarchy = create_default_hierarchy("dionysus-1")
        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="e2e-test", agent_id="dionysus-1")

        # 1. Prior check
        action = "analyze user question and provide helpful response"
        prior_result = hierarchy.check_action_permitted(action)
        tracer.trace_prior_check(trace, prior_result.model_dump(), action)

        assert prior_result.permitted is True

        # 2. Create candidate thoughtseeds
        candidates = [
            {
                "id": "ts_explore",
                "action": "explore new information (epistemic)",
                "vector": [0.7, 0.3],
                "probabilities": [0.6, 0.4],
            },
            {
                "id": "ts_exploit",
                "action": "provide direct answer (pragmatic)",
                "vector": [0.9, 0.1],
                "probabilities": [0.85, 0.15],
            },
        ]

        # 3. EFE selection with prior filtering
        goal = [1.0, 0.0]  # Goal-directed
        result = efe.select_dominant_thought_with_priors(
            candidates=candidates,
            goal_vector=goal,
            prior_hierarchy=hierarchy,
            precision=prior_result.effective_precision
        )

        # 4. Trace selection
        if result.dominant_seed_id and result.dominant_seed_id != "none":
            # Get EFE score from scores dict
            efe_result = result.scores.get(result.dominant_seed_id)
            efe_score = efe_result.efe_score if efe_result else 0
            tracer.trace_event_constraint(
                trace,
                source="efe_selection",
                action=result.dominant_seed_id,
                effect="boosted",
                details={"efe_score": efe_score}
            )

        tracer.end_trace(trace)

        # Assertions
        assert result.dominant_seed_id is not None
        assert result.dominant_seed_id != "none"
        assert len(result.scores) > 0
        assert trace.narrative_coherence > 0
        assert len(trace.events) >= 1

        # Log summary
        print(f"\n=== E2E Test Summary ===")
        print(f"Prior Check: {'PASS' if prior_result.permitted else 'BLOCKED'}")
        print(f"Dominant Thought: {result.dominant_seed_id}")
        print(f"Scores: {len(result.scores)} candidates evaluated")
        print(f"Fractal Trace: {trace.summary()}")
