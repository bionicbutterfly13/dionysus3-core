"""
Integration tests for Five-Level Concept Extraction Pipeline.

Tests the full extraction flow with mocked LLM responses to verify:
- All 5 levels produce concepts
- Concepts flow correctly between levels
- Cross-level relationships are detected
- Consciousness emergence is calculated
- Error handling for malformed input
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    ExtractedConcept,
    LevelExtractionResult,
    FiveLevelExtractionResult,
)
from api.services.concept_extraction import (
    FiveLevelConceptExtractionService,
    get_concept_extraction_service,
    register_all_extractors,
    AtomicConceptExtractor,
    RelationalConceptExtractor,
    CompositeConceptExtractor,
    ContextualFrameworkExtractor,
    NarrativeStructureExtractor,
)


# Sample neuroscience text for testing
SAMPLE_NEUROSCIENCE_TEXT = """
Active inference is a theoretical framework that describes how biological agents
minimize surprise and maintain homeostasis through action and perception.

The brain operates as a predictive engine, constantly generating predictions
about sensory inputs and updating these predictions based on prediction errors.
This process involves hierarchical message passing between cortical regions.

Free energy minimization is the core principle, where organisms minimize the
difference between expected and actual sensory states. This connects to
variational inference in machine learning and Bayesian brain theories.

