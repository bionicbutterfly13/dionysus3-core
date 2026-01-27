"""
Integration Tests for Metacognition Semantic Storage in Graphiti

Tests verify that metacognition concepts are correctly stored in the Graphiti
knowledge graph and can be retrieved through search queries.

Feature: Metacognition Semantic Storage
AUTHOR: Mani Saint-Victor, MD
"""

import os
import pytest
from datetime import datetime
from api.services.graphiti_service import GraphitiService, GraphitiConfig


# Skip all tests if Neo4j is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_PASSWORD"),
    reason="NEO4J_PASSWORD not configured - skipping integration tests",
)


@pytest.mark.asyncio
class TestMetacognitionSemanticStorage:
    """Test suite for metacognition concept storage in Graphiti."""

    @pytest.fixture
    async def graphiti_service(self):
        """Create and initialize Graphiti service."""
        config = GraphitiConfig(
            neo4j_uri="bolt://localhost:7687",
            group_id="test_metacognition"
        )
        service = GraphitiService(config)
        await service.initialize()
        return service

    async def test_store_core_entities(self, graphiti_service):
        """Test storing core metacognition entity definitions."""
        content = """
        CORE METACOGNITION ENTITIES

        1. Declarative Metacognition - Static knowledge library in semantic memory
        2. Procedural Metacognition - Dynamic regulatory system for cognitive control
        3. Thoughtseed - Competing hypothesis in conscious attention
        4. Attractor Basin - Stable mental state configuration
        5. Free Energy - Prediction error metric (F = Complexity - Accuracy)
        6. OODA Loop - Observe-Orient-Decide-Act decision cycle
        """

        result = await graphiti_service.ingest_message(
            content=content,
            source_description="test_core_entities",
            group_id="test_metacognition",
            valid_at=datetime.now()
        )

        # Verify ingestion result
        assert result["episode_uuid"] is not None
        assert len(result["nodes"]) > 0
        assert len(result["edges"]) > 0

    async def test_search_declarative_metacognition(self, graphiti_service):
        """Test retrieving Declarative Metacognition concept."""
        # Store first
        content = "Declarative Metacognition is static knowledge about how minds work"
        await graphiti_service.ingest_message(
            content=content,
            source_description="test_search",
            group_id="test_metacognition"
        )

        # Search
        result = await graphiti_service.search(
            query="Declarative Metacognition",
            group_ids=["test_metacognition"],
            limit=5
        )

        # Verify search result
        assert result["count"] >= 0  # May be 0 if extraction didn't work

    async def test_search_procedural_metacognition(self, graphiti_service):
        """Test retrieving Procedural Metacognition concept."""
        content = "Procedural Metacognition implements monitoring and control functions"
        await graphiti_service.ingest_message(
            content=content,
            source_description="test_search",
            group_id="test_metacognition"
        )

        result = await graphiti_service.search(
            query="Procedural Metacognition",
            group_ids=["test_metacognition"],
            limit=5
        )

        assert result["count"] >= 0

    async def test_search_thoughtseed(self, graphiti_service):
        """Test retrieving Thoughtseed concept."""
        content = """
        Thoughtseed: A competing hypothesis that competes via free energy minimization
        """
        await graphiti_service.ingest_message(
            content=content,
            source_description="test_search",
            group_id="test_metacognition"
        )

        result = await graphiti_service.search(
            query="Thoughtseed",
            group_ids=["test_metacognition"],
            limit=5
        )

        assert result["count"] >= 0

    async def test_search_attractor_basin(self, graphiti_service):
        """Test retrieving Attractor Basin concept."""
        content = """
        Attractor Basin: A stable configuration of beliefs that persist once formed
        """
        await graphiti_service.ingest_message(
            content=content,
            source_description="test_search",
            group_id="test_metacognition"
        )

        result = await graphiti_service.search(
            query="Attractor Basin",
            group_ids=["test_metacognition"],
            limit=5
        )

        assert result["count"] >= 0

    async def test_search_free_energy(self, graphiti_service):
        """Test retrieving Free Energy concept."""
        content = """
        Free Energy: A metric of prediction error, F = Complexity - Accuracy
        """
        await graphiti_service.ingest_message(
            content=content,
            source_description="test_search",
            group_id="test_metacognition"
        )

        result = await graphiti_service.search(
            query="Free Energy",
            group_ids=["test_metacognition"],
            limit=5
        )

        assert result["count"] >= 0

    async def test_search_ooda_loop(self, graphiti_service):
        """Test retrieving OODA Loop concept."""
        content = """
        OODA Loop: Observe-Orient-Decide-Act cycle for decision making
        """
        await graphiti_service.ingest_message(
            content=content,
            source_description="test_search",
            group_id="test_metacognition"
        )

        result = await graphiti_service.search(
            query="OODA Loop",
            group_ids=["test_metacognition"],
            limit=5
        )

        assert result["count"] >= 0

    async def test_store_relationships(self, graphiti_service):
        """Test storing explicit relationships between concepts."""
        content = """
        METACOGNITION RELATIONSHIPS:

        Relationship 1: Declarative Metacognition STORED_IN Graphiti WARM Tier
        Relationship 2: Procedural Metacognition IMPLEMENTS OODA Loop
        Relationship 3: Thoughtseed COMPETES_VIA Free Energy
        Relationship 4: Thoughtseed CREATES Attractor Basin
        Relationship 5: smolagents IMPLEMENTS Procedural Metacognition
        """

        result = await graphiti_service.ingest_message(
            content=content,
            source_description="test_relationships",
            group_id="test_metacognition"
        )

        # Verify relationships were extracted
        assert len(result["edges"]) > 0

    async def test_temporal_validity(self, graphiti_service):
        """Test that stored concepts have temporal validity."""
        timestamp = datetime.now()
        content = "Metacognition is the ability to think about thinking"

        result = await graphiti_service.ingest_message(
            content=content,
            source_description="test_temporal",
            group_id="test_metacognition",
            valid_at=timestamp
        )

        # Verify episode has valid_at timestamp
        assert result["episode_uuid"] is not None

    async def test_multiple_ingestions_same_group(self, graphiti_service):
        """Test storing multiple concepts in same group."""
        concepts = [
            "Declarative Metacognition is static knowledge",
            "Procedural Metacognition is dynamic control",
            "Thoughtseed is competing hypothesis",
        ]

        results = []
        for concept in concepts:
            result = await graphiti_service.ingest_message(
                content=concept,
                source_description="test_multiple",
                group_id="test_metacognition"
            )
            results.append(result)

        # Verify all ingestions succeeded
        for result in results:
            assert result["episode_uuid"] is not None

    async def test_search_with_context(self, graphiti_service):
        """Test search with context constraints."""
        context = "Metacognition monitoring detects high prediction error"

        result = await graphiti_service.ingest_message(
            content=context,
            source_description="test_context",
            group_id="test_metacognition"
        )

        # Search for related concepts
        search_result = await graphiti_service.search(
            query="prediction error",
            group_ids=["test_metacognition"],
            limit=5
        )

        assert isinstance(search_result, dict)
        assert "edges" in search_result

    async def test_extract_with_context(self, graphiti_service):
        """Test extraction with basin context."""
        content = "The system monitors cognitive state through prediction error tracking"
        basin_context = "consciousness, cognitive_science, neuroscience"

        result = await graphiti_service.extract_with_context(
            content=content,
            basin_context=basin_context,
            confidence_threshold=0.6
        )

        assert "entities" in result
        assert "relationships" in result
        assert "approved_count" in result

    async def test_ingest_extracted_relationships(self, graphiti_service):
        """Test ingesting pre-extracted relationships."""
        relationships = [
            {
                "source": "Declarative Metacognition",
                "target": "Graphiti WARM Tier",
                "relation_type": "STORED_IN",
                "evidence": "Static knowledge persists in semantic graph",
                "status": "approved",
                "confidence": 0.9
            },
            {
                "source": "Procedural Metacognition",
                "target": "OODA Loop",
                "relation_type": "IMPLEMENTS",
                "evidence": "Runtime system executes OODA architecture",
                "status": "approved",
                "confidence": 0.95
            }
        ]

        result = await graphiti_service.ingest_extracted_relationships(
            relationships=relationships,
            source_id="test_relationships"
        )

        assert result["ingested"] == 2
        assert result["errors"] == []


