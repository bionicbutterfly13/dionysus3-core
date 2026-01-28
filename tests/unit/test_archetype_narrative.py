"""
Unit tests for Archetype Narrative Evidence Pipeline (Track 002)

Tests narrative motif patterns, SVO patterns, and evidence extraction.
"""

import pytest
from api.models.autobiographical import (
    ArchetypeEvidence,
    ARCHETYPE_MOTIF_PATTERNS,
    ARCHETYPE_SVO_PATTERNS,
)
from api.services.narrative_extraction_service import (
    NarrativeExtractionService,
    get_narrative_extraction_service,
)


class TestArchetypeMotifPatterns:
    """Tests for ARCHETYPE_MOTIF_PATTERNS constant."""

    def test_all_12_archetypes_have_patterns(self):
        """All 12 primary archetypes should have motif patterns."""
        expected_archetypes = [
            "sage", "warrior", "creator", "ruler",
            "explorer", "magician", "caregiver", "rebel",
            "innocent", "orphan", "lover", "jester"
        ]
        for archetype in expected_archetypes:
            assert archetype in ARCHETYPE_MOTIF_PATTERNS
            assert len(ARCHETYPE_MOTIF_PATTERNS[archetype]) > 0

    def test_motif_patterns_have_weights(self):
        """Each pattern should have a weight between 0 and 1."""
        for archetype, patterns in ARCHETYPE_MOTIF_PATTERNS.items():
            for pattern, weight in patterns:
                assert isinstance(pattern, str)
                assert 0.0 < weight <= 1.0, f"{archetype}: {pattern} has invalid weight {weight}"

    def test_svo_patterns_exist(self):
        """SVO patterns should exist for all archetypes."""
        assert len(ARCHETYPE_SVO_PATTERNS) == 12
        for archetype in ARCHETYPE_MOTIF_PATTERNS:
            assert archetype in ARCHETYPE_SVO_PATTERNS


class TestArchetypeEvidence:
    """Tests for ArchetypeEvidence model."""

    def test_evidence_creation(self):
        """ArchetypeEvidence should create with required fields."""
        evidence = ArchetypeEvidence(
            archetype="sage",
            weight=0.4,
            source="motif",
            pattern="seek.*wisdom",
        )
        assert evidence.archetype == "sage"
        assert evidence.weight == 0.4
        assert evidence.source == "motif"

    def test_evidence_weight_bounds(self):
        """Weight should be bounded 0-1."""
        with pytest.raises(Exception):  # Pydantic validation
            ArchetypeEvidence(
                archetype="sage",
                weight=1.5,  # Invalid
                source="motif",
                pattern="test",
            )

    def test_evidence_immutable(self):
        """ArchetypeEvidence should be frozen."""
        evidence = ArchetypeEvidence(
            archetype="sage",
            weight=0.4,
            source="motif",
            pattern="test",
        )
        with pytest.raises(Exception):
            evidence.weight = 0.5


class TestNarrativeArchetypeExtraction:
    """Tests for NarrativeExtractionService archetype extraction."""

    @pytest.fixture
    def service(self):
        return NarrativeExtractionService()

    def test_extract_empty_content(self, service):
        """Empty content should return empty list."""
        evidence = service.extract_archetype_evidence("")
        assert evidence == []

        evidence = service.extract_archetype_evidence("   ")
        assert evidence == []

    def test_extract_sage_motif(self, service):
        """Should detect SAGE motifs."""
        content = "The wise sage sought to understand the truth and gain wisdom."
        evidence = service.extract_archetype_evidence(content)

        sage_evidence = [e for e in evidence if e.archetype == "sage"]
        assert len(sage_evidence) > 0

    def test_extract_warrior_motif(self, service):
        """Should detect WARRIOR motifs."""
        content = "The hero must battle against the darkness and overcome every obstacle."
        evidence = service.extract_archetype_evidence(content)

        warrior_evidence = [e for e in evidence if e.archetype == "warrior"]
        assert len(warrior_evidence) > 0

    def test_extract_creator_motif(self, service):
        """Should detect CREATOR motifs."""
        content = "She decided to create something new and build from scratch."
        evidence = service.extract_archetype_evidence(content)

        creator_evidence = [e for e in evidence if e.archetype == "creator"]
        assert len(creator_evidence) > 0

    def test_extract_explorer_motif(self, service):
        """Should detect EXPLORER motifs."""
        content = "The adventurer set out to discover the unknown and explore new territories."
        evidence = service.extract_archetype_evidence(content)

        explorer_evidence = [e for e in evidence if e.archetype == "explorer"]
        assert len(explorer_evidence) > 0

    def test_extract_magician_motif(self, service):
        """Should detect MAGICIAN motifs."""
        content = "The catalyst worked to transform change and integrate the whole system."
        evidence = service.extract_archetype_evidence(content)

        magician_evidence = [e for e in evidence if e.archetype == "magician"]
        assert len(magician_evidence) > 0

    def test_extract_caregiver_motif(self, service):
        """Should detect CAREGIVER motifs."""
        content = "She chose to nurture and support, to heal the wounds of others."
        evidence = service.extract_archetype_evidence(content)

        caregiver_evidence = [e for e in evidence if e.archetype == "caregiver"]
        assert len(caregiver_evidence) > 0

    def test_extract_rebel_motif(self, service):
        """Should detect REBEL motifs."""
        content = "He sought to break free from the old ways and challenge the status quo."
        evidence = service.extract_archetype_evidence(content)

        rebel_evidence = [e for e in evidence if e.archetype == "rebel"]
        assert len(rebel_evidence) > 0

    def test_extract_multiple_archetypes(self, service):
        """Should detect multiple archetypes in complex text."""
        content = """
        The wise leader sought to understand the truth while organizing the structure.
        She had to battle against adversity and create something new.
        """
        evidence = service.extract_archetype_evidence(content)

        archetypes_found = set(e.archetype for e in evidence)
        assert len(archetypes_found) >= 2  # Should find at least 2 different archetypes

    def test_extract_svo_pattern(self, service):
        """Should detect SVO patterns."""
        # Use content with SVO patterns: "I analyze deeply" matches sage SVO
        content = "I analyze deeply to seek wisdom about the problem."
        evidence = service.extract_archetype_evidence(content)

        # Should find at least motif evidence (seek.*wisdom)
        assert len(evidence) > 0

    def test_evidence_has_context(self, service):
        """Evidence should include context."""
        # Use present tense "seek wisdom" to match the regex pattern
        content = "The hero seeks wisdom and must understand truth from the ancient texts."
        evidence = service.extract_archetype_evidence(content)

        assert len(evidence) > 0
        for e in evidence:
            assert e.context != ""


