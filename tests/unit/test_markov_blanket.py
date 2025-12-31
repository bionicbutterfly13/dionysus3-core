"""
Unit tests for Markov Blanket models and enforcement service.

Feature: 038-thoughtseeds-framework (Priority 2)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.markov_blanket import (
    MarkovBlanketPartition,
    NestedMarkovBlanket,
    MarkovBlanketHierarchy,
    ValidationResult,
    BlanketValidationStatus,
    Neo4jBlanketEdgeType,
)
from api.services.blanket_enforcement import (
    BlanketEnforcementService,
    get_blanket_enforcement_service,
    get_neo4j_schema_additions,
)


# ---------------------------------------------------------------------------
# MarkovBlanketPartition Tests
# ---------------------------------------------------------------------------


class TestMarkovBlanketPartition:
    """Tests for MarkovBlanketPartition model."""
    
    def test_valid_partition_no_overlaps(self):
        """Valid partition with no overlapping sets."""
        partition = MarkovBlanketPartition(
            external_paths={"env-1", "env-2"},
            sensory_paths={"sensor-1"},
            active_paths={"action-1"},
            internal_paths={"belief-1", "goal-1"}
        )
        
        assert partition.is_valid_partition()
        assert len(partition.get_overlaps()) == 0
    
    def test_invalid_partition_external_sensory_overlap(self):
        """Invalid partition with external-sensory overlap."""
        partition = MarkovBlanketPartition(
            external_paths={"env-1", "shared"},
            sensory_paths={"shared", "sensor-1"},
            active_paths={"action-1"},
            internal_paths={"belief-1"}
        )
        
        assert not partition.is_valid_partition()
        overlaps = partition.get_overlaps()
        assert "external-sensory" in overlaps
        assert "shared" in overlaps["external-sensory"]
    
    def test_invalid_partition_internal_external_overlap(self):
        """Invalid partition with internal-external overlap."""
        partition = MarkovBlanketPartition(
            external_paths={"env-1", "leaked"},
            sensory_paths={"sensor-1"},
            active_paths={"action-1"},
            internal_paths={"belief-1", "leaked"}
        )
        
        assert not partition.is_valid_partition()
        overlaps = partition.get_overlaps()
        assert "external-internal" in overlaps
        assert "leaked" in overlaps["external-internal"]
    
    def test_blanket_paths_union(self):
        """Blanket paths is union of sensory and active."""
        partition = MarkovBlanketPartition(
            external_paths=set(),
            sensory_paths={"s1", "s2"},
            active_paths={"a1", "a2"},
            internal_paths=set()
        )
        
        blanket = partition.blanket_paths
        assert blanket == {"s1", "s2", "a1", "a2"}
    
    def test_all_paths_complete_union(self):
        """All paths includes all partition sets."""
        partition = MarkovBlanketPartition(
            external_paths={"e1"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"i1"}
        )
        
        all_paths = partition.all_paths
        assert all_paths == {"e1", "s1", "a1", "i1"}


# ---------------------------------------------------------------------------
# NestedMarkovBlanket Tests
# ---------------------------------------------------------------------------


class TestNestedMarkovBlanket:
    """Tests for NestedMarkovBlanket model."""
    
    def test_enforce_conditional_independence_success(self):
        """Conditional independence with disjoint internal/external."""
        partition = MarkovBlanketPartition(
            external_paths={"env-1", "env-2"},
            sensory_paths={"sensor-1"},
            active_paths={"action-1"},
            internal_paths={"belief-1", "goal-1"}
        )
        
        blanket = NestedMarkovBlanket(
            level=0,
            partition=partition
        )
        
        assert blanket.enforce_conditional_independence()
    
    def test_enforce_conditional_independence_failure(self):
        """Conditional independence violation with overlapping paths."""
        partition = MarkovBlanketPartition(
            external_paths={"env-1", "leaked"},
            sensory_paths={"sensor-1"},
            active_paths={"action-1"},
            internal_paths={"belief-1", "leaked"}  # Overlap!
        )
        
        blanket = NestedMarkovBlanket(
            level=0,
            partition=partition
        )
        
        assert not blanket.enforce_conditional_independence()
    
    def test_validate_partition_valid(self):
        """Validate partition returns valid for good partition."""
        partition = MarkovBlanketPartition(
            external_paths={"e1"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"i1"}
        )
        
        blanket = NestedMarkovBlanket(level=0, partition=partition)
        result = blanket.validate_partition()
        
        assert result.is_valid
        assert result.status == BlanketValidationStatus.VALID
    
    def test_validate_partition_invalid(self):
        """Validate partition returns invalid for overlapping partition."""
        partition = MarkovBlanketPartition(
            external_paths={"shared"},
            sensory_paths={"shared"},  # Overlap!
            active_paths={"a1"},
            internal_paths={"i1"}
        )
        
        blanket = NestedMarkovBlanket(level=0, partition=partition)
        result = blanket.validate_partition()
        
        assert not result.is_valid
        assert result.status == BlanketValidationStatus.INVALID_PARTITION
        assert len(result.errors) > 0


# ---------------------------------------------------------------------------
# MarkovBlanketHierarchy Tests
# ---------------------------------------------------------------------------


class TestMarkovBlanketHierarchy:
    """Tests for MarkovBlanketHierarchy model."""
    
    def test_add_and_get_blanket(self):
        """Add blanket and retrieve it."""
        hierarchy = MarkovBlanketHierarchy()
        
        blanket = NestedMarkovBlanket(
            id="blanket-1",
            level=0,
            partition=MarkovBlanketPartition()
        )
        
        hierarchy.add_blanket(blanket)
        
        assert hierarchy.get_blanket("blanket-1") == blanket
        assert hierarchy.root_id == "blanket-1"
    
    def test_validate_nesting_success(self):
        """Valid nesting with child internal subset of parent."""
        parent_partition = MarkovBlanketPartition(
            internal_paths={"i1", "i2", "i3"}
        )
        child_partition = MarkovBlanketPartition(
            internal_paths={"i1", "i2"}  # Subset of parent
        )
        
        parent = NestedMarkovBlanket(id="parent", level=0, partition=parent_partition)
        child = NestedMarkovBlanket(id="child", level=1, partition=child_partition, parent_id="parent")
        
        hierarchy = MarkovBlanketHierarchy()
        hierarchy.add_blanket(parent)
        hierarchy.add_blanket(child)
        
        assert hierarchy.validate_nesting(child, parent)
    
    def test_validate_nesting_failure_not_subset(self):
        """Invalid nesting with child internal not subset of parent."""
        parent_partition = MarkovBlanketPartition(
            internal_paths={"i1", "i2"}
        )
        child_partition = MarkovBlanketPartition(
            internal_paths={"i1", "i3"}  # i3 not in parent!
        )
        
        parent = NestedMarkovBlanket(id="parent", level=0, partition=parent_partition)
        child = NestedMarkovBlanket(id="child", level=1, partition=child_partition, parent_id="parent")
        
        hierarchy = MarkovBlanketHierarchy()
        
        assert not hierarchy.validate_nesting(child, parent)
    
    def test_validate_nesting_failure_wrong_level(self):
        """Invalid nesting with child level <= parent level."""
        parent = NestedMarkovBlanket(id="parent", level=1, partition=MarkovBlanketPartition())
        child = NestedMarkovBlanket(id="child", level=1, partition=MarkovBlanketPartition())  # Same level!
        
        hierarchy = MarkovBlanketHierarchy()
        
        assert not hierarchy.validate_nesting(child, parent)
    
    def test_validate_all_success(self):
        """Full hierarchy validation success."""
        parent_partition = MarkovBlanketPartition(
            external_paths={"e1"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"i1", "i2", "i3"}
        )
        child_partition = MarkovBlanketPartition(
            external_paths={"e2"},
            sensory_paths={"s2"},
            active_paths={"a2"},
            internal_paths={"i1", "i2"}  # Subset
        )
        
        parent = NestedMarkovBlanket(id="parent", level=0, partition=parent_partition)
        child = NestedMarkovBlanket(id="child", level=1, partition=child_partition, parent_id="parent")
        parent.child_ids = ["child"]
        
        hierarchy = MarkovBlanketHierarchy()
        hierarchy.add_blanket(parent)
        hierarchy.add_blanket(child)
        
        result = hierarchy.validate_all()
        
        assert result.is_valid
    
    def test_validate_all_failure(self):
        """Full hierarchy validation with nesting error."""
        parent_partition = MarkovBlanketPartition(
            internal_paths={"i1", "i2"}
        )
        child_partition = MarkovBlanketPartition(
            internal_paths={"i1", "i3"}  # i3 not in parent!
        )
        
        parent = NestedMarkovBlanket(id="parent", level=0, partition=parent_partition)
        child = NestedMarkovBlanket(id="child", level=1, partition=child_partition, parent_id="parent")
        parent.child_ids = ["child"]
        
        hierarchy = MarkovBlanketHierarchy()
        hierarchy.add_blanket(parent)
        hierarchy.add_blanket(child)
        
        result = hierarchy.validate_all()
        
        assert not result.is_valid
        assert BlanketValidationStatus.INVALID_NESTING == result.status


# ---------------------------------------------------------------------------
# Neo4jBlanketEdgeType Tests
# ---------------------------------------------------------------------------


class TestNeo4jBlanketEdgeType:
    """Tests for Neo4j edge type helpers."""
    
    def test_sensory_edge_pattern(self):
        """Sensory edge Cypher pattern."""
        pattern = Neo4jBlanketEdgeType.get_sensory_edge_cypher()
        assert "SENSORY" in pattern
        assert "ThoughtSeed" in pattern
    
    def test_active_edge_pattern(self):
        """Active edge Cypher pattern."""
        pattern = Neo4jBlanketEdgeType.get_active_edge_cypher()
        assert "ACTIVE" in pattern
        assert "ThoughtSeed" in pattern
    
    def test_create_sensory_cypher(self):
        """Generate sensory edge creation Cypher."""
        cypher, params = Neo4jBlanketEdgeType.get_create_sensory_cypher(
            "source-1", "seed-1", {"weight": 0.5}
        )
        
        assert "SENSORY" in cypher
        assert params["source_id"] == "source-1"
        assert params["target_id"] == "seed-1"
        assert params["props"]["weight"] == 0.5
    
    def test_create_active_cypher(self):
        """Generate active edge creation Cypher."""
        cypher, params = Neo4jBlanketEdgeType.get_create_active_cypher(
            "seed-1", "target-1", {"precision": 0.8}
        )
        
        assert "ACTIVE" in cypher
        assert params["source_id"] == "seed-1"
        assert params["target_id"] == "target-1"
        assert params["props"]["precision"] == 0.8


# ---------------------------------------------------------------------------
# BlanketEnforcementService Tests
# ---------------------------------------------------------------------------


class TestBlanketEnforcementService:
    """Tests for BlanketEnforcementService."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = MagicMock()
        driver.execute_query = AsyncMock(return_value=[])
        return driver
    
    @pytest.fixture
    def service(self, mock_driver):
        """Create service with mock driver."""
        return BlanketEnforcementService(driver=mock_driver)
    
    def test_validate_blanket_structure_valid(self, service):
        """Validate a valid blanket structure."""
        partition = MarkovBlanketPartition(
            external_paths={"e1"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"i1"}
        )
        blanket = NestedMarkovBlanket(level=0, partition=partition)
        
        result = service.validate_blanket_structure(blanket)
        
        assert result.is_valid
    
    def test_validate_blanket_structure_invalid_partition(self, service):
        """Validate an invalid blanket with overlapping partition."""
        partition = MarkovBlanketPartition(
            external_paths={"shared"},
            sensory_paths={"shared"},
            active_paths={"a1"},
            internal_paths={"i1"}
        )
        blanket = NestedMarkovBlanket(level=0, partition=partition)
        
        result = service.validate_blanket_structure(blanket)
        
        assert not result.is_valid
    
    def test_check_conditional_independence_true(self, service):
        """Check conditional independence returns true for valid blanket."""
        partition = MarkovBlanketPartition(
            external_paths={"e1"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"i1"}
        )
        blanket = NestedMarkovBlanket(level=0, partition=partition)
        
        assert service.check_conditional_independence(blanket)
    
    def test_check_conditional_independence_false(self, service):
        """Check conditional independence returns false for violated blanket."""
        partition = MarkovBlanketPartition(
            external_paths={"leaked"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"leaked"}
        )
        blanket = NestedMarkovBlanket(level=0, partition=partition)
        
        assert not service.check_conditional_independence(blanket)
    
    def test_create_nested_blanket_valid(self, service):
        """Create a valid nested blanket."""
        blanket = service.create_nested_blanket(
            level=0,
            external_paths={"e1"},
            sensory_paths={"s1"},
            active_paths={"a1"},
            internal_paths={"i1", "i2"},
            thoughtseed_id="seed-1"
        )
        
        assert blanket.level == 0
        assert blanket.thoughtseed_id == "seed-1"
        assert blanket.partition.internal_paths == {"i1", "i2"}
    
    def test_create_nested_blanket_with_parent(self, service):
        """Create nested blanket with valid parent."""
        parent = service.create_nested_blanket(
            level=0,
            internal_paths={"i1", "i2", "i3"}
        )
        
        child = service.create_nested_blanket(
            level=1,
            parent=parent,
            internal_paths={"i1", "i2"}  # Subset of parent
        )
        
        assert child.level == 1
        assert child.parent_id == parent.id
        assert parent.child_ids == [child.id]
    
    def test_create_nested_blanket_invalid_nesting(self, service):
        """Create nested blanket with invalid nesting raises error."""
        parent = service.create_nested_blanket(
            level=0,
            internal_paths={"i1", "i2"}
        )
        
        with pytest.raises(ValueError, match="Nesting constraint violated"):
            service.create_nested_blanket(
                level=1,
                parent=parent,
                internal_paths={"i1", "i3"}  # i3 not in parent!
            )
    
    def test_create_nested_blanket_invalid_partition(self, service):
        """Create nested blanket with invalid partition raises error."""
        with pytest.raises(ValueError, match="Invalid partition"):
            service.create_nested_blanket(
                level=0,
                external_paths={"shared"},
                sensory_paths={"shared"},  # Overlap!
                active_paths={"a1"},
                internal_paths={"i1"}
            )
    
    def test_validate_nesting_constraint_valid(self, service):
        """Validate nesting constraint for valid pair."""
        parent_partition = MarkovBlanketPartition(internal_paths={"i1", "i2", "i3"})
        child_partition = MarkovBlanketPartition(internal_paths={"i1", "i2"})
        
        parent = NestedMarkovBlanket(id="parent", level=0, partition=parent_partition)
        child = NestedMarkovBlanket(id="child", level=1, partition=child_partition)
        
        result = service.validate_nesting_constraint(child, parent)
        
        assert result.is_valid
    
    def test_validate_nesting_constraint_invalid_level(self, service):
        """Validate nesting constraint with wrong levels."""
        parent = NestedMarkovBlanket(id="parent", level=1, partition=MarkovBlanketPartition())
        child = NestedMarkovBlanket(id="child", level=0, partition=MarkovBlanketPartition())
        
        result = service.validate_nesting_constraint(child, parent)
        
        assert not result.is_valid
        assert "must be greater than" in result.errors[0]
    
    def test_create_hierarchy(self, service):
        """Create a blanket hierarchy."""
        root = service.create_nested_blanket(level=0, internal_paths={"i1"})
        hierarchy = service.create_hierarchy(root)
        
        assert hierarchy.root_id == root.id
        assert root.id in hierarchy.blankets
    
    def test_create_hierarchy_wrong_level(self, service):
        """Create hierarchy with non-zero level root raises error."""
        non_root = service.create_nested_blanket(level=1, internal_paths={"i1"})
        
        with pytest.raises(ValueError, match="must be level 0"):
            service.create_hierarchy(non_root)
    
    @pytest.mark.asyncio
    async def test_discover_blanket_paths(self, service, mock_driver):
        """Discover blanket paths from Neo4j."""
        mock_driver.execute_query.return_value = [{
            "partition": {
                "internal": ["seed-1", "child-1"],
                "sensory": ["sensor-1"],
                "active": ["action-1"],
                "external": ["env-1"]
            }
        }]
        
        partition = await service.discover_blanket_paths("seed-1")
        
        assert "seed-1" in partition.internal_paths
        assert "sensor-1" in partition.sensory_paths
        assert "action-1" in partition.active_paths
        assert "env-1" in partition.external_paths
    
    @pytest.mark.asyncio
    async def test_discover_blanket_paths_fallback(self, service, mock_driver):
        """Discover blanket paths falls back on error."""
        mock_driver.execute_query.side_effect = Exception("Neo4j error")
        
        partition = await service.discover_blanket_paths("seed-1")
        
        assert partition.internal_paths == {"seed-1"}
        assert len(partition.sensory_paths) == 0
    
    @pytest.mark.asyncio
    async def test_create_sensory_edge(self, service, mock_driver):
        """Create a sensory edge in Neo4j."""
        mock_driver.execute_query.return_value = [{"r": {}}]
        
        result = await service.create_sensory_edge("source-1", "seed-1", weight=0.5)
        
        assert result is True
        mock_driver.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_active_edge(self, service, mock_driver):
        """Create an active edge in Neo4j."""
        mock_driver.execute_query.return_value = [{"r": {}}]
        
        result = await service.create_active_edge("seed-1", "target-1", precision=0.8)
        
        assert result is True
        mock_driver.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_blanket_in_neo4j_not_found(self, service, mock_driver):
        """Validate blanket returns invalid when ThoughtSeed not found."""
        mock_driver.execute_query.return_value = []
        
        result = await service.validate_blanket_in_neo4j("nonexistent")
        
        assert not result.is_valid
        assert "not found" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_validate_blanket_in_neo4j_success(self, service, mock_driver):
        """Validate blanket returns valid for existing ThoughtSeed."""
        mock_driver.execute_query.return_value = [{
            "validation": {
                "exists": True,
                "has_blanket": True,
                "sensory_count": 2,
                "active_count": 1,
                "bypass_edges": 0
            }
        }]
        
        result = await service.validate_blanket_in_neo4j("seed-1")
        
        assert result.is_valid
    
    @pytest.mark.asyncio
    async def test_get_blanket_edges(self, service, mock_driver):
        """Get blanket edges from Neo4j."""
        mock_driver.execute_query.return_value = [{
            "sensory_edges": [{"source_id": "s1", "weight": 0.5}],
            "active_edges": [{"target_id": "a1", "weight": 0.8}]
        }]
        
        edges = await service.get_blanket_edges("seed-1")
        
        assert len(edges["sensory_edges"]) == 1
        assert len(edges["active_edges"]) == 1
        assert edges["sensory_edges"][0]["source_id"] == "s1"


# ---------------------------------------------------------------------------
# Schema Helper Tests
# ---------------------------------------------------------------------------


class TestSchemaHelpers:
    """Tests for schema generation helpers."""
    
    def test_get_neo4j_schema_additions(self):
        """Get Neo4j schema additions."""
        schema = get_neo4j_schema_additions()
        
        assert "edge_types" in schema
        assert len(schema["edge_types"]) == 2
        
        edge_names = [e["type"] for e in schema["edge_types"]]
        assert "SENSORY" in edge_names
        assert "ACTIVE" in edge_names
        
        assert "cypher_queries" in schema
        assert "validate_blanket_isolation" in schema["cypher_queries"]


# ---------------------------------------------------------------------------
# Factory Tests
# ---------------------------------------------------------------------------


class TestFactory:
    """Tests for service factory."""
    
    def test_get_blanket_enforcement_service_singleton(self):
        """Factory returns singleton instance."""
        # Reset singleton for test
        import api.services.blanket_enforcement as module
        module._instance = None
        
        service1 = get_blanket_enforcement_service()
        service2 = get_blanket_enforcement_service()
        
        assert service1 is service2
        
        # Clean up
        module._instance = None
