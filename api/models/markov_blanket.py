"""
Markov Blanket Models for ThoughtSeed isolation.

Feature: 038-thoughtseeds-framework (Priority 2)

Implements N-level nested Markov blankets with proper conditional independence:
- Each level: external paths (eta), blanket (b = sensory + active), internal paths (mu)
- Constraint: mu^(n+1) is subset of mu^n (higher-level internal paths subset of lower-level)

Neo4j representation:
- [:SENSORY] edges: input surface connections
- [:ACTIVE] edges: output surface connections
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Set, List
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger("dionysus.markov_blanket")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BlanketValidationStatus(str, Enum):
    """Validation status for blanket structure."""
    VALID = "valid"
    INVALID_PARTITION = "invalid_partition"  # Overlapping partitions
    INVALID_NESTING = "invalid_nesting"  # mu^(n+1) not subset of mu^n
    INVALID_INDEPENDENCE = "invalid_independence"  # Conditional independence violated


class PathType(str, Enum):
    """Type of path in the Markov blanket partition."""
    EXTERNAL = "external"  # eta - environmental/external states
    SENSORY = "sensory"    # s - input surface (part of blanket)
    ACTIVE = "active"      # a - output surface (part of blanket)
    INTERNAL = "internal"  # mu - internal states


# ---------------------------------------------------------------------------
# Markov Blanket Partition
# ---------------------------------------------------------------------------


class MarkovBlanketPartition(BaseModel):
    """
    Four-way partition of state space for a Markov blanket.
    
    Based on the Free Energy Principle:
    - eta (external): States outside the system's boundary
    - s (sensory): Input surface - how external states influence internal
    - a (active): Output surface - how internal states influence external  
    - mu (internal): States that constitute the system's "self"
    
    The blanket b = s U a separates internal from external.
    Conditional independence: mu ⊥ eta | b
    """
    
    external_paths: Set[str] = Field(
        default_factory=set,
        description="eta - external state identifiers (node IDs or path names)"
    )
    sensory_paths: Set[str] = Field(
        default_factory=set,
        description="s - input surface paths ([:SENSORY] edge endpoints)"
    )
    active_paths: Set[str] = Field(
        default_factory=set,
        description="a - output surface paths ([:ACTIVE] edge endpoints)"
    )
    internal_paths: Set[str] = Field(
        default_factory=set,
        description="mu - internal state identifiers"
    )
    
    @property
    def blanket_paths(self) -> Set[str]:
        """b = s U a - the complete blanket (sensory + active)."""
        return self.sensory_paths | self.active_paths
    
    @property
    def all_paths(self) -> Set[str]:
        """All paths in the partition."""
        return self.external_paths | self.sensory_paths | self.active_paths | self.internal_paths
    
    def is_valid_partition(self) -> bool:
        """
        Check if the four sets form a valid partition (no overlaps).
        
        A valid partition requires:
        - eta ∩ s = empty
        - eta ∩ a = empty
        - eta ∩ mu = empty
        - s ∩ a = empty
        - s ∩ mu = empty
        - a ∩ mu = empty
        """
        sets = [self.external_paths, self.sensory_paths, self.active_paths, self.internal_paths]
        for i, s1 in enumerate(sets):
            for s2 in sets[i+1:]:
                if s1 & s2:  # Non-empty intersection
                    return False
        return True
    
    def get_overlaps(self) -> dict[str, Set[str]]:
        """Return any overlapping paths between partition sets."""
        overlaps = {}
        pairs = [
            ("external-sensory", self.external_paths, self.sensory_paths),
            ("external-active", self.external_paths, self.active_paths),
            ("external-internal", self.external_paths, self.internal_paths),
            ("sensory-active", self.sensory_paths, self.active_paths),
            ("sensory-internal", self.sensory_paths, self.internal_paths),
            ("active-internal", self.active_paths, self.internal_paths),
        ]
        for name, s1, s2 in pairs:
            intersection = s1 & s2
            if intersection:
                overlaps[name] = intersection
        return overlaps


# ---------------------------------------------------------------------------
# Validation Result
# ---------------------------------------------------------------------------


class ValidationResult(BaseModel):
    """Result of blanket structure validation."""
    
    is_valid: bool = Field(description="Overall validity")
    status: BlanketValidationStatus = Field(description="Specific validation status")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def valid(cls) -> "ValidationResult":
        """Create a valid result."""
        return cls(is_valid=True, status=BlanketValidationStatus.VALID)
    
    @classmethod
    def invalid(cls, status: BlanketValidationStatus, errors: List[str]) -> "ValidationResult":
        """Create an invalid result."""
        return cls(is_valid=False, status=status, errors=errors)


# ---------------------------------------------------------------------------
# Nested Markov Blanket
# ---------------------------------------------------------------------------


class NestedMarkovBlanket(BaseModel):
    """
    N-level nested Markov blanket for hierarchical isolation.
    
    Implements the nesting constraint from active inference:
    mu^(n+1) ⊂ mu^n - higher-level internal paths are a subset of lower-level internal paths.
    
    This means:
    - Level 0 (base): Largest internal state space
    - Level 1: Internal paths ⊂ Level 0's internal paths
    - Level N: Smallest "cognitive core" at the top of hierarchy
    
    The blanket at each level provides conditional independence:
    mu^n ⊥ eta^n | b^n
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    level: int = Field(ge=0, description="Hierarchy level (0 = base, higher = more nested)")
    partition: MarkovBlanketPartition = Field(description="Four-way state partition")
    
    # Hierarchical relationships (stored as IDs, not full objects to avoid cycles)
    parent_id: Optional[str] = Field(None, description="Parent blanket ID (level - 1)")
    child_ids: List[str] = Field(default_factory=list, description="Child blanket IDs (level + 1)")
    
    # Metadata
    thoughtseed_id: Optional[str] = Field(None, description="Associated ThoughtSeed ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "blanket-001",
                "level": 0,
                "partition": {
                    "external_paths": {"env-001", "env-002"},
                    "sensory_paths": {"sensor-001"},
                    "active_paths": {"action-001"},
                    "internal_paths": {"belief-001", "belief-002", "goal-001"}
                },
                "parent_id": None,
                "child_ids": ["blanket-002"]
            }
        }
    }
    
    def enforce_conditional_independence(self) -> bool:
        """
        Verify conditional independence: mu ⊥ eta | b.
        
        Internal states are independent of external states given the blanket.
        In graph terms: all paths from mu to eta must pass through b.
        
        This is a structural check - actual independence depends on the
        graph topology in Neo4j.
        
        Returns:
            True if structural independence is maintained (no direct mu-eta paths).
        """
        # Structural check: mu and eta should share no direct paths
        # They can only communicate through the blanket (s and a)
        direct_overlap = self.partition.internal_paths & self.partition.external_paths
        
        if direct_overlap:
            logger.warning(
                f"Conditional independence violated: direct paths between "
                f"internal and external: {direct_overlap}"
            )
            return False
        
        return True
    
    def validate_partition(self) -> ValidationResult:
        """Validate that the partition is well-formed (no overlaps)."""
        if not self.partition.is_valid_partition():
            overlaps = self.partition.get_overlaps()
            errors = [f"Overlapping paths in {k}: {v}" for k, v in overlaps.items()]
            return ValidationResult.invalid(BlanketValidationStatus.INVALID_PARTITION, errors)
        return ValidationResult.valid()


