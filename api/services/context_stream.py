"""
Context Stream Service - River Metaphor Flow Analysis
Feature: 027-river-metaphor

Analyzes information flow and detects 'turbulence' in reasoning.
"""

import logging
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from api.models.cognitive import FlowState
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)

class ContextFlow(BaseModel):
    state: FlowState
    density: float # Facts per episode
    turbulence: float # Variance/error proxy
    summary: str

class ContextStreamService:
    def __init__(self):
        self.history: List[ContextFlow] = []

    async def analyze_current_flow(self, project_id: str) -> ContextFlow:
        """
        Calculate flow state based on recent Graphiti activity.
        FR-002: Information Density and Turbulence Level.
        """
        graphiti = await get_graphiti_service()
        
        # 1. Fetch recent episodes for context
        results = await graphiti.search(f"Latest activity for project {project_id}", limit=10)
        edges = results.get("edges", [])
        
        # 2. Calculate Density
        # Simple proxy: number of factual edges retrieved divided by window size
        density = len(edges) / 10.0
        
        # 3. Calculate Turbulence
        # In this implementation, we check for 'contradiction' or 'failed' keywords in the facts
        turbulence = 0.0
        negative_markers = ["contradict", "fail", "error", "hallucination", "mismatch", "unclear"]
        
        for edge in edges:
            fact = str(edge.get("fact", "")).lower()
            if any(m in fact for m in negative_markers):
                turbulence += 0.2
        
        turbulence = min(1.0, turbulence)
        
        # 4. Map to FlowState
        if turbulence > 0.6:
            state = FlowState.TURBULENT
        elif density < 0.2:
            state = FlowState.EMERGING
        elif turbulence < 0.2 and density > 0.5:
            state = FlowState.STABLE
        elif density > 0.3:
            state = FlowState.FLOWING
        else:
            state = FlowState.CONVERGING
            
        flow = ContextFlow(
            state=state,
            density=density,
            turbulence=turbulence,
            summary=f"River is {state.value.upper()}. Density: {density:.2f}, Turbulence: {turbulence:.2f}"
        )
        
        self.history.append(flow)
        return flow

_context_stream_service: Optional[ContextStreamService] = None

def get_context_stream_service() -> ContextStreamService:
    global _context_stream_service
    if _context_stream_service is None:
        _context_stream_service = ContextStreamService()
    return _context_stream_service
