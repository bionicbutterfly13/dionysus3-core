import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("dionysus.services.arbitration")

class ArbitrationResult(BaseModel):
    use_s2: bool
    reason: str
    trust_score: float
    risk_aversion: float

class ArbitrationService:
    """
    Implements SOFAI (Slow and Fast AI) arbitration logic.
    Determines whether to accept a System 1 (Fast) proposal or 
    invoke a System 2 (Slow) reasoning process.
    """

    def __init__(self, default_risk_aversion: float = 0.5):
        self.risk_aversion = default_risk_aversion
        # Reflection bias is updated by the ReflectionService (Algorithm 2)
        # Persistent bias towards S2 based on counterfactual history
        self.reflection_bias = 0.0 

    def arbitrate(
        self, 
        s1_confidence: float, 
        success_rate: float, 
        current_energy: float,
        complexity_estimate: float = 0.5
    ) -> ArbitrationResult:
        """
        Decision matrix for S1 vs S2 switching.
        
        Args:
            s1_confidence: The confidence score from the fast pass (0-1).
            success_rate: Historical success rate for this class of task.
            current_energy: Available resource budget.
            complexity_estimate: Estimated cognitive load of the task.
        """
        # 1. Calculate Trust in System 1 (Algorithm 1, Line 1)
        trust_s1 = min(s1_confidence, success_rate)
        
        # 2. Check for "Resource Exhaustion" (Safety Check)
        if current_energy < 0.2:
            return ArbitrationResult(
                use_s2=False,
                reason="INSUFFICIENT_ENERGY",
                trust_score=trust_s1,
                risk_aversion=self.risk_aversion
            )

        # 3. Decision Logic (Algorithm 1, Line 2 & 10)
        # We trigger S2 if trust is low OR if the potential gain exceeds the cost
        # The reflection_bias represents the "Architecture Hunger"
        
        trigger_reasons = []
        if trust_s1 <= self.risk_aversion:
            trigger_reasons.append(f"LOW_TRUST ({trust_s1:.2f} <= {self.risk_aversion:.2f})")
            
        # Simplification of EFE gap: complexity - reflection_bias
        # High complexity or high reflection (history of S2 superiority) triggers S2
        if (complexity_estimate - self.reflection_bias) > 0.7:
             trigger_reasons.append("HIGH_COMPLEXITY_OR_BIAS")

        if trigger_reasons:
            return ArbitrationResult(
                use_s2=True,
                reason=" | ".join(trigger_reasons),
                trust_score=trust_s1,
                risk_aversion=self.risk_aversion
            )

        return ArbitrationResult(
            use_s2=False,
            reason="S1_SUFFICIENT",
            trust_score=trust_s1,
            risk_aversion=self.risk_aversion
        )

# Global singleton
_service = None

def get_arbitration_service() -> ArbitrationService:
    global _service
    if _service is None:
        _service = ArbitrationService()
    return _service
