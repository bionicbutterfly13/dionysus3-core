from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ActiveInferenceScore(BaseModel):
    """
    Represents the 'Active Inference Currency' used to value a reasoning step.
    Balancing Exploration (reducing uncertainty) vs Exploitation (goal achievement).
    """
    expected_free_energy: float = Field(..., description="EFE: The primary value function.")
    surprise: float = Field(..., description="Entropy/Novelty: Unexpectedness of the thought.")
    prediction_error: float = Field(..., description="Deviation from internal world model.")
    precision: float = Field(default=1.0, description="Confidence/Reliability of the signal.")

class ThoughtNode(BaseModel):
    """
    A single node in the Tree of Thought (Meta-ToT).
    Represents a discrete cognitive state or reasoning step.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    content: str = Field(..., description="The textual content of the thought.")
    
    # The 'Physics' of the thought
    score: Optional[ActiveInferenceScore] = None
    
    # Graphiti Integration
    basin_id: Optional[str] = Field(None, description="ID of the Attractor Basin this thought deepens.")
    
    depth: int = 0
    children_ids: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReasoningBranch(BaseModel):
    """
    A unified sequence of thoughts representing a potential future or solution path.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_ids: List[str]
    total_efe: float = 0.0
    is_pruned: bool = False
    
    def length(self) -> int:
        return len(self.node_ids)
