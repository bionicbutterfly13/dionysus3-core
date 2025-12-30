import enum
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class FlowState(str, enum.Enum):
    """River Metaphor states for metacognition (Feature 027)."""
    EMERGING = "emerging"
    FLOWING = "flowing"
    CONVERGING = "converging"
    STABLE = "stable"
    TURBULENT = "turbulent"
    STAGNANT = "stagnant" # Low compression, high input/output with no gain
    DRIFTING = "drifting" # Low resonance with goals

class EFEResult(BaseModel):
    """Result of an Expected Free Energy calculation for a ThoughtSeed."""
    seed_id: str
    efe_score: float
    uncertainty: float
    goal_divergence: float

class EFEResponse(BaseModel):
    """Ranked results from the EFE Engine."""
    dominant_seed_id: str
    scores: Dict[str, EFEResult] # seed_id -> detailed result

class NeuronalPacketModel(BaseModel):
    """Data model for a synergistic group of ThoughtSeeds."""
    packet_id: str
    seed_ids: List[str]
    state_vector: List[float]
    cohesion_weight: float = Field(default=1.0)
    boundary_energy: float = Field(default=0.5)
    stability: float = Field(default=0.5)

class MemoryCluster(BaseModel):
    """Augmented MemoryCluster node model for Energy-Well stability."""
    cluster_id: str
    name: str
    boundary_energy: float = Field(default=0.5, ge=0.0, le=1.0)
    cohesion_ratio: float = Field(default=1.0, ge=0.0)
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
