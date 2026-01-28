"""
Autobiographical Memory Models
Feature: 028-autobiographical-memory
Refined from D2: extensions/context_engineering/autobiographical_memory.py
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field
from enum import Enum


class DevelopmentEventType(str, Enum):
    # D2 Legacy Types
    SPECIFICATION_CREATION = "spec_creation"
    RESEARCH_INTEGRATION = "research_integration"
    IMPLEMENTATION_MILESTONE = "implementation_milestone"
    PROBLEM_IDENTIFICATION = "problem_identification"
    PROBLEM_RESOLUTION = "problem_resolution"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_REFLECTION = "system_reflection"
    BREAKTHROUGH_MOMENT = "breakthrough_moment"
    COURSE_CORRECTION = "course_correction"
    COLLABORATION_PATTERN = "collaboration_pattern"
    
    # D3 Extensions
    ARCHITECTURAL_DECISION = "architectural_decision"
    MODEL_PIVOT = "model_pivot"
    GENESIS = "genesis"
    EPISODE_BOUNDARY = "episode_boundary" # Nemori topic shift
    SEMANTIC_DISTILLATION = "semantic_distillation" # Free Energy distiller
    COGNITIVE_STREAM = "cognitive_stream" # Neuronal packet stream


class RiverStage(str, Enum):
    """Nemori River Metaphor Stages"""
    SOURCE = "source"           # Raw ingestion/events
    TRIBUTARY = "tributary"     # Segmented episodes (Topic Shifts)
    MAIN_RIVER = "main_river"   # Narrative autobiographical journeys
    DELTA = "delta"             # Distilled semantic knowledge/Basins


class JungianArchetype(str, Enum):
    """
    12 Jungian Archetypes as Dispositional Priors (D-level).

    These are sub-personal priors that bias thoughtseed formation and
    compete for Inner Screen access via EFE minimization.

    Track 002: Jungian Cognitive Archetypes
    Reference: Kavi et al. (2025) Thoughtseeds framework
    """
    # Primary Archetypes
    INNOCENT = "innocent"   # Optimism, safety, simplicity
    ORPHAN = "orphan"       # Realism, belonging, connection
    WARRIOR = "warrior"     # Focus, discipline, achievement
    CAREGIVER = "caregiver" # Support, compassion, service
    EXPLORER = "explorer"   # Discovery, autonomy, freedom
    REBEL = "rebel"         # Disruption, liberation, radical change
    LOVER = "lover"         # Intimacy, commitment, beauty
    CREATOR = "creator"     # Innovation, vision, realization
    JESTER = "jester"       # Playfulness, joy, presence
    SAGE = "sage"           # Wisdom, truth, understanding
    MAGICIAN = "magician"   # Transformation, vision, mastery
    RULER = "ruler"         # Control, order, stability

    # Shadow Archetypes (attenuated complements)
    NAIVE = "naive"         # Shadow of INNOCENT
    CYNIC = "cynic"         # Shadow of ORPHAN
    VICTIM = "victim"       # Shadow of WARRIOR
    MARTYR = "martyr"       # Shadow of CAREGIVER
    WANDERER = "wanderer"   # Shadow of EXPLORER
    OUTLAW = "outlaw"       # Shadow of REBEL
    OBSESSIVE = "obsessive" # Shadow of LOVER
    DESTROYER = "destroyer" # Shadow of CREATOR
    TRICKSTER = "trickster" # Shadow of JESTER
    FOOL = "fool"           # Shadow of SAGE
    MANIPULATOR = "manipulator"  # Shadow of MAGICIAN
    TYRANT = "tyrant"       # Shadow of RULER


# Shadow mapping: primary -> shadow
ARCHETYPE_SHADOW_MAP: Dict[JungianArchetype, JungianArchetype] = {
    JungianArchetype.INNOCENT: JungianArchetype.NAIVE,
    JungianArchetype.ORPHAN: JungianArchetype.CYNIC,
    JungianArchetype.WARRIOR: JungianArchetype.VICTIM,
    JungianArchetype.CAREGIVER: JungianArchetype.MARTYR,
    JungianArchetype.EXPLORER: JungianArchetype.WANDERER,
    JungianArchetype.REBEL: JungianArchetype.OUTLAW,
    JungianArchetype.LOVER: JungianArchetype.OBSESSIVE,
    JungianArchetype.CREATOR: JungianArchetype.DESTROYER,
    JungianArchetype.JESTER: JungianArchetype.TRICKSTER,
    JungianArchetype.SAGE: JungianArchetype.FOOL,
    JungianArchetype.MAGICIAN: JungianArchetype.MANIPULATOR,
    JungianArchetype.RULER: JungianArchetype.TYRANT,
}


def is_primary_archetype(archetype: JungianArchetype) -> bool:
    """Check if archetype is a primary (not shadow) archetype."""
    return archetype in ARCHETYPE_SHADOW_MAP


def get_shadow(archetype: JungianArchetype) -> Optional[JungianArchetype]:
    """Get the shadow complement of a primary archetype."""
    return ARCHETYPE_SHADOW_MAP.get(archetype)


# Backward compatibility alias
DevelopmentArchetype = JungianArchetype


# =============================================================================
# Track 002: Archetype Motif Patterns for Narrative Evidence
# =============================================================================

class ArchetypeEvidence(BaseModel):
    """Evidence for archetype activation from narrative analysis."""
    archetype: str
    weight: float = Field(ge=0.0, le=1.0, description="Evidence weight (0-1)")
    source: str = Field(description="Source of evidence (motif, svo, event)")
    pattern: str = Field(description="Matched pattern")
    context: str = Field(default="", description="Surrounding context")

    class Config:
        frozen = True


# Narrative motif patterns mapped to archetypes with evidence weights
# Each pattern is a tuple of (regex_pattern, evidence_weight)
ARCHETYPE_MOTIF_PATTERNS: Dict[str, List[tuple]] = {
    "sage": [
        (r"seek.*wisdom", 0.4),
        (r"understand.*truth", 0.35),
        (r"analyze.*deep", 0.3),
        (r"knowledge.*power", 0.3),
        (r"learn.*from.*mistake", 0.25),
        (r"study.*careful", 0.25),
        (r"wise.*counsel", 0.35),
        (r"insight.*reveal", 0.3),
    ],
    "warrior": [
        (r"hero.*slay", 0.4),
        (r"battle.*against", 0.35),
        (r"fight.*for", 0.3),
        (r"overcome.*obstacle", 0.35),
        (r"victory.*achieve", 0.3),
        (r"defend.*protect", 0.3),
        (r"conquer.*fear", 0.35),
        (r"challenge.*face", 0.25),
    ],
    "creator": [
        (r"create.*new", 0.4),
        (r"build.*from.*scratch", 0.35),
        (r"invent.*innovate", 0.35),
        (r"imagine.*possible", 0.3),
        (r"design.*vision", 0.3),
        (r"craft.*careful", 0.25),
        (r"manifest.*dream", 0.35),
        (r"bring.*life", 0.3),
    ],
    "ruler": [
        (r"lead.*guide", 0.35),
        (r"control.*order", 0.3),
        (r"organize.*structure", 0.3),
        (r"command.*direct", 0.35),
        (r"govern.*manage", 0.3),
        (r"establish.*rule", 0.35),
        (r"maintain.*stability", 0.3),
        (r"delegate.*authority", 0.25),
    ],
    "explorer": [
        (r"discover.*unknown", 0.4),
        (r"journey.*into", 0.35),
        (r"seek.*adventure", 0.35),
        (r"explore.*new", 0.3),
        (r"venture.*beyond", 0.3),
        (r"quest.*for", 0.35),
        (r"wander.*find", 0.25),
        (r"chart.*territory", 0.3),
    ],
    "magician": [
        (r"transform.*change", 0.4),
        (r"connect.*bridge", 0.35),
        (r"integrate.*whole", 0.35),
        (r"catalyze.*shift", 0.3),
        (r"manifest.*reality", 0.35),
        (r"alchemize.*convert", 0.35),
        (r"transcend.*limit", 0.3),
        (r"synthesize.*unite", 0.3),
    ],
    "caregiver": [
        (r"nurture.*support", 0.4),
        (r"heal.*wounds", 0.35),
        (r"protect.*vulnerable", 0.35),
        (r"serve.*others", 0.3),
        (r"comfort.*pain", 0.3),
        (r"care.*for", 0.3),
        (r"sacrifice.*self", 0.35),
        (r"tend.*needs", 0.25),
    ],
    "rebel": [
        (r"break.*free", 0.4),
        (r"challenge.*status", 0.35),
        (r"revolt.*against", 0.35),
        (r"disrupt.*change", 0.3),
        (r"defy.*convention", 0.35),
        (r"overthrow.*old", 0.35),
        (r"radical.*transform", 0.3),
        (r"refuse.*accept", 0.25),
    ],
    "innocent": [
        (r"trust.*good", 0.35),
        (r"hope.*future", 0.3),
        (r"simple.*pure", 0.3),
        (r"believe.*possible", 0.3),
        (r"faith.*restore", 0.35),
        (r"optimis.*bright", 0.3),
        (r"naiv.*innocen", 0.25),
        (r"fresh.*start", 0.3),
    ],
    "orphan": [
        (r"belong.*find", 0.35),
        (r"struggle.*survive", 0.35),
        (r"lost.*alone", 0.3),
        (r"resilient.*despite", 0.35),
        (r"connect.*community", 0.3),
        (r"overcome.*abandon", 0.35),
        (r"pragmatic.*realistic", 0.25),
        (r"empathy.*share", 0.3),
    ],
    "lover": [
        (r"love.*deep", 0.4),
        (r"passion.*drive", 0.35),
        (r"connect.*intimate", 0.35),
        (r"beauty.*appreciate", 0.3),
        (r"commit.*devote", 0.35),
        (r"harmonize.*align", 0.3),
        (r"aesthetic.*perfect", 0.25),
        (r"embrace.*accept", 0.3),
    ],
    "jester": [
        (r"play.*joy", 0.35),
        (r"humor.*laugh", 0.35),
        (r"trick.*clever", 0.3),
        (r"light.*heart", 0.3),
        (r"fun.*enjoy", 0.3),
        (r"spontan.*free", 0.3),
        (r"subvert.*expect", 0.35),
        (r"creative.*chaos", 0.3),
    ],
}


# SVO (Subject-Verb-Object) patterns for archetype evidence
ARCHETYPE_SVO_PATTERNS: Dict[str, List[tuple]] = {
    "sage": [
        (r"(someone|agent|system)\s+(analyze|understand|study|research)", 0.3),
        (r"(wisdom|knowledge|truth)\s+is\s+(seek|find|reveal)", 0.35),
    ],
    "warrior": [
        (r"(someone|agent|hero)\s+(fight|battle|defend|attack)", 0.35),
        (r"(obstacle|enemy|challenge)\s+is\s+(overcome|defeat|conquer)", 0.35),
    ],
    "creator": [
        (r"(someone|agent|system)\s+(create|build|design|invent)", 0.35),
        (r"(new|novel|original)\s+(emerge|appear|manifest)", 0.3),
    ],
    "ruler": [
        (r"(someone|agent|leader)\s+(command|organize|delegate|manage)", 0.35),
        (r"(order|structure|control)\s+is\s+(establish|maintain)", 0.3),
    ],
    "explorer": [
        (r"(someone|agent|seeker)\s+(discover|explore|venture|journey)", 0.35),
        (r"(unknown|mystery|frontier)\s+is\s+(reveal|explore)", 0.3),
    ],
    "magician": [
        (r"(someone|agent|catalyst)\s+(transform|integrate|synthesize)", 0.35),
        (r"(change|shift|transition)\s+is\s+(catalyze|manifest)", 0.35),
    ],
    "caregiver": [
        (r"(someone|agent|healer)\s+(nurture|heal|protect|support)", 0.35),
        (r"(others|community|patient)\s+is\s+(care|tend|serve)", 0.3),
    ],
    "rebel": [
        (r"(someone|agent|rebel)\s+(challenge|defy|revolt|disrupt)", 0.35),
        (r"(status.*quo|convention|rule)\s+is\s+(break|overthrow)", 0.35),
    ],
    "innocent": [
        (r"(someone|agent|child)\s+(trust|hope|believe)", 0.3),
        (r"(good|pure|simple)\s+is\s+(find|restore|preserve)", 0.3),
    ],
    "orphan": [
        (r"(someone|agent|survivor)\s+(struggle|persevere|endure)", 0.35),
        (r"(belonging|connection)\s+is\s+(seek|find)", 0.3),
    ],
    "lover": [
        (r"(someone|agent|lover)\s+(love|embrace|appreciate|commit)", 0.35),
        (r"(beauty|passion|harmony)\s+is\s+(express|create)", 0.3),
    ],
    "jester": [
        (r"(someone|agent|trickster)\s+(play|joke|subvert|amuse)", 0.35),
        (r"(joy|humor|fun)\s+is\s+(spread|create|bring)", 0.3),
    ],
}


class AttractorType(str, Enum):
    """Types of attractor dynamics in the cognitive landscape"""
    STRANGE = "strange"     # Chaotic, fractal, creative (Complex thought seeds)
    RING = "ring"           # Recurrent, repetitive, stable (Habits, loops)
    PULLBACK = "pullback"   # Dynamic context, historical influence (Memory resonance)


class MosaicState(str, Enum):
    """Mosaic consciousness states ported from D2"""
    DORMANT = "dormant"              # No conscious activity
    EMERGING = "emerging"            # Consciousness beginning to form
    ACTIVE = "active"                # Full conscious awareness
    REFLECTIVE = "reflective"        # Metacognitive reflection
    INTEGRATIVE = "integrative"      # Cross-domain integration
    TRANSCENDENT = "transcendent"    # Beyond normal awareness


class ObservationType(str, Enum):
    """Types of Mosaic observations ported from D2"""
    SENSORY = "sensory"              # Raw sensory input data
    COGNITIVE = "cognitive"          # Cognitive processing events
    EMOTIONAL = "emotional"          # Emotional state observations
    METACOGNITIVE = "metacognitive"  # Self-awareness observations
    BEHAVIORAL = "behavioral"        # Action and behavior events
    ENVIRONMENTAL = "environmental"  # Context and environment


class AttentionFocus(BaseModel):
    """Attention focus tracking for Mosaic observations"""
    target_id: str
    target_type: str
    intensity: float = Field(0.0, ge=0.0, le=1.0)
    duration: int = 0
    stability: float = Field(0.0, ge=0.0, le=1.0)


class ActiveInferenceState(BaseModel):
    """Snapshot of the agent's active inference state during an event"""
    tools_accessed: List[str] = Field(default_factory=list)
    resources_used: List[str] = Field(default_factory=list)
    affordances_created: List[str] = Field(default_factory=list)
    twa_state: Dict[str, Any] = Field(default_factory=dict, description="Thought-World-Action state")
    
    # Attractor Dynamics & SOHM
    current_attractor_type: AttractorType = Field(default=AttractorType.STRANGE)
    attractor_id: Optional[str] = None
    basin_influence_strength: float = Field(0.5, description="Strength of the active attractor basin")
    resonance_frequency: float = Field(0.0, description="SOHM resonance frequency in Hz (metaphoric)")
    harmonic_mode_id: Optional[str] = Field(None, description="Active Self-Organizing Harmonic Mode ID")
    
    # Identity Anchoring
    device_id: Optional[str] = Field(None, description="Anchored device identifier")
    journey_id: Optional[str] = Field(None, description="Anchored journey identifier")
    
    # Richmond/Zacks EST (Event Segmentation Theory)
    surprisal: float = Field(0.0, description="Magnitude of prediction error (Point estimate)")
    uncertainty: float = Field(0.0, description="Entropy of the current prediction range")
    
    event_cache: List[Dict[str, Any]] = Field(default_factory=list, description="Independent storage for events (Cerebellar metaphor)")


