"""
Marketing & Funnel Architecture Models

Pydantic models for structured funnel strategies, PDP sections, and copywriting elements.
Inspired by RMBC2 (Stefan Georgi) and IAS frameworks.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from datetime import datetime
from uuid import uuid4

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


# --- PRODUCT & OFFER MODELS ---

class KeyPhrase(BaseModel):
    """Specific language patterns used by/for the avatar."""
    phrase: str
    category: Literal["pain", "desire", "objection", "identity"]
    resonance_score: float = Field(0.0, description="0.0 to 1.0 score of how hard this hits")

class Avatar(BaseModel):
    """The target audience profile."""
    name: str = Field(..., description="e.g. 'The Analytical Empath'")
    pain_points: List[str]
    desires: List[str]
    obstacles: List[str]
    old_way: str = Field(..., description="The status quo mechanism (e.g. Willpower)")
    new_way: str = Field(..., description="The new mechanism (e.g. Identity Architecture)")
    
    # Specific Messaging / Language
    core_identity_statement: Optional[str] = None # "I am the adult in the room..."
    key_phrases: List[KeyPhrase] = Field(default_factory=list)

class Solution(BaseModel):
    """The fix for a specific obstacle."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., description="The exact solution/script")
    mechanism: Optional[str] = None

class Obstacle(BaseModel):
    """A potential friction point in a step."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    solution: Solution

class Step(BaseModel):
    """A concrete action within a lesson."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    order: int
    name: str
    instruction: str
    obstacles: List[Obstacle] = Field(default_factory=list, description="The 3 potential obstacles")

class Lesson(BaseModel):
    """A single unit of curriculum (1 of 3 in a Phase)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    promise: Optional[str] = None
    key_concept: str
    action_step: str
    mechanism: Optional[str] = None
    transformation: str = Field(..., description="The specific shift this lesson provides")
    steps: List[Step] = Field(default_factory=list, description="The 3 steps to execute this lesson")

class Module(BaseModel):
    """A collection of lessons (e.g., a Phase)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    promise: Optional[str] = None
    lessons: List[Lesson] = Field(default_factory=list)

class Bonus(BaseModel):
    """A value-add item included in an offer."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Name of the bonus")
    description: str = Field(..., description="What it solves")
    value: float = Field(..., description="Perceived value (e.g. $500)")
    price: float = Field(0.0, description="Actual price (usually 0 if included)")
    delivery_format: str = Field("digital", description="PDF, Video, Notion, etc.")

class Product(BaseModel):
    """The core IP / Curriculum (e.g., Inner Architect System)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    avatar: Avatar
    promise: str
    mechanism: str
    modules: List[Module]
    bonuses: List[Bonus] = Field(default_factory=list)

class Offer(BaseModel):
    """A structured sales proposition wrapping a Product."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str # e.g. "The 48-Hour Loop Breaker"
    product_ref_id: str = Field(..., description="ID of the underlying Product")
    included_modules_ids: List[str] = Field(..., description="Which modules are included?")
    included_bonuses: List[Bonus] = Field(default_factory=list, description="Specific bonuses for this offer")
    price: float
    guarantee: str
    scarcity: Optional[str] = None
    
    def get_total_value(self) -> float:
        return self.price + sum(b.value for b in self.included_bonuses)

