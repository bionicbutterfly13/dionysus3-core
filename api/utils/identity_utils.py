"""
Identity Utilities (Cognee Port)
Feature: 069-hexis-subconscious-integration

Extracted from `cognee.modules.engine.utils.generate_node_id`.
Provides deterministic UUID generation for content-addressable memory.
This solves the "Amnesia" problem by ensuring repeated concepts resolve to the same ID.
"""

from uuid import NAMESPACE_OID, uuid5
from typing import Any, Optional, List, Dict

def generate_deterministic_id(content: str, prefix: Optional[str] = None) -> str:
    """
    Generates a deterministic UUID based on content string.
    Matches Cognee's normalization logic with additional robustness.
    
    Args:
        content: The string to hash.
        prefix: Optional namespace prefix (e.g., 'goal:', 'task:').
    """
    if not content:
        raise ValueError("Content cannot be empty for deterministic ID generation")
        
    # Robust normalization: lower, strip, internal whitespace to underscore, strip special chars
    import re
    # Remove all non-alphanumeric except spaces/underscores/hyphens
    clean = re.sub(r'[^a-zA-Z0-9\s_\-]', '', content.lower())
    # Collapse multiple spaces/underscores into one underscore
    normalized = re.sub(r'[\s_\-]+', '_', clean).strip('_')
    
    if prefix:
        normalized = f"{prefix.lower().strip(':')}:{normalized}"
        
    return str(uuid5(NAMESPACE_OID, normalized))

def generate_edge_id(source_id: str, target_id: str, relationship_type: str) -> str:
    """
    Generates a deterministic ID for an edge.
    Matches Cognee's edge logic.
    """
    # Create a composite key
    composite = f"{source_id}_{relationship_type}_{target_id}"
    return generate_deterministic_id(composite)