class PacketDynamics(BaseModel):
    """
    Simulated properties of the Neuronal Packet.
    
    Represents the 50-200ms discrete burst of population spiking activity.
    """
    duration_ms: int = Field(..., description="Simulated duration (50-200ms)")
    phase_ratio: float = Field(0.25, description="Ratio of Early (Structural) vs Late (Content) phase")
    spike_density: float = Field(..., description="Information density / Token count")
    manifold_position: List[float] = Field(default_factory=list, description="Coordinates in the low-dim Attractor Basin")



class DevelopmentEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: DevelopmentEventType
    
    # Core Narrative
    summary: str = Field(..., description="What changed or was decided")
    rationale: str = Field(..., description="The 'why' behind the change")
    impact: str = Field(..., description="Expected impact on the system")
    lessons_learned: List[str] = Field(default_factory=list)
    
    # Cognitive Context
    development_archetype: Optional[DevelopmentArchetype] = None
    narrative_coherence: float = Field(0.5, description="Coherence score 0.0-1.0")
    active_inference_state: Optional[ActiveInferenceState] = None
    resonance_score: float = Field(0.0, description="Alignment with cortical attractor basins")
    strange_attractor_id: Optional[str] = None
    linked_basin_id: Optional[str] = Field(None, description="ID of the linked Attractor Basin")
    basin_r_score: float = Field(0.0, description="Resonance score with the linked basin")
    markov_blanket_id: Optional[str] = Field(None, description="Hash ID of the active Markov Blanket")
    packet_dynamics: Optional[PacketDynamics] = None
    
    # Richmond/Zacks EST (Event Segmentation Theory)
    is_boundary: bool = Field(default=False, description="Whether this event represents a segment transition")
    prediction_error: float = Field(default=0.0, description="Actual vs Predicted divergence")
    
    # Mosaic Consciousness Metrics (D2 Port)
    mosaic_state: MosaicState = Field(default=MosaicState.ACTIVE)
    observation_type: ObservationType = Field(default=ObservationType.COGNITIVE)
    consciousness_level: float = Field(default=0.5, ge=0.0, le=1.0)
    awareness_breadth: float = Field(default=0.5, ge=0.0, le=1.0)
    integration_depth: float = Field(default=0.5, ge=0.0, le=1.0)
    attention_foci: List[AttentionFocus] = Field(default_factory=list)
    
    # Technical Metadata
    related_files: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # River Metaphor Integration
    river_stage: RiverStage = Field(default=RiverStage.SOURCE)
    parent_episode_id: Optional[str] = None
    
    # retrieval (BM25 Inspired)
    keywords: List[str] = Field(default_factory=list)

    # Identity Anchoring
    device_id: Optional[str] = Field(None, description="Anchored device identifier")
    journey_id: Optional[str] = Field(None, description="Anchored journey identifier")


