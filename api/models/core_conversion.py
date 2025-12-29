"""
Core Conversion Content Models

Pydantic models for structured sales scripts, client stories, and belief shifts.
Based on BE MEMBERSHIP CORE CONVERSION CONTENT WORKBOOK framework.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class BeliefShiftType(str, Enum):
    """Types of belief shifts in the 6 Core Beliefs framework."""
    CORE = "core"           # Big Domino - fastest way to get goal
    REAL_PROBLEM = "real_problem"  # What the real problem is
    TIME = "time"           # Now is the right time
    MONEY = "money"         # Best use of money
    METHOD = "method"       # Best method to achieve goal
    HELP = "help"           # Why you vs others


class TransformationPhase(str, Enum):
    """IAS transformation phases."""
    REVELATION = "revelation"      # Phase 1: Hidden sabotage to clear map
    REPATTERNING = "repatterning"  # Phase 2: Internal conflict to recoded identity
    STABILIZATION = "stabilization"  # Phase 3: Fragile change to fortified growth


# ============== CLIENT STORY COMPONENTS ==============

class ExternalMarker(BaseModel):
    """External success marker visible to others."""
    category: str = Field(..., description="Category: career, financial, family, status, community")
    description: str = Field(..., description="The specific marker")
    significance: Optional[str] = Field(None, description="Why this matters to the story")


class InternalExperience(BaseModel):
    """Internal emotional/psychological experience."""
    feeling: str = Field(..., description="The feeling or experience")
    trigger: Optional[str] = Field(None, description="What triggers this")
    frequency: str = Field(default="often", description="How often: daily, often, sometimes")
    expressed_as: Optional[str] = Field(None, description="How they describe it")


class HiddenBelief(BaseModel):
    """The root belief driving the problem."""
    statement: str = Field(..., description="The belief in their words")
    origin: Optional[str] = Field(None, description="Where this belief came from")
    manifestations: List[str] = Field(default_factory=list, description="How this belief shows up")
    cost: Optional[str] = Field(None, description="What this belief costs them")


class TransformationMoment(BaseModel):
    """The specific moment of shift."""
    description: str = Field(..., description="What happened")
    setting: Optional[str] = Field(None, description="Where/when this occurred")
    realization: Optional[str] = Field(None, description="What they realized")
    action_taken: Optional[str] = Field(None, description="What they did differently")
    response_received: Optional[str] = Field(None, description="How others responded")


class ClientStory(BaseModel):
    """Complete client case study for Core Conversion Content."""
    # Identity
    id: str = Field(..., description="Unique identifier (e.g., dr-danielle)")
    name: str = Field(..., description="Display name (can be pseudonym)")
    avatar_type: str = Field(default="analytical_empath", description="Avatar archetype")

    # Demographics
    role: str = Field(..., description="Professional role")
    industry: Optional[str] = Field(None, description="Industry/field")
    location_type: Optional[str] = Field(None, description="Urban, suburban, rural")
    family_status: Optional[str] = Field(None, description="Family situation")
    status_markers: List[str] = Field(default_factory=list, description="Status indicators")

    # Before State
    external_success_markers: List[ExternalMarker] = Field(
        default_factory=list,
        description="External success visible to others"
    )
    internal_experiences: List[InternalExperience] = Field(
        default_factory=list,
        description="Internal emotional experiences"
    )
    core_pain_pattern: str = Field(..., description="The central pain pattern")
    surface_complaint: Optional[str] = Field(None, description="What they say the problem is")

    # Root Cause
    hidden_belief: HiddenBelief = Field(..., description="The belief driving everything")

    # Transformation
    method_used: str = Field(default="Hidden Block Decoder", description="Product/method name")
    key_intervention: str = Field(..., description="What specifically helped")
    transformation_moment: Optional[TransformationMoment] = Field(
        None,
        description="The specific moment of shift"
    )

    # After State
    internal_shifts: List[str] = Field(default_factory=list, description="Internal changes")
    external_changes: List[str] = Field(default_factory=list, description="Visible changes")
    specific_outcomes: List[str] = Field(default_factory=list, description="Concrete results")

    # Hell Island / Heaven Island
    hell_island: Optional[str] = Field(
        None,
        description="What would have happened if they continued (vivid)"
    )
    heaven_island: Optional[str] = Field(
        None,
        description="What life looks like now (vivid scene)"
    )

    # Framework Connections
    maps_to_lessons: List[str] = Field(default_factory=list, description="IAS lessons this maps to")
    maps_to_patterns: List[str] = Field(default_factory=list, description="Self-sabotage patterns")
    maps_to_desires: List[str] = Field(default_factory=list, description="Core desires addressed")

    # Metadata
    needs_filling: List[str] = Field(
        default_factory=list,
        description="Fields that need more information"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============== BELIEF SHIFT COMPONENTS ==============

class BeliefShift(BaseModel):
    """A single belief shift for the 6 Beliefs framework."""
    shift_type: BeliefShiftType
    old_belief: str = Field(..., description="What they currently believe")
    new_belief: str = Field(..., description="What they need to believe")
    problems_old_causes: List[str] = Field(default_factory=list, description="Problems from old belief")
    cost_of_keeping: Optional[str] = Field(None, description="Hell Island for this belief")
    life_with_new: Optional[str] = Field(None, description="Heaven Island with new belief")
    authority_quote: Optional[str] = Field(None, description="Expert backing this up")
    universal_analogy: Optional[str] = Field(None, description="Story/parable reinforcing it")
    personal_story: Optional[str] = Field(None, description="Your hell to heaven journey")
    client_proof: Optional[str] = Field(None, description="Client who made this shift")


# ============== PHASE COMPONENTS ==============

class ContentPhase(BaseModel):
    """A phase in the 3-phase solution delivery."""
    phase_number: int = Field(..., ge=1, le=3)
    phase_type: TransformationPhase
    name: str = Field(..., description="Phase name (e.g., Revelation)")
    big_idea: str = Field(..., description="The core concept")
    what_it_is: str = Field(..., description="What they get/learn")
    how_avoids_old_complaints: str = Field(..., description="Why this is different")
    tangible_result: str = Field(..., description="What they walk away with")
    why_necessary: str = Field(..., description="Why this is required for the goal")
    lessons_included: List[str] = Field(default_factory=list, description="Lessons in this phase")


# ============== MAIN STRUCTURE ==============

class HookSection(BaseModel):
    """Section 1: Hook."""
    product_name: str = Field(..., description="Hidden Block Decoder, etc.")
    number_helped_technique: str = Field(..., description="How many the technique has helped")
    number_helped_personal: str = Field(..., description="How many you've personally helped")
    ideal_audience: str = Field(..., description="Who this is for")
    big_goal: str = Field(..., description="What they achieve")
    time_period: str = Field(..., description="How long it takes")
    old_methods_failed: List[str] = Field(default_factory=list, description="What didn't work")
    opening_statement: Optional[str] = Field(None, description="The actual hook copy")


class OverviewSection(BaseModel):
    """Section 3: Overview - Three things they'll learn."""
    learning_1: str
    learning_2: str
    learning_3: str


