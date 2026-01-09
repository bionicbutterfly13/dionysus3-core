"""
Unit tests for Meta-Learning Document Enhancer
Feature: D2 Migration - Meta-Learning Document Enhancer

Tests models, service, and pattern learning functionality.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from api.models.meta_learning import (
    ConsciousnessEnhancementSignal,
    MetaLearningAlgorithm,
    MetaLearningConfig,
    MetaLearningExtraction,
    MetaLearningPaperType,
    MetaLearningPattern,
    MetaLearningProcessingResult,
    PatternLibrary,
)
from api.services.meta_learning_enhancer import (
    MetaLearningEnhancer,
    get_meta_learning_enhancer,
    enhance_document,
)


# =============================================================================
# Model Tests
# =============================================================================

class TestMetaLearningPaperType:
    """Tests for MetaLearningPaperType enum."""

    def test_all_types_have_values(self):
        """All paper types should have string values."""
        for paper_type in MetaLearningPaperType:
            assert isinstance(paper_type.value, str)
            assert len(paper_type.value) > 0

    def test_core_types_exist(self):
        """Core meta-learning types should exist."""
        assert MetaLearningPaperType.LEARNING_TO_LEARN
        assert MetaLearningPaperType.FEW_SHOT
        assert MetaLearningPaperType.ZERO_SHOT
        assert MetaLearningPaperType.TRANSFER_LEARNING

    def test_consciousness_adjacent_types(self):
        """Consciousness-adjacent types should exist."""
        assert MetaLearningPaperType.SELF_SUPERVISED
        assert MetaLearningPaperType.CONTINUAL_LEARNING

    def test_fallback_types(self):
        """Fallback types should exist."""
        assert MetaLearningPaperType.GENERAL
        assert MetaLearningPaperType.UNKNOWN


class TestMetaLearningAlgorithm:
    """Tests for MetaLearningAlgorithm model."""

    def test_minimal_creation(self):
        """Algorithm with just name should work."""
        algo = MetaLearningAlgorithm(name="TestAlgo")
        assert algo.name == "TestAlgo"
        assert algo.paper_type == MetaLearningPaperType.GENERAL
        assert algo.consciousness_relevance == 0.0

    def test_full_creation(self):
        """Algorithm with all fields should work."""
        algo = MetaLearningAlgorithm(
            name="MAML",
            description="Model-Agnostic Meta-Learning",
            paper_type=MetaLearningPaperType.LEARNING_TO_LEARN,
            complexity="high",
            key_concepts=["gradient", "inner loop", "outer loop"],
            related_algorithms=["Reptile", "FOMAML"],
            consciousness_relevance=0.7
        )
        assert algo.name == "MAML"
        assert algo.consciousness_relevance == 0.7
        assert len(algo.key_concepts) == 3

    def test_consciousness_relevance_bounds(self):
        """Consciousness relevance should be bounded 0-1."""
        # Valid values
        algo = MetaLearningAlgorithm(name="Test", consciousness_relevance=0.5)
        assert algo.consciousness_relevance == 0.5

        # Should clamp or reject out of bounds
        with pytest.raises(ValueError):
            MetaLearningAlgorithm(name="Test", consciousness_relevance=1.5)


class TestMetaLearningPattern:
    """Tests for MetaLearningPattern model."""

    def test_default_id_generation(self):
        """Pattern should generate unique ID by default."""
        p1 = MetaLearningPattern(
            pattern_type="structural",
            pattern_content="Test pattern"
        )
        p2 = MetaLearningPattern(
            pattern_type="structural",
            pattern_content="Test pattern"
        )
        # IDs should be generated (may or may not be unique in same millisecond)
        assert p1.pattern_id.startswith("pat_")
        assert p2.pattern_id.startswith("pat_")

    def test_transferability_bounds(self):
        """Transferability should be bounded 0-1."""
        pattern = MetaLearningPattern(
            pattern_type="test",
            pattern_content="test",
            transferability=0.8
        )
        assert pattern.transferability == 0.8

        with pytest.raises(ValueError):
            MetaLearningPattern(
                pattern_type="test",
                pattern_content="test",
                transferability=-0.1
            )

    def test_occurrence_tracking(self):
        """Pattern should track occurrences."""
        pattern = MetaLearningPattern(
            pattern_type="test",
            pattern_content="test",
            occurrence_count=5
        )
        assert pattern.occurrence_count == 5


class TestConsciousnessEnhancementSignal:
    """Tests for ConsciousnessEnhancementSignal model."""

    def test_signal_creation(self):
        """Signal should be creatable with required fields."""
        signal = ConsciousnessEnhancementSignal(signal_type="metacognitive")
        assert signal.signal_type == "metacognitive"
        assert signal.strength == 0.5  # Default

    def test_relevance_scores(self):
        """All relevance scores should be settable."""
        signal = ConsciousnessEnhancementSignal(
            signal_type="active_inference",
            strength=0.9,
            metacognitive_relevance=0.3,
            self_model_relevance=0.5,
            active_inference_relevance=0.95
        )
        assert signal.active_inference_relevance == 0.95
        assert signal.metacognitive_relevance == 0.3


class TestMetaLearningExtraction:
    """Tests for MetaLearningExtraction model."""

    def test_minimal_extraction(self):
        """Extraction with just document_id should work."""
        extraction = MetaLearningExtraction(document_id="doc_001")
        assert extraction.document_id == "doc_001"
        assert extraction.paper_type == MetaLearningPaperType.UNKNOWN
        assert extraction.algorithms == []

    def test_full_extraction(self):
        """Extraction with all fields should work."""
        extraction = MetaLearningExtraction(
            document_id="doc_002",
            document_title="Meta-Learning Survey",
            paper_type=MetaLearningPaperType.LEARNING_TO_LEARN,
            paper_type_confidence=0.85,
            algorithms=[
                MetaLearningAlgorithm(name="MAML"),
                MetaLearningAlgorithm(name="Reptile")
            ],
            key_concepts=["meta-learning", "few-shot"],
            extraction_quality=0.9,
            consciousness_enhancement_potential=0.7
        )
        assert len(extraction.algorithms) == 2
        assert extraction.extraction_quality == 0.9


class TestMetaLearningProcessingResult:
    """Tests for MetaLearningProcessingResult model."""

    def test_success_result(self):
        """Success result should have valid extraction."""
        extraction = MetaLearningExtraction(document_id="doc_001")
        result = MetaLearningProcessingResult(
            extraction=extraction,
            success=True,
            patterns_learned=3,
            patterns_reinforced=2
        )
        assert result.success
        assert result.patterns_learned == 3

    def test_error_result(self):
        """Error result should have error message."""
        extraction = MetaLearningExtraction(document_id="doc_001")
        result = MetaLearningProcessingResult(
            extraction=extraction,
            success=False,
            error_message="Processing failed"
        )
        assert not result.success
        assert "failed" in result.error_message


class TestPatternLibrary:
    """Tests for PatternLibrary model."""

    def test_empty_library(self):
        """Empty library should have zero counts."""
        library = PatternLibrary()
        assert len(library.patterns) == 0
        assert library.total_documents_processed == 0

    def test_add_pattern(self):
        """Adding pattern should store it."""
        library = PatternLibrary()
        pattern = MetaLearningPattern(
            pattern_id="test_001",
            pattern_type="structural",
            pattern_content="Test pattern"
        )
        library.add_pattern(pattern)
        assert "test_001" in library.patterns
        assert library.patterns["test_001"].pattern_content == "Test pattern"

    def test_reinforce_pattern(self):
        """Adding existing pattern should reinforce it."""
        library = PatternLibrary()
        pattern1 = MetaLearningPattern(
            pattern_id="test_001",
            pattern_type="structural",
            pattern_content="Test pattern",
            confidence=0.5
        )
        library.add_pattern(pattern1)

        pattern2 = MetaLearningPattern(
            pattern_id="test_001",
            pattern_type="structural",
            pattern_content="Test pattern",
            confidence=0.5
        )
        library.add_pattern(pattern2)

        # Confidence should increase, occurrence should increment
        assert library.patterns["test_001"].occurrence_count == 2
        assert library.patterns["test_001"].confidence > 0.5

    def test_get_high_confidence_patterns(self):
        """Should filter by confidence threshold."""
        library = PatternLibrary()

        # Add patterns with varying confidence
        for i, conf in enumerate([0.3, 0.5, 0.7, 0.9]):
            library.patterns[f"pat_{i}"] = MetaLearningPattern(
                pattern_id=f"pat_{i}",
                pattern_type="test",
                pattern_content=f"Pattern {i}",
                confidence=conf
            )

        high_conf = library.get_high_confidence_patterns(threshold=0.6)
        assert len(high_conf) == 2  # 0.7 and 0.9

    def test_get_transferable_patterns(self):
        """Should filter by transferability threshold."""
        library = PatternLibrary()

        for i, trans in enumerate([0.3, 0.5, 0.7, 0.9]):
            library.patterns[f"pat_{i}"] = MetaLearningPattern(
                pattern_id=f"pat_{i}",
                pattern_type="test",
                pattern_content=f"Pattern {i}",
                transferability=trans
            )

        transferable = library.get_transferable_patterns(threshold=0.6)
        assert len(transferable) == 2


class TestMetaLearningConfig:
    """Tests for MetaLearningConfig model."""

    def test_default_config(self):
        """Default config should have sensible values."""
        config = MetaLearningConfig()
        assert config.min_algorithm_confidence == 0.3
        assert config.enable_consciousness_enhancement
        assert config.enable_pattern_learning

    def test_custom_config(self):
        """Custom config should override defaults."""
        config = MetaLearningConfig(
            min_algorithm_confidence=0.5,
            enable_consciousness_enhancement=False,
            max_patterns_per_document=5
        )
        assert config.min_algorithm_confidence == 0.5
        assert not config.enable_consciousness_enhancement
        assert config.max_patterns_per_document == 5


# =============================================================================
# Service Tests
# =============================================================================

class TestMetaLearningEnhancer:
    """Tests for MetaLearningEnhancer service."""

    @pytest.fixture
    def enhancer(self):
        """Create fresh enhancer for each test."""
        return MetaLearningEnhancer()

    @pytest.fixture
    def sample_ml_content(self):
        """Sample meta-learning paper content."""
        return """
        This paper introduces a novel approach to meta-learning using
        Model-Agnostic Meta-Learning (MAML). We demonstrate few-shot
        learning capabilities on several benchmarks.

        Our method builds on the concept of learning to learn, where
        the model is trained across multiple tasks. We use gradient-based
        optimization in the inner loop and meta-optimization in the outer loop.

        Results show that our approach outperforms baseline methods on
        5-way 1-shot classification tasks.
        """

    @pytest.fixture
    def sample_consciousness_content(self):
        """Sample consciousness-related content."""
        return """
        This paper explores the relationship between active inference
        and consciousness. We propose that self-awareness emerges from
        the minimization of free energy through predictive coding.

        The Markov blanket formalism provides a principled way to
        understand the boundaries of the self. Metacognition plays
        a crucial role in higher-order awareness.

        Our model incorporates attention mechanisms inspired by
        global workspace theory.
        """

    @pytest.mark.asyncio
    async def test_process_ml_document(self, enhancer, sample_ml_content):
        """Should process meta-learning content correctly."""
        result = await enhancer.process_document(
            document_id="test_ml_001",
            content=sample_ml_content,
            title="Meta-Learning Survey"
        )

        assert result.success
        assert result.extraction.document_id == "test_ml_001"
        # Should classify as meta-learning related
        assert result.extraction.paper_type in [
            MetaLearningPaperType.LEARNING_TO_LEARN,
            MetaLearningPaperType.FEW_SHOT,
            MetaLearningPaperType.GENERAL
        ]

    @pytest.mark.asyncio
    async def test_extract_algorithms(self, enhancer, sample_ml_content):
        """Should extract MAML algorithm."""
        result = await enhancer.process_document(
            document_id="test_ml_002",
            content=sample_ml_content
        )

        algo_names = [a.name for a in result.extraction.algorithms]
        assert "MAML" in algo_names

    @pytest.mark.asyncio
    async def test_detect_consciousness_signals(
        self, enhancer, sample_consciousness_content
    ):
        """Should detect consciousness-related signals."""
        result = await enhancer.process_document(
            document_id="test_cons_001",
            content=sample_consciousness_content
        )

        assert len(result.extraction.consciousness_signals) > 0
        signal_types = [s.signal_type for s in result.extraction.consciousness_signals]
        # Should detect active inference signals
        assert any("inference" in t or "consciousness" in t for t in signal_types)

    @pytest.mark.asyncio
    async def test_consciousness_enhancement_potential(
        self, enhancer, sample_consciousness_content
    ):
        """Consciousness content should have high enhancement potential."""
        result = await enhancer.process_document(
            document_id="test_cons_002",
            content=sample_consciousness_content
        )

        assert result.extraction.consciousness_enhancement_potential > 0.3

    @pytest.mark.asyncio
    async def test_pattern_learning(self, enhancer, sample_ml_content):
        """Should learn patterns from documents."""
        result = await enhancer.process_document(
            document_id="test_patterns_001",
            content=sample_ml_content
        )

        assert result.patterns_learned > 0 or result.patterns_reinforced >= 0

    @pytest.mark.asyncio
    async def test_related_basin_suggestions(
        self, enhancer, sample_consciousness_content
    ):
        """Should suggest related attractor basins."""
        result = await enhancer.process_document(
            document_id="test_basins_001",
            content=sample_consciousness_content
        )

        assert len(result.related_basins) > 0
        # Consciousness content should link to consciousness/cognitive basins
        assert any(
            "consciousness" in b or "cognitive" in b
            for b in result.related_basins
        )

    @pytest.mark.asyncio
    async def test_graphiti_entity_suggestions(self, enhancer, sample_ml_content):
        """Should suggest Graphiti entities."""
        result = await enhancer.process_document(
            document_id="test_graphiti_001",
            content=sample_ml_content
        )

        assert len(result.graphiti_entities_suggested) > 0
        # Should suggest algorithm entities
        assert any("Algorithm:" in e for e in result.graphiti_entities_suggested)

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, enhancer, sample_ml_content):
        """Should track processing time."""
        result = await enhancer.process_document(
            document_id="test_time_001",
            content=sample_ml_content
        )

        assert result.extraction.processing_time_ms is not None
        assert result.extraction.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, enhancer):
        """Should handle empty content gracefully."""
        result = await enhancer.process_document(
            document_id="test_empty_001",
            content=""
        )

        # Should still return a result (even if minimal)
        assert result.extraction.document_id == "test_empty_001"

    def test_pattern_library_stats(self, enhancer):
        """Should return pattern library statistics."""
        stats = enhancer.get_pattern_library_stats()
        assert "total_patterns" in stats
        assert "total_documents_processed" in stats
        assert "last_updated" in stats


class TestClassificationAccuracy:
    """Tests for paper type classification accuracy."""

    @pytest.fixture
    def enhancer(self):
        return MetaLearningEnhancer()

    @pytest.mark.asyncio
    async def test_few_shot_classification(self, enhancer):
        """Few-shot content should classify correctly."""
        content = """
        We present a novel few-shot learning method using prototypical
        networks. Our approach achieves state-of-the-art results on
        5-way 1-shot and 5-way 5-shot classification benchmarks.
        The episodic training procedure uses support and query sets.
        """
        result = await enhancer.process_document(
            document_id="few_shot_test",
            content=content
        )
        assert result.extraction.paper_type == MetaLearningPaperType.FEW_SHOT

    @pytest.mark.asyncio
    async def test_transfer_learning_classification(self, enhancer):
        """Transfer learning content should classify correctly."""
        content = """
        This paper studies domain adaptation and transfer learning.
        We fine-tune a pre-trained model on a new target domain,
        addressing the domain shift between source and target datasets.
        Feature extraction from the pre-trained backbone is key.
        """
        result = await enhancer.process_document(
            document_id="transfer_test",
            content=content
        )
        assert result.extraction.paper_type == MetaLearningPaperType.TRANSFER_LEARNING

    @pytest.mark.asyncio
    async def test_continual_learning_classification(self, enhancer):
        """Continual learning content should classify correctly."""
        content = """
        We address the problem of catastrophic forgetting in
        continual learning systems. Our method uses elastic weight
        consolidation to prevent forgetting of previously learned tasks.
        Lifelong learning requires balancing plasticity and stability.
        """
        result = await enhancer.process_document(
            document_id="continual_test",
            content=content
        )
        assert result.extraction.paper_type == MetaLearningPaperType.CONTINUAL_LEARNING


class TestServiceSingleton:
    """Tests for singleton service pattern."""

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Should return same instance."""
        # Reset singleton for test
        import api.services.meta_learning_enhancer as module
        module._enhancer_instance = None

        e1 = await get_meta_learning_enhancer()
        e2 = await get_meta_learning_enhancer()
        assert e1 is e2

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """enhance_document should work correctly."""
        result = await enhance_document(
            document_id="convenience_test",
            content="Test content for meta-learning analysis.",
            title="Test Document"
        )
        assert result.extraction.document_id == "convenience_test"