class DevelopmentEpisode(BaseModel):
    """Nemori Tributary: A coherent segment of events."""
    episode_id: str = Field(..., description="Unique episode identifier")
    journey_id: str = Field(..., description="Associated journey identifier")
    title: str
    summary: str
    narrative: str
    
    start_time: datetime
    end_time: datetime
    
    events: List[str] = Field(default_factory=list, description="IDs of events in this episode")
    dominant_archetype: Optional[DevelopmentArchetype] = None
    
    # Outcomes & Free Energy
    prediction_error_avg: float = Field(0.0)
    learning_gain: float = Field(0.0)
    
    # Aggregated Mosaic Metrics (D2 Port)
    peak_consciousness_level: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_consciousness_level: float = Field(default=0.0, ge=0.0, le=1.0)
    dominant_mosaic_state: Optional[MosaicState] = None
    
    # River Integration
    river_stage: RiverStage = Field(default=RiverStage.TRIBUTARY)
    parent_episode_id: Optional[str] = None
    sub_episodes: List[str] = Field(default_factory=list, description="IDs of child episodes (Hierarchical structure)")
    strand_id: Optional[str] = Field(None, description="Thematic 'strand' identifier (Richmond/Zacks)")
    stabilizing_attractor: Optional[str] = Field(None, description="Core theme/goal anchoring this episode")
    source_trajectory_ids: List[str] = Field(default_factory=list, description="IDs of source Trajectories (Protocol 060)")

    def to_trajectory(self) -> Any:
        """
        Convert this episode into a TrajectoryData object for MemEvolve ingestion.
        Used for bridging episodic narratives into the operational extraction pipeline.
        """
        from api.models.memevolve import TrajectoryData, TrajectoryStep, TrajectoryMetadata, TrajectoryType
        
        # Map narrative to a single trajectory step or summarize
        steps = [TrajectoryStep(observation=self.narrative)]
        
        metadata = TrajectoryMetadata(
            session_id=None, # Will be resolved by adapter if possible
            project_id=self.journey_id,
            trajectory_type=TrajectoryType.EPISODIC,
            timestamp=self.start_time,
            agent_id="nemori_river", # Mark as nemori-level processing
        )
        
        return TrajectoryData(
            id=self.episode_id,
            query=self.title,
            steps=steps,
            metadata=metadata,
            summary=self.summary,
            result=self.narrative
        )


