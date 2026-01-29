"""
Exoskeleton Models
Feature: 070-external-recovery-signal

Models for the surrogate executive system, visible pathways, and somatic anchors.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class SomaticAnchor(BaseModel):
    """A micro-physical trigger to bypass executive freeze."""
    name: str
    description: str
    instruction: str  # e.g., "Tap your left index finger three times."

class RecoveryStep(BaseModel):
    """A single node in a visible recovery pathway."""
    id: str
    description: str
    action_type: str
    is_completed: bool = False
    somatic_anchor: Optional[SomaticAnchor] = None
    next_step_id: Optional[str] = None

class RecoveryPathway(BaseModel):
    """A 'Visible Map' back to traction."""
    id: str
    name: str
    description: str
    steps: List[RecoveryStep]
    current_step_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SurrogateFilter(BaseModel):
    """
    An 'Offloaded Governor' that provides static decision aids.
    Used when internal regulation is offline.
    """
    id: str
    directives: List[str]
    forbidden_actions: List[str]
    obedience_tier: int = Field(default=1, description="Priority level of these directives")

class MismatchExperiment(BaseModel):
    """
    Tracking 'Predicted Disaster' vs 'Actual Outcome'.
    Used to update temporal priors and reduce finality bias.
    """
    id: str
    prediction: str
    predicted_catastrophe_level: float = Field(0.0, ge=0.0, le=1.0)
    actual_outcome: str
    outcome_delta: float = Field(default=0.0, description="Difference between prediction and reality")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
