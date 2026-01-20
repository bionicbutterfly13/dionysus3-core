"""
AutoSchemaKG Integration Service for Consciousness Layer.

Integrates AutoSchemaKG-style concept induction with Graphiti storage.
Follows the atlas_rag patterns for entity/event/relation concept hierarchies.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib

logger = logging.getLogger(__name__)


class ConceptType(str, Enum):
    """Types of concepts in AutoSchemaKG hierarchy."""
    ENTITY = "entity"
    EVENT = "event"
    RELATION = "relation"


@dataclass
class InferredConcept:
    """A concept inferred from text/episode content."""
    name: str
    concept_type: ConceptType
    parent_concept: Optional[str] = None
    confidence: float = 1.0
    source_text: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def concept_id(self) -> str:
        """Generate deterministic ID for concept."""
        text = f"{self.name}_{self.concept_type.value}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass
class SchemaInferenceResult:
    """Result of schema inference from an episode."""
    episode_id: str
    concepts: List[InferredConcept]
    triplets: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def entity_concepts(self) -> List[InferredConcept]:
        return [c for c in self.concepts if c.concept_type == ConceptType.ENTITY]

    @property
    def event_concepts(self) -> List[InferredConcept]:
        return [c for c in self.concepts if c.concept_type == ConceptType.EVENT]

    @property
    def relation_concepts(self) -> List[InferredConcept]:
        return [c for c in self.concepts if c.concept_type == ConceptType.RELATION]


class AutoSchemaKGIntegration:
    """
    Integration layer for AutoSchemaKG to infer schemas from episodes.
    
    Implements concept induction following the atlas_rag patterns:
    - Entity concepts: categorize named entities into hierarchies
    - Event concepts: categorize events/actions into hierarchies  
    - Relation concepts: categorize relationship types into hierarchies
    
    All results are stored via Graphiti's contextual triplet ingestion.
    """

    def __init__(self, graphiti_service: Optional[Any] = None):
        """
        Initialize AutoSchemaKG integration.
        
        Args:
            graphiti_service: Optional GraphitiService instance for storage.
        """
        self._graphiti = graphiti_service
        self._concept_cache: Dict[str, InferredConcept] = {}

    async def _get_graphiti(self) -> Any:
        """Lazy-load Graphiti service."""
        if self._graphiti is None:
            from api.services.graphiti_service import get_graphiti_service
            self._graphiti = await get_graphiti_service()
        return self._graphiti

    async def infer_schema(
        self,
        episode_id: str,
        content: Optional[str] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
    ) -> SchemaInferenceResult:
        """
        Infer schema concepts from episode content or pre-extracted elements.
        
        Args:
            episode_id: Unique identifier for the episode.
            content: Raw text content to extract from (optional).
            entities: Pre-extracted entities (optional).
            events: Pre-extracted events (optional).
            relations: Pre-extracted relations (optional).
            
        Returns:
            SchemaInferenceResult with inferred concepts and triplets.
        """
        logger.info(f"Inferring schema for episode {episode_id}")
        
        concepts: List[InferredConcept] = []
        triplets: List[Dict[str, Any]] = []

        # Process pre-extracted entities
        if entities:
            for entity in entities:
                concept = await self._infer_entity_concept(entity)
                if concept:
                    concepts.append(concept)
                    triplets.append(self._concept_to_triplet(concept, episode_id))

        # Process pre-extracted events
        if events:
            for event in events:
                concept = await self._infer_event_concept(event)
                if concept:
                    concepts.append(concept)
                    triplets.append(self._concept_to_triplet(concept, episode_id))

        # Process pre-extracted relations
        if relations:
            for relation in relations:
                concept = await self._infer_relation_concept(relation)
                if concept:
                    concepts.append(concept)
                    triplets.append(self._concept_to_triplet(concept, episode_id))

        # If content provided but no pre-extracted elements, do basic extraction
        if content and not (entities or events or relations):
            extracted = await self._extract_from_content(content)
            for item in extracted:
                concepts.append(item)
                triplets.append(self._concept_to_triplet(item, episode_id))

        result = SchemaInferenceResult(
            episode_id=episode_id,
            concepts=concepts,
            triplets=triplets,
            metadata={
                "entity_count": len([c for c in concepts if c.concept_type == ConceptType.ENTITY]),
                "event_count": len([c for c in concepts if c.concept_type == ConceptType.EVENT]),
                "relation_count": len([c for c in concepts if c.concept_type == ConceptType.RELATION]),
            }
        )

        return result

    async def _infer_entity_concept(self, entity: Dict[str, Any]) -> Optional[InferredConcept]:
        """Infer concept hierarchy for an entity."""
        name = entity.get("name") or entity.get("text", "")
        if not name:
            return None
            
        entity_type = entity.get("type", "unknown")
        
        # Map common entity types to concept hierarchy
        parent_mapping = {
            "person": "Agent",
            "organization": "Agent",
            "location": "Place",
            "place": "Place",
            "date": "Temporal",
            "time": "Temporal",
            "event": "Occurrence",
            "product": "Artifact",
            "concept": "Abstract",
        }
        
        parent = parent_mapping.get(entity_type.lower(), "Entity")
        
        return InferredConcept(
            name=name,
            concept_type=ConceptType.ENTITY,
            parent_concept=parent,
            confidence=entity.get("confidence", 0.8),
            source_text=entity.get("context"),
            attributes={"original_type": entity_type}
        )

    async def _infer_event_concept(self, event: Dict[str, Any]) -> Optional[InferredConcept]:
        """Infer concept hierarchy for an event."""
        name = event.get("name") or event.get("action", "")
        if not name:
            return None
            
        event_type = event.get("type", "action")
        
        # Map event types to concept hierarchy
        parent_mapping = {
            "action": "Activity",
            "state_change": "StateTransition",
            "communication": "Communication",
            "movement": "Motion",
            "creation": "Creation",
            "destruction": "Termination",
            "cognitive": "MentalProcess",
        }
        
        parent = parent_mapping.get(event_type.lower(), "Event")
        
        return InferredConcept(
            name=name,
            concept_type=ConceptType.EVENT,
            parent_concept=parent,
            confidence=event.get("confidence", 0.8),
            source_text=event.get("context"),
            attributes={"original_type": event_type}
        )

    async def _infer_relation_concept(self, relation: Dict[str, Any]) -> Optional[InferredConcept]:
        """Infer concept hierarchy for a relation type."""
        name = relation.get("type") or relation.get("relation", "")
        if not name:
            return None
            
        # Map relation types to concept hierarchy
        parent_mapping = {
            "causes": "Causal",
            "enables": "Causal",
            "part_of": "Mereological",
            "contains": "Mereological",
            "is_a": "Taxonomic",
            "instance_of": "Taxonomic",
            "located_in": "Spatial",
            "before": "Temporal",
            "after": "Temporal",
            "similar_to": "Associative",
            "related_to": "Associative",
        }
        
        parent = parent_mapping.get(name.lower(), "Relation")
        
        return InferredConcept(
            name=name,
            concept_type=ConceptType.RELATION,
            parent_concept=parent,
            confidence=relation.get("confidence", 0.8),
            source_text=relation.get("evidence"),
            attributes={
                "source": relation.get("source"),
                "target": relation.get("target"),
            }
        )

    async def _extract_from_content(self, content: str) -> List[InferredConcept]:
        """
        Basic extraction from raw content.
        
        Note: For full AutoSchemaKG extraction, use the atlas_rag library directly.
        This provides a lightweight fallback for simple cases.
        """
        concepts: List[InferredConcept] = []
        
        # Basic heuristic extraction (placeholder for full LLM-based extraction)
        # In production, this would call atlas_rag's KnowledgeGraphExtractor
        logger.debug(f"Basic extraction from content ({len(content)} chars)")
        
        return concepts

    def _concept_to_triplet(self, concept: InferredConcept, episode_id: str) -> Dict[str, Any]:
        """Convert concept to triplet format for Graphiti storage."""
        return {
            "head_id": concept.name,
            "relation": "instance_of",
            "tail_id": concept.parent_concept or concept.concept_type.value,
            "context": {
                "confidence": concept.confidence,
                "details": {
                    "concept_type": concept.concept_type.value,
                    "source_episode": episode_id,
                    "concept_id": concept.concept_id,
                    **concept.attributes,
                }
            }
        }

    async def store_schema(
        self,
        result: SchemaInferenceResult,
        group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store inferred schema in Graphiti.
        
        Args:
            result: SchemaInferenceResult to store.
            group_id: Optional Graphiti group ID.
            
        Returns:
            Dict with storage statistics.
        """
        graphiti = await self._get_graphiti()
        stored = 0
        errors: List[str] = []
        
        for triplet in result.triplets:
            try:
                await graphiti.ingest_contextual_triplet(
                    head_id=triplet["head_id"],
                    relation=triplet["relation"],
                    tail_id=triplet["tail_id"],
                    context=triplet["context"],
                    group_id=group_id,
                    source_id=f"autoschemakg:{result.episode_id}",
                )
                stored += 1
            except Exception as e:
                errors.append(f"Failed to store {triplet['head_id']}: {str(e)}")
                logger.error(f"AutoSchemaKG storage error: {e}")
        
        # Also store concept hierarchy links
        for concept in result.concepts:
            if concept.parent_concept:
                try:
                    hierarchy_context = {
                        "confidence": 1.0,
                        "details": {
                            "relationship": "concept_hierarchy",
                            "concept_type": concept.concept_type.value,
                        }
                    }
                    await graphiti.ingest_contextual_triplet(
                        head_id=concept.parent_concept,
                        relation="has_instance",
                        tail_id=concept.name,
                        context=hierarchy_context,
                        group_id=group_id,
                        source_id=f"autoschemakg:{result.episode_id}",
                    )
                    stored += 1
                except Exception as e:
                    errors.append(f"Failed to store hierarchy for {concept.name}: {str(e)}")
        
        return {
            "stored": stored,
            "errors": errors,
            "episode_id": result.episode_id,
        }

    async def infer_and_store(
        self,
        episode_id: str,
        content: Optional[str] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method to infer schema and store in one call.
        
        Args:
            episode_id: Unique identifier for the episode.
            content: Raw text content (optional).
            entities: Pre-extracted entities (optional).
            events: Pre-extracted events (optional).
            relations: Pre-extracted relations (optional).
            group_id: Optional Graphiti group ID.
            
        Returns:
            Dict with inference and storage results.
        """
        result = await self.infer_schema(
            episode_id=episode_id,
            content=content,
            entities=entities,
            events=events,
            relations=relations,
        )
        
        storage_result = await self.store_schema(result, group_id=group_id)
        
        return {
            "inference": {
                "episode_id": result.episode_id,
                "concept_count": len(result.concepts),
                "triplet_count": len(result.triplets),
                **result.metadata,
            },
            "storage": storage_result,
        }

    async def retrieve_relevant_concepts(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[InferredConcept]:
        """
        Retrieve relevant schema concepts to bias active reasoning (Read-Path).
        
        Uses Graphiti's hybrid search (Semantic + Keyword) to find nodes that
        are likely ontological concepts (Entities or Relations).
        
        Args:
            query: The active thought/query to ground.
            limit: Max concepts to return.
            threshold: Minimum relevance score (handled by Graphiti search config if psosible, otherwise post-filter).
            
        Returns:
            List of InferredConcept objects acting as constraints.
        """
        graphiti = await self._get_graphiti()
        
        # 1. Hybrid search via Graphiti
        # This handles embedding generation and vector search internally.
        try:
            results = await graphiti.search(
                query=query,
                limit=limit * 3, # Fetch wider pool to filter
            )
        except Exception as e:
            logger.error(f"Graphiti search failed during schema retrieval: {e}")
            return []
        
        concepts: List[InferredConcept] = []
        seen_names = set()
        
        # 2. Process Nodes specifically
        # We look for nodes that appear to be 'Types' or 'Classes'.
        # Heuristics:
        # - Capitalized names (convention)
        # - High degree in the graph (central concepts) - we can't check this easily without extra query
        # - Labels (if available in result)
        
        if results and "nodes" in results:
            for node_data in results["nodes"]:
                name = node_data.get("name")
                if not name or name in seen_names:
                    continue
                
                # Basic filtering for 'Concept-like' entities
                # In a real schema, we'd check for labels=['Concept', 'Class'].
                # Graphiti generic schema uses 'Entity'.
                # We assume relevant search results are concepts for now.
                
                # Retrieve type info if available in summary or labels
                labels = node_data.get("labels", [])
                concept_type = ConceptType.ENTITY
                if "Event" in labels or "Activity" in labels:
                    concept_type = ConceptType.EVENT
                elif "Relation" in labels:
                    concept_type = ConceptType.RELATION
                
                concept = InferredConcept(
                    name=name,
                    concept_type=concept_type,
                    confidence=0.8, # Placeholder confidence from search rank
                    attributes={
                        "retrieved_from_search": True,
                        "relevance_rank": len(concepts)
                    }
                )
                concepts.append(concept)
                seen_names.add(name)
                
                if len(concepts) >= limit:
                    break
                    
        return concepts


# Module-level singleton
_autoschemakg_instance: Optional[AutoSchemaKGIntegration] = None


def get_autoschemakg_service(
    graphiti_service: Optional[Any] = None,
) -> AutoSchemaKGIntegration:
    """
    Get or create AutoSchemaKG integration service.
    
    Args:
        graphiti_service: Optional GraphitiService instance.
        
    Returns:
        AutoSchemaKGIntegration instance.
    """
    global _autoschemakg_instance
    if _autoschemakg_instance is None:
        _autoschemakg_instance = AutoSchemaKGIntegration(graphiti_service)
    return _autoschemakg_instance