# ---------------------------------------------------------------------------
# Blanket Hierarchy (for multi-level validation)
# ---------------------------------------------------------------------------


class MarkovBlanketHierarchy(BaseModel):
    """
    Complete hierarchy of nested Markov blankets for validation.
    
    Enforces the nesting constraint across all levels:
    mu^(n+1) ⊂ mu^n for all n in [0, max_level - 1]
    """
    
    blankets: dict[str, NestedMarkovBlanket] = Field(
        default_factory=dict,
        description="Map of blanket ID to blanket"
    )
    root_id: Optional[str] = Field(None, description="ID of level-0 (root) blanket")
    
    def add_blanket(self, blanket: NestedMarkovBlanket) -> None:
        """Add a blanket to the hierarchy."""
        self.blankets[blanket.id] = blanket
        if blanket.level == 0:
            self.root_id = blanket.id
    
    def get_blanket(self, blanket_id: str) -> Optional[NestedMarkovBlanket]:
        """Get a blanket by ID."""
        return self.blankets.get(blanket_id)
    
    def get_parent(self, blanket: NestedMarkovBlanket) -> Optional[NestedMarkovBlanket]:
        """Get parent blanket."""
        if blanket.parent_id:
            return self.blankets.get(blanket.parent_id)
        return None
    
    def get_children(self, blanket: NestedMarkovBlanket) -> List[NestedMarkovBlanket]:
        """Get child blankets."""
        return [self.blankets[cid] for cid in blanket.child_ids if cid in self.blankets]
    
    def validate_nesting(self, child: NestedMarkovBlanket, parent: NestedMarkovBlanket) -> bool:
        """
        Validate nesting constraint: mu^(n+1) ⊂ mu^n.
        
        The child's internal paths must be a subset of the parent's internal paths.
        This ensures that higher levels deal with increasingly abstract/constrained state spaces.
        
        Args:
            child: Higher-level blanket (level n+1)
            parent: Lower-level blanket (level n)
            
        Returns:
            True if child.internal_paths ⊂ parent.internal_paths
        """
        if child.level <= parent.level:
            logger.error(f"Invalid nesting: child level {child.level} <= parent level {parent.level}")
            return False
        
        child_internal = child.partition.internal_paths
        parent_internal = parent.partition.internal_paths
        
        if not child_internal.issubset(parent_internal):
            extra = child_internal - parent_internal
            logger.warning(
                f"Nesting violation: child has internal paths not in parent: {extra}"
            )
            return False
        
        return True
    
    def validate_all(self) -> ValidationResult:
        """
        Validate the entire hierarchy.
        
        Checks:
        1. Each blanket has valid partition
        2. Each blanket maintains conditional independence
        3. All parent-child relationships satisfy nesting constraint
        """
        errors = []
        warnings = []
        
        for blanket_id, blanket in self.blankets.items():
            # Check partition validity
            partition_result = blanket.validate_partition()
            if not partition_result.is_valid:
                errors.extend([f"[{blanket_id}] {e}" for e in partition_result.errors])
            
            # Check conditional independence
            if not blanket.enforce_conditional_independence():
                errors.append(f"[{blanket_id}] Conditional independence violated")
            
            # Check nesting with parent
            parent = self.get_parent(blanket)
            if parent and not self.validate_nesting(blanket, parent):
                errors.append(
                    f"[{blanket_id}] Nesting violation: internal paths not subset of parent"
                )
        
        if errors:
            return ValidationResult.invalid(
                BlanketValidationStatus.INVALID_NESTING,
                errors
            )
        
        result = ValidationResult.valid()
        result.warnings = warnings
        return result


