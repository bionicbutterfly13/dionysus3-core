"""
Blanket Enforcement Service for Markov Blanket validation and management.

Feature: 038-thoughtseeds-framework (Priority 2)

Provides:
- Blanket structure validation
- Nested blanket creation with constraint checking
- Conditional independence verification
- Neo4j schema operations for [:SENSORY] and [:ACTIVE] edges

Database: Neo4j via WebhookNeo4jDriver (n8n webhooks)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List, Set
from uuid import uuid4

from api.models.markov_blanket import (
    MarkovBlanketPartition,
    NestedMarkovBlanket,
    MarkovBlanketHierarchy,
    ValidationResult,
    BlanketValidationStatus,
    Neo4jBlanketEdgeType,
)
from api.services.webhook_neo4j_driver import WebhookNeo4jDriver, get_neo4j_driver

logger = logging.getLogger("dionysus.blanket_enforcement")


# ---------------------------------------------------------------------------
# Blanket Enforcement Service
# ---------------------------------------------------------------------------


class BlanketEnforcementService:
    """
    Service for managing and validating Markov blanket structures.
    
    Responsibilities:
    1. Validate blanket structure (partition validity, conditional independence)
    2. Create nested blankets with proper constraint checking
    3. Verify nesting constraints (mu^(n+1) subset of mu^n)
    4. Manage Neo4j [:SENSORY] and [:ACTIVE] edges
    """
    
    def __init__(self, driver: Optional[WebhookNeo4jDriver] = None):
        """Initialize with Neo4j driver."""
        self._driver = driver or get_neo4j_driver()
        self._hierarchy_cache: dict[str, MarkovBlanketHierarchy] = {}
    
    # -------------------------------------------------------------------------
    # Validation Methods
    # -------------------------------------------------------------------------
    
    def validate_blanket_structure(self, blanket: NestedMarkovBlanket) -> ValidationResult:
        """
        Validate a blanket's structure for consistency and independence.
        
        Checks:
        1. Partition validity (no overlapping sets)
        2. Conditional independence (mu disjoint from eta)
        
        Args:
            blanket: The blanket to validate
            
        Returns:
            ValidationResult with status and any errors
        """
        errors = []
        
        # Check 1: Valid partition (no overlaps)
        if not blanket.partition.is_valid_partition():
            overlaps = blanket.partition.get_overlaps()
            for name, paths in overlaps.items():
                errors.append(f"Partition overlap in {name}: {paths}")
        
        # Check 2: Conditional independence
        if not blanket.enforce_conditional_independence():
            overlap = blanket.partition.internal_paths & blanket.partition.external_paths
            errors.append(f"Conditional independence violated: direct internal-external paths: {overlap}")
        
        if errors:
            return ValidationResult.invalid(
                BlanketValidationStatus.INVALID_PARTITION,
                errors
            )
        
        logger.debug(f"Blanket {blanket.id} validated successfully")
        return ValidationResult.valid()
    
    def check_conditional_independence(self, blanket: NestedMarkovBlanket) -> bool:
        """
        Check if a blanket maintains conditional independence.
        
        Conditional independence: mu (internal) is independent of eta (external)
        given b (blanket = sensory + active).
        
        In structural terms: internal and external paths must be disjoint,
        and all communication must flow through the blanket.
        
        Args:
            blanket: The blanket to check
            
        Returns:
            True if conditional independence is maintained
        """
        return blanket.enforce_conditional_independence()
    
    def validate_nesting_constraint(
        self,
        child: NestedMarkovBlanket,
        parent: NestedMarkovBlanket
    ) -> ValidationResult:
        """
        Validate the nesting constraint between parent and child blankets.
        
        Constraint: mu^(n+1) subset of mu^n
        The child's internal paths must be a subset of the parent's internal paths.
        
        Args:
            child: Higher-level blanket (level n+1)
            parent: Lower-level blanket (level n)
            
        Returns:
            ValidationResult with status
        """
        if child.level <= parent.level:
            return ValidationResult.invalid(
                BlanketValidationStatus.INVALID_NESTING,
                [f"Child level ({child.level}) must be greater than parent level ({parent.level})"]
            )
        
        child_internal = child.partition.internal_paths
        parent_internal = parent.partition.internal_paths
        
        if not child_internal.issubset(parent_internal):
            extra_paths = child_internal - parent_internal
            return ValidationResult.invalid(
                BlanketValidationStatus.INVALID_NESTING,
                [f"Child has internal paths not in parent: {extra_paths}"]
            )
        
        return ValidationResult.valid()
    
    # -------------------------------------------------------------------------
    # Blanket Creation Methods
    # -------------------------------------------------------------------------
    
    def create_nested_blanket(
        self,
        level: int,
        parent: Optional[NestedMarkovBlanket] = None,
        external_paths: Optional[Set[str]] = None,
        sensory_paths: Optional[Set[str]] = None,
        active_paths: Optional[Set[str]] = None,
        internal_paths: Optional[Set[str]] = None,
        thoughtseed_id: Optional[str] = None,
    ) -> NestedMarkovBlanket:
        """
        Create a new nested Markov blanket with validation.
        
        If a parent is provided:
        - Validates that internal_paths is a subset of parent's internal_paths
        - Automatically registers the child with the parent
        
        Args:
            level: Hierarchy level (0 = base)
            parent: Optional parent blanket for nesting
            external_paths: External state identifiers
            sensory_paths: Input surface paths
            active_paths: Output surface paths
            internal_paths: Internal state identifiers
            thoughtseed_id: Associated ThoughtSeed ID
            
        Returns:
            Created NestedMarkovBlanket
            
        Raises:
            ValueError: If nesting constraint is violated
        """
        # Create partition
        partition = MarkovBlanketPartition(
            external_paths=external_paths or set(),
            sensory_paths=sensory_paths or set(),
            active_paths=active_paths or set(),
            internal_paths=internal_paths or set(),
        )
        
        # Validate partition
        if not partition.is_valid_partition():
            overlaps = partition.get_overlaps()
            raise ValueError(f"Invalid partition - overlapping paths: {overlaps}")
        
        # Create blanket
        blanket_id = str(uuid4())
        blanket = NestedMarkovBlanket(
            id=blanket_id,
            level=level,
            partition=partition,
            parent_id=parent.id if parent else None,
            child_ids=[],
            thoughtseed_id=thoughtseed_id,
        )
        
        # Validate nesting if parent provided
        if parent:
            result = self.validate_nesting_constraint(blanket, parent)
            if not result.is_valid:
                raise ValueError(f"Nesting constraint violated: {result.errors}")
            
            # Register child with parent (in-memory, would need persistence)
            parent.child_ids.append(blanket_id)
            parent.updated_at = datetime.utcnow()
        
        # Validate conditional independence
        if not blanket.enforce_conditional_independence():
            overlap = partition.internal_paths & partition.external_paths
            raise ValueError(f"Conditional independence violated: {overlap}")
        
        logger.info(
            f"Created nested blanket {blanket_id} at level {level}"
            f"{f' (parent: {parent.id})' if parent else ''}"
        )
        
        return blanket
    
    def create_blanket_from_thoughtseed(
        self,
        thoughtseed_id: str,
        level: int = 0,
        parent: Optional[NestedMarkovBlanket] = None,
    ) -> NestedMarkovBlanket:
        """
        Create a blanket for a ThoughtSeed by querying its Neo4j relationships.
        
        Discovers:
        - Sensory paths: Nodes connected via [:SENSORY] edges (inbound)
        - Active paths: Nodes connected via [:ACTIVE] edges (outbound)
        - Internal paths: The ThoughtSeed itself and nested components
        - External paths: Nodes beyond the sensory boundary
        
        Args:
            thoughtseed_id: ID of the ThoughtSeed
            level: Hierarchy level
            parent: Optional parent blanket
            
        Returns:
            NestedMarkovBlanket with discovered paths
        """
        # This would be an async method in practice
        # For now, return a template that can be populated
        return self.create_nested_blanket(
            level=level,
            parent=parent,
            internal_paths={thoughtseed_id},
            thoughtseed_id=thoughtseed_id,
        )
    
    # -------------------------------------------------------------------------
    # Hierarchy Management
    # -------------------------------------------------------------------------
    
    def create_hierarchy(self, root_blanket: NestedMarkovBlanket) -> MarkovBlanketHierarchy:
        """
        Create a new blanket hierarchy with the given root.
        
        Args:
            root_blanket: Level 0 blanket to use as root
            
        Returns:
            MarkovBlanketHierarchy containing the root
            
        Raises:
            ValueError: If root is not level 0
        """
        if root_blanket.level != 0:
            raise ValueError(f"Root blanket must be level 0, got level {root_blanket.level}")
        
        hierarchy = MarkovBlanketHierarchy()
        hierarchy.add_blanket(root_blanket)
        
        return hierarchy
    
    def validate_hierarchy(self, hierarchy: MarkovBlanketHierarchy) -> ValidationResult:
        """
        Validate an entire blanket hierarchy.
        
        Checks all blankets and their relationships.
        
        Args:
            hierarchy: The hierarchy to validate
            
        Returns:
            ValidationResult with status
        """
        return hierarchy.validate_all()
    
    # -------------------------------------------------------------------------
    # Neo4j Operations
    # -------------------------------------------------------------------------
    
    async def discover_blanket_paths(
        self,
        thoughtseed_id: str,
        max_depth: int = 2
    ) -> MarkovBlanketPartition:
        """
        Discover the blanket paths for a ThoughtSeed from Neo4j.
        
        Queries the graph to find:
        - Sensory paths: Sources of [:SENSORY] edges to this ThoughtSeed
        - Active paths: Targets of [:ACTIVE] edges from this ThoughtSeed
        - External paths: Nodes beyond sensory boundary (not directly connected)
        - Internal paths: The ThoughtSeed and its internal components
        
        Args:
            thoughtseed_id: ID of the ThoughtSeed
            max_depth: How deep to search for external paths
            
        Returns:
            MarkovBlanketPartition with discovered paths
        """
        cypher = """
        // Get the ThoughtSeed
        MATCH (ts:ThoughtSeed {id: $seed_id})
        
        // Find sensory inputs (inbound SENSORY edges)
        OPTIONAL MATCH (sensory_source)-[:SENSORY]->(ts)
        WITH ts, COLLECT(DISTINCT sensory_source.id) as sensory_paths
        
        // Find active outputs (outbound ACTIVE edges)
        OPTIONAL MATCH (ts)-[:ACTIVE]->(active_target)
        WITH ts, sensory_paths, COLLECT(DISTINCT active_target.id) as active_paths
        
        // Find internal components (nested ThoughtSeeds)
        OPTIONAL MATCH (ts)-[:HAS_CHILD]->(child:ThoughtSeed)
        WITH ts, sensory_paths, active_paths, COLLECT(DISTINCT child.id) as child_ids
        
        // External: nodes connected to sensory sources but not directly to ts
        OPTIONAL MATCH (external)-[]->(sensory_source)
        WHERE sensory_source.id IN sensory_paths
        AND NOT (external)-[:SENSORY]->(ts)
        AND NOT external.id = ts.id
        WITH ts, sensory_paths, active_paths, child_ids, 
             COLLECT(DISTINCT external.id) as external_paths
        
        RETURN {
            internal: [$seed_id] + child_ids,
            sensory: sensory_paths,
            active: active_paths,
            external: external_paths
        } as partition
        """
        
        try:
            result = await self._driver.execute_query(cypher, {"seed_id": thoughtseed_id})
            
            if result and result[0]:
                partition_data = result[0].get("partition", {})
                return MarkovBlanketPartition(
                    internal_paths=set(partition_data.get("internal", [thoughtseed_id])),
                    sensory_paths=set(partition_data.get("sensory", [])),
                    active_paths=set(partition_data.get("active", [])),
                    external_paths=set(partition_data.get("external", [])),
                )
        except Exception as e:
            logger.error(f"Error discovering blanket paths for {thoughtseed_id}: {e}")
        
        # Fallback: minimal partition with just the ThoughtSeed
        return MarkovBlanketPartition(internal_paths={thoughtseed_id})
    
    async def create_sensory_edge(
        self,
        source_id: str,
        target_seed_id: str,
        weight: float = 1.0,
        precision: float = 0.5
    ) -> bool:
        """
        Create a [:SENSORY] edge in Neo4j.
        
        Represents the input surface of a ThoughtSeed's Markov blanket.
        
        Args:
            source_id: ID of the source node (external state)
            target_seed_id: ID of the target ThoughtSeed
            weight: Connection weight (0-1)
            precision: Precision/confidence of the sensory channel (0-1)
            
        Returns:
            True if edge created successfully
        """
        cypher, params = Neo4jBlanketEdgeType.get_create_sensory_cypher(
            source_id,
            target_seed_id,
            {"weight": weight, "precision": precision}
        )
        
        try:
            await self._driver.execute_query(cypher, params)
            logger.debug(f"Created SENSORY edge: {source_id} -> {target_seed_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating SENSORY edge: {e}")
            return False
    
    async def create_active_edge(
        self,
        source_seed_id: str,
        target_id: str,
        weight: float = 1.0,
        precision: float = 0.5
    ) -> bool:
        """
        Create an [:ACTIVE] edge in Neo4j.
        
        Represents the output surface of a ThoughtSeed's Markov blanket.
        
        Args:
            source_seed_id: ID of the source ThoughtSeed
            target_id: ID of the target node (action or external state)
            weight: Connection weight (0-1)
            precision: Precision/confidence of the active channel (0-1)
            
        Returns:
            True if edge created successfully
        """
        cypher, params = Neo4jBlanketEdgeType.get_create_active_cypher(
            source_seed_id,
            target_id,
            {"weight": weight, "precision": precision}
        )
        
        try:
            await self._driver.execute_query(cypher, params)
            logger.debug(f"Created ACTIVE edge: {source_seed_id} -> {target_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating ACTIVE edge: {e}")
            return False
    
    async def validate_blanket_in_neo4j(self, thoughtseed_id: str) -> ValidationResult:
        """
        Validate a ThoughtSeed's blanket structure in Neo4j.
        
        Checks:
        1. ThoughtSeed exists
        2. Has at least one SENSORY or ACTIVE edge (has a blanket)
        3. No direct internal-external connections bypassing blanket
        
        Args:
            thoughtseed_id: ID of the ThoughtSeed
            
        Returns:
            ValidationResult
        """
        # Check existence and blanket edges
        cypher = """
        MATCH (ts:ThoughtSeed {id: $seed_id})
        OPTIONAL MATCH (ts)<-[:SENSORY]-(sensory)
        OPTIONAL MATCH (ts)-[:ACTIVE]->(active)
        WITH ts, 
             COUNT(DISTINCT sensory) as sensory_count,
             COUNT(DISTINCT active) as active_count
        
        // Check for direct connections that bypass blanket
        OPTIONAL MATCH (ts)-[r]-(other)
        WHERE NOT type(r) IN ['SENSORY', 'ACTIVE', 'HAS_CHILD', 'PART_OF', 'PRODUCED_SEED']
        WITH ts, sensory_count, active_count, COUNT(r) as bypass_count
        
        RETURN {
            exists: ts IS NOT NULL,
            has_blanket: sensory_count > 0 OR active_count > 0,
            sensory_count: sensory_count,
            active_count: active_count,
            bypass_edges: bypass_count
        } as validation
        """
        
        try:
            result = await self._driver.execute_query(cypher, {"seed_id": thoughtseed_id})
            
            if not result or not result[0]:
                return ValidationResult.invalid(
                    BlanketValidationStatus.INVALID_PARTITION,
                    ["ThoughtSeed not found in Neo4j"]
                )
            
            validation = result[0].get("validation", {})
            
            if not validation.get("exists"):
                return ValidationResult.invalid(
                    BlanketValidationStatus.INVALID_PARTITION,
                    [f"ThoughtSeed {thoughtseed_id} not found"]
                )
            
            errors = []
            warnings = []
            
            if not validation.get("has_blanket"):
                warnings.append("ThoughtSeed has no SENSORY or ACTIVE edges (no blanket)")
            
            if validation.get("bypass_edges", 0) > 0:
                warnings.append(
                    f"ThoughtSeed has {validation['bypass_edges']} edges that bypass the blanket"
                )
            
            result = ValidationResult.valid()
            result.warnings = warnings
            return result
            
        except Exception as e:
            logger.error(f"Error validating blanket in Neo4j: {e}")
            return ValidationResult.invalid(
                BlanketValidationStatus.INVALID_PARTITION,
                [f"Neo4j validation error: {str(e)}"]
            )
    
    async def get_blanket_edges(self, thoughtseed_id: str) -> dict:
        """
        Get all blanket edges (SENSORY and ACTIVE) for a ThoughtSeed.
        
        Args:
            thoughtseed_id: ID of the ThoughtSeed
            
        Returns:
            Dict with sensory_edges and active_edges lists
        """
        cypher = """
        MATCH (ts:ThoughtSeed {id: $seed_id})
        
        OPTIONAL MATCH (sensory_source)-[sr:SENSORY]->(ts)
        WITH ts, COLLECT({
            source_id: sensory_source.id,
            weight: sr.weight,
            precision: sr.precision,
            created_at: sr.created_at
        }) as sensory_edges
        
        OPTIONAL MATCH (ts)-[ar:ACTIVE]->(active_target)
        WITH ts, sensory_edges, COLLECT({
            target_id: active_target.id,
            weight: ar.weight,
            precision: ar.precision,
            created_at: ar.created_at
        }) as active_edges
        
        RETURN sensory_edges, active_edges
        """
        
        try:
            result = await self._driver.execute_query(cypher, {"seed_id": thoughtseed_id})
            
            if result and result[0]:
                return {
                    "sensory_edges": result[0].get("sensory_edges", []),
                    "active_edges": result[0].get("active_edges", []),
                }
        except Exception as e:
            logger.error(f"Error getting blanket edges: {e}")
        
        return {"sensory_edges": [], "active_edges": []}


# ---------------------------------------------------------------------------
# Schema Generation Helpers
# ---------------------------------------------------------------------------


def get_neo4j_schema_additions() -> dict:
    """
    Get Neo4j schema additions required for Markov blanket implementation.
    
    Returns:
        Dict with constraint and index definitions
    """
    return {
        "edge_types": [
            {
                "type": "SENSORY",
                "description": "Input surface of Markov blanket - how external states influence ThoughtSeed",
                "properties": {
                    "weight": "float (0-1)",
                    "precision": "float (0-1)",
                    "created_at": "datetime",
                    "updated_at": "datetime"
                }
            },
            {
                "type": "ACTIVE", 
                "description": "Output surface of Markov blanket - how ThoughtSeed influences external states",
                "properties": {
                    "weight": "float (0-1)",
                    "precision": "float (0-1)",
                    "created_at": "datetime",
                    "updated_at": "datetime"
                }
            }
        ],
        "cypher_queries": {
            "validate_blanket_isolation": """
            // Verify no direct internal-external connections
            MATCH (ts:ThoughtSeed {id: $seed_id})
            OPTIONAL MATCH (ts)-[r]-(other)
            WHERE NOT type(r) IN ['SENSORY', 'ACTIVE', 'HAS_CHILD', 'PART_OF', 'PRODUCED_SEED']
            RETURN COUNT(r) = 0 as is_isolated
            """,
            "get_blanket_summary": """
            MATCH (ts:ThoughtSeed {id: $seed_id})
            OPTIONAL MATCH (sensory)-[:SENSORY]->(ts)
            OPTIONAL MATCH (ts)-[:ACTIVE]->(active)
            RETURN {
                thoughtseed_id: ts.id,
                sensory_count: COUNT(DISTINCT sensory),
                active_count: COUNT(DISTINCT active),
                has_blanket: COUNT(sensory) > 0 OR COUNT(active) > 0
            }
            """
        }
    }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


_instance: Optional[BlanketEnforcementService] = None


def get_blanket_enforcement_service(
    driver: Optional[WebhookNeo4jDriver] = None
) -> BlanketEnforcementService:
    """Get or create the blanket enforcement service singleton."""
    global _instance
    if _instance is None:
        _instance = BlanketEnforcementService(driver=driver)
    return _instance
