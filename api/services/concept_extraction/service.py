"""
Five-Level Concept Extraction Service.

Main orchestration service that coordinates all five extraction levels
and provides the unified API for concept extraction.
"""

import logging
import time
from typing import Any, Optional

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    CrossLevelRelationship,
    ExtractedConcept,
    FiveLevelExtractionResult,
    LevelExtractionResult,
)
from .base import BaseLevelExtractor
from .atomic_extractor import AtomicConceptExtractor
from .relational_extractor import RelationalConceptExtractor
from .composite_extractor import CompositeConceptExtractor
from .contextual_extractor import ContextualFrameworkExtractor
from .narrative_extractor import NarrativeStructureExtractor

logger = logging.getLogger(__name__)

# Module-level singleton
_service_instance: Optional["FiveLevelConceptExtractionService"] = None


class FiveLevelConceptExtractionService:
    """Orchestrates five-level concept extraction pipeline."""

    def __init__(self):
        """Initialize the service with empty extractor registry."""
        self._extractors: dict[ConceptExtractionLevel, BaseLevelExtractor] = {}
        self._level_order = [
            ConceptExtractionLevel.ATOMIC,
            ConceptExtractionLevel.RELATIONAL,
            ConceptExtractionLevel.COMPOSITE,
            ConceptExtractionLevel.CONTEXTUAL,
            ConceptExtractionLevel.NARRATIVE,
        ]

    def register_extractor(
        self, level: ConceptExtractionLevel, extractor: BaseLevelExtractor
    ) -> None:
        """Register an extractor for a specific level.

        Args:
            level: The extraction level.
            extractor: The extractor instance to register.
        """
        self._extractors[level] = extractor
        logger.info(f"Registered extractor for level {level.name}")

    def get_extractor(self, level: ConceptExtractionLevel) -> Optional[BaseLevelExtractor]:
        """Get the extractor for a specific level.

        Args:
            level: The extraction level.

        Returns:
            The registered extractor or None.
        """
        return self._extractors.get(level)

    async def extract_all(
        self,
        content: str,
        context: Optional[dict] = None,
        document_id: str = "",
    ) -> FiveLevelExtractionResult:
        """Run full five-level extraction pipeline.

        Args:
            content: Text content to extract concepts from.
            context: Optional context with domain_focus, min_confidence, etc.
            document_id: Optional document identifier for tracking.

        Returns:
            FiveLevelExtractionResult with all extracted concepts.
        """
        start_time = time.time()
        context = context or {}

        result = FiveLevelExtractionResult(
            document_id=document_id,
            level_results={},
            all_concepts=[],
        )

        all_concepts: list[ExtractedConcept] = []
        level_results: dict[int, LevelExtractionResult] = {}

        # Process each level in order, passing accumulated concepts up
        for level in self._level_order:
            extractor = self._extractors.get(level)
            if not extractor:
                logger.warning(f"No extractor registered for level {level.name}")
                # Create empty result for missing level
                level_results[level.value] = LevelExtractionResult(
                    level=level,
                    concepts=[],
                    extraction_time=0.0,
                    content_length=len(content),
                )
                continue

            try:
                level_result = await extractor.extract(
                    content=content,
                    context=context,
                    lower_level_concepts=all_concepts if all_concepts else None,
                )

                level_results[level.value] = level_result
                all_concepts.extend(level_result.concepts)

                logger.info(
                    f"Level {level.name}: extracted {len(level_result.concepts)} concepts"
                )

            except Exception as e:
                logger.error(f"Extraction failed at level {level.name}: {e}")
                result.errors.append(f"Level {level.name} failed: {str(e)}")
                level_results[level.value] = LevelExtractionResult(
                    level=level,
                    concepts=[],
                    extraction_time=0.0,
                    content_length=len(content),
                )

        # Build final result
        result.level_results = level_results
        result.all_concepts = all_concepts
        result.total_processing_time = time.time() - start_time

        # Post-processing: build hierarchy and find cross-level relationships
        result.concept_hierarchy = self._build_hierarchy(all_concepts)
        result.cross_level_relationships = self._find_cross_level_relationships(all_concepts)
        result.overall_consciousness_level = self._calculate_consciousness_level(all_concepts)
        result.meta_cognitive_insights = self._generate_meta_insights(all_concepts, level_results)

        result.success = len(result.errors) == 0

        logger.info(
            f"Extraction complete: {len(all_concepts)} concepts in {result.total_processing_time:.2f}s"
        )
        return result

    def _build_hierarchy(
        self, concepts: list[ExtractedConcept]
    ) -> dict[str, list[str]]:
        """Build parent->children hierarchy from concept relationships.

        Args:
            concepts: All extracted concepts.

        Returns:
            Dict mapping parent concept IDs to lists of child concept IDs.
        """
        hierarchy: dict[str, list[str]] = {}

        for concept in concepts:
            # From explicit parent relationships
            for parent_id in concept.parent_concepts:
                if parent_id not in hierarchy:
                    hierarchy[parent_id] = []
                hierarchy[parent_id].append(concept.concept_id)

            # From composite structures
            if concept.child_concepts:
                hierarchy[concept.concept_id] = concept.child_concepts

        return hierarchy

    def _find_cross_level_relationships(
        self, concepts: list[ExtractedConcept]
    ) -> list[CrossLevelRelationship]:
        """Find relationships between concepts at different levels.

        Detects relationships based on:
        - Name similarity (shared terms)
        - Explicit related_concepts references

        Args:
            concepts: All extracted concepts.

        Returns:
            List of CrossLevelRelationship objects.
        """
        relationships: list[CrossLevelRelationship] = []
        concept_by_id = {c.concept_id: c for c in concepts}
        concept_by_name = {c.name.lower(): c for c in concepts}

        for concept in concepts:
            # Check related_concepts references
            for related_id in concept.related_concepts:
                related = concept_by_id.get(related_id) or concept_by_name.get(
                    related_id.lower()
                )
                if related and related.level != concept.level:
                    rel = CrossLevelRelationship(
                        source_concept_id=concept.concept_id,
                        source_level=concept.level,
                        target_concept_id=related.concept_id,
                        target_level=related.level,
                        relationship_type="related",
                        strength=0.7,
                    )
                    relationships.append(rel)

        return relationships

    def _calculate_consciousness_level(
        self, concepts: list[ExtractedConcept]
    ) -> float:
        """Calculate overall consciousness emergence metric.

        Based on:
        - Coverage across levels (more levels = higher emergence)
        - Average confidence across concepts
        - Interconnection density

        Args:
            concepts: All extracted concepts.

        Returns:
            Consciousness level between 0.0 and 1.0.
        """
        if not concepts:
            return 0.0

        # Level coverage (what % of levels have concepts)
        levels_with_concepts = len(set(c.level for c in concepts))
        level_coverage = levels_with_concepts / len(self._level_order)

        # Average confidence
        avg_confidence = sum(c.confidence for c in concepts) / len(concepts)

        # Interconnection density (concepts with relationships / total)
        connected = sum(
            1 for c in concepts if c.related_concepts or c.parent_concepts or c.child_concepts
        )
        connection_ratio = connected / len(concepts) if concepts else 0

        # Weighted combination
        consciousness = (
            0.3 * level_coverage + 0.4 * avg_confidence + 0.3 * connection_ratio
        )
        return min(1.0, consciousness)

    def _generate_meta_insights(
        self,
        concepts: list[ExtractedConcept],
        level_results: dict[int, LevelExtractionResult],
    ) -> list[dict[str, Any]]:
        """Generate meta-cognitive insights about the extraction.

        Args:
            concepts: All extracted concepts.
            level_results: Results by level.

        Returns:
            List of insight dictionaries.
        """
        insights: list[dict[str, Any]] = []

        # Insight: Level distribution
        level_counts = {}
        for level in ConceptExtractionLevel:
            count = len([c for c in concepts if c.level == level])
            level_counts[level.name] = count

        insights.append({
            "type": "level_distribution",
            "description": "Concept count by extraction level",
            "data": level_counts,
        })

        # Insight: Dominant domains
        all_domains: dict[str, int] = {}
        for c in concepts:
            for domain in c.domain_tags:
                all_domains[domain] = all_domains.get(domain, 0) + 1

        if all_domains:
            insights.append({
                "type": "dominant_domains",
                "description": "Most frequent domain tags",
                "data": dict(sorted(all_domains.items(), key=lambda x: -x[1])[:5]),
            })

        # Insight: Processing efficiency
        total_time = sum(r.extraction_time for r in level_results.values())
        if total_time > 0:
            insights.append({
                "type": "processing_efficiency",
                "description": "Concepts extracted per second",
                "data": {"concepts_per_second": len(concepts) / total_time},
            })

        return insights

    async def store_in_graphiti(
        self,
        result: FiveLevelExtractionResult,
        graphiti_service: Any,
        group_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Store extraction results in Graphiti knowledge graph.

        Args:
            result: The extraction result to store.
            graphiti_service: GraphitiService instance.
            group_id: Optional Graphiti group ID.

        Returns:
            Dict with storage statistics.
        """
        stored_entities = 0
        stored_relationships = 0
        errors: list[str] = []

        for concept in result.all_concepts:
            try:
                # Build context dict for Graphiti's ingest_contextual_triplet
                context_dict = {
                    "confidence": concept.confidence,
                    "details": {
                        "description": concept.description,
                        "source_type": f"concept_{concept.level.name.lower()}",
                        "target_type": "concept_type",
                    }
                }
                
                # Store concept as entity using correct parameter names
                await graphiti_service.ingest_contextual_triplet(
                    head_id=concept.name,
                    relation="is_a",
                    tail_id=concept.concept_type,
                    context=context_dict,
                    group_id=group_id,
                )
                stored_entities += 1

                # Store relationships
                for related_id in concept.related_concepts:
                    rel_context = {
                        "confidence": concept.confidence,
                        "details": {
                            "description": f"Cross-concept relationship from {concept.level.name}",
                            "source_type": f"concept_{concept.level.name.lower()}",
                            "target_type": "concept",
                        }
                    }
                    await graphiti_service.ingest_contextual_triplet(
                        head_id=concept.name,
                        relation="relates_to",
                        tail_id=related_id,
                        context=rel_context,
                        group_id=group_id,
                    )
                    stored_relationships += 1

            except Exception as e:
                errors.append(f"Failed to store {concept.name}: {str(e)}")

        return {
            "stored_entities": stored_entities,
            "stored_relationships": stored_relationships,
            "errors": errors,
        }


def register_all_extractors(service: FiveLevelConceptExtractionService) -> None:
    """Register all five extractors with the service.

    Args:
        service: The service instance to register extractors with.
    """
    service.register_extractor(ConceptExtractionLevel.ATOMIC, AtomicConceptExtractor())
    service.register_extractor(ConceptExtractionLevel.RELATIONAL, RelationalConceptExtractor())
    service.register_extractor(ConceptExtractionLevel.COMPOSITE, CompositeConceptExtractor())
    service.register_extractor(ConceptExtractionLevel.CONTEXTUAL, ContextualFrameworkExtractor())
    service.register_extractor(ConceptExtractionLevel.NARRATIVE, NarrativeStructureExtractor())


async def get_concept_extraction_service(
    auto_register: bool = True,
) -> FiveLevelConceptExtractionService:
    """Get or create the singleton concept extraction service.

    Args:
        auto_register: If True, register all extractors automatically.

    Returns:
        The FiveLevelConceptExtractionService singleton.
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = FiveLevelConceptExtractionService()
        if auto_register:
            register_all_extractors(_service_instance)

    return _service_instance
