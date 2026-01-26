import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

class MetacognitiveParticle(BaseModel):
    """
    Atomic unit of thought in the Dionysus cognitive architecture.
    
    A Particle represents a single cognitive event, observation, or deduction.
    It carries epistemic metadata (precision, entropy) to support Active Inference.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="The textual representation of the thought.")
    source_agent: str = Field(..., description="ID of the agent/process that generated this.")
    context_id: Optional[str] = Field(None, description="UUID of the Session or Journey context.")
    provenance_ids: List[str] = Field(default_factory=list, description="IDs of Neuronal Packets (Nodes) this thought is derived from.")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Active Inference States
    precision: float = Field(default=1.0, ge=0.0, le=5.0, description="Inverse variance (Confidence).")
    entropy: float = Field(default=0.0, ge=0.0, description="Uncertainty measure.")
    
    # Global Workspace Dynamics
    resonance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Activation level in GW.")
    is_active: bool = Field(default=True, description="Whether the particle is currently held in working memory.")
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('precision')
    @classmethod
    def validate_precision(cls, v):
        """Ensure precision is within reasonable bounds (0.0 to 5.0)."""
        return max(0.0, min(5.0, v))

    def decay(self, rate: float = 0.1) -> None:
        """Apply temporal decay to resonance."""
        self.resonance_score = max(0.0, self.resonance_score * (1.0 - rate))
        if self.resonance_score < 0.05:
            self.is_active = False

    def reinforce(self, amount: float = 0.2) -> None:
        """Boost resonance (Attention)."""
        self.resonance_score = min(1.0, self.resonance_score + amount)
        self.is_active = True

    def to_graphiti_node(self) -> Dict[str, Any]:
        """Convert to Graphiti-compatible node dictionary."""
        return {
            "type": "MetacognitiveParticle",
            "name": self.content[:50] + "..." if len(self.content) > 50 else self.content,
            "summary": self.content,
            "created_at": self.timestamp.isoformat(),
            "valid_at": self.timestamp.isoformat(),
            "res_score": self.resonance_score,
            "precision": self.precision,
            "source": self.source_agent,
            "context_id": self.context_id,
            "provenance": self.provenance_ids
        }

    def calculate_free_energy(self) -> float:
        """
        Calculate Variational Free Energy (VFE).
        F = Complexity - Accuracy
        Currently a placeholder using Entropy and Precision as proxies.
        """
        # Complexity ≈ Entropy (Divergence from prior)
        # Accuracy ≈ Precision (Confidence in prediction)
        # High Precision -> Low VFE (Good)
        # High Entropy -> High VFE (Bad/Uncertain)
        return self.entropy - (self.precision / 5.0)
