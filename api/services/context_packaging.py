"""
Context Packaging Service - Cellular Memory Physics.

Implements Context-Engineering patterns for token budgets, resonance coupling,
and symbolic residue tracking in the Nemori memory system.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)


class CellPriority(str, Enum):
    """Priority levels for context cells."""
    CRITICAL = "critical"  # Must be included (identity, goals)
    HIGH = "high"          # Strong relevance to current task
    MEDIUM = "medium"      # Supporting context
    LOW = "low"            # Background/historical
    EPHEMERAL = "ephemeral"  # Can be dropped first


@dataclass
class TokenBudget:
    """Token allocation for a context cell."""
    allocated: int
    used: int = 0
    reserved: int = 0  # Pre-allocated for expected content
    
    @property
    def available(self) -> int:
        return max(0, self.allocated - self.used - self.reserved)
    
    @property
    def utilization(self) -> float:
        return self.used / self.allocated if self.allocated > 0 else 0.0
    
    def can_fit(self, tokens: int) -> bool:
        return tokens <= self.available
    
    def consume(self, tokens: int) -> bool:
        """Consume tokens from budget. Returns False if insufficient."""
        if not self.can_fit(tokens):
            return False
        self.used += tokens
        return True


@dataclass
class ContextCell:
    """
    A cellular unit of context with token budget awareness.
    
    Follows Context-Engineering's "Cellular Memory Physics" pattern where
    context is organized into discrete cells with explicit resource management.
    """
    cell_id: str
    content: str
    priority: CellPriority
    token_count: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    
    # Resonance and attractor properties
    resonance_score: float = 0.5  # Semantic alignment with current goal
    attractor_strength: float = 1.0  # Persistence strength (decays over time)
    basin_id: Optional[str] = None  # Associated attractor basin
    
    # Symbolic residue tracking
    causal_links: List[str] = field(default_factory=list)  # IDs of cells this derives from
    derived_cells: List[str] = field(default_factory=list)  # IDs of cells derived from this
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def touch(self) -> None:
        """Mark cell as accessed, updating timestamp and count."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
        # Reinforce attractor strength on access
        self.attractor_strength = min(1.0, self.attractor_strength + 0.1)
    
    def decay(self, rate: float = 0.01) -> None:
        """Apply decay to attractor strength."""
        self.attractor_strength = max(0.0, self.attractor_strength - rate)
    
    @property
    def effective_priority(self) -> float:
        """
        Compute effective priority combining base priority, resonance, and strength.
        Higher values = more important to keep.
        """
        priority_weights = {
            CellPriority.CRITICAL: 1.0,
            CellPriority.HIGH: 0.8,
            CellPriority.MEDIUM: 0.5,
            CellPriority.LOW: 0.2,
            CellPriority.EPHEMERAL: 0.1,
        }
        base = priority_weights.get(self.priority, 0.5)
        return base * 0.4 + self.resonance_score * 0.3 + self.attractor_strength * 0.3
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize cell to dictionary."""
        return {
            "cell_id": self.cell_id,
            "content": self.content,
            "priority": self.priority.value,
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "resonance_score": self.resonance_score,
            "attractor_strength": self.attractor_strength,
            "basin_id": self.basin_id,
            "causal_links": self.causal_links,
            "derived_cells": self.derived_cells,
            "effective_priority": self.effective_priority,
            "metadata": self.metadata,
        }


@dataclass
class SchemaContextCell(ContextCell):
    """
    A cell carrying active schema constraints to bias agent reasoning.
    Prevents 'Semantic Drift' by enforcing established ontologies.
    """
    schema_domain: str = "general"
    constraints: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Auto-generate content XML if not provided."""
        if not self.content and self.constraints:
            items = "\n".join(f"    <constraint>{c}</constraint>" for c in self.constraints)
            self.content = f"""<active_schema domain="{self.schema_domain}">
{items}
</active_schema>"""


