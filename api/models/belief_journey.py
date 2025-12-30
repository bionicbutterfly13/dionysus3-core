"""
Belief Journey Tracking Models

Pydantic models for tracking belief transformation through the IAS journey.
Integrates with Graphiti for Neo4j persistence.

Feature: IAS Belief Tracking
Based on Inner Architect System curriculum analysis.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4


# =============================================================================
# Enums
# =============================================================================


class BeliefStatus(str, Enum):
    """Lifecycle status for limiting beliefs."""
    IDENTIFIED = "identified"     # First recognized in Lesson 1
    MAPPED = "mapped"             # Connected to behaviors/self-talk
    TESTED = "tested"             # Experiment run in Lesson 4
    DISSOLVING = "dissolving"     # Evidence weakening
    DISSOLVED = "dissolved"       # No longer active


class EmpoweringBeliefStatus(str, Enum):
    """Lifecycle status for empowering beliefs."""
    PROPOSED = "proposed"         # Bridge belief created
    TESTING = "testing"           # Being tested via experiments
    STRENGTHENING = "strengthening"  # Building evidence
    EMBODIED = "embodied"         # Integrated into identity


class ExperimentOutcome(str, Enum):
    """Outcome of a belief experiment."""
    CONFIRMING = "confirming"     # Old belief confirmed (rare but possible)
    DISCONFIRMING = "disconfirming"  # Old belief challenged
    MIXED = "mixed"               # Partial evidence both ways
    INCONCLUSIVE = "inconclusive"  # Need more data


class ReplayLoopStatus(str, Enum):
    """Status of a replay loop pattern."""
    ACTIVE = "active"             # Currently recurring
    INTERRUPTED = "interrupted"    # Process applied, loop broken
    RESOLVED = "resolved"         # Pattern no longer triggers
    DORMANT = "dormant"           # May resurface under stress


class IASPhase(str, Enum):
    """IAS transformation phases."""
    REVELATION = "revelation"
    REPATTERNING = "repatterning"
    STABILIZATION = "stabilization"


class IASLesson(str, Enum):
    """IAS lessons for tracking progress."""
    BREAKTHROUGH_MAPPING = "lesson_1_breakthrough_mapping"
    MOSAEIC_METHOD = "lesson_2_mosaeic_method"
    REPLAY_LOOP_BREAKER = "lesson_3_replay_loop_breaker"
    CONVICTION_GAUNTLET = "lesson_4_conviction_gauntlet"
    PERSPECTIVE_MATRIX = "lesson_5_perspective_matrix"
    VISION_ACCELERATOR = "lesson_6_vision_accelerator"
    HABIT_HARMONIZER = "lesson_7_habit_harmonizer"
    EXECUTION_ENGINE = "lesson_8_execution_engine"
    GROWTH_ANCHOR = "lesson_9_growth_anchor"


# =============================================================================
# Core Belief Models
# =============================================================================


class LimitingBelief(BaseModel):
    """
    A limiting belief identified through IAS journey.
    
    Tracks full lifecycle from identification through dissolution.
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # Content
    content: str = Field(..., description="The belief statement verbatim")
    pattern_name: Optional[str] = Field(None, description="Named pattern (e.g., 'armor_exhaustion')")
    
    # Origin tracking
    origin_memory: Optional[str] = Field(None, description="Where this belief likely came from")
    origin_lesson: Optional[IASLesson] = Field(None, description="When first identified")
    
    # Evidence structure
    evidence_for: List[str] = Field(default_factory=list, description="Evidence supporting belief")
    evidence_against: List[str] = Field(default_factory=list, description="Evidence challenging belief")
    
    # Behavioral mapping (from Lesson 1)
    self_talk: List[str] = Field(default_factory=list, description="Internal dialogue this produces")
    mental_blocks: List[str] = Field(default_factory=list, description="Blocks this creates")
    self_sabotage_behaviors: List[str] = Field(default_factory=list, description="Behaviors this drives")
    protects_from: Optional[str] = Field(None, description="What this belief protects emotionally")
    
    # Strength tracking
    strength: float = Field(default=0.8, ge=0.0, le=1.0, description="Current belief strength (0=dissolved, 1=absolute)")
    certainty_at_identification: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Status
    status: BeliefStatus = Field(default=BeliefStatus.IDENTIFIED)
    
    # Relationships
    blocks_desires: List[str] = Field(default_factory=list, description="Desires this belief blocks")
    triggers_replay_loops: List[UUID] = Field(default_factory=list, description="Replay loops this feeds")
    replaced_by: Optional[UUID] = Field(None, description="Empowering belief that replaced this")
    
    # Timestamps
    identified_at: datetime = Field(default_factory=datetime.utcnow)
    last_tested_at: Optional[datetime] = None
    dissolved_at: Optional[datetime] = None
    
    # Graphiti metadata
    graphiti_node_uuid: Optional[str] = Field(None, description="UUID in Neo4j via Graphiti")


