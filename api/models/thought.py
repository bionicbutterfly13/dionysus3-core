from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class ThoughtLayer(str, Enum):
    SENSORIMOTOR = "sensorimotor"
    PERCEPTUAL = "perceptual"
    CONCEPTUAL = "conceptual"
    ABSTRACT = "abstract"
    METACOGNITIVE = "metacognitive"

class MarkovBlanket(str, Enum):
    """
    Partitions of the Free Energy Principle's Markov Blanket.
    """
    SENSORY = "sensory"     # Inputs from world/user (Read-Only)
    ACTIVE = "active"       # Outputs to world/tools (Write-Only)
    INTERNAL = "internal"   # Private cognitive states (Protected)
    EXTERNAL = "external"   # World states hidden from internal (Unknown)

class CompetitionStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"

class ThoughtSeed(BaseModel):
    """
    A unit of cognitive processing at a specific layer.
    Can contain references to child thoughts, enabling fractal structures.
    """
    id: UUID = Field(default_factory=uuid4)
    layer: ThoughtLayer
    blanket_tag: MarkovBlanket = Field(
        default=MarkovBlanket.INTERNAL,
        description="The Markov Blanket partition this thought belongs to"
    )
    content: str
    activation_level: float = Field(default=0.0, ge=0.0, le=1.0)
    competition_status: CompetitionStatus = Field(default=CompetitionStatus.PENDING)
    
    # Fractal/Recursive properties (Feature 037)
    child_thought_ids: List[UUID] = Field(default_factory=list)
    parent_thought_id: Optional[UUID] = None
    
    # Metadata and provenance
    source_id: Optional[str] = None
    neuronal_packet: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "layer": "conceptual",
                "content": "Identifying recursive pattern in user feedback",
                "activation_level": 0.85,
                "child_thought_ids": ["660e8400-e29b-41d4-a716-446655440001"],
            }
        }
    }
