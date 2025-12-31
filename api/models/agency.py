"""
Agency Models for Sense of Agency Detection
Feature: 038-thoughtseeds-framework (Priority 3)

Based on Metacognitive Particles paper:
- Sense of agency = D_KL[p(μ,a) || p(μ)p(a)]
- High KL = strong coupling between internal states and actions = AGENCY
- Zero KL = statistical independence = NO AGENCY (mere observation)
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgencyAttributionType(str, Enum):
    """Attribution type for an action's causal origin."""
    SELF = "self"           # Action caused by internal states (high agency)
    EXTERNAL = "external"   # Action caused by external factors (low agency)
    AMBIGUOUS = "ambiguous" # Unclear causal attribution


class AgencyThresholds(BaseModel):
    """
    Configuration thresholds for agency classification.
    
    Based on KL divergence interpretation:
    - KL > high_agency_threshold → self-caused
    - KL < low_agency_threshold → externally-caused
    - Otherwise → ambiguous
    """
    high_agency_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="KL divergence above this indicates strong self-agency"
    )
    low_agency_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="KL divergence below this indicates external causation"
    )
    confidence_decay: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Rate at which confidence decays in ambiguous zone"
    )


class AgencyAttribution(BaseModel):
    """
    Result of agency detection for an action.
    
    Provides:
    - score: Raw KL divergence (0 = no agency, higher = more agency)
    - attribution: Categorical classification (self/external/ambiguous)
    - confidence: Certainty of the attribution (0-1)
    """
    score: float = Field(
        ge=0.0,
        description="KL divergence between joint and product of marginals"
    )
    attribution: AgencyAttributionType = Field(
        description="Categorical classification of action's causal origin"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Certainty of the attribution classification"
    )
    internal_entropy: Optional[float] = Field(
        default=None,
        description="Entropy of internal state distribution H(μ)"
    )
    active_entropy: Optional[float] = Field(
        default=None,
        description="Entropy of active state distribution H(a)"
    )
    joint_entropy: Optional[float] = Field(
        default=None,
        description="Joint entropy H(μ,a)"
    )
    mutual_information: Optional[float] = Field(
        default=None,
        description="Mutual information I(μ;a) = H(μ) + H(a) - H(μ,a)"
    )


class AgencyWeightedEFE(BaseModel):
    """
    EFE calculation weighted by agency score.
    
    Higher agency → more confidence in predicted outcomes
    Lower agency → increased uncertainty about action effects
    """
    base_efe: float = Field(
        description="Original EFE score before agency weighting"
    )
    agency_score: float = Field(
        ge=0.0,
        description="Agency score from KL divergence calculation"
    )
    weighted_efe: float = Field(
        description="EFE adjusted by agency confidence"
    )
    agency_modifier: float = Field(
        description="Multiplicative factor applied to EFE"
    )
    attribution: AgencyAttributionType = Field(
        description="Agency attribution for context"
    )


# Default thresholds instance
DEFAULT_AGENCY_THRESHOLDS = AgencyThresholds()