class EmpoweringBelief(BaseModel):
    """
    An empowering belief being built through IAS journey.
    
    Starts as bridge belief, strengthens through evidence, becomes embodied.
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # Content
    content: str = Field(..., description="The new belief statement")
    bridge_version: Optional[str] = Field(None, description="Initial softer version for testing")
    
    # Replaces
    replaces_belief_id: Optional[UUID] = Field(None, description="Limiting belief this replaces")
    
    # Evidence building
    experiments_run: List[UUID] = Field(default_factory=list, description="Experiments testing this")
    evidence_collected: List[str] = Field(default_factory=list, description="Real-world evidence")
    
    # Embodiment tracking
    embodiment_level: float = Field(default=0.1, ge=0.0, le=1.0, description="How embodied (0=intellectual, 1=automatic)")
    
    # Status
    status: EmpoweringBeliefStatus = Field(default=EmpoweringBeliefStatus.PROPOSED)
    
    # Anchoring (from Lesson 7)
    habit_stack: Optional[str] = Field(None, description="Daily habit this is stacked with")
    daily_checklist_items: List[str] = Field(default_factory=list, description="Behaviors reflecting this belief")
    
    # Timestamps
    proposed_at: datetime = Field(default_factory=datetime.utcnow)
    first_tested_at: Optional[datetime] = None
    embodied_at: Optional[datetime] = None
    
    # Graphiti metadata
    graphiti_node_uuid: Optional[str] = Field(None, description="UUID in Neo4j via Graphiti")


# =============================================================================
# Experiment & Testing Models
# =============================================================================


class BeliefExperiment(BaseModel):
    """
    A real-world experiment testing a belief (Lesson 4 Conviction Gauntlet).
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # What's being tested
    limiting_belief_id: Optional[UUID] = Field(None, description="Limiting belief being tested")
    empowering_belief_id: Optional[UUID] = Field(None, description="Empowering belief being tested")
    
    # Experiment design
    hypothesis: str = Field(..., description="What we expect to find")
    action_taken: str = Field(..., description="The specific action/behavior tried")
    context: str = Field(..., description="Situation/stakes level (low/mid/high)")
    
    # Results
    outcome: Optional[ExperimentOutcome] = None
    actual_result: Optional[str] = Field(None, description="What actually happened")
    emotional_response: Optional[str] = Field(None, description="How it felt")
    belief_shift_observed: Optional[str] = Field(None, description="Any shift in belief strength")
    
    # Impact
    limiting_belief_strength_before: Optional[float] = Field(None, ge=0.0, le=1.0)
    limiting_belief_strength_after: Optional[float] = Field(None, ge=0.0, le=1.0)
    empowering_belief_strength_before: Optional[float] = Field(None, ge=0.0, le=1.0)
    empowering_belief_strength_after: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Timestamps
    designed_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    
    # Graphiti metadata
    graphiti_edge_uuid: Optional[str] = Field(None, description="Relationship UUID in Neo4j")


# =============================================================================
# Replay Loop Models
# =============================================================================


