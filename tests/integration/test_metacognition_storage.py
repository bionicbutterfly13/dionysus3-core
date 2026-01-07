"""
Integration tests for metacognition storage across all memory tiers.

Tests the complete storage flow from store_metacognition_memory.py:
- Episodic: HOT tier (timeline events)
- Semantic: Graphiti WARM tier (concept graph)
- Procedural: HOT tier (execution patterns)
- Strategic: HOT tier (meta-learnings)

Author: Mani Saint-Victor, MD
Feature: 057-complete-placeholder-implementations (US6, FR-010)
"""

import os
import pytest
import uuid
from scripts.store_metacognition_memory import MemoryStorageDemo

# Skip semantic tests if NEO4J_PASSWORD not available
SKIP_SEMANTIC = not os.getenv("NEO4J_PASSWORD")
skip_semantic_reason = "NEO4J_PASSWORD not available (use VPS for full integration test)"


class TestMetacognitionStorage:
    """Integration tests for multi-tier metacognition storage."""

    @pytest.fixture
    async def storage_demo(self):
        """Create storage demo instance."""
        return MemoryStorageDemo()

    @pytest.mark.asyncio
    async def test_store_episodic(self, storage_demo):
        """
        Test episodic storage stores 3 events in HOT tier.

        FR-010: Episodic memory stored in HOT tier with 24h TTL
        """
        result = await storage_demo.store_episodic()

        # Verify structure
        assert "events" in result
        assert "stored_ids" in result

        # Verify 3 events stored
        assert len(result["events"]) == 3
        assert len(result["stored_ids"]) == 3

        # Verify all item IDs are valid UUIDs
        for item_id in result["stored_ids"]:
            assert isinstance(item_id, str)
            uuid.UUID(item_id)  # Raises ValueError if invalid

        # Verify event content preserved
        assert result["events"][0]["event"] == "User requested metacognition theory integration"
        assert result["events"][1]["emotional_valence"] == "aha_moment"
        # Event 2 has free_energy instead of surprise_score
        assert "emotional_valence" in result["events"][2]

    @pytest.mark.asyncio
    @pytest.mark.skipif(SKIP_SEMANTIC, reason=skip_semantic_reason)
    async def test_store_semantic(self, storage_demo):
        """
        Test semantic storage stores 6 entities + 7 relationships in Graphiti.

        FR-010: Semantic memory stored in Graphiti WARM tier
        """
        result = await storage_demo.store_semantic()

        # Verify structure
        assert "entities" in result
        assert "relationships" in result

        # Verify 6 entities + 7 relationships
        assert len(result["entities"]) == 6
        assert len(result["relationships"]) == 7

        # Verify entity names
        entity_names = [e["name"] for e in result["entities"]]
        assert "Declarative Metacognition" in entity_names
        assert "Procedural Metacognition" in entity_names
        assert "Thoughtseed" in entity_names
        assert "Attractor Basin" in entity_names
        assert "Free Energy" in entity_names
        assert "OODA Loop" in entity_names

        # Verify relationship structure
        rel = result["relationships"][0]
        assert "source" in rel
        assert "relation" in rel
        assert "target" in rel
        assert "properties" in rel

    @pytest.mark.asyncio
    async def test_store_procedural(self, storage_demo):
        """
        Test procedural storage stores 5 patterns in HOT tier.

        FR-010: Procedural memory stored in HOT tier for fast access
        """
        result = await storage_demo.store_procedural()

        # Verify structure
        assert "patterns" in result
        assert "stored_ids" in result

        # Verify 5 patterns stored
        assert len(result["patterns"]) == 5
        assert len(result["stored_ids"]) == 5

        # Verify all item IDs are valid UUIDs
        for item_id in result["stored_ids"]:
            assert isinstance(item_id, str)
            uuid.UUID(item_id)  # Raises ValueError if invalid

        # Verify pattern names
        pattern_names = list(result["patterns"].keys())
        assert "metacognition_monitoring" in pattern_names
        assert "metacognition_control" in pattern_names
        assert "thoughtseed_competition" in pattern_names
        assert "loop_prevention" in pattern_names
        assert "ralph_orchestration" in pattern_names

    @pytest.mark.asyncio
    async def test_store_strategic(self, storage_demo):
        """
        Test strategic storage stores 4 learnings in HOT tier.

        FR-010: Strategic memory stored in HOT tier with confidence weighting
        """
        result = await storage_demo.store_strategic()

        # Verify structure
        assert "strategies" in result
        assert "stored_ids" in result

        # Verify 4 strategies stored
        assert len(result["strategies"]) == 4
        assert len(result["stored_ids"]) == 4

        # Verify all item IDs are valid UUIDs
        for item_id in result["stored_ids"]:
            assert isinstance(item_id, str)
            uuid.UUID(item_id)  # Raises ValueError if invalid

        # Verify strategy content
        strategy_names = [s["strategy"] for s in result["strategies"]]
        assert "Documentation pivot when implementation blocked" in strategy_names
        assert "Meta-ToT for multi-option analysis" in strategy_names

        # Verify confidence updates present
        for strategy in result["strategies"]:
            assert "confidence_update" in strategy
            assert isinstance(strategy["confidence_update"], (int, float))

    @pytest.mark.asyncio
    @pytest.mark.skipif(SKIP_SEMANTIC, reason=skip_semantic_reason)
    async def test_run_complete_storage(self, storage_demo):
        """
        Test complete storage flow executes all 4 phases.

        FR-010: Full metacognition storage across episodic, semantic, procedural, strategic tiers
        """
        results = await storage_demo.run_complete_storage()

        # Verify all 4 phases completed
        assert "episodic" in results
        assert "semantic" in results
        assert "procedural" in results
        assert "strategic" in results

        # Verify episodic phase
        assert len(results["episodic"]["events"]) == 3
        assert len(results["episodic"]["stored_ids"]) == 3

        # Verify semantic phase
        assert len(results["semantic"]["entities"]) == 6
        assert len(results["semantic"]["relationships"]) == 7

        # Verify procedural phase
        assert len(results["procedural"]["patterns"]) == 5
        assert len(results["procedural"]["stored_ids"]) == 5

        # Verify strategic phase
        assert len(results["strategic"]["strategies"]) == 4
        assert len(results["strategic"]["stored_ids"]) == 4

        # Total verification: 3 episodic + 5 procedural + 4 strategic = 12 HOT tier items
        total_hot_items = (
            len(results["episodic"]["stored_ids"])
            + len(results["procedural"]["stored_ids"])
            + len(results["strategic"]["stored_ids"])
        )
        assert total_hot_items == 12

    @pytest.mark.asyncio
    @pytest.mark.skipif(SKIP_SEMANTIC, reason=skip_semantic_reason)
    async def test_item_id_uniqueness(self, storage_demo):
        """
        Test all stored item IDs are unique UUIDs.

        Ensures no ID collisions across memory tiers.
        """
        results = await storage_demo.run_complete_storage()

        # Collect all stored IDs
        all_ids = []
        all_ids.extend(results["episodic"]["stored_ids"])
        all_ids.extend(results["procedural"]["stored_ids"])
        all_ids.extend(results["strategic"]["stored_ids"])

        # Verify uniqueness
        assert len(all_ids) == len(set(all_ids)), "Duplicate item IDs detected"

        # Verify all are valid UUIDs
        for item_id in all_ids:
            uuid.UUID(item_id)  # Raises ValueError if invalid