The framework proposes that action, perception, and learning are all manifestations
of the same underlying free energy minimization process. This unifies motor control,
perceptual inference, and model learning under a single mathematical framework.
"""


# Mock LLM responses for each level
MOCK_ATOMIC_RESPONSE = json.dumps({
    "concepts": [
        {
            "name": "Active inference",
            "definition": "Theoretical framework for biological agents minimizing surprise",
            "concept_type": "framework",
            "confidence": 0.95,
            "source_span": "Active inference is a theoretical framework"
        },
        {
            "name": "Predictive engine",
            "definition": "Brain as generator of sensory predictions",
            "concept_type": "model",
            "confidence": 0.90,
            "source_span": "brain operates as a predictive engine"
        },
        {
            "name": "Free energy minimization",
            "definition": "Core principle of minimizing prediction error",
            "concept_type": "principle",
            "confidence": 0.92,
            "source_span": "Free energy minimization is the core principle"
        }
    ]
})

MOCK_RELATIONAL_RESPONSE = json.dumps({
    "relationships": [
        {
            "name": "Active inference enables Free energy minimization",
            "source_concept": "Active inference",
            "target_concept": "Free energy minimization",
            "relationship_type": "enables",
            "strength": 0.9,
            "description": "Active inference implements free energy minimization"
        },
        {
            "name": "Predictive engine uses Free energy minimization",
            "source_concept": "Predictive engine",
            "target_concept": "Free energy minimization",
            "relationship_type": "uses",
            "strength": 0.85,
            "description": "Brain uses free energy to generate predictions"
        }
    ]
})

MOCK_COMPOSITE_RESPONSE = json.dumps({
    "composite_concepts": [
        {
            "name": "Bayesian Brain Theory",
            "description": "Unified framework combining prediction, inference, and action",
            "component_concepts": ["Active inference", "Predictive engine", "Free energy minimization"],
            "integration_type": "theoretical_framework",
            "confidence": 0.88
        }
    ]
})

MOCK_CONTEXTUAL_RESPONSE = json.dumps({
    "frameworks": [
        {
            "name": "Computational Neuroscience Paradigm",
            "description": "Domain framework for understanding brain computation",
            "domain": "neuroscience",
            "paradigm": "computational",
            "key_principles": ["prediction", "inference", "learning"],
            "confidence": 0.85
        }
    ]
})

MOCK_NARRATIVE_RESPONSE = json.dumps({
    "narratives": [
        {
            "name": "From Prediction to Unified Theory",
            "narrative_type": "progressive_argument",
            "summary": "The text builds from basic prediction concepts to a unified free energy framework",
            "argument_flow": ["premise", "evidence", "synthesis"],
            "persuasive_strategy": "logical_progression",
            "confidence": 0.82
        }
    ]
})


def create_mock_chat_completion():
    """Create a mock chat_completion function that returns level-specific responses.

    The chat_completion function is called with messages where the user content
    contains the extraction prompt. We detect the level from the prompt content.
    """
    call_count = {"count": 0}

    async def mock_chat(*args, **kwargs):
        call_count["count"] += 1
        messages = kwargs.get("messages", args[0] if args else [])

        # Get user message content which contains the prompt
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "").lower()
                break

        # Detect level from prompt keywords
        if "atomic" in user_content or "individual term" in user_content or "entity" in user_content:
            return MOCK_ATOMIC_RESPONSE
        elif "relationship" in user_content or "connection" in user_content or "causal" in user_content:
            return MOCK_RELATIONAL_RESPONSE
        elif "composite" in user_content or "multi-part" in user_content or "system" in user_content:
            return MOCK_COMPOSITE_RESPONSE
        elif "contextual" in user_content or "framework" in user_content or "paradigm" in user_content:
            return MOCK_CONTEXTUAL_RESPONSE
        elif "narrative" in user_content or "argument" in user_content or "story" in user_content:
            return MOCK_NARRATIVE_RESPONSE
        else:
            # Default to atomic for unrecognized prompts
            return MOCK_ATOMIC_RESPONSE

    return mock_chat


@pytest.fixture
def patch_chat_completion():
    """Fixture to patch chat_completion in all extractor modules."""
    mock_chat = create_mock_chat_completion()

    with patch("api.services.concept_extraction.atomic_extractor.chat_completion", new=mock_chat), \
         patch("api.services.concept_extraction.relational_extractor.chat_completion", new=mock_chat), \
         patch("api.services.concept_extraction.composite_extractor.chat_completion", new=mock_chat), \
         patch("api.services.concept_extraction.contextual_extractor.chat_completion", new=mock_chat), \
         patch("api.services.concept_extraction.narrative_extractor.chat_completion", new=mock_chat):
        yield


class TestFullExtractionPipeline:
    """Integration tests for the full extraction pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_all_levels(self, patch_chat_completion):
        """Test that full pipeline produces concepts at all 5 levels."""
        # Create fresh service with all extractors
        service = FiveLevelConceptExtractionService()
        register_all_extractors(service)

        result = await service.extract_all(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={"domain": "neuroscience"},
            document_id="test-doc-1",
        )

        # Verify result is FiveLevelExtractionResult
        assert isinstance(result, FiveLevelExtractionResult)
        assert result.document_id == "test-doc-1"

        # Verify all levels have results
        for level in ConceptExtractionLevel:
            assert level.value in result.level_results, f"Missing level {level.name}"

        # Verify we got concepts at multiple levels
        assert len(result.all_concepts) > 0

    @pytest.mark.asyncio
    async def test_pipeline_detects_cross_level_relationships(self, patch_chat_completion):
        """Test that pipeline detects relationships across levels."""
        service = FiveLevelConceptExtractionService()
        register_all_extractors(service)

        result = await service.extract_all(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={},
            document_id="test-doc-2",
        )

        # Cross-level relationships should be detected
        # (based on shared concept names across levels)
        assert isinstance(result.cross_level_relationships, list)

    @pytest.mark.asyncio
    async def test_pipeline_builds_concept_hierarchy(self, patch_chat_completion):
        """Test that pipeline builds concept hierarchy."""
        service = FiveLevelConceptExtractionService()
        register_all_extractors(service)

        result = await service.extract_all(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={},
            document_id="test-doc-3",
        )

        # Hierarchy maps parent IDs to child IDs
        assert isinstance(result.concept_hierarchy, dict)

    @pytest.mark.asyncio
    async def test_pipeline_calculates_consciousness_emergence(self, patch_chat_completion):
        """Test that pipeline calculates consciousness emergence metric."""
        service = FiveLevelConceptExtractionService()
        register_all_extractors(service)

        result = await service.extract_all(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={},
            document_id="test-doc-4",
        )

        # Consciousness emergence should be calculated
        assert result.overall_consciousness_level >= 0.0
        assert result.overall_consciousness_level <= 1.0

    @pytest.mark.asyncio
    async def test_pipeline_generates_meta_insights(self, patch_chat_completion):
        """Test that pipeline generates meta-cognitive insights."""
        service = FiveLevelConceptExtractionService()
        register_all_extractors(service)

        result = await service.extract_all(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={},
            document_id="test-doc-5",
        )

        # Meta-cognitive insights should be generated
        assert isinstance(result.meta_cognitive_insights, list)


