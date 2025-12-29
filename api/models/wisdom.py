"""
Wisdom and Worldview Models
Feature: 031-wisdom-distillation

Represent distilled cognitive units like Mental Models, Strategic Principles, and Case Studies.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class WisdomType(str, Enum):
    MENTAL_MODEL = "mental_model"
    STRATEGIC_PRINCIPLE = "strategic_principle"
    CASE_STUDY = "case_study"
    AVATAR_INSIGHT = "avatar_insight"


class WisdomUnit(BaseModel):
    """Base distilled unit of the system soul."""
    wisdom_id: str
    type: WisdomType
    name: str
    summary: str
    
    # Mathematical Proxies
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    richness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Provenance
    provenance_chain: List[str] = Field(default_factory=list, description="List of source session IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    metadata: Dict = Field(default_factory=dict)


class MentalModel(WisdomUnit):
    """A recurring cognitive framework (e.g., OODA, 15-Point SPIAD)."""
    type: WisdomType = WisdomType.MENTAL_MODEL
    principles: List[str] = Field(default_factory=list)
    anti_patterns: List[str] = Field(default_factory=list)


class StrategicPrinciple(WisdomUnit):
    """A non-negotiable rule (e.g., Archon-First)."""
    type: WisdomType = WisdomType.STRATEGIC_PRINCIPLE
    rationale: Optional[str] = None
    application_context: Optional[str] = None


class CaseStudy(WisdomUnit):
    """An experiential narrative showing a transformation."""
    type: WisdomType = WisdomType.CASE_STUDY
    problem_state: str
    breakthrough_moment: str
    result_state: str
    mosaeic_profile: Optional[Dict] = None