class BackstorySection(BaseModel):
    """Section 4: Your story."""
    problems_you_had: List[str] = Field(default_factory=list)
    complaints_you_made: List[str] = Field(default_factory=list)
    unwanted_feelings: List[str] = Field(default_factory=list)
    old_methods_tried: List[str] = Field(default_factory=list)
    discovery_moment: str = Field(..., description="The turning point")
    transformation: str = Field(..., description="What changed")
    results_proof: str = Field(..., description="Evidence it worked")


class IdentitySection(BaseModel):
    """Section 5: Old vs Aspiring Identity."""
    old_identity_name: str
    old_identity_results: str
    old_identity_complaints: str
    old_identity_methods: str
    old_identity_feelings: str
    old_identity_attributes: str
    old_identity_beliefs: str

    aspiring_identity_name: str
    aspiring_identity_results: str
    aspiring_identity_reality: str
    aspiring_identity_methods: str
    aspiring_identity_feelings: str
    aspiring_identity_attributes: str
    aspiring_identity_beliefs: str

    # For analytical empaths specifically
    shell_public_avatar: Optional[str] = Field(None, description="The public persona")
    core_private_self: Optional[str] = Field(None, description="The private self")


class CloseSection(BaseModel):
    """Section 12: Close."""
    diy_path: str = Field(..., description="What happens if they do it alone")
    guided_path: str = Field(..., description="What your offer provides")
    dream_paint: str = Field(..., description="Emotional vision of success")
    scarcity_urgency: Optional[str] = Field(None, description="Why now")
    accolades: List[str] = Field(default_factory=list)
    mission: str = Field(...)
    reason_why: str = Field(..., description="Why you do this")


class CoreConversionContent(BaseModel):
    """
    Complete Core Conversion Content structure.

    This is the master container for all sales script content,
    with client stories as an array that can grow over time.
    """
    id: str = Field(default="ias-core-conversion-v1")
    name: str = Field(default="IAS Hidden Block Decoder")
    version: str = Field(default="1.0")

    # Section 1: Hook
    hook: HookSection

    # Section 2: Social Proof - Array of client stories
    client_stories: List[ClientStory] = Field(default_factory=list)

    # Section 3: Overview
    overview: Optional[OverviewSection] = None

    # Section 4: Backstory
    backstory: Optional[BackstorySection] = None

    # Section 5: Identity
    identity: Optional[IdentitySection] = None

    # Section 6: Core Belief (Big Domino)
    core_belief: Optional[BeliefShift] = None

    # Section 7: Real Problem Belief
    real_problem_belief: Optional[BeliefShift] = None

    # Sections 8-10: Phases
    phases: List[ContentPhase] = Field(default_factory=list)

    # Section 11: Recap (derived from overview)

    # Section 12: Close
    close: Optional[CloseSection] = None

    # Metadata
    avatar_id: str = Field(default="analytical-empath")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Gaps tracking
    needs_filling: List[str] = Field(
        default_factory=list,
        description="Sections/fields that need more information"
    )