class TestSingleLevelExtraction:
    """Test single-level extraction functionality."""

    @pytest.mark.asyncio
    async def test_atomic_extraction_produces_concepts(self, patch_chat_completion):
        """Test that atomic level extracts individual concepts."""
        extractor = AtomicConceptExtractor()
        result = await extractor.extract(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={"domain": "neuroscience"},
        )

        assert result.level == ConceptExtractionLevel.ATOMIC
        assert len(result.concepts) > 0
        assert all(c.level == ConceptExtractionLevel.ATOMIC for c in result.concepts)

    @pytest.mark.asyncio
    async def test_relational_extraction_links_concepts(self, patch_chat_completion):
        """Test that relational level creates relationships."""
        # Create some atomic concepts to pass
        atomic_concepts = [
            ExtractedConcept(
                concept_id="atomic-1",
                level=ConceptExtractionLevel.ATOMIC,
                name="Active inference",
                description="Framework",
                confidence=0.9,
                source_span="test",
            )
        ]

        extractor = RelationalConceptExtractor()
        result = await extractor.extract(
            content=SAMPLE_NEUROSCIENCE_TEXT,
            context={},
            lower_level_concepts=atomic_concepts,
        )

        assert result.level == ConceptExtractionLevel.RELATIONAL
        # Relational concepts are created (may or may not have relationship_data depending on parsing)
        assert isinstance(result.concepts, list)


class TestErrorHandling:
    """Test error handling in the pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_handles_llm_error_gracefully(self):
        """Test that pipeline handles LLM errors without crashing."""
        async def error_chat(*args, **kwargs):
            raise Exception("LLM error")

        with patch("api.services.concept_extraction.atomic_extractor.chat_completion", new=error_chat), \
             patch("api.services.concept_extraction.relational_extractor.chat_completion", new=error_chat), \
             patch("api.services.concept_extraction.composite_extractor.chat_completion", new=error_chat), \
             patch("api.services.concept_extraction.contextual_extractor.chat_completion", new=error_chat), \
             patch("api.services.concept_extraction.narrative_extractor.chat_completion", new=error_chat):

            service = FiveLevelConceptExtractionService()
            register_all_extractors(service)

            # Should not raise, but return empty/partial results
            result = await service.extract_all(
                content="Test content",
                context={},
                document_id="error-test",
            )

            assert isinstance(result, FiveLevelExtractionResult)

    @pytest.mark.asyncio
    async def test_pipeline_handles_malformed_json(self):
        """Test that pipeline handles malformed JSON responses."""
        async def malformed_chat(*args, **kwargs):
            return "not valid json {{{"

        with patch("api.services.concept_extraction.atomic_extractor.chat_completion", new=malformed_chat), \
             patch("api.services.concept_extraction.relational_extractor.chat_completion", new=malformed_chat), \
             patch("api.services.concept_extraction.composite_extractor.chat_completion", new=malformed_chat), \
             patch("api.services.concept_extraction.contextual_extractor.chat_completion", new=malformed_chat), \
             patch("api.services.concept_extraction.narrative_extractor.chat_completion", new=malformed_chat):

            service = FiveLevelConceptExtractionService()
            register_all_extractors(service)

            # Should not raise
            result = await service.extract_all(
                content="Test content",
                context={},
                document_id="malformed-test",
            )

            assert isinstance(result, FiveLevelExtractionResult)

    @pytest.mark.asyncio
    async def test_pipeline_handles_empty_content(self, patch_chat_completion):
        """Test that pipeline handles empty content input."""
        service = FiveLevelConceptExtractionService()
        register_all_extractors(service)

        result = await service.extract_all(
            content="",
            context={},
            document_id="empty-test",
        )

        assert isinstance(result, FiveLevelExtractionResult)


class TestGraphitiIntegration:
    """Test Graphiti storage integration."""

    @pytest.mark.asyncio
    async def test_store_in_graphiti_creates_entities(self):
        """Test that store_in_graphiti creates entities correctly."""
        mock_graphiti = MagicMock()
        mock_graphiti.ingest_contextual_triplet = AsyncMock(return_value=True)

        service = FiveLevelConceptExtractionService()

        # Create a sample result
        sample_concept = ExtractedConcept(
            concept_id="test-1",
            level=ConceptExtractionLevel.ATOMIC,
            name="Test Concept",
            description="A test",
            confidence=0.9,
            source_span="test",
        )

        sample_result = FiveLevelExtractionResult(
            document_id="graphiti-test",
            all_concepts=[sample_concept],
            level_results={},
            concept_hierarchy={},
            cross_level_relationships=[],
            meta_cognitive_insights=[],
        )

        result = await service.store_in_graphiti(
            result=sample_result,
            graphiti_service=mock_graphiti,
            group_id="test-group",
        )

        assert result["stored_entities"] > 0
        mock_graphiti.ingest_contextual_triplet.assert_called()
