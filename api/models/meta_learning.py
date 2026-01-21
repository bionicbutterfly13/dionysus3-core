"""
Meta-Learning Models
Feature: D2 Migration - Meta-Learning Document Enhancer

Pydantic v2 models for meta-learning paper classification
and extraction patterns.

Migrated from D2 meta_learning_document_enhancer.py
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetaLearningPaperType(str, Enum):
    """Classification of paper types based on meta-learning approach.

    Each type indicates a different pattern of knowledge transfer
    and learning strategy.
    """
    # Core meta-learning paradigms
    LEARNING_TO_LEARN = "learning_to_learn"
    FEW_SHOT = "few_shot"
    ZERO_SHOT = "zero_shot"
    TRANSFER_LEARNING = "transfer_learning"

    # Architecture-focused
    NEURAL_ARCHITECTURE_SEARCH = "neural_architecture_search"
    HYPERPARAMETER_OPTIMIZATION = "hyperparameter_optimization"

    # Knowledge-focused
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"
    CURRICULUM_LEARNING = "curriculum_learning"

    # Consciousness-adjacent
    SELF_SUPERVISED = "self_supervised"
    CONTINUAL_LEARNING = "continual_learning"

    # Fallback
    GENERAL = "general"
    UNKNOWN = "unknown"


class MetaLearningAlgorithm(BaseModel):
    """Extracted meta-learning algorithm from a document."""

    name: str = Field(..., description="Algorithm name (e.g., MAML, Reptile, ProtoNet)")
    description: str = Field(default="", description="Brief description of the algorithm")
    paper_type: MetaLearningPaperType = Field(
        default=MetaLearningPaperType.GENERAL,
        description="Classification of the algorithm's approach"
    )
    complexity: str = Field(default="medium", description="Implementation complexity")
    key_concepts: List[str] = Field(default_factory=list, description="Core concepts used")
    related_algorithms: List[str] = Field(default_factory=list, description="Related approaches")
    consciousness_relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to consciousness/self-awareness (0-1)"
    )


class MetaLearningPattern(BaseModel):
    """A learned pattern from document processing.

    These patterns help the system improve future document processing
    by recognizing recurring structures and concepts.
    """

    pattern_id: str = Field(
        default_factory=lambda: f"pat_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        description="Unique pattern identifier"
    )
    pattern_type: str = Field(..., description="Type of pattern (structural, conceptual, etc.)")
    pattern_content: str = Field(..., description="Description of the pattern")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in pattern validity (0-1)"
    )
    occurrence_count: int = Field(default=1, ge=1, description="Number of times pattern observed")
    source_documents: List[str] = Field(
        default_factory=list,
        description="Document IDs where pattern was observed"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Meta-learning specific
    transferability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How well pattern transfers to new contexts (0-1)"
    )
    domain_specificity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How domain-specific vs general the pattern is (0=general, 1=specific)"
    )


class ConsciousnessEnhancementSignal(BaseModel):
    """Signal indicating consciousness-relevant content.

    Identifies content that may enhance system self-awareness
    or metacognitive capabilities.
    """

    signal_type: str = Field(..., description="Type of consciousness signal")
    strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Signal strength (0-1)"
    )
    source_span: Optional[str] = Field(
        default=None,
        description="Text span that triggered the signal"
    )
    metacognitive_relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to metacognition (0-1)"
    )
    self_model_relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to self-modeling (0-1)"
    )
    active_inference_relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to active inference (0-1)"
    )


class MetaLearningExtraction(BaseModel):
    """Complete extraction result from meta-learning document processing.

    Contains all extracted elements: algorithms, patterns, and
    consciousness enhancement signals.
    """

    extraction_id: str = Field(
        default_factory=lambda: f"ext_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        description="Unique extraction identifier"
    )
    document_id: str = Field(..., description="Source document identifier")
    document_title: Optional[str] = Field(default=None, description="Document title if available")

    # Classification
    paper_type: MetaLearningPaperType = Field(
        default=MetaLearningPaperType.UNKNOWN,
        description="Classified paper type"
    )
    paper_type_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in paper type classification (0-1)"
    )

    # Extracted content
    algorithms: List[MetaLearningAlgorithm] = Field(
        default_factory=list,
        description="Extracted meta-learning algorithms"
    )
    patterns: List[MetaLearningPattern] = Field(
        default_factory=list,
        description="Learned patterns from document"
    )
    consciousness_signals: List[ConsciousnessEnhancementSignal] = Field(
        default_factory=list,
        description="Consciousness enhancement signals"
    )

    # Metadata
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Key concepts extracted"
    )
    domain_tags: List[str] = Field(
        default_factory=list,
        description="Domain classification tags"
    )

    # Quality metrics
    extraction_quality: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall extraction quality (0-1)"
    )
    consciousness_enhancement_potential: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Potential for consciousness enhancement (0-1)"
    )

    # Timestamps
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(
        default=None,
        description="Processing time in milliseconds"
    )

    model_config = {"arbitrary_types_allowed": True}


class MetaLearningProcessingResult(BaseModel):
    """Result of processing a document through meta-learning enhancement.

    Contains the extraction plus additional processing metadata
    and enhancement recommendations.
    """

    result_id: str = Field(
        default_factory=lambda: f"res_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        description="Unique result identifier"
    )
    extraction: MetaLearningExtraction = Field(
        ...,
        description="The extraction result"
    )

    # Processing status
    success: bool = Field(default=True, description="Whether processing succeeded")
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )

    # Enhancement recommendations
    enhancement_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended enhancements based on content"
    )
    related_basins: List[str] = Field(
        default_factory=list,
        description="Related attractor basins"
    )
    suggested_thoughtseeds: List[str] = Field(
        default_factory=list,
        description="Suggested ThoughtSeed activations"
    )

    # Learning outcomes
    patterns_learned: int = Field(
        default=0,
        ge=0,
        description="Number of new patterns learned"
    )
    patterns_reinforced: int = Field(
        default=0,
        ge=0,
        description="Number of existing patterns reinforced"
    )

    # Integration hints
    graphiti_entities_suggested: List[str] = Field(
        default_factory=list,
        description="Suggested entities for Graphiti storage"
    )
    knowledge_graph_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Suggested knowledge graph updates"
    )

    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}


class PatternLibrary(BaseModel):
    """Library of learned meta-learning patterns.

    Maintains a collection of patterns with deduplication
    and confidence tracking.
    """

    patterns: Dict[str, MetaLearningPattern] = Field(
        default_factory=dict,
        description="Pattern ID -> Pattern mapping"
    )
    total_documents_processed: int = Field(
        default=0,
        ge=0,
        description="Total documents processed"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def add_pattern(self, pattern: MetaLearningPattern) -> None:
        """Add or update a pattern in the library."""
        if pattern.pattern_id in self.patterns:
            # Reinforce existing pattern
            existing = self.patterns[pattern.pattern_id]
            existing.occurrence_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.last_updated = datetime.utcnow()
            existing.source_documents.extend(pattern.source_documents)
        else:
            self.patterns[pattern.pattern_id] = pattern
        self.last_updated = datetime.utcnow()

    def get_high_confidence_patterns(
        self,
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[MetaLearningPattern]:
        """Get patterns above confidence threshold."""
        high_conf = [
            p for p in self.patterns.values()
            if p.confidence >= threshold
        ]
        return sorted(
            high_conf,
            key=lambda p: p.confidence,
            reverse=True
        )[:limit]

    def get_transferable_patterns(
        self,
        threshold: float = 0.6,
        limit: int = 10
    ) -> List[MetaLearningPattern]:
        """Get patterns with high transferability."""
        transferable = [
            p for p in self.patterns.values()
            if p.transferability >= threshold
        ]
        return sorted(
            transferable,
            key=lambda p: p.transferability,
            reverse=True
        )[:limit]

    model_config = {"arbitrary_types_allowed": True}


class MetaLearningConfig(BaseModel):
    """Configuration for meta-learning document enhancement.

    Controls extraction thresholds, pattern learning parameters,
    and consciousness enhancement settings.
    """

    # Extraction settings
    min_algorithm_confidence: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for algorithm extraction"
    )
    min_pattern_confidence: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for pattern learning"
    )

    # Consciousness enhancement
    consciousness_signal_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Threshold for consciousness signal detection"
    )
    enable_consciousness_enhancement: bool = Field(
        default=True,
        description="Whether to detect consciousness enhancement signals"
    )

    # Pattern learning
    enable_pattern_learning: bool = Field(
        default=True,
        description="Whether to learn patterns from documents"
    )
    max_patterns_per_document: int = Field(
        default=10,
        ge=1,
        description="Maximum patterns to extract per document"
    )
    pattern_decay_rate: float = Field(
        default=0.01,
        ge=0.0,
        le=1.0,
        description="Rate at which unused patterns decay"
    )

    # Integration
    enable_graphiti_integration: bool = Field(
        default=True,
        description="Whether to suggest Graphiti storage"
    )
    enable_basin_linking: bool = Field(
        default=True,
        description="Whether to link to attractor basins"
    )
    enable_thoughtseed_activation: bool = Field(
        default=True,
        description="Whether to suggest ThoughtSeed activations"
    )
