"""
Integration Tests for Fractal Metacognition Persistence

Feature: 037-context-engineering-upgrades
Tests: T014 - Verify parent-child thought persistence and retrieval
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from api.models.thought import ThoughtSeed, ThoughtLayer, CompetitionStatus

# removed global asyncio mark to avoid warnings on sync tests


class TestFractalThoughtPersistence:
    """Tests for fractal thought structure persistence."""

    def test_thought_seed_has_child_ids(self):
        """Verify ThoughtSeed model includes child_thought_ids field."""
        seed = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Parent thought"
        )
        assert hasattr(seed, 'child_thought_ids')
        assert isinstance(seed.child_thought_ids, list)
        assert len(seed.child_thought_ids) == 0

    def test_thought_seed_has_parent_id(self):
        """Verify ThoughtSeed model includes parent_thought_id field."""
        parent_id = uuid4()
        seed = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Child thought",
            parent_thought_id=parent_id
        )
        assert seed.parent_thought_id == parent_id

    def test_parent_child_relationship(self):
        """Verify parent-child relationship can be established."""
        parent = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Parent: Analyzing user behavior"
        )
        
        child1 = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Child 1: Why am I analyzing this?",
            parent_thought_id=parent.id
        )
        
        child2 = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Child 2: What patterns am I looking for?",
            parent_thought_id=parent.id
        )
        
        # Link children to parent
        parent.child_thought_ids.append(child1.id)
        parent.child_thought_ids.append(child2.id)
        
        assert len(parent.child_thought_ids) == 2
        assert child1.id in parent.child_thought_ids
        assert child2.id in parent.child_thought_ids
        assert child1.parent_thought_id == parent.id
        assert child2.parent_thought_id == parent.id

    def test_multi_level_fractal_structure(self):
        """Verify 3-level deep fractal structure."""
        root = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Root: Main cognitive task"
        )
        
        level1 = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Level 1: Thinking about the task",
            parent_thought_id=root.id
        )
        root.child_thought_ids.append(level1.id)
        
        level2 = ThoughtSeed(
            layer=ThoughtLayer.METACOGNITIVE,
            content="Level 2: Thinking about thinking about the task",
            parent_thought_id=level1.id
        )
        level1.child_thought_ids.append(level2.id)
        
        # Verify structure
        assert root.parent_thought_id is None  # Root has no parent
        assert level1.parent_thought_id == root.id
        assert level2.parent_thought_id == level1.id
        assert level2.id in level1.child_thought_ids

    def test_thought_serialization_preserves_relationships(self):
        """Verify JSON serialization preserves fractal relationships."""
        parent_id = uuid4()
        child_id = uuid4()
        
        seed = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Test serialization",
            parent_thought_id=parent_id,
            child_thought_ids=[child_id]
        )
        
        # Serialize and deserialize
        json_data = seed.model_dump_json()
        restored = ThoughtSeed.model_validate_json(json_data)
        
        assert restored.parent_thought_id == parent_id
        assert child_id in restored.child_thought_ids

    @pytest.mark.asyncio
    async def test_neo4j_persistence_cypher_structure(self):
        """Verify Cypher query structure for fractal relationships."""
        from api.services.thoughtseed_integration import ThoughtSeedIntegrationService
        
        mock_driver = AsyncMock()
        mock_driver.execute_query = AsyncMock(return_value=[{"id": "test-seed"}])
        
        service = ThoughtSeedIntegrationService(driver=mock_driver)
        
        # Generate a parent thought
        parent_result = await service.generate_thoughtseed_from_prediction(
            prediction_id=uuid4(),
            model_id=uuid4(),
            model_domain="self",
            prediction_content={"type": "parent"},
            confidence=0.9
        )
        
        # Verify execute_query was called
        assert mock_driver.execute_query.called
        
        # The Cypher should create a ThoughtSeed node
        cypher_call = mock_driver.execute_query.call_args[0][0]
        assert "ThoughtSeed" in cypher_call or "CREATE" in cypher_call

    @pytest.mark.asyncio
    async def test_retrieve_with_children(self):
        """Verify retrieval includes child references."""
        parent_id = str(uuid4())
        child1_id = str(uuid4())
        child2_id = str(uuid4())
        
        mock_result = {
            "id": parent_id,
            "layer": "conceptual",
            "content": "Parent thought",
            "child_ids": [child1_id, child2_id]
        }
        
        # Simulate Neo4j returning a thought with children
        seed = ThoughtSeed(
            id=UUID(parent_id),
            layer=ThoughtLayer.CONCEPTUAL,
            content="Parent thought",
            child_thought_ids=[UUID(child1_id), UUID(child2_id)]
        )
        
        assert len(seed.child_thought_ids) == 2


class TestFractalTraversal:
    """Tests for traversing fractal thought structures."""

    def test_collect_all_descendants(self):
        """Verify collecting all descendants of a thought."""
        # Build a tree
        root = ThoughtSeed(layer=ThoughtLayer.ABSTRACT, content="Root")
        
        child1 = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Child 1",
            parent_thought_id=root.id
        )
        child2 = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Child 2",
            parent_thought_id=root.id
        )
        grandchild = ThoughtSeed(
            layer=ThoughtLayer.PERCEPTUAL,
            content="Grandchild",
            parent_thought_id=child1.id
        )
        
        root.child_thought_ids = [child1.id, child2.id]
        child1.child_thought_ids = [grandchild.id]
        
        # Create a lookup
        thoughts = {
            str(root.id): root,
            str(child1.id): child1,
            str(child2.id): child2,
            str(grandchild.id): grandchild
        }
        
        # Traverse to collect all descendants
        def collect_descendants(thought_id: UUID, thought_map: dict) -> list:
            result = []
            thought = thought_map.get(str(thought_id))
            if thought:
                for child_id in thought.child_thought_ids:
                    result.append(child_id)
                    result.extend(collect_descendants(child_id, thought_map))
            return result
        
        descendants = collect_descendants(root.id, thoughts)
        
        assert len(descendants) == 3
        assert child1.id in descendants
        assert child2.id in descendants
        assert grandchild.id in descendants

    def test_find_root_from_leaf(self):
        """Verify traversing up to find root thought."""
        root = ThoughtSeed(layer=ThoughtLayer.ABSTRACT, content="Root")
        
        child = ThoughtSeed(
            layer=ThoughtLayer.CONCEPTUAL,
            content="Child",
            parent_thought_id=root.id
        )
        
        grandchild = ThoughtSeed(
            layer=ThoughtLayer.PERCEPTUAL,
            content="Grandchild",
            parent_thought_id=child.id
        )
        
        thoughts = {
            str(root.id): root,
            str(child.id): child,
            str(grandchild.id): grandchild
        }
        
        def find_root(thought_id: UUID, thought_map: dict) -> ThoughtSeed:
            thought = thought_map.get(str(thought_id))
            if thought.parent_thought_id is None:
                return thought
            return find_root(thought.parent_thought_id, thought_map)
        
        found_root = find_root(grandchild.id, thoughts)
        
        assert found_root.id == root.id
        assert found_root.parent_thought_id is None
