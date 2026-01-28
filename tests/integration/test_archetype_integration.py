"""
Integration tests for Archetype Integration (Track 002: Jungian Cognitive Archetypes)

Tests end-to-end archetype flow through ConsciousnessManager and related services.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.priors import (
    ArchetypePrior,
    get_default_archetype_priors,
    RESONANCE_THRESHOLD,
)
from api.models.autobiographical import JungianArchetype
from api.services.efe_engine import EFEEngine, get_efe_engine
from api.services.shadow_log_service import (
    ArchetypeShadowLog,
    get_archetype_shadow_log,
    reset_archetype_shadow_log,
)
from api.services.narrative_extraction_service import (
    NarrativeExtractionService,
    get_narrative_extraction_service,
)


class TestArchetypeEFEIntegration:
    """Tests for EFE-based archetype competition integration."""

    @pytest.fixture
    def efe_engine(self):
        return EFEEngine()

    @pytest.fixture
    def archetypes(self):
        return get_default_archetype_priors()

    def test_archetype_selection_warrior_content(self, efe_engine, archetypes):
        """WARRIOR should win for urgent/fix/battle content."""
        content = "urgent critical fix needed for this bug error"

        dominant, suppressed, scores = efe_engine.select_dominant_archetype(
            content=content,
            archetypes=archetypes,
        )

        assert dominant is not None
        assert dominant.archetype == "warrior"
        assert len(suppressed) == 11  # All others suppressed

    def test_archetype_selection_sage_content(self, efe_engine, archetypes):
        """SAGE should win for analysis/understand/why content."""
        content = "I need to understand and analyze why this happens"

        dominant, suppressed, scores = efe_engine.select_dominant_archetype(
            content=content,
            archetypes=archetypes,
        )

        assert dominant is not None
        assert dominant.archetype == "sage"

    def test_archetype_selection_creator_content(self, efe_engine, archetypes):
        """CREATOR should win for build/create/design content."""
        content = "let me build and create a new implementation design"

        dominant, suppressed, scores = efe_engine.select_dominant_archetype(
            content=content,
            archetypes=archetypes,
        )

        assert dominant is not None
        assert dominant.archetype == "creator"


class TestNarrativeToArchetypeFlow:
    """Tests for narrative → archetype evidence flow."""

    @pytest.fixture
    def narrative_service(self):
        return NarrativeExtractionService()

    @pytest.fixture
    def efe_engine(self):
        return EFEEngine()

    def test_narrative_evidence_to_precision_update(self, narrative_service, efe_engine):
        """Narrative evidence should update archetype precision."""
        # Create archetype prior
        sage_prior = ArchetypePrior(
            archetype="sage",
            dominant_attractor="cognitive_science",
            shadow="fool",
            precision=0.5,
        )

        # Extract evidence from sage-like content
        content = "The wise sage seeks wisdom and must understand truth deeply."
        evidence = narrative_service.extract_archetype_evidence(content)

        # Should find sage evidence
        sage_evidence = [e for e in evidence if e.archetype == "sage"]
        assert len(sage_evidence) > 0

        # Aggregate and update precision
        aggregated = narrative_service.aggregate_archetype_evidence(evidence)
        if "sage" in aggregated:
            new_precision = efe_engine.update_archetype_precision_bayesian(
                sage_prior,
                evidence_weight=aggregated["sage"],
                direction="increase",
            )
            assert new_precision > 0.5  # Precision increased

    def test_warrior_narrative_extraction(self, narrative_service):
        """WARRIOR patterns should extract from battle narrative."""
        content = "The hero must battle against the darkness and overcome every obstacle."

        evidence = narrative_service.extract_archetype_evidence(content)
        warrior_evidence = [e for e in evidence if e.archetype == "warrior"]

        assert len(warrior_evidence) > 0
        assert any(e.weight > 0.3 for e in warrior_evidence)


class TestSuppressionAndResonanceCycle:
    """Tests for suppression → shadow log → resonance cycle."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_archetype_shadow_log()

    @pytest.fixture
    def shadow_log(self):
        return get_archetype_shadow_log()

    @pytest.fixture
    def efe_engine(self):
        return EFEEngine()

    @pytest.fixture
    def archetypes(self):
        return get_default_archetype_priors()

    def test_suppression_to_shadow_log(self, efe_engine, archetypes, shadow_log):
        """Suppressed archetypes should be logged to shadow log."""
        content = "urgent critical fix needed"

        dominant, suppressed, scores = efe_engine.select_dominant_archetype(
            content=content,
            archetypes=archetypes,
        )

        # Log suppressions
        entries = shadow_log.log_suppressions_batch(
            suppressed_archetypes=suppressed,
            efe_scores=scores,
            context=content,
            basin=None,
            dominant_archetype=dominant.archetype,
        )

        assert len(entries) == 11  # 12 - 1 dominant
        assert shadow_log.size >= 11

    def test_resonance_after_suppressions(self, efe_engine, archetypes, shadow_log):
        """Resonance should trigger after high allostatic load with valid candidates."""
        # First cycle: warrior wins, sage is suppressed with low EFE
        content1 = "urgent critical fix needed"
        dominant1, suppressed1, scores1 = efe_engine.select_dominant_archetype(
            content=content1,
            archetypes=archetypes,
        )

        shadow_log.log_suppressions_batch(
            suppressed_archetypes=suppressed1,
            efe_scores=scores1,
            context=content1,
            basin=None,
            dominant_archetype=dominant1.archetype,
        )

        # Manually add a suppression with EFE below threshold for test reliability
        shadow_log.log_suppression(
            archetype="sage",
            efe_score=0.25,  # Below RESONANCE_ACTIVATION_EFE (0.4)
            context="forced low EFE for test",
            dominant_archetype="warrior",
        )

        # Check resonance with high load
        candidate = shadow_log.check_resonance(allostatic_load=0.85)

        # Should have a candidate (lowest EFE suppressed archetype)
        assert candidate is not None
        assert candidate.efe_score < 0.4  # Below RESONANCE_ACTIVATION_EFE

    def test_multi_cycle_archetype_tracking(self, efe_engine, archetypes, shadow_log):
        """Track archetype changes across multiple cycles."""
        contents = [
            "urgent critical fix needed for bug",  # WARRIOR
            "I need to understand and analyze why",  # SAGE
            "let me build and create new design",  # CREATOR
        ]

        history = []
        for content in contents:
            dominant, suppressed, scores = efe_engine.select_dominant_archetype(
                content=content,
                archetypes=archetypes,
            )
            history.append(dominant.archetype)

            shadow_log.log_suppressions_batch(
                suppressed_archetypes=suppressed,
                efe_scores=scores,
                context=content,
                basin=None,
                dominant_archetype=dominant.archetype,
            )

        assert history == ["warrior", "sage", "creator"]


