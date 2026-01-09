"""
Domain Specialization Models.

Pydantic v2 models for neuroscience/AI domain specialization:
- Domain types and concept categories
- Domain concepts with rich metadata
- Academic structure and citations
- Cross-domain mappings

Migrated from Dionysus 2.0 domain_specialization.py.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DomainType(str, Enum):
    """Specialized domain types for content analysis."""

    NEUROSCIENCE = "neuroscience"
    ARTIFICIAL_INTELLIGENCE = "artificial_intelligence"
    COMPUTATIONAL_NEUROSCIENCE = "computational_neuroscience"
    COGNITIVE_SCIENCE = "cognitive_science"
    MACHINE_LEARNING = "machine_learning"
    DEEP_LEARNING = "deep_learning"
    BIOINFORMATICS = "bioinformatics"
    NEUROMORPHIC_COMPUTING = "neuromorphic_computing"


class ConceptCategory(str, Enum):
    """Categories of domain concepts."""

    ANATOMICAL = "anatomical"
    PHYSIOLOGICAL = "physiological"
    MOLECULAR = "molecular"
    ALGORITHMIC = "algorithmic"
    ARCHITECTURAL = "architectural"
    THEORETICAL = "theoretical"
    METHODOLOGICAL = "methodological"
    CLINICAL = "clinical"


class AcademicSection(str, Enum):
    """Standard academic paper sections."""

    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    BACKGROUND = "background"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    APPENDIX = "appendix"


class DomainConcept(BaseModel):
    """Specialized domain concept with rich metadata."""

    concept_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str = Field(default="", description="The concept term or name")
    definition: str = Field(default="", description="Definition of the concept")
    domain: DomainType = Field(
        default=DomainType.NEUROSCIENCE, description="Primary domain"
    )
    category: ConceptCategory = Field(
        default=ConceptCategory.THEORETICAL, description="Concept category"
    )

    # Terminology data
    synonyms: list[str] = Field(default_factory=list, description="Alternative names")
    abbreviations: list[str] = Field(default_factory=list, description="Common abbreviations")
    related_terms: list[str] = Field(default_factory=list, description="Related concepts")

    # Domain-specific metadata
    anatomical_location: Optional[str] = Field(
        default=None, description="For neuroscience: anatomical location"
    )
    molecular_pathway: Optional[str] = Field(
        default=None, description="For neuroscience: molecular pathway"
    )
    algorithm_family: Optional[str] = Field(
        default=None, description="For AI: algorithm family"
    )
    neural_mechanism: Optional[str] = Field(
        default=None, description="For neuroscience: underlying mechanism"
    )

    # Cross-domain mappings
    cross_domain_equivalents: dict[str, str] = Field(
        default_factory=dict, description="Equivalent concepts in other domains"
    )
    analogies: list[dict[str, str]] = Field(
        default_factory=list, description="Analogies to other concepts"
    )

    # Academic context
    typical_contexts: list[str] = Field(
        default_factory=list, description="Typical usage contexts"
    )
    research_areas: list[str] = Field(
        default_factory=list, description="Related research areas"
    )
    key_papers: list[str] = Field(
        default_factory=list, description="Key papers referencing this concept"
    )

    # Usage patterns
    frequency_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Usage frequency score"
    )
    importance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Domain importance score"
    )
    complexity_level: int = Field(
        default=1, ge=1, le=5, description="Complexity level 1-5"
    )

    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="manual", description="Source of concept data")


class Citation(BaseModel):
    """Academic citation with metadata."""

    citation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_text: str = Field(default="", description="Raw citation text")
    authors: list[str] = Field(default_factory=list, description="List of authors")
    title: str = Field(default="", description="Paper/article title")
    journal: str = Field(default="", description="Journal name")
    year: Optional[int] = Field(default=None, description="Publication year")
    volume: Optional[str] = Field(default=None, description="Journal volume")
    pages: Optional[str] = Field(default=None, description="Page numbers")
    doi: Optional[str] = Field(default=None, description="DOI identifier")
    pmid: Optional[str] = Field(default=None, description="PubMed ID")

    # Context
    citation_type: str = Field(
        default="reference", description="Type: reference, in_text, footnote"
    )
    section: Optional[AcademicSection] = Field(
        default=None, description="Section where citation appears"
    )
    context_sentence: str = Field(
        default="", description="Sentence containing the citation"
    )

    # Domain classification
    primary_domain: Optional[DomainType] = Field(
        default=None, description="Primary domain of cited work"
    )
    research_area: str = Field(default="", description="Research area")
    methodology: str = Field(default="", description="Methodology used")


class SectionInfo(BaseModel):
    """Information about a detected academic section."""

    found: bool = Field(default=False, description="Whether section was detected")
    position: int = Field(default=0, description="Character position in text")
    text: str = Field(default="", description="Matched text")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Detection confidence"
    )


class AcademicStructure(BaseModel):
    """Detected academic paper structure."""

    document_type: str = Field(default="research_paper", description="Type of document")
    detected_sections: dict[str, SectionInfo] = Field(
        default_factory=dict, description="Detected sections with metadata"
    )
    abstract_present: bool = Field(default=False, description="Whether abstract is present")
    methodology_described: bool = Field(
        default=False, description="Whether methodology is described"
    )
    results_reported: bool = Field(default=False, description="Whether results are reported")
    citations_found: list[Citation] = Field(
        default_factory=list, description="Citations found in document"
    )

    # Quality metrics
    structure_completeness: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Completeness of academic structure"
    )
    academic_rigor_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Academic rigor score"
    )
    domain_specificity: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Domain specificity score"
    )


class CrossDomainMapping(BaseModel):
    """Mapping between concepts in different domains."""

    source_concept: str = Field(..., description="Source concept term")
    source_domain: DomainType = Field(..., description="Source domain")
    target_concept: str = Field(..., description="Target concept term")
    target_domain: DomainType = Field(..., description="Target domain")
    mapping_type: str = Field(
        default="functional_analogy",
        description="Type: functional_analogy, mechanistic_analogy, learning_analogy",
    )
    strength: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Mapping strength"
    )
    description: str = Field(default="", description="Description of the mapping")
    similarities: list[str] = Field(
        default_factory=list, description="Similarities between concepts"
    )
    differences: list[str] = Field(
        default_factory=list, description="Differences between concepts"
    )


class DomainBridge(BaseModel):
    """A cross-domain bridge found in text."""

    neuro_concept: str = Field(..., description="Neuroscience concept")
    ai_concept: str = Field(..., description="AI concept")
    mapping: CrossDomainMapping = Field(..., description="The mapping between concepts")
    bridge_strength: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Bridge strength"
    )
    context: str = Field(default="", description="Context in which bridge was found")


class DomainAnalysisResult(BaseModel):
    """Result of domain analysis on text content."""

    success: bool = Field(default=True, description="Whether analysis succeeded")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    processing_time: float = Field(default=0.0, description="Processing time in seconds")

    # Domain analysis
    neuroscience_concepts: list[dict[str, Any]] = Field(
        default_factory=list, description="Detected neuroscience concepts"
    )
    ai_concepts: list[dict[str, Any]] = Field(
        default_factory=list, description="Detected AI concepts"
    )
    primary_domain: str = Field(
        default="interdisciplinary",
        description="Primary domain: neuroscience_primary, ai_primary, interdisciplinary",
    )
    domain_mix_ratio: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Ratio of neuro to AI concepts"
    )

    # Academic structure
    academic_structure: Optional[AcademicStructure] = Field(
        default=None, description="Detected academic structure"
    )

    # Cross-domain mappings
    cross_domain_mappings: list[dict[str, Any]] = Field(
        default_factory=list, description="Cross-domain concept bridges"
    )

    # Specialized prompts for extraction
    specialized_prompts: dict[str, str] = Field(
        default_factory=dict, description="Domain-specific extraction prompts"
    )

    # Quality metrics
    domain_specificity: float = Field(
        default=0.0, description="Domain-specific terminology density"
    )
    cross_domain_connectivity: int = Field(
        default=0, description="Number of cross-domain bridges"
    )
    academic_completeness: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Academic structure completeness"
    )
    terminology_density: float = Field(
        default=0.0, description="Density of domain terms"
    )
    complexity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall complexity score"
    )


class DomainAnalysisRequest(BaseModel):
    """Request for domain analysis."""

    content: str = Field(..., min_length=1, description="Text content to analyze")
    domain_focus: list[str] = Field(
        default_factory=lambda: ["neuroscience", "artificial_intelligence"],
        description="Domains to focus on",
    )
    include_prompts: bool = Field(
        default=True, description="Include specialized extraction prompts"
    )
    max_concepts: int = Field(
        default=50, ge=1, le=200, description="Maximum concepts to return"
    )
