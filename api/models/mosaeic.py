"""
MOSAEIC Protocol Models
Feature: 024-mosaeic-protocol

Mental Observation of Senses, Actions, Emotions, Impulses, Cognitions.
"""

from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


class MOSAEICWindow(BaseModel):
    """A single window into the experience."""
    content: str = Field(..., description="The observed content of this window")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)


class MOSAEICCapture(BaseModel):
    """The complete five-window experiential capture."""
    senses: MOSAEICWindow = Field(..., description="External and internal physical sensations")
    actions: MOSAEICWindow = Field(..., description="Observable behaviors and motor outputs")
    emotions: MOSAEICWindow = Field(..., description="Feeling states and visceral affects")
    impulses: MOSAEICWindow = Field(..., description="Urges and pre-action tendencies")
    cognitions: MOSAEICWindow = Field(..., description="Thoughts, beliefs, and internal dialogue")
    
    summary: str = Field(..., description="Synthesized meaning of the experience")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_id: str = Field(default="user_narrative")


class TurningPoint(BaseModel):
    """A critical shift in the MOSAEIC state."""
    before: MOSAEICCapture
    after: MOSAEICCapture
    catalyst: str = Field(..., description="What triggered the shift")
    insight: str = Field(..., description="What was learned from the shift")
