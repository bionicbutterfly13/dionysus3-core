"""
Identity Utilities (Cognee Port)
Feature: 069-hexis-subconscious-integration

Extracted from `cognee.modules.engine.utils.generate_node_id`.
Provides deterministic UUID generation for content-addressable memory.
This solves the "Amnesia" problem by ensuring repeated concepts resolve to the same ID.
"""

from uuid import NAMESPACE_OID, uuid5
from typing import Any

def generate_deterministic_id(content: str) -> str:
    """
    Generates a deterministic UUID based on content string.
    Matches Cognee's normalization logic.
    """
    if not content:
        raise ValueError("Content cannot be empty for deterministic ID generation")
        
    normalized = content.lower().strip().replace(" ", "_").replace("'", "")
    return str(uuid5(NAMESPACE_OID, normalized))

def generate_edge_id(source_id: str, target_id: str, relationship_type: str) -> str:
    """
    Generates a deterministic ID for an edge.
    Matches Cognee's edge logic.
    """
    # Create a composite key
    composite = f"{source_id}_{relationship_type}_{target_id}"
    return generate_deterministic_id(composite)
