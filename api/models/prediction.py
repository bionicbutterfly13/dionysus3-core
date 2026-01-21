"""
Models for Self-Modeling Predictions.
Feature: 034-network-self-modeling
"""

from typing import Dict, Optional
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class PredictionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    predicted_state: Dict[str, float] = Field(..., description="Predicted W/T/H values")
    actual_state: Optional[Dict[str, float]] = None
    prediction_error: Optional[float] = None
    resolved_at: Optional[datetime] = None

class PredictionAccuracy(BaseModel):
    agent_id: str
    average_error: float
    sample_count: int
    window_start: datetime
    window_end: datetime
