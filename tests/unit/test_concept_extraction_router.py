"""
Unit tests for the concept extraction router.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    ExtractedConcept,
    LevelExtractionResult,
    FiveLevelExtractionResult,
)
from api.routers import concept_extraction


@pytest.fixture
def sample_concept():
    """Create a sample extracted concept."""
    return ExtractedConcept(
        concept_id="concept-1",
        level=ConceptExtractionLevel.ATOMIC,
        name="Test Concept",
        description="A test concept",
        confidence=0.95,
        source_span="test content",
    )


@pytest.fixture
def sample_level_result(sample_concept):
    """Create a sample level extraction result."""
    return LevelExtractionResult(
        level=ConceptExtractionLevel.ATOMIC,
        concepts=[sample_concept],
        extraction_time=0.5,
        content_length=100,
    )


@pytest.fixture
def sample_full_result(sample_concept, sample_level_result):
    """Create a sample full extraction result."""
    return FiveLevelExtractionResult(
        document_id="doc-1",
        all_concepts=[sample_concept],
        level_results={
            ConceptExtractionLevel.ATOMIC.value: sample_level_result,
        },
        concept_hierarchy={sample_concept.concept_id: []},
        cross_level_relationships=[],
        meta_cognitive_insights=[{"key": "test", "value": "insight"}],
        total_processing_time=1.0,
        overall_consciousness_level=0.8,
    )


class TestExtractEndpoint:
    """Tests for extract_concepts endpoint function."""

    @pytest.mark.asyncio
    async def test_extract_returns_result(self, sample_full_result):
        """Test that extraction returns the full result."""
        mock_service = MagicMock()
        mock_service.extract_all = AsyncMock(return_value=sample_full_result)

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = concept_extraction.ExtractionRequest(
                content="Test content for extraction",
                document_id="doc-1",
            )
            result = await concept_extraction.extract_concepts(request)

        assert result.document_id == "doc-1"
        assert len(result.all_concepts) == 1
        assert result.overall_consciousness_level == 0.8

    @pytest.mark.asyncio
    async def test_extract_calls_service_with_params(self, sample_full_result):
        """Test that extraction passes parameters correctly."""
        mock_service = MagicMock()
        mock_service.extract_all = AsyncMock(return_value=sample_full_result)

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = concept_extraction.ExtractionRequest(
                content="Test content",
                document_id="my-doc",
                context={"domain": "neuroscience"},
            )
            await concept_extraction.extract_concepts(request)

        mock_service.extract_all.assert_called_once_with(
            content="Test content",
            context={"domain": "neuroscience"},
            document_id="my-doc",
        )

    @pytest.mark.asyncio
    async def test_extract_handles_error(self):
        """Test that extraction handles errors gracefully."""
        mock_service = MagicMock()
        mock_service.extract_all = AsyncMock(side_effect=Exception("Test error"))

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = concept_extraction.ExtractionRequest(content="Test content")
            with pytest.raises(Exception) as exc_info:
                await concept_extraction.extract_concepts(request)
            assert "Test error" in str(exc_info.value)


class TestExtractSingleLevelEndpoint:
    """Tests for extract_single_level endpoint function."""

    @pytest.mark.asyncio
    async def test_extract_single_level(self, sample_level_result):
        """Test single level extraction."""
        mock_extractor = MagicMock()
        mock_extractor.extract = AsyncMock(return_value=sample_level_result)

        mock_service = MagicMock()
        mock_service.get_extractor.return_value = mock_extractor

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = concept_extraction.ExtractionRequest(content="Test content")
            result = await concept_extraction.extract_single_level(
                level=ConceptExtractionLevel.ATOMIC,
                request=request,
                include_lower_concepts=False,
            )

        assert result.level == ConceptExtractionLevel.ATOMIC
        assert len(result.concepts) == 1

    @pytest.mark.asyncio
    async def test_extract_level_not_registered(self):
        """Test extraction when level is not registered."""
        mock_service = MagicMock()
        mock_service.get_extractor.return_value = None

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = concept_extraction.ExtractionRequest(content="Test content")
            with pytest.raises(Exception) as exc_info:
                await concept_extraction.extract_single_level(
                    level=ConceptExtractionLevel.ATOMIC,
                    request=request,
                    include_lower_concepts=False,
                )
            assert "No extractor registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_with_lower_concepts(self, sample_level_result):
        """Test extraction with include_lower_concepts=True."""
        atomic_concept = ExtractedConcept(
            concept_id="atomic-1",
            level=ConceptExtractionLevel.ATOMIC,
            name="Atomic Concept",
            description="From lower level",
            confidence=0.9,
            source_span="test",
        )

        atomic_result = LevelExtractionResult(
            level=ConceptExtractionLevel.ATOMIC,
            concepts=[atomic_concept],
            extraction_time=0.3,
            content_length=100,
        )

        relational_result = sample_level_result
        relational_result.level = ConceptExtractionLevel.RELATIONAL

        mock_atomic = MagicMock()
        mock_atomic.extract = AsyncMock(return_value=atomic_result)

        mock_relational = MagicMock()
        mock_relational.extract = AsyncMock(return_value=relational_result)

        def get_extractor(level):
            if level == ConceptExtractionLevel.ATOMIC:
                return mock_atomic
            elif level == ConceptExtractionLevel.RELATIONAL:
                return mock_relational
            return None

        mock_service = MagicMock()
        mock_service.get_extractor.side_effect = get_extractor

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            request = concept_extraction.ExtractionRequest(content="Test content")
            await concept_extraction.extract_single_level(
                level=ConceptExtractionLevel.RELATIONAL,
                request=request,
                include_lower_concepts=True,
            )

        # Verify atomic was called first
        mock_atomic.extract.assert_called_once()
        # Verify relational was called with atomic concepts
        mock_relational.extract.assert_called_once()
        call_kwargs = mock_relational.extract.call_args[1]
        assert call_kwargs["lower_level_concepts"] is not None
        assert len(call_kwargs["lower_level_concepts"]) == 1


class TestStoreEndpoint:
    """Tests for store_extraction_results endpoint function."""

    @pytest.mark.asyncio
    async def test_store_extraction_results(self, sample_full_result):
        """Test storing extraction results."""
        mock_service = MagicMock()
        mock_service.store_in_graphiti = AsyncMock(
            return_value={
                "stored_entities": 5,
                "stored_relationships": 3,
                "errors": [],
            }
        )

        mock_graphiti = MagicMock()

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            with patch(
                "api.services.graphiti_service.get_graphiti_service",
                new=AsyncMock(return_value=mock_graphiti),
            ):
                request = concept_extraction.StoreRequest(
                    extraction_result=sample_full_result.model_dump(),
                    group_id="test-group",
                )
                result = await concept_extraction.store_extraction_results(request)

        assert result.stored_entities == 5
        assert result.stored_relationships == 3
        assert result.errors == []


class TestLevelsEndpoint:
    """Tests for list_extraction_levels endpoint function."""

    @pytest.mark.asyncio
    async def test_list_levels(self):
        """Test listing extraction levels."""
        result = await concept_extraction.list_extraction_levels()

        assert "levels" in result
        assert len(result["levels"]) == 5

        level_names = [l["name"] for l in result["levels"]]
        assert "ATOMIC" in level_names
        assert "NARRATIVE" in level_names


class TestHealthEndpoint:
    """Tests for health_check endpoint function."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when all extractors registered."""
        mock_extractor = MagicMock()
        mock_extractor.__class__.__name__ = "MockExtractor"

        mock_service = MagicMock()
        mock_service.get_extractor.return_value = mock_extractor

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            result = await concept_extraction.health_check()

        assert result["healthy"] is True
        assert result["all_levels_registered"] is True

    @pytest.mark.asyncio
    async def test_health_check_missing_extractors(self):
        """Test health check when some extractors missing."""
        mock_service = MagicMock()
        mock_service.get_extractor.return_value = None

        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(return_value=mock_service),
        ):
            result = await concept_extraction.health_check()

        assert result["healthy"] is True  # Still healthy, just not all registered
        assert result["all_levels_registered"] is False

    @pytest.mark.asyncio
    async def test_health_check_error(self):
        """Test health check when service fails."""
        with patch.object(
            concept_extraction,
            "get_concept_extraction_service",
            new=AsyncMock(side_effect=Exception("Service unavailable")),
        ):
            result = await concept_extraction.health_check()

        assert result["healthy"] is False
        assert "Service unavailable" in result["error"]
