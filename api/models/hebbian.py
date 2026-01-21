"""
Models for Hebbian Learning connection weights.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from api.utils.math_utils import hebbian_update, weight_decay

class HebbianConnection(BaseModel):
    source_id: str
    target_id: str
    weight: float = Field(0.5, ge=0.01, le=0.99)
    last_activated: datetime = Field(default_factory=datetime.utcnow)
    
    def apply_hebbian_update(self, v1: float, v2: float, mu: float = 0.9):
        """Update weight based on co-activation."""
        self.weight = hebbian_update(v1, v2, self.weight, mu)
        self.last_activated = datetime.utcnow()
        
    def apply_decay(self, decay_rate: float = 0.01):
        """Apply time-based decay."""
        now = datetime.utcnow()
        days = (now - self.last_activated).total_seconds() / (24 * 3600)
        if days > 0:
            self.weight = weight_decay(self.weight, decay_rate, days)