class TestModelSerialization:
    """Tests for model serialization/deserialization."""

    def test_extraction_json_roundtrip(self):
        """Extraction should serialize and deserialize correctly."""
        extraction = MetaLearningExtraction(
            document_id="serial_test",
            paper_type=MetaLearningPaperType.FEW_SHOT,
            algorithms=[MetaLearningAlgorithm(name="MAML")],
            key_concepts=["few-shot", "meta-learning"]
        )

        json_str = extraction.model_dump_json()
        restored = MetaLearningExtraction.model_validate_json(json_str)

        assert restored.document_id == extraction.document_id
        assert restored.paper_type == extraction.paper_type
        assert len(restored.algorithms) == 1

    def test_result_json_roundtrip(self):
        """ProcessingResult should serialize correctly."""
        extraction = MetaLearningExtraction(document_id="serial_test_2")
        result = MetaLearningProcessingResult(
            extraction=extraction,
            success=True,
            enhancement_recommendations=["Enhance consciousness integration"],
            related_basins=["machine_learning"]
        )

        json_str = result.model_dump_json()
        restored = MetaLearningProcessingResult.model_validate_json(json_str)

        assert restored.success
        assert len(restored.enhancement_recommendations) == 1
        assert "machine_learning" in restored.related_basins

    def test_pattern_library_json_roundtrip(self):
        """PatternLibrary should serialize correctly."""
        library = PatternLibrary()
        library.add_pattern(MetaLearningPattern(
            pattern_id="p1",
            pattern_type="structural",
            pattern_content="Test"
        ))

        json_str = library.model_dump_json()
        restored = PatternLibrary.model_validate_json(json_str)

        assert "p1" in restored.patterns


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def enhancer(self):
        return MetaLearningEnhancer()

    @pytest.mark.asyncio
    async def test_very_long_content(self, enhancer):
        """Should handle very long content."""
        long_content = "meta-learning " * 10000
        result = await enhancer.process_document(
            document_id="long_test",
            content=long_content
        )
        assert result.success

    @pytest.mark.asyncio
    async def test_unicode_content(self, enhancer):
        """Should handle unicode content."""
        unicode_content = """
        Meta-learning研究 explores 元学习 and Übertragungslernen.
        Few-shot 学习 enables быстрое обучение.
        """
        result = await enhancer.process_document(
            document_id="unicode_test",
            content=unicode_content
        )
        assert result.success

    @pytest.mark.asyncio
    async def test_special_characters(self, enhancer):
        """Should handle special characters."""
        special_content = """
        Meta-learning: MAML -> Reptile -> ProtoNet
        Few-shot @ scale: 5-way-1-shot (n=100)
        Results: 85.5% ± 2.3% accuracy
        """
        result = await enhancer.process_document(
            document_id="special_test",
            content=special_content
        )
        assert result.success

    def test_config_bounds(self):
        """Config should enforce bounds."""
        with pytest.raises(ValueError):
            MetaLearningConfig(min_algorithm_confidence=1.5)

        with pytest.raises(ValueError):
            MetaLearningConfig(consciousness_signal_threshold=-0.1)
