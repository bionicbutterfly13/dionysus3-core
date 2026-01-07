from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class SystemMoment(BaseModel):
    """
    A snapshot of the system's internal state at a specific point in time.
    Used for continuous self-monitoring.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Cognitive Metrics
    energy_level: float = 0.0
    active_basins_count: int = 0
    total_memories_count: int = 0
    
    # Performance Metrics
    avg_surprise_score: float = 0.0
    avg_confidence_score: float = 0.0
    
    # State
    current_focus: Optional[str] = None
    recent_errors: List[str] = Field(default_factory=list)

class EvolutionUpdate(BaseModel):
    """
    A proposed update to the system's internal strategy or structure.
    Generated during the evolution cycle.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Changes
    target_basin_id: Optional[str] = None
    new_strategy_description: str
    rationale: str
    
    # Meta
    affected_tool_sequences: List[str] = Field(default_factory=list)
    expected_improvement: float = 0.0