# ---------------------------------------------------------------------------
# Neo4j Edge Types (for documentation/schema generation)
# ---------------------------------------------------------------------------


class Neo4jBlanketEdgeType:
    """
    Neo4j edge type definitions for Markov blanket structure.
    
    These edges connect ThoughtSeeds and represent the blanket boundary:
    - [:SENSORY]: Input surface - how external states influence the ThoughtSeed
    - [:ACTIVE]: Output surface - how the ThoughtSeed influences external states
    """
    
    SENSORY = "SENSORY"
    ACTIVE = "ACTIVE"
    
    @classmethod
    def get_sensory_edge_cypher(cls) -> str:
        """Cypher pattern for sensory edges (inbound to ThoughtSeed)."""
        return "(source)-[:SENSORY]->(target:ThoughtSeed)"
    
    @classmethod
    def get_active_edge_cypher(cls) -> str:
        """Cypher pattern for active edges (outbound from ThoughtSeed)."""
        return "(source:ThoughtSeed)-[:ACTIVE]->(target)"
    
    @classmethod
    def get_create_sensory_cypher(
        cls,
        source_id: str,
        target_seed_id: str,
        properties: Optional[dict] = None
    ) -> tuple[str, dict]:
        """
        Generate Cypher to create a SENSORY edge.
        
        Args:
            source_id: ID of the source node (external state)
            target_seed_id: ID of the target ThoughtSeed
            properties: Optional edge properties
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        props = properties or {}
        cypher = """
        MATCH (source {id: $source_id})
        MATCH (target:ThoughtSeed {id: $target_id})
        MERGE (source)-[r:SENSORY]->(target)
        SET r += $props
        SET r.created_at = COALESCE(r.created_at, datetime())
        SET r.updated_at = datetime()
        RETURN r
        """
        return cypher, {"source_id": source_id, "target_id": target_seed_id, "props": props}
    
    @classmethod
    def get_create_active_cypher(
        cls,
        source_seed_id: str,
        target_id: str,
        properties: Optional[dict] = None
    ) -> tuple[str, dict]:
        """
        Generate Cypher to create an ACTIVE edge.
        
        Args:
            source_seed_id: ID of the source ThoughtSeed
            target_id: ID of the target node (action or external state)
            properties: Optional edge properties
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        props = properties or {}
        cypher = """
        MATCH (source:ThoughtSeed {id: $source_id})
        MATCH (target {id: $target_id})
        MERGE (source)-[r:ACTIVE]->(target)
        SET r += $props
        SET r.created_at = COALESCE(r.created_at, datetime())
        SET r.updated_at = datetime()
        RETURN r
        """
        return cypher, {"source_id": source_seed_id, "target_id": target_id, "props": props}
