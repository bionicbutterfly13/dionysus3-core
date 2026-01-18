"""
Tests for AutoSchemaKG integration service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from api.services.consciousness.autoschemakg_integration import (
    AutoSchemaKGIntegration,
    InferredConcept,
    ConceptType,
    SchemaInferenceResult,
    get_autoschemakg_service,
)


class TestInferredConcept:
    """Tests for InferredConcept dataclass."""

    def test_concept_id_is_deterministic(self):
        """Same name+type should produce same ID."""
        concept1 = InferredConcept(name="Person", concept_type=ConceptType.ENTITY)
        concept2 = InferredConcept(name="Person", concept_type=ConceptType.ENTITY)
        
        assert concept1.concept_id == concept2.concept_id
    
    def test_concept_id_differs_for_different_types(self):
        """Different types should produce different IDs."""
        entity = InferredConcept(name="Create", concept_type=ConceptType.ENTITY)
        event = InferredConcept(name="Create", concept_type=ConceptType.EVENT)
        
        assert entity.concept_id != event.concept_id

    def test_concept_has_expected_length(self):
        """Concept ID should be 16 hex chars."""
        concept = InferredConcept(name="Test", concept_type=ConceptType.RELATION)
        assert len(concept.concept_id) == 16


class TestSchemaInferenceResult:
    """Tests for SchemaInferenceResult dataclass."""

    def test_filters_by_concept_type(self):
        """Should correctly filter concepts by type."""
        result = SchemaInferenceResult(
            episode_id="ep-1",
            concepts=[
                InferredConcept(name="Alice", concept_type=ConceptType.ENTITY),
                InferredConcept(name="Bob", concept_type=ConceptType.ENTITY),
                InferredConcept(name="Meeting", concept_type=ConceptType.EVENT),
                InferredConcept(name="works_with", concept_type=ConceptType.RELATION),
            ],
            triplets=[],
        )
        
        assert len(result.entity_concepts) == 2
        assert len(result.event_concepts) == 1
        assert len(result.relation_concepts) == 1


class TestAutoSchemaKGIntegration:
    """Tests for AutoSchemaKGIntegration service."""

    @pytest.mark.asyncio
    async def test_infer_entity_concept(self):
        """Should correctly infer entity concept hierarchy."""
        service = AutoSchemaKGIntegration()
        
        entity = {"name": "John Smith", "type": "person", "confidence": 0.9}
        concept = await service._infer_entity_concept(entity)
        
        assert concept is not None
        assert concept.name == "John Smith"
        assert concept.concept_type == ConceptType.ENTITY
        assert concept.parent_concept == "Agent"
        assert concept.confidence == 0.9

    @pytest.mark.asyncio
    async def test_infer_entity_concept_with_location(self):
        """Location entities should map to Place hierarchy."""
        service = AutoSchemaKGIntegration()
        
        entity = {"name": "New York", "type": "location"}
        concept = await service._infer_entity_concept(entity)
        
        assert concept.parent_concept == "Place"

    @pytest.mark.asyncio
    async def test_infer_event_concept(self):
        """Should correctly infer event concept hierarchy."""
        service = AutoSchemaKGIntegration()
        
        event = {"name": "Send Message", "type": "communication", "confidence": 0.85}
        concept = await service._infer_event_concept(event)
        
        assert concept is not None
        assert concept.name == "Send Message"
        assert concept.concept_type == ConceptType.EVENT
        assert concept.parent_concept == "Communication"
        assert concept.confidence == 0.85

    @pytest.mark.asyncio
    async def test_infer_relation_concept(self):
        """Should correctly infer relation concept hierarchy."""
        service = AutoSchemaKGIntegration()
        
        relation = {"type": "causes", "source": "A", "target": "B", "confidence": 0.7}
        concept = await service._infer_relation_concept(relation)
        
        assert concept is not None
        assert concept.name == "causes"
        assert concept.concept_type == ConceptType.RELATION
        assert concept.parent_concept == "Causal"
        assert concept.attributes["source"] == "A"
        assert concept.attributes["target"] == "B"

    @pytest.mark.asyncio
    async def test_infer_schema_with_entities(self):
        """Should infer schema from pre-extracted entities."""
        service = AutoSchemaKGIntegration()
        
        entities = [
            {"name": "Alice", "type": "person"},
            {"name": "Acme Corp", "type": "organization"},
        ]
        
        result = await service.infer_schema(
            episode_id="ep-test-1",
            entities=entities,
        )
        
        assert result.episode_id == "ep-test-1"
        assert len(result.concepts) == 2
        assert len(result.triplets) == 2
        assert result.metadata["entity_count"] == 2
        assert result.metadata["event_count"] == 0

    @pytest.mark.asyncio
    async def test_infer_schema_with_mixed_elements(self):
        """Should handle mixed entities, events, and relations."""
        service = AutoSchemaKGIntegration()
        
        result = await service.infer_schema(
            episode_id="ep-mixed",
            entities=[{"name": "User", "type": "person"}],
            events=[{"name": "Login", "type": "action"}],
            relations=[{"type": "triggers", "source": "User", "target": "Login"}],
        )
        
        assert len(result.concepts) == 3
        assert result.metadata["entity_count"] == 1
        assert result.metadata["event_count"] == 1
        assert result.metadata["relation_count"] == 1

    @pytest.mark.asyncio
    async def test_concept_to_triplet_format(self):
        """Should correctly format concept as triplet."""
        service = AutoSchemaKGIntegration()
        
        concept = InferredConcept(
            name="Alice",
            concept_type=ConceptType.ENTITY,
            parent_concept="Agent",
            confidence=0.9,
            attributes={"original_type": "person"},
        )
        
        triplet = service._concept_to_triplet(concept, "ep-123")
        
        assert triplet["head_id"] == "Alice"
        assert triplet["relation"] == "instance_of"
        assert triplet["tail_id"] == "Agent"
        assert triplet["context"]["confidence"] == 0.9
        assert triplet["context"]["details"]["source_episode"] == "ep-123"

    @pytest.mark.asyncio
    async def test_store_schema_uses_graphiti(self):
        """Should store schema via Graphiti ingest_contextual_triplet."""
        mock_graphiti = AsyncMock()
        mock_graphiti.ingest_contextual_triplet.return_value = True
        
        service = AutoSchemaKGIntegration(graphiti_service=mock_graphiti)
        
        result = SchemaInferenceResult(
            episode_id="ep-store-test",
            concepts=[
                InferredConcept(
                    name="TestEntity",
                    concept_type=ConceptType.ENTITY,
                    parent_concept="Agent",
                )
            ],
            triplets=[
                {
                    "head_id": "TestEntity",
                    "relation": "instance_of",
                    "tail_id": "Agent",
                    "context": {"confidence": 1.0, "details": {}},
                }
            ],
        )
        
        storage_result = await service.store_schema(result, group_id="test-group")
        
        assert storage_result["stored"] >= 1
        assert mock_graphiti.ingest_contextual_triplet.called
        
        # Check call args
        call_kwargs = mock_graphiti.ingest_contextual_triplet.call_args_list[0].kwargs
        assert call_kwargs["head_id"] == "TestEntity"
        assert call_kwargs["group_id"] == "test-group"

    @pytest.mark.asyncio
    async def test_infer_and_store_convenience_method(self):
        """Should infer and store in one call."""
        mock_graphiti = AsyncMock()
        mock_graphiti.ingest_contextual_triplet.return_value = True
        
        service = AutoSchemaKGIntegration(graphiti_service=mock_graphiti)
        
        result = await service.infer_and_store(
            episode_id="ep-convenience",
            entities=[{"name": "Bob", "type": "person"}],
            group_id="test-group",
        )
        
        assert "inference" in result
        assert "storage" in result
        assert result["inference"]["concept_count"] == 1
        assert result["storage"]["episode_id"] == "ep-convenience"


class TestGetAutoSchemaKGService:
    """Tests for the singleton getter."""

    def test_returns_instance(self):
        """Should return an AutoSchemaKGIntegration instance."""
        # Reset singleton for test
        import api.services.consciousness.autoschemakg_integration as module
        module._autoschemakg_instance = None
        
        service = get_autoschemakg_service()
        assert isinstance(service, AutoSchemaKGIntegration)

    def test_returns_same_instance(self):
        """Should return the same instance on subsequent calls."""
        import api.services.consciousness.autoschemakg_integration as module
        module._autoschemakg_instance = None
        
        service1 = get_autoschemakg_service()
        service2 = get_autoschemakg_service()
        
        assert service1 is service2