class TestArchetypeBasinAlignment:
    """Tests for archetype → basin affinity alignment."""

    @pytest.fixture
    def archetypes(self):
        return get_default_archetype_priors()

    def test_archetype_basin_affinities(self, archetypes):
        """Each archetype should have basin affinity mappings."""
        for prior in archetypes:
            assert prior.dominant_attractor is not None
            assert len(prior.dominant_attractor) > 0

    def test_sage_cognitive_science_affinity(self, archetypes):
        """SAGE should have cognitive_science basin affinity."""
        sage = next((a for a in archetypes if a.archetype == "sage"), None)
        assert sage is not None
        assert sage.dominant_attractor == "cognitive_science"

    def test_warrior_systems_theory_affinity(self, archetypes):
        """WARRIOR should have systems_theory basin affinity."""
        warrior = next((a for a in archetypes if a.archetype == "warrior"), None)
        assert warrior is not None
        assert warrior.dominant_attractor == "systems_theory"


class TestConsciousnessManagerArchetypeState:
    """Tests for ConsciousnessManager archetype state tracking."""

    def test_archetype_state_initialization(self):
        """ConsciousnessManager should initialize archetype state."""
        from api.agents.consciousness_manager import ConsciousnessManager

        # We can't fully test without mocking LLM, but can check initialization
        manager = ConsciousnessManager.__new__(ConsciousnessManager)

        # Initialize only archetype-related attributes
        manager.current_archetype = None
        manager.archetype_history = []
        manager._efe_engine = get_efe_engine()
        manager._shadow_log = get_archetype_shadow_log()
        manager._archetype_priors = get_default_archetype_priors()

        assert manager.current_archetype is None
        assert manager.archetype_history == []
        assert len(manager._archetype_priors) == 12

    def test_update_archetype_state_method(self):
        """Test update_archetype_state method in isolation."""
        from api.agents.consciousness_manager import ConsciousnessManager

        manager = ConsciousnessManager.__new__(ConsciousnessManager)

        # Initialize archetype-related attributes
        manager.current_archetype = None
        manager.archetype_history = []
        manager._efe_engine = get_efe_engine()
        manager._shadow_log = get_archetype_shadow_log()
        manager._archetype_priors = get_default_archetype_priors()

        # Manually call update_archetype_state
        result = manager.update_archetype_state(
            content="urgent critical fix needed for bug",
            context={"test": True},
            allostatic_load=None,
        )

        assert result["dominant"] == "warrior"
        assert result["suppressed_count"] == 11
        assert manager.current_archetype.archetype == "warrior"
        assert len(manager.archetype_history) == 1

    def test_get_archetype_context_method(self):
        """Test get_archetype_context returns proper structure."""
        from api.agents.consciousness_manager import ConsciousnessManager

        manager = ConsciousnessManager.__new__(ConsciousnessManager)

        # Initialize archetype-related attributes
        manager.current_archetype = None
        manager.archetype_history = []
        manager._efe_engine = get_efe_engine()
        manager._shadow_log = get_archetype_shadow_log()
        manager._archetype_priors = get_default_archetype_priors()

        # First get context with no archetype set
        ctx = manager.get_archetype_context()
        assert ctx["current_archetype"] is None
        assert ctx["archetype_basin_affinity"] is None

        # Update archetype
        manager.update_archetype_state("analyze why this happens", {})

        # Get context after update
        ctx = manager.get_archetype_context()
        assert ctx["current_archetype"] == "sage"
        assert ctx["archetype_basin_affinity"] == "cognitive_science"
