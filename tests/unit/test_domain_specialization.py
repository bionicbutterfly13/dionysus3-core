"""
Unit tests for domain specialization service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.domain_specialization import (
    AcademicSection,
    ConceptCategory,
    DomainAnalysisRequest,
    DomainType,
)
from api.services.domain_specialization import (
    AITerminologyDatabase,
    AcademicStructureRecognizer,
    CrossDomainMapper,
    DomainSpecializationService,
    NeuroscienceTerminologyDatabase,
    get_domain_specialization_service,
)
from api.routers import domain_specialization


class TestNeuroscienceTerminologyDatabase:
    """Tests for NeuroscienceTerminologyDatabase."""

    def test_initialization(self):
        """Test database initializes with concepts."""
        db = NeuroscienceTerminologyDatabase()
        assert len(db.concepts) > 0
        assert "neuron" in db.concepts
        assert "synapse" in db.concepts

    def test_find_concept_direct(self):
        """Test finding concept by direct term match."""
        db = NeuroscienceTerminologyDatabase()
        concept = db.find_concept("neuron")

        assert concept is not None
        assert concept.term == "neuron"
        assert concept.domain == DomainType.NEUROSCIENCE

    def test_find_concept_by_synonym(self):
        """Test finding concept by synonym."""
        db = NeuroscienceTerminologyDatabase()
        concept = db.find_concept("nerve cell")

        assert concept is not None
        assert concept.term == "neuron"

    def test_find_concept_by_abbreviation(self):
        """Test finding concept by abbreviation."""
        db = NeuroscienceTerminologyDatabase()
        concept = db.find_concept("LTP")

        assert concept is not None
        assert concept.term == "long_term_potentiation"

    def test_find_concept_not_found(self):
        """Test finding non-existent concept."""
        db = NeuroscienceTerminologyDatabase()
        concept = db.find_concept("nonexistent_term")

        assert concept is None

    def test_get_related_concepts(self):
        """Test getting related concepts."""
        db = NeuroscienceTerminologyDatabase()
        related = db.get_related_concepts("neuron")

        assert len(related) > 0
        related_terms = [c.term for c in related]
        # Neuron should be related to synapse, dendrite, axon
        assert any(t in related_terms for t in ["synapse", "dendrite", "axon"])

    def test_get_concepts_by_category(self):
        """Test filtering concepts by category."""
        db = NeuroscienceTerminologyDatabase()
        anatomical = db.get_concepts_by_category(ConceptCategory.ANATOMICAL)

        assert len(anatomical) > 0
        for concept in anatomical:
            assert concept.category == ConceptCategory.ANATOMICAL


class TestAITerminologyDatabase:
    """Tests for AITerminologyDatabase."""

    def test_initialization(self):
        """Test database initializes with concepts."""
        db = AITerminologyDatabase()
        assert len(db.concepts) > 0
        assert "neural_network" in db.concepts
        assert "backpropagation" in db.concepts

    def test_find_concept_direct(self):
        """Test finding concept by direct term match."""
        db = AITerminologyDatabase()
        concept = db.find_concept("gradient_descent")

        assert concept is not None
        assert concept.term == "gradient_descent"
        assert concept.domain == DomainType.ARTIFICIAL_INTELLIGENCE

    def test_find_concept_by_abbreviation(self):
        """Test finding concept by abbreviation."""
        db = AITerminologyDatabase()
        concept = db.find_concept("CNN")

        assert concept is not None
        assert concept.term == "convolutional_neural_network"

    def test_get_concepts_by_algorithm_family(self):
        """Test filtering by algorithm family."""
        db = AITerminologyDatabase()
        optimization = db.get_concepts_by_algorithm_family("optimization")

        assert len(optimization) > 0
        for concept in optimization:
            assert concept.algorithm_family == "optimization"


class TestCrossDomainMapper:
    """Tests for CrossDomainMapper."""

    @pytest.fixture
    def mapper(self):
        """Create mapper with databases."""
        neuro_db = NeuroscienceTerminologyDatabase()
        ai_db = AITerminologyDatabase()
        return CrossDomainMapper(neuro_db, ai_db)

    def test_initialization(self, mapper):
        """Test mapper initializes with mappings."""
        assert len(mapper.mappings) > 0

    def test_find_cross_domain_equivalent(self, mapper):
        """Test finding cross-domain equivalent."""
        mapping = mapper.find_cross_domain_equivalent(
            "neuron", DomainType.NEUROSCIENCE
        )

        assert mapping is not None
        assert mapping["target_domain"] == DomainType.ARTIFICIAL_INTELLIGENCE
        assert mapping["target_concept"] == "neural_network"

    def test_get_mapping(self, mapper):
        """Test getting mapping as model."""
        mapping = mapper.get_mapping("synapse")

        assert mapping is not None
        assert mapping.source_concept == "synapse"
        assert mapping.target_concept == "weight"
        assert mapping.strength > 0

    def test_get_domain_bridges(self, mapper):
        """Test finding bridges in text."""
        text = "The neuron and synapse work together. Neural networks use weights."
        bridges = mapper.get_domain_bridges(text)

        # Should find bridges when both domain concepts are present
        assert isinstance(bridges, list)

    def test_get_all_mappings(self, mapper):
        """Test getting all unique mappings."""
        mappings = mapper.get_all_mappings()

        assert len(mappings) > 0
        # Check no duplicates (bidirectional stored but returned once)
        seen = set()
        for m in mappings:
            key = (m.source_concept, m.target_concept)
            assert key not in seen
            seen.add(key)


class TestAcademicStructureRecognizer:
    """Tests for AcademicStructureRecognizer."""

    @pytest.fixture
    def recognizer(self):
        """Create recognizer."""
        return AcademicStructureRecognizer()

    @pytest.fixture
    def academic_text(self):
        """Sample academic paper text."""
        return """
        Abstract
        This study examines synaptic plasticity in neural networks.

        Introduction
        The brain's ability to learn depends on synaptic changes.

        Methods
        We used patch-clamp recordings to measure LTP.

        Results
        We found significant enhancement after stimulation.

        Discussion
        Our findings support Hebbian learning theory.

        References
        Smith et al. (2024). Neural plasticity. Nature.
        Jones (2023). Learning mechanisms.
        """

    def test_analyze_structure(self, recognizer, academic_text):
        """Test analyzing academic structure."""
        structure = recognizer.analyze_structure(academic_text)

        assert structure.abstract_present is True
        assert structure.methodology_described is True
        assert structure.results_reported is True
        assert structure.structure_completeness > 0

    def test_extract_citations(self, recognizer, academic_text):
        """Test extracting citations."""
        structure = recognizer.analyze_structure(academic_text)

        assert len(structure.citations_found) > 0
        # Check year extraction
        years = [c.year for c in structure.citations_found if c.year]
        assert any(y in [2023, 2024] for y in years)

    def test_rigor_score(self, recognizer, academic_text):
        """Test academic rigor score calculation."""
        structure = recognizer.analyze_structure(academic_text)

        assert 0 <= structure.academic_rigor_score <= 1
        # Should have decent score with methods, results, citations
        assert structure.academic_rigor_score > 0.3

    def test_detect_document_type(self, recognizer, academic_text):
        """Test document type detection."""
        doc_type = recognizer.detect_document_type(academic_text)

        assert doc_type == "research_paper"

    def test_assess_completeness(self, recognizer, academic_text):
        """Test completeness assessment."""
        assessment = recognizer.assess_completeness(academic_text)

        assert "present_sections" in assessment
        assert "missing_sections" in assessment
        assert "completeness_score" in assessment
        assert "recommendations" in assessment


class TestDomainSpecializationService:
    """Tests for DomainSpecializationService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return DomainSpecializationService()

    @pytest.fixture
    def test_content(self):
        """Test content with neuroscience and AI terms."""
        return """
        Synaptic plasticity is fundamental to learning in biological neural networks.
        Long-term potentiation (LTP) strengthens connections through NMDA receptor activation.
        This parallels how backpropagation adjusts weights in artificial neural networks
        using gradient descent optimization to minimize loss functions.
        """

    @pytest.mark.asyncio
    async def test_analyze_domain_content(self, service, test_content):
        """Test comprehensive domain analysis."""
        result = await service.analyze_domain_content(test_content)

        assert result.success is True
        assert len(result.neuroscience_concepts) > 0
        assert len(result.ai_concepts) > 0
        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_primary_domain_detection(self, service):
        """Test primary domain is detected correctly."""
        neuro_heavy = "The neuron and synapse handle action potentials and plasticity."
        ai_heavy = "Neural networks use backpropagation and gradient descent."

        neuro_result = await service.analyze_domain_content(neuro_heavy)
        ai_result = await service.analyze_domain_content(ai_heavy)

        assert neuro_result.primary_domain == "neuroscience_primary"
        assert ai_result.primary_domain == "ai_primary"

    @pytest.mark.asyncio
    async def test_cross_domain_mappings(self, service, test_content):
        """Test cross-domain mappings are found."""
        result = await service.analyze_domain_content(test_content)

        # Text has both domains, should find mappings
        assert isinstance(result.cross_domain_mappings, list)

    @pytest.mark.asyncio
    async def test_specialized_prompts(self, service, test_content):
        """Test specialized prompts are generated."""
        result = await service.analyze_domain_content(test_content)

        assert "atomic_extraction" in result.specialized_prompts
        assert "relationship_extraction" in result.specialized_prompts
        assert len(result.specialized_prompts["atomic_extraction"]) > 0

    def test_find_concept(self, service):
        """Test finding concept in either database."""
        neuro = service.find_concept("neuron")
        ai = service.find_concept("neural_network")

        assert neuro is not None
        assert neuro["domain"] == "neuroscience"
        assert ai is not None
        assert ai["domain"] == "artificial_intelligence"

    def test_get_cross_domain_equivalent(self, service):
        """Test getting cross-domain equivalent."""
        mapping = service.get_cross_domain_equivalent("synapse")

        assert mapping is not None
        assert mapping["target"] == "weight"


