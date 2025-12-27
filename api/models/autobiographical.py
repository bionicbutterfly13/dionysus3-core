"""
Autobiographical Memory Models
Feature: 028-autobiographical-memory
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DevelopmentEventType(str, Enum):
    SPEC_CREATION = "spec_creation"
    ARCHITECTURAL_DECISION = "architectural_decision"
    SYSTEM_REFLECTION = "system_reflection"
    MODEL_PIVOT = "model_pivot"
    GENESIS = "genesis"


class DevelopmentEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: DevelopmentEventType
    
    summary: str = Field(..., description="What changed or was decided")
    rationale: str = Field(..., description="The 'why' behind the change")
    impact: str = Field(..., description="Expected impact on the system")
    lessons_learned: List[str] = Field(default_factory=list)
    
    metadata: Dict = Field(default_factory=dict)
