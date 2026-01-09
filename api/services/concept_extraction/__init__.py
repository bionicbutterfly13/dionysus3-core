"""
Five-Level Concept Extraction Service Package.

Provides hierarchical concept extraction at five levels:
- ATOMIC: Individual terms, entities, definitions
- RELATIONAL: Connections, causality, dependencies
- COMPOSITE: Complex multi-part ideas and systems
- CONTEXTUAL: Domain paradigms, theoretical frameworks
- NARRATIVE: Argument flows, story progressions

Usage:
    from api.services.concept_extraction import get_concept_extraction_service

    service = await get_concept_extraction_service(auto_register=True)
    result = await service.extract_all(content="...", document_id="doc-1")
"""

from .base import BaseLevelExtractor
from .atomic_extractor import AtomicConceptExtractor
from .relational_extractor import RelationalConceptExtractor
from .composite_extractor import CompositeConceptExtractor
from .contextual_extractor import ContextualFrameworkExtractor
from .narrative_extractor import NarrativeStructureExtractor
from .service import (
    FiveLevelConceptExtractionService,
    get_concept_extraction_service,
    register_all_extractors,
)

__all__ = [
    # Base
    "BaseLevelExtractor",
    # Extractors
    "AtomicConceptExtractor",
    "RelationalConceptExtractor",
    "CompositeConceptExtractor",
    "ContextualFrameworkExtractor",
    "NarrativeStructureExtractor",
    # Service
    "FiveLevelConceptExtractionService",
    "get_concept_extraction_service",
    "register_all_extractors",
]