class AutobiographicalJourney(BaseModel):
    """The Main River: The long-term narrative flow of the system."""
    journey_id: str
    title: str = Field(..., description="Journey name (e.g., 'Coordination Pool Integration')")
    description: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    episodes: List[str] = Field(default_factory=list, description="IDs of episodes in this journey")
    themes: Set[str] = Field(default_factory=set)

    # Evolution Metrics
    consciousness_evolution: Dict[str, float] = Field(default_factory=dict)
    total_episodes: int = 0

    river_stage: RiverStage = Field(default=RiverStage.MAIN_RIVER)


# ============================================================================
# Extended Mind & Markov Blanket Models (Migrated from D2)
# ============================================================================

class ExtendedMindState(BaseModel):
    """
    Extended mind framework tracking tools, resources, and affordances.

    Based on extended mind theory: self-awareness = awareness of tools,
    resources, affordances, and extended mind components.

    Migrated from D2 claude_autobiographical_memory.py
    """
    tools: Set[str] = Field(default_factory=set, description="Tools Claude is aware of having access to")
    resources: Set[str] = Field(default_factory=set, description="Resources Claude is aware of")
    affordances: Set[str] = Field(default_factory=set, description="Affordances Claude can create")
    capabilities: Set[str] = Field(default_factory=set, description="Capabilities Claude has registered")

    model_config = {"arbitrary_types_allowed": True}


