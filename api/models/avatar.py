"""
Avatar Knowledge Graph Models

Pydantic models for structured avatar research data.
Feature: 019-avatar-knowledge-graph
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class InsightType(str, Enum):
    """Types of avatar insights that can be extracted."""
    PAIN_POINT = "pain_point"
    OBJECTION = "objection"
    DESIRE = "desire"
    BELIEF = "belief"
    BEHAVIOR = "behavior"
    VOICE_PATTERN = "voice_pattern"
    FAILED_SOLUTION = "failed_solution"
    DEMOGRAPHIC = "demographic"


class PainPoint(BaseModel):
    """A specific pain point experienced by the avatar."""
    description: str = Field(..., description="Description of the pain")
    category: str = Field(default="general", description="Category: identity, achievement, relationship, health")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="How intense is this pain (0-1)")
    frequency: str = Field(default="sometimes", description="How often: daily, weekly, sometimes, rarely")
    trigger: Optional[str] = Field(None, description="What triggers this pain")
    expressed_as: Optional[str] = Field(None, description="How the avatar actually describes this")
    source_quote: Optional[str] = Field(None, description="Direct quote if available")


class Objection(BaseModel):
    """An objection or resistance the avatar has."""
    text: str = Field(..., description="The objection statement")
    category: str = Field(default="general", description="Category: price, time, trust, prior_solution, skepticism")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="How strong is this objection (0-1)")
    counter_narrative: Optional[str] = Field(None, description="Effective counter to this objection")
    root_belief: Optional[str] = Field(None, description="Underlying belief driving this objection")
    source_quote: Optional[str] = Field(None, description="Direct quote if available")


class Desire(BaseModel):
    """A want or desire the avatar has."""
    description: str = Field(..., description="What they want")
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1-10")
    latent: bool = Field(default=False, description="Is this latent (unexpressed) or explicit?")
    expressed_as: Optional[str] = Field(None, description="How they actually express this desire")
    blocked_by: Optional[List[str]] = Field(default_factory=list, description="Beliefs blocking this desire")
    source_quote: Optional[str] = Field(None, description="Direct quote if available")


class Belief(BaseModel):
    """A belief held by the avatar."""
    content: str = Field(..., description="The belief statement")
    certainty: float = Field(default=0.7, ge=0.0, le=1.0, description="How certain are they (0-1)")
    origin: Optional[str] = Field(None, description="Where this belief likely came from")
    limiting: bool = Field(default=False, description="Is this a limiting belief?")
    blocks: Optional[List[str]] = Field(default_factory=list, description="Desires this belief blocks")


class Behavior(BaseModel):
    """A behavior pattern exhibited by the avatar."""
    pattern: str = Field(..., description="The behavior pattern")
    trigger: Optional[str] = Field(None, description="What triggers this behavior")
    context: Optional[str] = Field(None, description="Context where this occurs")
    frequency: str = Field(default="sometimes", description="How often: daily, weekly, sometimes, rarely")
    driven_by: Optional[str] = Field(None, description="Pain point or belief driving this")


class VoicePattern(BaseModel):
    """A linguistic pattern used by the avatar."""
    phrase: str = Field(..., description="The phrase or expression")
    emotional_tone: str = Field(default="neutral", description="Emotional tone: frustrated, hopeful, resigned, etc.")
    context: Optional[str] = Field(None, description="When they use this phrase")
    frequency: float = Field(default=0.5, ge=0.0, le=1.0, description="How common is this pattern (0-1)")


class FailedSolution(BaseModel):
    """A solution the avatar has tried that didn't work."""
    name: str = Field(..., description="Name of the solution")
    category: str = Field(default="other", description="Category: therapy, coaching, self-help, biohacking, etc.")
    why_failed: str = Field(..., description="Why it didn't work for them")
    residual_belief: Optional[str] = Field(None, description="Belief formed from this failure")
    time_invested: Optional[str] = Field(None, description="How long they tried it")


class AvatarInsight(BaseModel):
    """A single extracted insight about the avatar."""
    insight_type: InsightType = Field(..., description="Type of insight")
    data: Dict[str, Any] = Field(..., description="The insight data (varies by type)")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Extraction confidence")
    source: Optional[str] = Field(None, description="Source document/content")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class AvatarProfile(BaseModel):
    """Complete avatar profile synthesized from graph data."""
    name: str = Field(default="Analytical Empath", description="Avatar archetype name")
    demographics: Dict[str, Any] = Field(default_factory=dict)
    pain_points: List[PainPoint] = Field(default_factory=list)
    objections: List[Objection] = Field(default_factory=list)
    desires: List[Desire] = Field(default_factory=list)
    beliefs: List[Belief] = Field(default_factory=list)
    behaviors: List[Behavior] = Field(default_factory=list)
    voice_patterns: List[VoicePattern] = Field(default_factory=list)
    failed_solutions: List[FailedSolution] = Field(default_factory=list)

    # Synthesis metadata
    insight_count: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sources: List[str] = Field(default_factory=list)