class ReplayLoop(BaseModel):
    """
    A mental replay loop pattern (Lesson 3 Replay Loop Breaker).
    
    Tracks the story, emotion, and resolution of rumination patterns.
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # Trigger
    trigger_situation: str = Field(..., description="What triggers this replay")
    pattern_name: Optional[str] = Field(None, description="Named pattern (e.g., 'I said too much')")
    
    # The story (Step 1)
    story_text: str = Field(..., description="The story behind the replay")
    story_snapshot: Optional[str] = Field(None, description="One-sentence version")
    
    # The emotion (Step 2)
    emotion: str = Field(..., description="Primary emotion (shame, fear, etc.)")
    fear_underneath: str = Field(..., description="The fear driving the emotion")
    compassionate_reflection: Optional[str] = Field(None, description="Self-compassion statement")
    
    # Resolution (Step 3)
    lesson_found: Optional[str] = Field(None, description="Genuine lesson extracted")
    comfort_offered: Optional[str] = Field(None, description="Self-comfort statement")
    next_step_taken: Optional[str] = Field(None, description="Action taken to close loop")
    
    # Tracking
    status: ReplayLoopStatus = Field(default=ReplayLoopStatus.ACTIVE)
    occurrence_count: int = Field(default=1, ge=1, description="How many times this has occurred")
    avg_duration_minutes: Optional[float] = Field(None, description="How long replays typically last")
    time_to_resolution_minutes: Optional[float] = Field(None, description="How long to break the loop")
    
    # Connections
    fed_by_belief_id: Optional[UUID] = Field(None, description="Limiting belief feeding this loop")
    
    # Timestamps
    first_identified_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Graphiti metadata
    graphiti_node_uuid: Optional[str] = Field(None, description="UUID in Neo4j via Graphiti")


# =============================================================================
# Vision & Future Models
# =============================================================================


class VisionElement(BaseModel):
    """
    A vision element from Lesson 6 Vision Accelerator.
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # Content
    description: str = Field(..., description="The vision described")
    category: str = Field(default="general", description="career, creative, relationship, lifestyle, contribution")
    
    # Values alignment
    values_aligned: List[str] = Field(default_factory=list, description="Values this fulfills")
    
    # Progression
    status: str = Field(default="dream", description="dream, pilot, active, achieved")
    first_step: Optional[str] = Field(None, description="Immediate next action")
    
    # Blocks
    requires_dissolution_of: List[UUID] = Field(default_factory=list, description="Limiting beliefs blocking this")
    
    # Timestamps
    envisioned_at: datetime = Field(default_factory=datetime.utcnow)
    pilot_started_at: Optional[datetime] = None
    achieved_at: Optional[datetime] = None
    
    # Graphiti metadata
    graphiti_node_uuid: Optional[str] = Field(None, description="UUID in Neo4j via Graphiti")


# =============================================================================
# Support & Sustainability Models
# =============================================================================


class SupportCircleMember(BaseModel):
    """A member of the support circle (Lesson 9)."""
    role: str = Field(..., description="mentor, peer, mentee")
    name: Optional[str] = Field(None, description="Name or identifier")
    relationship_quality: float = Field(default=0.5, ge=0.0, le=1.0)
    check_in_frequency: str = Field(default="monthly", description="weekly, biweekly, monthly, quarterly")
    last_contact: Optional[datetime] = None
    value_provided: Optional[str] = Field(None, description="What this relationship provides")


