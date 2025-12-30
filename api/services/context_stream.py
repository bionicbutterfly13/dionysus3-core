"""
Context Stream Service - River Metaphor Flow Analysis
Feature: 027-river-metaphor

Analyzes information flow and detects 'turbulence' in reasoning.
Upgraded with Neural Field Metrics (Feature 037).
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
    compression: float = 1.0 # tokens_in / tokens_out
    resonance: float = 0.5 # semantic alignment with goal
    summary: str

class ContextStreamService:
    def __init__(self):
        self.history: List[ContextFlow] = []

    def calculate_compression(self, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate compression ratio (tokens_in / tokens_out).
        High ratio (> 1.0) means concise summary/high info gain.
        """
        if tokens_out == 0:
            return 1.0
        return float(tokens_in) / float(tokens_out)

    async def calculate_resonance(self, goal_text: str, action_output: str) -> float:
        """
        Calculate semantic resonance (similarity) using EmbeddingService.
        """
        from api.services.embedding import get_embedding_service
        try:
            embed_svc = get_embedding_service()
            return await embed_svc.calculate_similarity(goal_text, action_output)
        except Exception as e:
            logger.warning(f"Resonance calculation failed: {e}")
            return 0.5

    def map_to_flow_state(
        self, 
        density: float, 
        turbulence: float, 
        compression: float, 
        resonance: float
    ) -> ContextFlow:
        """Maps metrics to a FlowState."""
        
        if turbulence > 0.6:
            state = FlowState.TURBULENT
        elif resonance < 0.3:
            state = FlowState.DRIFTING
        elif compression < 0.2 and density > 0.5:
            state = FlowState.STAGNANT
        elif resonance > 0.7 and turbulence < 0.2 and density > 0.5:
            state = FlowState.STABLE
        elif density > 0.3:
            state = FlowState.FLOWING
        elif density < 0.2:
            state = FlowState.EMERGING
        else:
            state = FlowState.CONVERGING
            
        return ContextFlow(
            state=state,
            density=density,
            turbulence=turbulence,
            compression=compression,
            resonance=resonance,
            summary=f"River is {state.value.upper()}. Comp: {compression:.2f}, Res: {resonance:.2f}"
        )

    async def analyze_current_flow(
        self, 
        project_id: str, 
        tokens_in: int = 0, 
        tokens_out: int = 0,
        goal_text: Optional[str] = None,
        last_output: Optional[str] = None
    ) -> ContextFlow:
        """
        Calculate flow state based on recent Graphiti activity and neural metrics.
        """
        graphiti = await get_graphiti_service()
        
        # 1. Fetch recent episodes for context
        results = await graphiti.search(f"Latest activity for project {project_id}", limit=10)
        edges = results.get("edges", [])
        
        # 2. Calculate Density
        density = len(edges) / 10.0
        
        # 3. Calculate Turbulence
        turbulence = 0.0
        negative_markers = ["contradict", "fail", "error", "hallucination", "mismatch", "unclear"]
        for edge in edges:
            fact = str(edge.get("fact", "")).lower()
            if any(m in fact for m in negative_markers):
                turbulence += 0.2
        turbulence = min(1.0, turbulence)
        
        # 4. Neural Metrics
        compression = self.calculate_compression(tokens_in, tokens_out)
        resonance = 0.5
        if goal_text and last_output:
            resonance = await self.calculate_resonance(goal_text, last_output)
            
        flow = self.map_to_flow_state(density, turbulence, compression, resonance)
        self.history.append(flow)
        return flow

_context_stream_service: Optional[ContextStreamService] = None

def get_context_stream_service() -> ContextStreamService:
    global _context_stream_service
    if _context_stream_service is None:
        _context_stream_service = ContextStreamService()
    return _context_stream_service