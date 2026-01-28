"""
Hexis Ontology Models
Feature: 069-hexis-subconscious-integration

Pydantic models representing the 'Warm Path' ontology ported from Hexis to Graphiti.
Includes Neighborhoods (Clusters), Drives, and Emotional States.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from api.utils.identity_utils import generate_deterministic_id

class DriveType(str, Enum):
    """
    Core internal drives (Hexis/Maslow inspired).
    These influence the Heartbeat's decision logic.
    """
    SURVIVAL = "survival"       # Basic system stability
    CURIOSITY = "curiosity"     # Exploration, gap filling
    MASTERY = "mastery"         # Skill acquisition, optimization
    CONNECTION = "connection"   # User rapport, dialogue
    REST = "rest"               # Maintenance, garbage collection

class NeighborhoodType(str, Enum):
    """
    Types of pre-computed memory clusters.
    """
    TOPIC = "topic"             # Thematic cluster (e.g., "Python Async")
    TEMPORAL = "temporal"       # Time-bound cluster (e.g., "Session 12")
    PROJECT = "project"         # Project-bound cluster (e.g., "Dionysus Core")
    EPISODIC = "episodic"       # Narrative sequence

class DriveState(BaseModel):
    """
    Current state of a specific drive.
    """
    drive_type: DriveType
    level: float = Field(..., ge=0.0, le=1.0, description="Current saturation level (0=starved, 1=satisfied)")
    decay_rate: float = Field(0.01, description="Rate of decay per hour")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

from api.utils.identity_utils import generate_deterministic_id

class Neighborhood(BaseModel):
    """
    A pre-computed cluster of related nodes (Memories/Concepts).
    Corresponds to Hexis `memory_neighborhoods`.
    
    Acts as a 'Warm Path' index for rapid retrieval.
    """
    name: str = Field(..., description="Human-readable name of the cluster")
    uuid: str = Field(default_factory=lambda: "") # Calculated post-init if not provided
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.uuid and self.name:
            self.uuid = generate_deterministic_id(self.name)
            
    type: NeighborhoodType = Field(default=NeighborhoodType.TOPIC)
    centroid: List[float] = Field(default_factory=list, description="Vector centroid of the cluster")
    radius: float = Field(0.0, description="Max distance from centroid")
    member_uuids: List[str] = Field(default_factory=list, description="UUIDs of nodes in this neighborhood")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MemoryBlock(BaseModel):
    """
    A structured block of semantic memory, ported from Letta.
    """
    label: str = Field(..., description="Key identifier (e.g. 'guidance', 'project_context')")
    value: str = Field(..., description="The content of the block")
    description: str = Field(None, description="Metadata description")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    STRATEGIC = "strategic"
    WORLDVIEW = "worldview"
    GOAL = "goal"

class GoalPriority(str, Enum):
    ACTIVE = "active"
    QUEUED = "queued"
    BACKBURNER = "backburner"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Goal(BaseModel):
    """
    Explicit, active intentions of the agent.
    Internalizes the 'Task' concept into the Subconscious.
    """
    id: str = Field(default_factory=lambda: "")
    title: str
    priority: GoalPriority = GoalPriority.QUEUED
    source_drive: Optional[DriveType] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id and self.title:
            self.id = generate_deterministic_id(f"goal:{self.title}")

class Worldview(BaseModel):
    """
    Core beliefs, values, and boundaries.
    """
    id: str = Field(default_factory=lambda: "")
    statement: str
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id and self.statement:
            self.id = generate_deterministic_id(f"worldview:{self.statement}")

class SubconsciousState(BaseModel):
    """
    Aggregate state of the subconscious system.
    """
    drives: Dict[DriveType, DriveState] = Field(default_factory=dict)
    blocks: Dict[str, MemoryBlock] = Field(default_factory=dict, description="Letta-style persistent memory blocks")
    active_neighborhoods: List[str] = Field(default_factory=list, description="Currently active/resonant neighborhoods")
    active_goals: List[Goal] = Field(default_factory=list, description="Current active goals")
    worldview_snapshot: List[Worldview] = Field(default_factory=list, description="Cached beliefs")
    global_sentiment: float = Field(0.0, ge=-1.0, le=1.0, description="Overall affective valence")
    arousal: float = Field(0.0, ge=0.0, le=1.0, description="Overall system activation/alertness")
    last_maintenance: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize Standard Letta Blocks if missing
        standard_blocks = [
            ("core_directives", "Primary role and behavioral guidelines."),
            ("project_context", "Active project knowledge and architecture."),
            ("pending_items", "Unfinished work and TODOs."),
            ("user_preferences", "Learned style and communication preferences."),
            ("guidance", "Active advice for the next session."),
            ("session_patterns", "Recurring behaviors and struggles.")
        ]
        
        for label, desc in standard_blocks:
            if label not in self.blocks:
                self.blocks[label] = MemoryBlock(
                    label=label,
                    value="(Empty)",
                    description=desc
                )