class SupportCircle(BaseModel):
    """
    The support circle from Lesson 9 Growth Anchor.
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # Members
    members: List[SupportCircleMember] = Field(default_factory=list)
    
    # Health metrics
    total_members: int = Field(default=0)
    active_members: int = Field(default=0)
    avg_contact_frequency_days: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# MOSAEIC Enhancement
# =============================================================================


class MOSAEICCapture(BaseModel):
    """
    Enhanced MOSAEIC capture with belief tracking (Lesson 2).
    
    Extends the base MOSAEIC model with IAS-specific connections.
    """
    id: UUID = Field(default_factory=uuid4)
    journey_id: UUID = Field(..., description="Parent journey/session ID")
    
    # Context
    high_pressure_context: str = Field(..., description="The situation being observed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # MOSAEIC domains
    mindful_observation: Optional[str] = Field(None, description="General awareness notes")
    sensations: List[str] = Field(default_factory=list, description="Physical sensations")
    actions: List[str] = Field(default_factory=list, description="Observable behaviors")
    emotions: List[str] = Field(default_factory=list, description="Feeling states")
    impulses: List[str] = Field(default_factory=list, description="Urges/pre-action tendencies")
    cognitions: List[str] = Field(default_factory=list, description="Thoughts, beliefs, dialogue")
    
    # Narrative extraction
    narrative_identified: Optional[str] = Field(None, description="Self-sabotaging narrative spotted")
    connects_to_belief_id: Optional[UUID] = Field(None, description="Limiting belief this reveals")
    
    # Graphiti metadata
    graphiti_node_uuid: Optional[str] = Field(None, description="UUID in Neo4j via Graphiti")


# =============================================================================
# Journey Aggregate
# =============================================================================


class BeliefJourney(BaseModel):
    """
    Aggregate root for an IAS belief transformation journey.
    
    Contains all beliefs, experiments, loops, and progress for one participant.
    """
    id: UUID = Field(default_factory=uuid4)
    participant_id: Optional[str] = Field(None, description="External participant identifier")
    
    # Current phase
    current_phase: IASPhase = Field(default=IASPhase.REVELATION)
    current_lesson: IASLesson = Field(default=IASLesson.BREAKTHROUGH_MAPPING)
    
    # Collections
    limiting_beliefs: List[LimitingBelief] = Field(default_factory=list)
    empowering_beliefs: List[EmpoweringBelief] = Field(default_factory=list)
    experiments: List[BeliefExperiment] = Field(default_factory=list)
    replay_loops: List[ReplayLoop] = Field(default_factory=list)
    mosaeic_captures: List[MOSAEICCapture] = Field(default_factory=list)
    vision_elements: List[VisionElement] = Field(default_factory=list)
    support_circle: Optional[SupportCircle] = None
    
    # Progress metrics
    lessons_completed: List[IASLesson] = Field(default_factory=list)
    total_experiments_run: int = Field(default=0)
    beliefs_dissolved: int = Field(default=0)
    beliefs_embodied: int = Field(default=0)
    replay_loops_resolved: int = Field(default=0)
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Graphiti metadata
    graphiti_group_id: Optional[str] = Field(None, description="Group ID for Graphiti episodes")


# =============================================================================
# Ingestion Schemas (for Graphiti)
# =============================================================================


class BeliefIngestionPayload(BaseModel):
    """Payload for ingesting a belief event into Graphiti."""
    event_type: str = Field(..., description="belief_identified, belief_tested, belief_dissolved, etc.")
    journey_id: UUID
    belief_id: UUID
    content: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def to_episode_text(self) -> str:
        """Format for Graphiti ingestion."""
        return f"""
BELIEF EVENT: {self.event_type}
Journey: {self.journey_id}
Belief: {self.content}
Context: {self.context}
Timestamp: {self.timestamp.isoformat()}
"""


class ExperimentIngestionPayload(BaseModel):
    """Payload for ingesting an experiment event into Graphiti."""
    journey_id: UUID
    experiment_id: UUID
    belief_tested: str
    hypothesis: str
    action_taken: str
    outcome: str
    result_description: str
    belief_shift: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def to_episode_text(self) -> str:
        """Format for Graphiti ingestion."""
        return f"""
BELIEF EXPERIMENT RESULT:
Journey: {self.journey_id}
Belief Tested: {self.belief_tested}
Hypothesis: {self.hypothesis}
Action Taken: {self.action_taken}
Outcome: {self.outcome}
Result: {self.result_description}
Belief Shift: {self.belief_shift or 'None observed'}
Timestamp: {self.timestamp.isoformat()}
"""


class ReplayLoopIngestionPayload(BaseModel):
    """Payload for ingesting a replay loop event into Graphiti."""
    event_type: str = Field(..., description="loop_identified, loop_interrupted, loop_resolved")
    journey_id: UUID
    loop_id: UUID
    trigger: str
    story: str
    emotion: str
    fear: str
    resolution: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def to_episode_text(self) -> str:
        """Format for Graphiti ingestion."""
        return f"""
REPLAY LOOP EVENT: {self.event_type}
Journey: {self.journey_id}
Trigger: {self.trigger}
Story: {self.story}
Emotion: {self.emotion}
Fear Underneath: {self.fear}
Resolution: {self.resolution or 'Pending'}
Timestamp: {self.timestamp.isoformat()}
"""
