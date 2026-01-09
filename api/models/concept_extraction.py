"""
Five-Level Concept Extraction Models.

Defines Pydantic v2 models for the five-level concept extraction system:
- Level 1: ATOMIC - Individual terms, entities, definitions
- Level 2: RELATIONAL - Connections, causality, dependencies
- Level 3: COMPOSITE - Complex multi-part ideas and systems
- Level 4: CONTEXTUAL - Domain paradigms, theoretical frameworks
- Level 5: NARRATIVE - Argument flows, story progressions

Migrated from Dionysus 2.0 with D3 patterns (Pydantic v2, async-ready).
"""

from datetime import datetime
from enum import IntEnum
from typing import Any, Optional
import uuid

from pydantic import BaseModel, Field


class ConceptExtractionLevel(IntEnum):
    """Five levels of concept extraction, ordered by complexity."""

    ATOMIC = 1  # Individual terms, entities, definitions
    RELATIONAL = 2  # Connections, causality, dependencies
    COMPOSITE = 3  # Complex multi-part ideas and systems
    CONTEXTUAL = 4  # Domain paradigms, theoretical frameworks
    NARRATIVE = 5  # Argument flows, story progressions


class ExtractedConcept(BaseModel):
    """A concept extracted at any level of the hierarchy."""

    concept_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: ConceptExtractionLevel = ConceptExtractionLevel.ATOMIC
    name: str = Field(..., description="Concept name or label")
    description: str = Field(default="", description="Concept description or definition")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Source tracking
    source_span: str = Field(default="", description="Original text span")
    source_chunk_id: Optional[str] = None
    document_id: Optional[str] = None

    # Metadata
    concept_type: str = Field(default="general", description="Category of concept")
    domain_tags: list[str] = Field(default_factory=list)
    extraction_method: str = Field(default="llm")

    # Relationships
    related_concepts: list[str] = Field(
        default_factory=list, description="IDs of related concepts"
    )
    parent_concepts: list[str] = Field(
        default_factory=list, description="IDs of parent concepts"
    )
    child_concepts: list[str] = Field(
        default_factory=list, description="IDs of child concepts"
    )

    # Level-specific data
    atomic_properties: dict[str, Any] = Field(default_factory=dict)
    relationship_data: dict[str, Any] = Field(default_factory=dict)
    composite_structure: dict[str, Any] = Field(default_factory=dict)
    contextual_framework: dict[str, Any] = Field(default_factory=dict)
    narrative_elements: dict[str, Any] = Field(default_factory=dict)

    # Consciousness metrics
    consciousness_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Timestamps
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    processing_duration: float = Field(default=0.0, description="Seconds to extract")


class LevelExtractionResult(BaseModel):
    """Results from extraction at a specific level."""

    level: ConceptExtractionLevel
    concepts: list[ExtractedConcept] = Field(default_factory=list)
    extraction_time: float = Field(default=0.0, description="Seconds to process level")
    content_length: int = Field(default=0, description="Characters processed")

    # Quality metrics
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    concept_count: int = Field(default=0)

    # Processing stats
    chunks_processed: int = Field(default=0)
    successful_extractions: int = Field(default=0)
    failed_extractions: int = Field(default=0)

    def model_post_init(self, __context: Any) -> None:
        """Compute derived fields after initialization."""
        if self.concepts and self.concept_count == 0:
            self.concept_count = len(self.concepts)
        if self.concepts and self.average_confidence == 0.0:
            confidences = [c.confidence for c in self.concepts]
            if confidences:
                self.average_confidence = sum(confidences) / len(confidences)


class CrossLevelRelationship(BaseModel):
    """A relationship between concepts at different levels."""

    relationship_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_concept_id: str
    source_level: ConceptExtractionLevel
    target_concept_id: str
    target_level: ConceptExtractionLevel
    relationship_type: str = Field(
        default="related", description="Type: contains, derives_from, exemplifies, etc."
    )
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    description: Optional[str] = None


class FiveLevelExtractionResult(BaseModel):
    """Complete five-level extraction results for a document."""

    document_id: str = Field(default="")

    # Results by level (keyed by level int value)
    level_results: dict[int, LevelExtractionResult] = Field(default_factory=dict)

    # Integrated results
    all_concepts: list[ExtractedConcept] = Field(default_factory=list)
    concept_hierarchy: dict[str, list[str]] = Field(
        default_factory=dict, description="Parent ID -> [Child IDs]"
    )
    cross_level_relationships: list[CrossLevelRelationship] = Field(
        default_factory=list
    )

    # Consciousness metrics
    overall_consciousness_level: float = Field(default=0.0, ge=0.0, le=1.0)
    emergence_indicators: list[str] = Field(default_factory=list)
    meta_cognitive_insights: list[dict[str, Any]] = Field(default_factory=list)

    # Processing metadata
    total_processing_time: float = Field(default=0.0)
    success: bool = Field(default=True)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def get_concepts_at_level(
        self, level: ConceptExtractionLevel
    ) -> list[ExtractedConcept]:
        """Get all concepts at a specific level."""
        return [c for c in self.all_concepts if c.level == level]

    def get_level_result(
        self, level: ConceptExtractionLevel
    ) -> Optional[LevelExtractionResult]:
        """Get extraction result for a specific level."""
        return self.level_results.get(level.value)
