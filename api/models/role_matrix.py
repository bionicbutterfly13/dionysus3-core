"""
Models for Declarative Role Matrix Network Specification.
"""

from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

class RoleNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    default_threshold: float = 0.5
    default_speed: float = 0.1

class RoleConnection(BaseModel):
    source_id: str
    target_id: str
    weight: float = 0.5
    bidirectional: bool = False

class RoleMatrixSpec(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    version: str = "1.0.0"
    nodes: List[RoleNode]
    connections: List[RoleConnection]
