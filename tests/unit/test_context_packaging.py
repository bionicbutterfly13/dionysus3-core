"""
Unit tests for Context Packaging - Cellular Memory Physics
Track: 057-memory-systems-integration
Task: 6.4 - TDD tests for context packaging

Tests verify:
1. TokenBudgetManager allocates and evicts cells correctly
2. ContextCell priority and resonance dynamics
3. SymbolicResidue tracks causal attribution
4. Budget-aware memory state packaging
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.context_packaging import (
    CellPriority,
    TokenBudget,
    ContextCell,
    TokenBudgetManager,
    SymbolicResidue,
    SymbolicResidueTracker,
)


class TestTokenBudget:
    """Tests for TokenBudget dataclass."""

    def test_budget_available_calculation(self):
        """Verify available tokens calculation."""
        budget = TokenBudget(allocated=1000, used=300, reserved=200)

        assert budget.available == 500
        assert budget.utilization == 0.3

    def test_budget_can_fit(self):
        """Verify can_fit checks available space."""
        budget = TokenBudget(allocated=1000, used=600, reserved=100)

        assert budget.can_fit(300) is True
        assert budget.can_fit(400) is False

    def test_budget_consume(self):
        """Verify consume updates used tokens."""
        budget = TokenBudget(allocated=1000, used=0, reserved=100)

        result = budget.consume(400)

        assert result is True
        assert budget.used == 400
        assert budget.available == 500

    def test_budget_consume_fails_insufficient(self):
        """Verify consume fails when insufficient."""
        budget = TokenBudget(allocated=1000, used=900, reserved=50)

        result = budget.consume(100)

        assert result is False
        assert budget.used == 900  # Unchanged


class TestContextCell:
    """Tests for ContextCell data structure."""

    def test_cell_creation_with_defaults(self):
        """Verify ContextCell has correct default values."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test content",
            priority=CellPriority.MEDIUM,
            token_count=50,
        )

        assert cell.cell_id == "cell-1"
        assert cell.content == "Test content"
        assert cell.priority == CellPriority.MEDIUM
        assert cell.token_count == 50
        assert cell.resonance_score == 0.5
        assert cell.attractor_strength == 1.0
        assert cell.basin_id is None
        assert cell.causal_links == []

    def test_cell_touch_updates_timestamp(self):
        """Verify touch() updates last_accessed."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.HIGH,
            token_count=10,
        )

        original_time = cell.last_accessed
        cell.touch()

        assert cell.last_accessed >= original_time
        assert cell.access_count == 1

    def test_cell_touch_reinforces_attractor_strength(self):
        """Verify touch() reinforces attractor strength."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.MEDIUM,
            token_count=10,
        )
        cell.attractor_strength = 0.5

        cell.touch()

        assert cell.attractor_strength == 0.6

    def test_cell_touch_caps_attractor_strength(self):
        """Verify touch() doesn't exceed 1.0."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.MEDIUM,
            token_count=10,
        )
        cell.attractor_strength = 0.95

        cell.touch()

        assert cell.attractor_strength == 1.0

    def test_cell_decay_reduces_strength(self):
        """Verify decay() reduces attractor strength."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.MEDIUM,
            token_count=10,
        )
        cell.attractor_strength = 0.5

        cell.decay(rate=0.1)

        assert cell.attractor_strength == 0.4

    def test_cell_decay_respects_floor(self):
        """Verify decay() doesn't go below 0.0."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.MEDIUM,
            token_count=10,
        )
        cell.attractor_strength = 0.05

        cell.decay(rate=0.1)

        assert cell.attractor_strength == 0.0

    def test_effective_priority_combines_factors(self):
        """Verify effective_priority combines priority, resonance, and strength."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.HIGH,  # 0.8 weight
            token_count=10,
            resonance_score=1.0,
            attractor_strength=1.0,
        )

        # effective = base * 0.4 + resonance * 0.3 + strength * 0.3
        # = 0.8 * 0.4 + 1.0 * 0.3 + 1.0 * 0.3 = 0.32 + 0.3 + 0.3 = 0.92
        expected = 0.8 * 0.4 + 1.0 * 0.3 + 1.0 * 0.3
        assert cell.effective_priority == pytest.approx(expected, rel=0.01)

    def test_effective_priority_with_low_resonance(self):
        """Verify low resonance reduces effective priority."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.HIGH,
            token_count=10,
            resonance_score=0.0,
            attractor_strength=1.0,
        )

        # effective = 0.8 * 0.4 + 0.0 * 0.3 + 1.0 * 0.3 = 0.32 + 0 + 0.3 = 0.62
        expected = 0.8 * 0.4 + 0.0 * 0.3 + 1.0 * 0.3
        assert cell.effective_priority == pytest.approx(expected, rel=0.01)

    def test_cell_to_dict(self):
        """Verify to_dict serialization."""
        cell = ContextCell(
            cell_id="cell-1",
            content="Test content",
            priority=CellPriority.HIGH,
            token_count=50,
            basin_id="test-basin",
        )

        data = cell.to_dict()

        assert data["cell_id"] == "cell-1"
        assert data["priority"] == "high"
        assert data["basin_id"] == "test-basin"
        assert "effective_priority" in data


class TestTokenBudgetManager:
    """Tests for TokenBudgetManager budget allocation."""

    def test_initial_budget_state(self):
        """Verify manager initializes with correct budget."""
        manager = TokenBudgetManager(total_budget=10000, reserve_ratio=0.1)

        stats = manager.get_stats()

        assert stats["total_budget"] == 10000
        assert stats["reserved_tokens"] == 1000
        assert stats["usable_budget"] == 9000
        assert stats["used_tokens"] == 0

    def test_add_cell_consumes_budget(self):
        """Verify adding cell consumes token budget."""
        manager = TokenBudgetManager(total_budget=1000, reserve_ratio=0.1)
        cell = ContextCell(
            cell_id="cell-1",
            content="Test content",
            priority=CellPriority.HIGH,
            token_count=200,
        )

        result = manager.add_cell(cell)

        assert result is True
        assert manager.used_tokens == 200
        assert manager.get_cell("cell-1") is not None

    def test_add_cell_fails_when_over_budget(self):
        """Verify cell rejected when budget exceeded."""
        manager = TokenBudgetManager(total_budget=100, reserve_ratio=0.1)
        # Usable is 90 tokens
        cell = ContextCell(
            cell_id="cell-1",
            content="Too large",
            priority=CellPriority.MEDIUM,
            token_count=200,
        )

        result = manager.add_cell(cell)

        assert result is False
        assert manager.get_cell("cell-1") is None

    def test_add_cell_evicts_low_priority_when_needed(self):
        """Verify low-priority cells evicted to make room."""
        manager = TokenBudgetManager(total_budget=200, reserve_ratio=0.0)

        # Add low-priority cell
        low_cell = ContextCell(
            cell_id="low",
            content="Low priority",
            priority=CellPriority.LOW,
            token_count=150,
            resonance_score=0.3,
            attractor_strength=0.3,
        )
        manager.add_cell(low_cell)

        # Add high-priority cell that needs the space
        high_cell = ContextCell(
            cell_id="high",
            content="High priority",
            priority=CellPriority.HIGH,
            token_count=150,
            resonance_score=0.8,
            attractor_strength=0.9,
        )
        result = manager.add_cell(high_cell)

        assert result is True
        assert manager.get_cell("high") is not None
        # Low cell should be removed (but get_cell marks as accessed, so check _cells)
        assert "low" not in manager._cells

    def test_remove_cell_frees_budget(self):
        """Verify removing cell frees token budget."""
        manager = TokenBudgetManager(total_budget=1000, reserve_ratio=0.1)
        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.MEDIUM,
            token_count=200,
        )
        manager.add_cell(cell)

        removed = manager.remove_cell("cell-1")

        assert removed is not None
        assert manager.used_tokens == 0

    def test_apply_decay_to_all_cells(self):
        """Verify decay applies to all cells."""
        manager = TokenBudgetManager(total_budget=1000)

        cell1 = ContextCell(
            cell_id="cell-1",
            content="Test 1",
            priority=CellPriority.HIGH,
            token_count=100,
        )
        cell1.attractor_strength = 1.0

        cell2 = ContextCell(
            cell_id="cell-2",
            content="Test 2",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        cell2.attractor_strength = 0.8

        manager.add_cell(cell1)
        manager.add_cell(cell2)

        manager.apply_decay(rate=0.1)

        assert manager._cells["cell-1"].attractor_strength == 0.9
        assert manager._cells["cell-2"].attractor_strength == pytest.approx(0.7, rel=0.01)

    def test_update_resonance_with_embeddings(self):
        """Verify resonance update with goal embeddings."""
        manager = TokenBudgetManager(total_budget=1000)

        cell1 = ContextCell(
            cell_id="cell-1",
            content="Aligned content",
            priority=CellPriority.MEDIUM,
            token_count=100,
            resonance_score=0.5,
        )
        cell2 = ContextCell(
            cell_id="cell-2",
            content="Different content",
            priority=CellPriority.MEDIUM,
            token_count=100,
            resonance_score=0.5,
        )
        manager.add_cell(cell1)
        manager.add_cell(cell2)

        # Update with embeddings (simulated)
        goal_embedding = [1.0, 0.0, 0.0]
        cell_embeddings = {
            "cell-1": [0.9, 0.1, 0.0],  # High similarity
            "cell-2": [0.0, 1.0, 0.0],  # Low similarity
        }

        manager.update_resonance(goal_embedding, cell_embeddings)

        # Cell 1 should have higher resonance
        assert manager._cells["cell-1"].resonance_score > manager._cells["cell-2"].resonance_score

    def test_get_context_package_respects_budget(self):
        """Verify context package fits within token limit."""
        manager = TokenBudgetManager(total_budget=1000, reserve_ratio=0.0)

        # Add cells with varying priorities
        for i in range(5):
            cell = ContextCell(
                cell_id=f"cell-{i}",
                content=f"Content {i}",
                priority=CellPriority.MEDIUM if i < 3 else CellPriority.LOW,
                token_count=100,
            )
            manager.add_cell(cell)

        context_string, metadata = manager.get_context_package(max_tokens=250)

        # Should include highest priority cells up to 250 tokens
        assert metadata["tokens_used"] <= 250
        assert len(metadata["cell_ids"]) <= 3

    def test_get_context_package_prioritizes_by_effective_priority(self):
        """Verify context package includes highest priority cells first."""
        manager = TokenBudgetManager(total_budget=500, reserve_ratio=0.0)

        low = ContextCell(
            cell_id="low",
            content="LOW",
            priority=CellPriority.LOW,
            token_count=100,
            resonance_score=0.1,
        )
        high = ContextCell(
            cell_id="high",
            content="HIGH",
            priority=CellPriority.HIGH,
            token_count=100,
            resonance_score=0.9,
        )
        manager.add_cell(low)
        manager.add_cell(high)

        context_string, metadata = manager.get_context_package(max_tokens=150)

        # High priority should be included
        assert "high" in metadata["cell_ids"]
        assert "HIGH" in context_string

    def test_critical_cells_preserved_in_package(self):
        """Verify CRITICAL priority cells included in package."""
        manager = TokenBudgetManager(total_budget=500, reserve_ratio=0.0)

        critical = ContextCell(
            cell_id="critical",
            content="CRITICAL",
            priority=CellPriority.CRITICAL,
            token_count=100,
        )
        other = ContextCell(
            cell_id="other",
            content="OTHER",
            priority=CellPriority.EPHEMERAL,
            token_count=100,
        )
        manager.add_cell(critical)
        manager.add_cell(other)

        context_string, metadata = manager.get_context_package(max_tokens=150)

        assert "critical" in metadata["cell_ids"]

    def test_utilization_tracking(self):
        """Verify utilization calculation."""
        manager = TokenBudgetManager(total_budget=1000, reserve_ratio=0.0)

        cell = ContextCell(
            cell_id="cell-1",
            content="Test",
            priority=CellPriority.MEDIUM,
            token_count=500,
        )
        manager.add_cell(cell)

        assert manager.utilization == 0.5


class TestSymbolicResidue:
    """Tests for SymbolicResidue tracking."""

    def test_residue_creation(self):
        """Verify SymbolicResidue records transformation metadata."""
        residue = SymbolicResidue(
            residue_id="res-1",
            source_cell_ids=["cell-1", "cell-2"],
            derived_cell_id="cell-3",
            transformation_type="compression",
            lost_details=["detail A", "detail B"],
            compression_ratio=0.5,
            attribution_chain=["cell-1", "cell-2", "cell-3"],
        )

        assert residue.residue_id == "res-1"
        assert len(residue.source_cell_ids) == 2
        assert residue.compression_ratio == 0.5
        assert len(residue.attribution_chain) == 3

    def test_residue_to_dict(self):
        """Verify to_dict serialization."""
        residue = SymbolicResidue(
            residue_id="res-1",
            source_cell_ids=["a", "b"],
            derived_cell_id="c",
            transformation_type="merge",
            compression_ratio=0.7,
        )

        data = residue.to_dict()

        assert data["residue_id"] == "res-1"
        assert data["transformation_type"] == "merge"
        assert "timestamp" in data


class TestSymbolicResidueTracker:
    """Tests for SymbolicResidueTracker causal attribution."""

    def test_record_transformation(self):
        """Verify tracker records transformations."""
        tracker = SymbolicResidueTracker()

        source1 = ContextCell(
            cell_id="a",
            content="Content A",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        source2 = ContextCell(
            cell_id="b",
            content="Content B",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        derived = ContextCell(
            cell_id="c",
            content="Merged content",
            priority=CellPriority.MEDIUM,
            token_count=50,
        )

        residue = tracker.record_transformation(
            source_cells=[source1, source2],
            derived_cell=derived,
            transformation_type="merge",
            lost_details=["detail 1"],
        )

        assert residue.residue_id is not None
        assert residue.derived_cell_id == "c"
        assert residue.compression_ratio == 0.25  # 50 / 200
        assert tracker.get_residue_for_cell("c") is not None

    def test_record_transformation_updates_cell_links(self):
        """Verify transformation updates causal links on cells."""
        tracker = SymbolicResidueTracker()

        source = ContextCell(
            cell_id="source",
            content="Original",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        derived = ContextCell(
            cell_id="derived",
            content="Summary",
            priority=CellPriority.MEDIUM,
            token_count=30,
        )

        tracker.record_transformation(
            source_cells=[source],
            derived_cell=derived,
            transformation_type="summarize",
        )

        # Derived cell should have causal link to source
        assert "source" in derived.causal_links
        # Source should track derived
        assert "derived" in source.derived_cells

    def test_get_attribution_chain(self):
        """Verify attribution chain traces back to sources."""
        tracker = SymbolicResidueTracker()

        # Build chain: a -> b -> c
        cell_a = ContextCell(
            cell_id="a",
            content="A",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        cell_b = ContextCell(
            cell_id="b",
            content="B",
            priority=CellPriority.MEDIUM,
            token_count=50,
        )
        cell_c = ContextCell(
            cell_id="c",
            content="C",
            priority=CellPriority.MEDIUM,
            token_count=25,
        )

        tracker.record_transformation(
            source_cells=[cell_a],
            derived_cell=cell_b,
            transformation_type="compress",
        )
        tracker.record_transformation(
            source_cells=[cell_b],
            derived_cell=cell_c,
            transformation_type="compress",
        )

        chain = tracker.get_attribution_chain("c")

        # Should trace c -> b -> a
        assert "a" in chain
        assert "b" in chain
        assert "c" in chain

    def test_attribution_chain_for_untransformed_cell(self):
        """Verify attribution chain for cell without transformations."""
        tracker = SymbolicResidueTracker()

        chain = tracker.get_attribution_chain("orphan")

        assert chain == ["orphan"]

    def test_multiple_transformations_tracked(self):
        """Verify multiple independent transformations tracked."""
        tracker = SymbolicResidueTracker()

        # First transformation
        source1 = ContextCell(
            cell_id="a",
            content="A",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        derived1 = ContextCell(
            cell_id="b",
            content="B",
            priority=CellPriority.MEDIUM,
            token_count=50,
        )
        tracker.record_transformation(
            source_cells=[source1],
            derived_cell=derived1,
            transformation_type="compress",
        )

        # Second independent transformation
        source2 = ContextCell(
            cell_id="x",
            content="X",
            priority=CellPriority.MEDIUM,
            token_count=100,
        )
        derived2 = ContextCell(
            cell_id="y",
            content="Y",
            priority=CellPriority.MEDIUM,
            token_count=50,
        )
        tracker.record_transformation(
            source_cells=[source2],
            derived_cell=derived2,
            transformation_type="compress",
        )

        assert tracker.get_residue_for_cell("b") is not None
        assert tracker.get_residue_for_cell("y") is not None


class TestIntegration:
    """Integration tests for context packaging system."""

    def test_budget_manager_with_basin_context(self):
        """Verify cells with basin context integrate correctly."""
        manager = TokenBudgetManager(total_budget=1000, reserve_ratio=0.0)

        # Add cells from different basins
        semantic_cell = ContextCell(
            cell_id="semantic-1",
            content="Fact about Python",
            priority=CellPriority.HIGH,
            token_count=100,
            basin_id="conceptual-basin",
            resonance_score=0.8,
        )
        episodic_cell = ContextCell(
            cell_id="episodic-1",
            content="Yesterday's meeting",
            priority=CellPriority.MEDIUM,
            token_count=150,
            basin_id="experiential-basin",
            resonance_score=0.6,
        )

        manager.add_cell(semantic_cell)
        manager.add_cell(episodic_cell)

        # Get context prioritizing high resonance
        context_string, metadata = manager.get_context_package(max_tokens=200)

        # Semantic cell should be included (higher effective priority)
        assert "semantic-1" in metadata["cell_ids"]
        assert "Fact about Python" in context_string

    def test_residue_tracking_during_eviction_scenario(self):
        """Verify residue tracking can capture eviction transformations."""
        manager = TokenBudgetManager(total_budget=200, reserve_ratio=0.0)
        tracker = SymbolicResidueTracker()

        # Add initial cell
        original = ContextCell(
            cell_id="original",
            content="Original detailed content with lots of information",
            priority=CellPriority.LOW,
            token_count=150,
        )
        manager.add_cell(original)

        # Simulate summarization before eviction
        summary = ContextCell(
            cell_id="summary",
            content="Summary",
            priority=CellPriority.MEDIUM,
            token_count=30,
        )

        # Record the transformation
        residue = tracker.record_transformation(
            source_cells=[original],
            derived_cell=summary,
            transformation_type="eviction_summary",
            lost_details=["Full original text"],
        )

        # Replace original with summary
        manager.remove_cell("original")
        manager.add_cell(summary)

        # Can trace back
        chain = tracker.get_attribution_chain("summary")
        assert "original" in chain
        assert residue.compression_ratio == 0.2  # 30/150

    def test_full_workflow_budget_to_residue(self):
        """Test complete workflow from budget management to residue tracking."""
        manager = TokenBudgetManager(total_budget=500, reserve_ratio=0.1)
        tracker = SymbolicResidueTracker()

        # Add several cells
        cells = [
            ContextCell(
                cell_id=f"cell-{i}",
                content=f"Content for cell {i}",
                priority=CellPriority.MEDIUM,
                token_count=100,
            )
            for i in range(4)
        ]
        for cell in cells:
            manager.add_cell(cell)

        # Need to add high-priority cell, but budget is full
        high_priority = ContextCell(
            cell_id="high",
            content="Important content",
            priority=CellPriority.HIGH,
            token_count=100,
            resonance_score=0.9,
            attractor_strength=0.9,
        )

        # Before adding, create residue for what will be evicted
        evicted = manager._cells.get("cell-0")  # Lowest by insertion order
        if evicted:
            tracker.record_transformation(
                source_cells=[evicted],
                derived_cell=high_priority,  # Conceptually replacing
                transformation_type="priority_eviction",
                lost_details=[evicted.content],
            )

        # Add high priority (may evict lower priority)
        result = manager.add_cell(high_priority)

        # Verify workflow completed
        assert result is True
        assert manager.get_cell("high") is not None

        # Get final context
        context, meta = manager.get_context_package()
        assert "high" in meta["cell_ids"]
