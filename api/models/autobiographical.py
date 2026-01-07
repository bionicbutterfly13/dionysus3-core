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


class RiverStage(str, Enum):
    """Nemori River Metaphor Stages"""
    SOURCE = "source"           # Raw ingestion/events
    TRIBUTARY = "tributary"     # Segmented episodes (Topic Shifts)
    MAIN_RIVER = "main_river"   # Narrative autobiographical journeys
    DELTA = "delta"             # Distilled semantic knowledge/Basins


class DevelopmentArchetype(str, Enum):
    """
    12 Jungian Archetypes as cognitive patterns/strange attractors.
    Refined for D3 Cognitive Architecture.
    """
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
    
    # Richmond/Zacks EST (Event Segmentation Theory)
    surprisal: float = Field(0.0, description="Magnitude of prediction error (Point estimate)")
    uncertainty: float = Field(0.0, description="Entropy of the current prediction range")
    
    event_cache: List[Dict[str, Any]] = Field(default_factory=list, description="Independent storage for events (Cerebellar metaphor)")


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
    
    # Retrieval (BM25 Inspired)
    keywords: List[str] = Field(default_factory=list)


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


class AutobiographicalJourney(BaseModel):
    """The Main River: The long-term narrative flow of the system."""
    journey_id: str
    title: str = Field(..., description="Journey name (e.g., 'Daedalus Integration')")
    description: str
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    episodes: List[str] = Field(default_factory=list, description="IDs of episodes in this journey")
    themes: Set[str] = Field(default_factory=set)
    
    # Evolution Metrics
    consciousness_evolution: Dict[str, float] = Field(default_factory=dict)
    total_episodes: int = 0
    
    river_stage: RiverStage = Field(default=RiverStage.MAIN_RIVER)
