"""
Resonance Detector Service.
Calculates cognitive resonance states using ULTRATHINK architectural synthesis.
"""

from typing import List, Optional
import logging
from datetime import datetime

from api.models.beautiful_loop import (
    ResonanceMode,
    ResonanceSignal,
    UnifiedRealityModel,
    BoundInference
)

logger = logging.getLogger(__name__)

class ResonanceDetector:
    """Detects and categorizes cognitive resonance for the Beautiful Loop."""

    def detect(
        self, 
        urm: UnifiedRealityModel, 
        cycle_id: Optional[str] = None
    ) -> ResonanceSignal:
        """
        Analyzes the Unified Reality Model to determine the resonance signal.
        
        Deep Reasoning Chain:
        1. Maximum Surprisal: Pulled from uncertainty reduction of bound inferences.
        2. Average Coherence: Internal consistency of the bound world model.
        3. State Assignment: Categorical mapping to ResonanceMode.
        """
        inferences = urm.bound_inferences
        
        if not inferences:
            # Darkness state: High discovery urgency
            return ResonanceSignal(
                mode=ResonanceMode.TURBULENT,
                resonance_score=0.2,
                surprisal=1.0,
                coherence=urm.coherence_score,
                discovery_urgency=0.9,
                cycle_id=cycle_id
            )

        # 1. Extract Surprisal (1 - mean_uncertainty_reduction)
        # Note: Uncertainty reduction is capped at 1.0
        avg_reduction = sum(inf.uncertainty_reduction for inf in inferences) / len(inferences)
        surprisal = max(0.0, min(1.0, 1.0 - avg_reduction))
        
        # 2. Extract Coherence
        coherence = urm.coherence_score
        
        # 3. Calculate Resonance Score (R = Coherence * (1 - Surprisal))
        resonance_score = coherence * (1.0 - surprisal)
        
        # 4. Mode Selection
        if surprisal > 0.7:
            mode = ResonanceMode.DISSONANT  # High surprisal = CRISIS
        elif coherence < 0.4:
            mode = ResonanceMode.TURBULENT  # Inconsistent model = UNCERTAINTY
        elif resonance_score > 0.8:
            mode = ResonanceMode.LUMINOUS   # High coherence + low surprise = CLARITY
        else:
            mode = ResonanceMode.STABLE     # DEFAULT exploitation
            
        # 5. Discovery Urgency
        discovery_urgency = 0.0
        if mode == ResonanceMode.DISSONANT:
            discovery_urgency = surprisal # Force discovery on high dissonance
        elif mode == ResonanceMode.TURBULENT:
            discovery_urgency = 1.0 - coherence # Seek clarity
            
        signal = ResonanceSignal(
            mode=mode,
            resonance_score=resonance_score,
            surprisal=surprisal,
            coherence=coherence,
            discovery_urgency=discovery_urgency,
            cycle_id=cycle_id
        )
        
        logger.info(f"Resonance Detected: {mode.value} (Score: {resonance_score:.2f}, Surprisal: {surprisal:.2f})")
        return signal

_detector: Optional[ResonanceDetector] = None

def get_resonance_detector() -> ResonanceDetector:
    global _detector
    if _detector is None:
        _detector = ResonanceDetector()
    return _detector
