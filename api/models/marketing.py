"""
Marketing & Funnel Architecture Models

Pydantic models for structured funnel strategies, PDP sections, and copywriting elements.
Inspired by RMBC2 (Stefan Georgi) and IAS frameworks.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class FunnelStepType(str, Enum):
    """Types of steps in a marketing funnel."""
    AD = "ad"
    ADVERTORIAL = "advertorial"
    OPT_IN = "opt_in"
    VSL = "vsl"
    TSL = "tsl"
    PDP = "pdp"
    ORDER_FORM = "order_form"
    UPSELL = "upsell"
    DOWNSELL = "downsell"
    THANK_YOU = "thank_you"
    EMAIL = "email"


class EmotionalTriggerType(str, Enum):
    """Panksepp's 7 Emotional Systems + Marketing triggers."""
    SEEKING = "seeking"
    RAGE = "rage"
    FEAR = "fear"
    LUST = "lust"
    CARE = "care"
    PANIC_GRIEF = "panic_grief"
    PLAY = "play"
    URGENCY = "urgency"
    SCARCITY = "scarcity"
    SOCIAL_PROOF = "social_proof"


class FunnelElement(BaseModel):
    """A specific component within a funnel step."""
    name: str = Field(..., description="Element name (e.g., Headline, Hook, CTA)")
    content_draft: str = Field(..., description="The actual copy or content")
    trigger: Optional[EmotionalTriggerType] = Field(None, description="Primary emotional trigger")
    purpose: str = Field(..., description="What this element is meant to achieve (e.g., 'Stop the scroll', 'Agitate pain')")
    tease_framework: Optional[str] = Field(None, description="IAS framework being teased (if any)")


class FunnelStep(BaseModel):
    """A discrete stage in the funnel."""
    step_type: FunnelStepType
    name: str = Field(..., description="Internal name for this step")
    elements: List[FunnelElement] = Field(default_factory=list)
    order: int = Field(..., description="Position in the funnel sequence")
    target_kpi: str = Field(default="CTR", description="Primary metric: CTR, CVR, Opt-in Rate")


class FunnelStrategy(BaseModel):
    """High-level strategy for an entire funnel."""
    name: str
    project_id: str
    avatar_name: str = Field(default="Analytical Empath")
    unique_mechanism_problem: str = Field(..., description="The UMP (e.g., Split Self Architecture)")
    unique_mechanism_solution: str = Field(..., description="The UMS (e.g., Predictive Identity Recalibration)")
    steps: List[FunnelStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PDPSectionType(str, Enum):
    """Standard sections for a Product Detail Page / Sales Letter."""
    HERO = "hero"
    LEAD = "lead"
    UMP_REVEAL = "ump_reveal"
    UMS_REVEAL = "ums_reveal"
    PRODUCT_TOUR = "product_tour"
    BONUS = "bonus"
    GUARANTEE = "guarantee"
    FAQ = "faq"
    PRICE_STACK = "price_stack"
    QUALIFICATION = "qualification"
    TESTIMONIALS = "testimonials"


class PDPArchitecture(BaseModel):
    """The structural blueprint for a PDP."""
    title: str
    sections: List[Dict[str, Any]] = Field(
        ..., 
        description="List of sections following the 15-point SPIAD or RMBC2 lead structure"
    )
    voice_rules: List[str] = Field(
        default_factory=lambda: ["5th grade reading level", "Zero em dashes", "Sentence case subject lines"]
    )
    copy_brief_ref: Optional[str] = Field(None, description="Reference to the full copy brief")
