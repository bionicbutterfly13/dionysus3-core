"""
Agentic Knowledge Graph Models
Feature: 022-agentic-kg-learning
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RelationshipProposal(BaseModel):
    source: str
    target: str
    relation_type: str = Field(..., alias="type")
    confidence: float = 0.0
    evidence: str = ""
    reasoning: Optional[str] = None


class ExtractionResult(BaseModel):
    entities: List[str] = Field(default_factory=list)
    relationships: List[RelationshipProposal] = Field(default_factory=list)
    provenance: Dict = Field(default_factory=dict)


class AttractorBasin(BaseModel):
    name: str
    strength: float = 1.0
    concepts: List[str] = Field(default_factory=list)
    last_strengthened: datetime = Field(default_factory=datetime.utcnow)


class CognitionStrategy(BaseModel):
    category: str  # e.g., 'relationship_types'
    name: str      # e.g., 'THEORETICALLY_EXTENDS'
    priority_boost: float = 0.0
    success_count: int = 0
    last_used: datetime = Field(default_factory=datetime.utcnow)
