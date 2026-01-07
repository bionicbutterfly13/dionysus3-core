from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class CognitiveEpisode(BaseModel):
    """
    Represents a single 'episode' of reasoning, capturing the task, the strategy used,
    and the outcome. Used for Episodic Meta-Learning.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Context
    task_query: str = Field(..., description="The original task or question.")
    task_context: Dict[str, Any] = Field(default_factory=dict, description="Key context variables.")
    
    # Strategy
    tools_used: List[str] = Field(default_factory=list, description="Names of tools called.")
    reasoning_trace: str = Field(default="", description="Summary of the reasoning path taken.")
    
    # Outcome
    success: bool = Field(False, description="Whether the task was deemed successful.")
    outcome_summary: str = Field(default="", description="The final result or answer.")
    surprise_score: float = Field(0.0, description="Metric of prediction error (0.0=Expected, 1.0=Total Surprise).")
    
    # Meta-Learning
    lessons_learned: str = Field(default="", description="Extracted insight for future reference.")
    
    def to_text_representation(self) -> str:
        """Convert to text for embedding."""
        return f"Task: {self.task_query}\nOutcome: {self.outcome_summary}\nLessons: {self.lessons_learned}"