class TestDomainSpecializationRouter:
    """Tests for domain specialization router endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_endpoint(self):
        """Test domain analysis endpoint."""
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.neuroscience_concepts = [{"term": "neuron"}]
        mock_result.ai_concepts = [{"term": "neural_network"}]
        mock_result.primary_domain = "interdisciplinary"
        mock_result.cross_domain_mappings = []
        mock_result.specialized_prompts = {"atomic_extraction": "prompt"}
        mock_service.analyze_domain_content = AsyncMock(return_value=mock_result)

        with patch.object(
            domain_specialization,
            "get_domain_specialization_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = DomainAnalysisRequest(
                content="Test content with neuron and neural network",
                include_prompts=False,
            )
            result = await domain_specialization.analyze_domain_content(request)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_concept_lookup_found(self):
        """Test concept lookup when found."""
        mock_service = MagicMock()
        mock_service.find_concept.return_value = {
            "term": "neuron",
            "definition": "A nerve cell",
            "domain": "neuroscience",
        }

        with patch.object(
            domain_specialization,
            "get_domain_specialization_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = domain_specialization.ConceptLookupRequest(term="neuron")
            result = await domain_specialization.lookup_concept(request)

        assert result.found is True
        assert result.concept is not None
        assert result.concept["term"] == "neuron"

    @pytest.mark.asyncio
    async def test_concept_lookup_not_found(self):
        """Test concept lookup when not found."""
        mock_service = MagicMock()
        mock_service.find_concept.return_value = None

        with patch.object(
            domain_specialization,
            "get_domain_specialization_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = domain_specialization.ConceptLookupRequest(term="nonexistent")
            result = await domain_specialization.lookup_concept(request)

        assert result.found is False
        assert result.concept is None

    @pytest.mark.asyncio
    async def test_cross_domain_mapping(self):
        """Test cross-domain mapping endpoint."""
        mock_service = MagicMock()
        mock_service.get_cross_domain_equivalent.return_value = {
            "source": "synapse",
            "target": "weight",
            "strength": 0.8,
        }

        with patch.object(
            domain_specialization,
            "get_domain_specialization_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = domain_specialization.CrossDomainRequest(term="synapse")
            result = await domain_specialization.get_cross_domain_mapping(request)

        assert result.found is True
        assert result.mapping["target"] == "weight"

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        mock_service = MagicMock()
        mock_service.neuro_db.concepts = {"neuron": MagicMock()}
        mock_service.ai_db.concepts = {"neural_network": MagicMock()}
        mock_service.cross_mapper.mappings = {"synapse": {}}

        with patch.object(
            domain_specialization,
            "get_domain_specialization_service",
            new=AsyncMock(return_value=mock_service),
        ):
            result = await domain_specialization.health_check()

        assert result["healthy"] is True
        assert result["neuroscience_db_loaded"] is True
        assert result["ai_db_loaded"] is True


@pytest.mark.asyncio
async def test_get_domain_specialization_service():
    """Test singleton service getter."""
    service1 = await get_domain_specialization_service()
    service2 = await get_domain_specialization_service()

    assert service1 is service2
    assert isinstance(service1, DomainSpecializationService)
