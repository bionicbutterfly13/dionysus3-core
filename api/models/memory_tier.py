from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class MemoryTier(str, Enum):
    HOT = "hot"       # Session cache / Redis
    WARM = "warm"     # Neo4j Graph
    COLD = "cold"     # Compressed archive / Vector

class TieredMemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    memory_type: str = "semantic"
    tier: MemoryTier = MemoryTier.HOT
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    importance_score: float = Field(0.5, ge=0.0, le=1.0)
    
    # Associations
    session_id: Optional[str] = None
    project_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MigrationReport(BaseModel):
    source_tier: MemoryTier
    target_tier: MemoryTier
    items_moved: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