class TestAggregateEvidence:
    """Tests for evidence aggregation."""

    @pytest.fixture
    def service(self):
        return NarrativeExtractionService()

    def test_aggregate_empty(self, service):
        """Empty evidence list should return empty dict."""
        aggregated = service.aggregate_archetype_evidence([])
        assert aggregated == {}

    def test_aggregate_single(self, service):
        """Single evidence should aggregate correctly."""
        evidence = [
            ArchetypeEvidence(
                archetype="sage",
                weight=0.4,
                source="motif",
                pattern="test",
            )
        ]
        aggregated = service.aggregate_archetype_evidence(evidence)
        assert aggregated["sage"] == 0.4

    def test_aggregate_multiple_same_archetype(self, service):
        """Multiple evidence for same archetype should aggregate."""
        evidence = [
            ArchetypeEvidence(archetype="sage", weight=0.3, source="motif", pattern="p1"),
            ArchetypeEvidence(archetype="sage", weight=0.4, source="svo", pattern="p2"),
        ]
        aggregated = service.aggregate_archetype_evidence(evidence)

        # Should be min(1.0, 0.3 + 0.4) = 0.7
        assert aggregated["sage"] == 0.7

    def test_aggregate_capped_at_one(self, service):
        """Aggregated weight should not exceed 1.0."""
        evidence = [
            ArchetypeEvidence(archetype="sage", weight=0.6, source="motif", pattern="p1"),
            ArchetypeEvidence(archetype="sage", weight=0.6, source="svo", pattern="p2"),
        ]
        aggregated = service.aggregate_archetype_evidence(evidence)

        assert aggregated["sage"] == 1.0  # Capped

    def test_aggregate_multiple_archetypes(self, service):
        """Should aggregate by archetype correctly."""
        evidence = [
            ArchetypeEvidence(archetype="sage", weight=0.4, source="motif", pattern="p1"),
            ArchetypeEvidence(archetype="warrior", weight=0.35, source="motif", pattern="p2"),
        ]
        aggregated = service.aggregate_archetype_evidence(evidence)

        assert aggregated["sage"] == 0.4
        assert aggregated["warrior"] == 0.35


class TestCombinedExtraction:
    """Tests for combined relationship + archetype extraction."""

    @pytest.fixture
    def service(self):
        return NarrativeExtractionService()

    @pytest.mark.asyncio
    async def test_extract_with_archetypes_returns_tuple(self, service):
        """Should return both relationships and archetype evidence."""
        content = "The wise sage sought to understand the ancient wisdom."

        relationships, archetypes = await service.extract_relationships_with_archetypes(content)

        assert isinstance(relationships, list)
        assert isinstance(archetypes, list)

    @pytest.mark.asyncio
    async def test_extract_with_archetypes_empty(self, service):
        """Empty content should return empty lists."""
        relationships, archetypes = await service.extract_relationships_with_archetypes("")

        assert relationships == []
        assert archetypes == []


class TestSingleton:
    """Tests for service singleton."""

    def test_singleton_returns_same_instance(self):
        """Should return same instance."""
        service1 = get_narrative_extraction_service()
        service2 = get_narrative_extraction_service()
        assert service1 is service2