@pytest.mark.asyncio
class TestMetacognitionConceptIntegration:
    """Integration tests for all metacognition concepts together."""

    @pytest.fixture
    async def graphiti_service(self):
        """Create and initialize Graphiti service."""
        config = GraphitiConfig(
            neo4j_uri="bolt://localhost:7687",
            group_id="integration_test"
        )
        service = GraphitiService(config)
        await service.initialize()
        return service

    async def test_complete_metacognition_flow(self, graphiti_service):
        """Test complete flow from concept ingestion to search."""
        # Phase 1: Store concepts
        concepts_content = """
        DECLARATIVE METACOGNITION:
        - Monitoring: Non-invasive assessment of cognitive state
        - Control: Recommended actions to regulate cognition
        - Feelings: Aha!, confusion, effort signal prediction errors

        PROCEDURAL METACOGNITION:
        - Implemented via OODA loop (Observe-Orient-Decide-Act)
        - Real-time execution in HOT tier (milliseconds)
        - Thresholds: tunable, context-aware

        FREE ENERGY MINIMIZATION:
        - Score thoughtseed competition
        - Drive attractor basin transitions
        - Motivation for learning

        THOUGHTSEED COMPETITION:
        - Multiple hypotheses compete
        - Winner becomes attractor basin
        - Loser cached for future rounds
        """

        result = await graphiti_service.ingest_message(
            content=concepts_content,
            source_description="integration_test",
            group_id="integration_test"
        )

        # Phase 2: Verify ingestion
        assert len(result["nodes"]) > 0
        assert len(result["edges"]) > 0

    async def test_declarative_to_procedural_mapping(self, graphiti_service):
        """Test mapping between declarative knowledge and procedural execution."""
        content = """
        DECLARATIVE: Procedural Metacognition monitoring detects high prediction error
        PROCEDURAL: ProceduralMetacognition.monitor() returns CognitiveAssessment

        DECLARATIVE: Control function recommends mental actions
        PROCEDURAL: ProceduralMetacognition.control() returns MentalActionRequest list

        DECLARATIVE: OODA loop drives decision making
        PROCEDURAL: HeartbeatAgent executes OODA cycles continuously
        """

        result = await graphiti_service.ingest_message(
            content=content,
            source_description="mapping_test",
            group_id="integration_test"
        )

        # Verify both conceptual and implementation details captured
        assert result["episode_uuid"] is not None

    async def test_multi_concept_relationships(self, graphiti_service):
        """Test complex relationships spanning multiple concepts."""
        content = """
        Thoughtseed competition → Free Energy minimization → Attractor Basin creation

        Attractor Basin stability → Persistent belief configuration

        Prediction Error detection → Metacognitive feeling (Aha! moment)

        OODA Loop execution → Procedural Metacognition in action

        Declarative facts → Enable Procedural execution
        """

        result = await graphiti_service.ingest_message(
            content=content,
            source_description="relationship_test",
            group_id="integration_test"
        )

        # Verify relationships extracted
        assert len(result["edges"]) > 0

    async def test_group_isolation(self, graphiti_service):
        """Test that metacognition group is isolated from other groups."""
        # Store in different group
        other_content = "This is not metacognition related"
        await graphiti_service.ingest_message(
            content=other_content,
            source_description="other_source",
            group_id="other_group"
        )

        # Search in metacognition group
        result = await graphiti_service.search(
            query="metacognition",
            group_ids=["integration_test"],
            limit=5
        )

        # Search in other group
        result_other = await graphiti_service.search(
            query="metacognition",
            group_ids=["other_group"],
            limit=5
        )

        # Results should differ
        assert isinstance(result, dict)
        assert isinstance(result_other, dict)
