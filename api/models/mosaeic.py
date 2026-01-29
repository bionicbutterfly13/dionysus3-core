"""
MOSAEIC Protocol Models
Feature: 024-mosaeic-protocol

Mental Observation of Senses, Actions, Emotions, Impulses, Cognitions.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MOSAEICWindow(BaseModel):
    """A single window into the experience."""
    content: str = Field(..., description="The observed content of this window")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    precision: float = Field(default=1.0, description="Bayesian precision (inverse variance) of this observation")
    surprisal: float = Field(default=0.0, description="Magnitude of prediction error (surprisal) for this window")
    narrative_theme: Optional[str] = Field(None, description="The overarching theme or narrative identified in this window")
    tags: List[str] = Field(default_factory=list)


class MOSAEICCapture(BaseModel):
    """The complete five-window experiential capture."""
    senses: MOSAEICWindow = Field(..., description="External and internal physical sensations")
    actions: MOSAEICWindow = Field(..., description="Observable behaviors and motor outputs")
    emotions: MOSAEICWindow = Field(..., description="Feeling states and visceral affects")
    impulses: MOSAEICWindow = Field(..., description="Urges and pre-action tendencies")
    cognitions: MOSAEICWindow = Field(..., description="Thoughts, beliefs, and internal dialogue")
    
    summary: str = Field(..., description="Synthesized meaning of the experience")
    coherence: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall narrative/probabilistic coherence")
    identity_congruence: float = Field(default=1.0, ge=0.0, le=1.0, description="Alignment with self-concept (0-1)")
    self_betrayal_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Cost of disregarding somatic markers (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_id: str = Field(default="user_narrative")


class TurningPoint(BaseModel):
    """A critical shift in the MOSAEIC state."""
    before: MOSAEICCapture
    after: MOSAEICCapture
    catalyst: str = Field(..., description="What triggered the shift")
    insight: str = Field(..., description="What was learned from the shift")