class TokenBudgetManager:
    """
    Manages token allocation across context cells.
    
    Implements budget-aware memory where cells compete for limited token space
    based on priority, resonance, and attractor strength.
    """
    
    def __init__(self, total_budget: int = 8000, reserve_ratio: float = 0.1):
        """
        Initialize budget manager.
        
        Args:
            total_budget: Total tokens available for context.
            reserve_ratio: Fraction to reserve for new content (0.0-0.5).
        """
        self.total_budget = total_budget
        self.reserve_ratio = min(0.5, max(0.0, reserve_ratio))
        self._cells: Dict[str, ContextCell] = {}
        self._cell_order: List[str] = []  # Maintains insertion order
    
    @property
    def reserved_tokens(self) -> int:
        return int(self.total_budget * self.reserve_ratio)
    
    @property
    def usable_budget(self) -> int:
        return self.total_budget - self.reserved_tokens
    
    @property
    def used_tokens(self) -> int:
        return sum(cell.token_count for cell in self._cells.values())
    
    @property
    def available_tokens(self) -> int:
        return max(0, self.usable_budget - self.used_tokens)
    
    @property
    def utilization(self) -> float:
        return self.used_tokens / self.usable_budget if self.usable_budget > 0 else 0.0
    
    def add_cell(self, cell: ContextCell) -> bool:
        """
        Add a cell to the budget. Returns False if insufficient space.
        May evict lower-priority cells to make room.
        """
        if cell.cell_id in self._cells:
            # Update existing cell
            old_cell = self._cells[cell.cell_id]
            self._cells[cell.cell_id] = cell
            return True
        
        # Check if fits directly
        if cell.token_count <= self.available_tokens:
            self._cells[cell.cell_id] = cell
            self._cell_order.append(cell.cell_id)
            return True
        
        # Try to evict lower-priority cells
        tokens_needed = cell.token_count - self.available_tokens
        evictable = self._get_evictable_cells(cell.effective_priority, tokens_needed)
        
        if evictable:
            for evict_id in evictable:
                self.remove_cell(evict_id)
            self._cells[cell.cell_id] = cell
            self._cell_order.append(cell.cell_id)
            return True
        
        return False
    
    def remove_cell(self, cell_id: str) -> Optional[ContextCell]:
        """Remove and return a cell."""
        cell = self._cells.pop(cell_id, None)
        if cell and cell_id in self._cell_order:
            self._cell_order.remove(cell_id)
        return cell
    
    def get_cell(self, cell_id: str) -> Optional[ContextCell]:
        """Get a cell by ID, marking it as accessed."""
        cell = self._cells.get(cell_id)
        if cell:
            cell.touch()
        return cell
    
    def _get_evictable_cells(self, min_priority: float, tokens_needed: int) -> List[str]:
        """
        Find cells that can be evicted to free up tokens.
        Returns cell IDs to evict, or empty list if not enough can be freed.
        """
        # Sort by effective priority (lowest first)
        candidates = sorted(
            [(cid, c) for cid, c in self._cells.items() if c.effective_priority < min_priority],
            key=lambda x: x[1].effective_priority
        )
        
        evict_ids = []
        freed = 0
        
        for cell_id, cell in candidates:
            if freed >= tokens_needed:
                break
            evict_ids.append(cell_id)
            freed += cell.token_count
        
        return evict_ids if freed >= tokens_needed else []
    
    def apply_decay(self, rate: float = 0.01) -> None:
        """Apply decay to all cells' attractor strength."""
        for cell in self._cells.values():
            cell.decay(rate)
    
    def update_resonance(self, goal_embedding: List[float], cell_embeddings: Dict[str, List[float]]) -> None:
        """
        Update resonance scores for cells based on goal alignment.
        
        Args:
            goal_embedding: Embedding vector for current goal.
            cell_embeddings: Map of cell_id -> embedding vector.
        """
        for cell_id, embedding in cell_embeddings.items():
            if cell_id in self._cells:
                similarity = self._cosine_similarity(goal_embedding, embedding)
                self._cells[cell_id].resonance_score = similarity
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b) or len(a) == 0:
            return 0.5
        
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.5
        
        return (dot / (norm_a * norm_b) + 1) / 2  # Normalize to [0, 1]
    
    def get_context_package(self, max_tokens: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Package cells into context string within token budget.
        
        Args:
            max_tokens: Maximum tokens to include (defaults to usable budget).
            
        Returns:
            Tuple of (context_string, metadata).
        """
        budget = max_tokens or self.usable_budget
        
        # Sort by effective priority (highest first)
        sorted_cells = sorted(
            self._cells.values(),
            key=lambda c: c.effective_priority,
            reverse=True
        )
        
        included = []
        total_tokens = 0
        
        for cell in sorted_cells:
            if total_tokens + cell.token_count <= budget:
                included.append(cell)
                total_tokens += cell.token_count
                cell.touch()
        
        # Build context string
        context_parts = [cell.content for cell in included]
        context_string = "\n\n".join(context_parts)
        
        metadata = {
            "cells_included": len(included),
            "cells_excluded": len(sorted_cells) - len(included),
            "tokens_used": total_tokens,
            "tokens_budget": budget,
            "utilization": total_tokens / budget if budget > 0 else 0.0,
            "cell_ids": [c.cell_id for c in included],
        }
        
        return context_string, metadata
    
    def get_stats(self) -> Dict[str, Any]:
        """Get budget statistics."""
        return {
            "total_budget": self.total_budget,
            "usable_budget": self.usable_budget,
            "reserved_tokens": self.reserved_tokens,
            "used_tokens": self.used_tokens,
            "available_tokens": self.available_tokens,
            "utilization": self.utilization,
            "cell_count": len(self._cells),
            "priority_distribution": self._get_priority_distribution(),
        }
    
    def _get_priority_distribution(self) -> Dict[str, int]:
        """Get count of cells by priority."""
        dist: Dict[str, int] = {}
        for cell in self._cells.values():
            key = cell.priority.value
            dist[key] = dist.get(key, 0) + 1
        return dist


@dataclass
class SymbolicResidue:
    """
    Tracks symbolic residue - the trace left by context transformations.
    
    When context is compressed, summarized, or transformed, symbolic residue
    captures what was lost and maintains causal attribution.
    """
    residue_id: str
    source_cell_ids: List[str]  # Original cells that were transformed
    derived_cell_id: str  # New cell created from transformation
    transformation_type: str  # e.g., "compression", "summarization", "abstraction"
    
    # What was lost/changed
    lost_details: List[str] = field(default_factory=list)
    compression_ratio: float = 1.0
    
    # Causal attribution
    timestamp: datetime = field(default_factory=datetime.utcnow)
    attribution_chain: List[str] = field(default_factory=list)  # Chain of transformations
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "residue_id": self.residue_id,
            "source_cell_ids": self.source_cell_ids,
            "derived_cell_id": self.derived_cell_id,
            "transformation_type": self.transformation_type,
            "lost_details": self.lost_details,
            "compression_ratio": self.compression_ratio,
            "timestamp": self.timestamp.isoformat(),
            "attribution_chain": self.attribution_chain,
        }


class SymbolicResidueTracker:
    """
    Tracks symbolic residue across context transformations.
    
    Maintains causal attribution trees showing how context evolved.
    """
    
    def __init__(self):
        self._residues: Dict[str, SymbolicResidue] = {}
        self._cell_to_residue: Dict[str, str] = {}  # cell_id -> residue_id
    
    def record_transformation(
        self,
        source_cells: List[ContextCell],
        derived_cell: ContextCell,
        transformation_type: str,
        lost_details: Optional[List[str]] = None,
    ) -> SymbolicResidue:
        """
        Record a context transformation.
        
        Args:
            source_cells: Original cells that were transformed.
            derived_cell: New cell created from transformation.
            transformation_type: Type of transformation performed.
            lost_details: Optional list of details that were lost.
            
        Returns:
            SymbolicResidue tracking the transformation.
        """
        import uuid
        
        source_tokens = sum(c.token_count for c in source_cells)
        compression_ratio = derived_cell.token_count / source_tokens if source_tokens > 0 else 1.0
        
        # Build attribution chain from source cells
        attribution_chain = []
        for sc in source_cells:
            if sc.cell_id in self._cell_to_residue:
                prev_residue = self._residues[self._cell_to_residue[sc.cell_id]]
                attribution_chain.extend(prev_residue.attribution_chain)
            attribution_chain.append(sc.cell_id)
        
        residue = SymbolicResidue(
            residue_id=str(uuid.uuid4())[:8],
            source_cell_ids=[c.cell_id for c in source_cells],
            derived_cell_id=derived_cell.cell_id,
            transformation_type=transformation_type,
            lost_details=lost_details or [],
            compression_ratio=compression_ratio,
            attribution_chain=list(set(attribution_chain)),  # Deduplicate
        )
        
        self._residues[residue.residue_id] = residue
        self._cell_to_residue[derived_cell.cell_id] = residue.residue_id
        
        # Update derived cell's causal links
        derived_cell.causal_links = residue.source_cell_ids
        for sc in source_cells:
            if derived_cell.cell_id not in sc.derived_cells:
                sc.derived_cells.append(derived_cell.cell_id)
        
        return residue
    
    def get_attribution_chain(self, cell_id: str) -> List[str]:
        """Get the full causal attribution chain for a cell."""
        if cell_id not in self._cell_to_residue:
            return [cell_id]
        
        residue = self._residues[self._cell_to_residue[cell_id]]
        return residue.attribution_chain + [cell_id]
    
    def get_residue(self, residue_id: str) -> Optional[SymbolicResidue]:
        return self._residues.get(residue_id)
    
    def get_residue_for_cell(self, cell_id: str) -> Optional[SymbolicResidue]:
        residue_id = self._cell_to_residue.get(cell_id)
        return self._residues.get(residue_id) if residue_id else None


# Module-level instances
_budget_manager: Optional[TokenBudgetManager] = None
_residue_tracker: Optional[SymbolicResidueTracker] = None


def get_token_budget_manager(total_budget: int = 8000) -> TokenBudgetManager:
    """Get or create the global TokenBudgetManager."""
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = TokenBudgetManager(total_budget=total_budget)
    return _budget_manager


def get_residue_tracker() -> SymbolicResidueTracker:
    """Get or create the global SymbolicResidueTracker."""
    global _residue_tracker
    if _residue_tracker is None:
        _residue_tracker = SymbolicResidueTracker()
    return _residue_tracker


async def fetch_schema_context(query: str, budget_manager: TokenBudgetManager) -> Optional[SchemaContextCell]:
    """
    Retrieves latent schemas from AutoSchemaKG to ground the current thought process.
    
    Orchestration:
    1. Call AutoSchemaKG Retrieval (Read-Path).
    2. Convert inferred concepts into 'Constraints'.
    3. Package into a SchemaContextCell (HIGH priority).
    4. Inject into Budget Manager.
    
    Args:
        query: The active thought/query to ground.
        budget_manager: The active token budget manager.
        
    Returns:
        The created SchemaContextCell if successful, else None.
    """
    try:
        # Lazy import to avoid circular dependency
        from api.services.consciousness.autoschemakg_integration import get_autoschemakg_service
        
        svc = get_autoschemakg_service()
        concepts = await svc.retrieve_relevant_concepts(query) 
        
        if concepts:
            constraints = [f"{c.name} ({c.concept_type.value})" for c in concepts]
            
            # Calculate tokens (approximation: chars / 4)
            # A strict budget tracking would use a tokenizer, but heuristic is fine here.
            total_chars = sum(len(c) for c in constraints) + len(concepts) * 10
            token_count = int(total_chars / 4) + 20
            
            cell = SchemaContextCell(
                cell_id=f"schema_{abs(hash(query))}",
                content="", # Will be auto-generated in post_init
                priority=CellPriority.HIGH, # Schema is non-negotiable
                token_count=token_count,
                schema_domain="inferred_ontology",
                constraints=constraints
            )
            created = budget_manager.add_cell(cell)
            if created:
                logger.info(f"Schema Constraint Injected: {len(constraints)} items from AutoSchemaKG")
                return cell
                
    except Exception as e:
        logger.warning(f"Failed to fetch schema context: {e}")
        
    return None
