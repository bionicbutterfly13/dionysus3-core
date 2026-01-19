"""
Agentic Knowledge Graph Models
Feature: 022-agentic-kg-learning
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RelationshipProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str
    target: str
    relation_type: str = Field(..., alias="type")
    confidence: float = 0.0
    evidence: str = ""
    reasoning: Optional[str] = None
    
    # Provenance (FR-004)
    run_id: Optional[str] = None
    model_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Review Status
    status: str = Field(default="pending", description="pending, approved, rejected, reviewed")


class ExtractionResult(BaseModel):
    entities: List[str] = Field(default_factory=list)
    relationships: List[RelationshipProposal] = Field(default_factory=list)
    provenance: Dict = Field(default_factory=dict)
    
    # Aggregate stats
    run_id: str = Field(default_factory=lambda: "run-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None


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


class RetrievalStrategy(BaseModel):
    """
    Defines the parameters for active inquiry (retrieval) in the memory system.
    Matches the 'RetrievalStrategy' Node in Graphiti.
    """
    strategy_name: str = Field(..., description="Unique name of the strategy (e.g., 'DeepResearch')")
    top_k: int = Field(default=10, description="Baseline number of results to fetch")
    alpha: float = Field(default=0.7, description="Balance between vector similarity (1.0) and graph traversal (0.0)")
    expansion_depth: int = Field(default=1, description="How many hops to traverse from focal points")
    focal_points: List[str] = Field(default_factory=list, description="Key concepts to boost ranking")
    
    # Active Inference Parameters
    min_confidence: float = Field(default=0.5, description="Minimum confidence for expanded terms")
    created_at: datetime = Field(default_factory=datetime.utcnow)