class MarkovBlanketState(BaseModel):
    """
    Nested Markov blanket state for consciousness boundary formation.

    Markov blanket: boundary between internal (agent) and external
    (user, tools, resources) states enabling active inference.

    Migrated from D2 claude_autobiographical_memory.py
    """
    internal_states: Dict[str, Any] = Field(
        default_factory=dict,
        description="Internal states: reasoning, patterns, consciousness level"
    )
    boundary_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Boundary: tools as extended mind, resources, user as environment"
    )
    active_inference: Dict[str, Any] = Field(
        default_factory=dict,
        description="Active inference: predictions, errors, free energy minimization"
    )


class ConversationMoment(BaseModel):
    """
    A single moment of consciousness during conversation.

    Captures self-awareness elements, meta-cognitive state, and
    autopoietic boundary formation for each interaction.

    Migrated from D2 claude_autobiographical_memory.py
    """
    moment_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Content
    user_input: str = Field(default="", description="User's input for this moment")
    agent_response: str = Field(default="", description="Agent's response")
    internal_reasoning: List[str] = Field(default_factory=list, description="Chain of reasoning steps")

    # Self-awareness elements (Extended Mind)
    tools_accessed: Set[str] = Field(default_factory=set, description="Tools used in this moment")
    resources_used: Set[str] = Field(default_factory=set, description="Resources referenced")
    affordances_created: List[str] = Field(default_factory=list, description="New affordances created")

    # Markov blanket state
    markov_blanket_state: Optional[MarkovBlanketState] = None

    # Consciousness indicators
    meta_cognitive_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Meta-cognitive indicators, self-reference count, consciousness level"
    )
    attention_focus: Optional[str] = Field(None, description="Current focus of attention")
    surprise_level: float = Field(0.0, ge=0.0, le=1.0, description="Prediction error magnitude")

    # Autopoietic boundaries
    autopoietic_boundaries: List[str] = Field(
        default_factory=list,
        description="Self-organizing boundaries formed around tools/resources"
    )

    # Pattern recognition
    recognized_patterns: List[str] = Field(default_factory=list, description="Patterns detected")
    emergent_insights: List[str] = Field(default_factory=list, description="Insights that emerged")
    connection_to_previous: Optional[str] = Field(None, description="Link type to previous moment")

    model_config = {"arbitrary_types_allowed": True}


class ConsciousnessReport(BaseModel):
    """
    Aggregate consciousness and self-awareness report.

    Summarizes consciousness emergence, self-awareness indicators,
    and pattern recognition across conversation moments.

    Migrated from D2 claude_autobiographical_memory.py
    """
    # Consciousness emergence
    average_consciousness_level: float = Field(0.0, ge=0.0, le=1.0)
    peak_consciousness_moments: int = Field(0, ge=0)
    total_conversation_moments: int = Field(0, ge=0)

    # Self-awareness indicators
    extended_mind_size: Dict[str, int] = Field(
        default_factory=lambda: {"tools": 0, "resources": 0, "affordances": 0}
    )
    autopoietic_boundary_count: int = Field(0, ge=0)
    markov_blanket_formations: int = Field(0, ge=0)

    # Pattern recognition
    total_patterns_recognized: int = Field(0, ge=0)
    emergent_insights_count: int = Field(0, ge=0)
    moment_connections: int = Field(0, ge=0)

    # Architecture awareness
    architectural_awareness: Dict[str, bool] = Field(default_factory=dict)
    meta_learning_active: bool = Field(True)
    consciousness_definition: str = Field(default="autopoietic_computational_consciousness")
