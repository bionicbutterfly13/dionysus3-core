"""
Metacognition REST API Router

Feature: 040-metacognitive-particles
Based on: Sandved-Smith & Da Costa (2024), Seragnoli et al. (2025)

Endpoints:
- POST /classify - Classify cognitive process into particle type
- POST /mental-action - Execute mental action on target agent
- GET /agency/{agent_id} - Get sense of agency strength
- POST /epistemic-gain/check - Check for epistemic gain event
- GET /monitoring/{agent_id} - Get cognitive assessment
- POST /control - Apply control action

AUTHOR: Mani Saint-Victor, MD
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.models.metacognitive_particle import (
    ClassificationResult,
    MentalActionType,
    ParticleType,
)
from api.models.belief_state import BeliefStateInput
from api.models.markov_blanket import MarkovBlanketPartition

logger = logging.getLogger("dionysus.routers.metacognition")


# =============================================================================
# Agent Hierarchy Registry (FR-007)
# =============================================================================
# Tracks agent levels for hierarchy validation. Higher-level agents cannot
# target lower-level agents (e.g., level 2 cannot modulate level 1).

_agent_level_registry: Dict[str, int] = {}


def get_agent_level(agent_id: str) -> int:
    """Get the hierarchical level of an agent (default: 1 for base level)."""
    return _agent_level_registry.get(agent_id, 1)


def set_agent_level(agent_id: str, level: int) -> None:
    """Set the hierarchical level of an agent."""
    _agent_level_registry[agent_id] = level


def validate_hierarchy(source_agent: str, target_agent: str) -> None:
    """
    Validate that source_agent can target target_agent.

    FR-007: Higher-level particles cannot target lower-level particles.
    Mental actions must flow DOWN the hierarchy (higher source → lower target).

    Args:
        source_agent: Agent executing the mental action
        target_agent: Agent being modulated

    Raises:
        PermissionError: If source cannot target destination (403 error)
    """
    source_level = get_agent_level(source_agent)
    target_level = get_agent_level(target_agent)

    if source_level <= target_level:
        raise PermissionError(
            f"Hierarchy violation: Agent '{source_agent}' (level {source_level}) "
            f"cannot modulate '{target_agent}' (level {target_level}). "
            f"Source must be at a higher level than target."
        )

router = APIRouter(prefix="/api/v1/metacognition", tags=["metacognition"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ClassifyRequest(BaseModel):
    """Request model for particle classification."""
    agent_id: str = Field(..., description="Agent identifier")
    blanket: MarkovBlanketPartition = Field(..., description="Markov blanket structure")


class MentalActionRequest(BaseModel):
    """Request model for mental action execution."""
    source_agent: str = Field(..., description="Agent executing the action")
    target_agent: str = Field(..., description="Agent being modulated")
    action_type: MentalActionType = Field(..., description="Type of modulation")
    modulation: Dict[str, Any] = Field(..., description="Action-specific parameters")


class MentalActionResult(BaseModel):
    """Response model for mental action execution."""
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    success: bool
    prior_state: Dict[str, Any]
    new_state: Dict[str, Any]
    modulations_applied: List[str]
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class AgencyResult(BaseModel):
    """Response model for agency strength query."""
    agent_id: str
    agency_strength: float = Field(ge=0.0, description="KL divergence value")
    has_agency: bool
    particle_type: Optional[ParticleType] = None
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class EpistemicGainCheckRequest(BaseModel):
    """Request model for epistemic gain check."""
    particle_id: str = Field(..., description="Particle UUID")
    prior_belief: BeliefStateInput = Field(..., description="Prior belief state")
    posterior_belief: BeliefStateInput = Field(..., description="Posterior belief state")
    threshold: float = Field(default=0.3, description="Minimum uncertainty reduction")


class EpistemicGainEvent(BaseModel):
    """Model for an epistemic gain event."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    magnitude: float = Field(ge=0.0, le=1.0)
    prior_entropy: float
    posterior_entropy: float
    noetic_quality: bool = Field(description="True if certainty without proportional evidence")
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class EpistemicGainCheckResult(BaseModel):
    """Response model for epistemic gain check."""
    gain_detected: bool
    event: Optional[EpistemicGainEvent] = None


class CognitiveAssessment(BaseModel):
    """Model for cognitive assessment from monitoring."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    progress: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    prediction_error: float
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


class ControlRequest(BaseModel):
    """Request model for control action."""
    assessment: CognitiveAssessment


class ControlResult(BaseModel):
    """Response model for control action."""
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)
    rationale: str = Field(default="")


# =============================================================================
# Endpoints - Phase 3 (US1: Classification)
# =============================================================================


@router.post(
    "/classify",
    response_model=ClassificationResult,
    summary="Classify a cognitive process into particle type",
    description="Analyzes Markov blanket structure to determine particle type."
)
async def classify_particle(request: ClassifyRequest) -> ClassificationResult:
    """
    Classify a cognitive process into particle type.

    Analyzes the Markov blanket structure to determine:
    - COGNITIVE: Basic beliefs about external
    - PASSIVE_METACOGNITIVE: Beliefs about beliefs, no direct control
    - ACTIVE_METACOGNITIVE: Has internal blanket with active paths
    - STRANGE_METACOGNITIVE: Actions inferred via sensory
    - NESTED_N_LEVEL: Multiple internal Markov blankets
    """
    # Import service lazily to avoid circular imports
    from api.services.particle_classifier import ParticleClassifier

    classifier = ParticleClassifier()
    try:
        particle_type, confidence, level, has_agency = await classifier.classify(
            agent_id=request.agent_id,
            blanket=request.blanket
        )
        return ClassificationResult(
            particle_id=str(uuid4()),
            particle_type=particle_type,
            confidence=confidence,
            level=level,
            has_agency=has_agency
        )
    except Exception as e:
        logger.error(f"Classification failed for agent {request.agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Classification failed: {str(e)}"
        )


# =============================================================================
# Endpoints - Phase 4 (US2: Mental Actions)
# =============================================================================


@router.post(
    "/mental-action",
    response_model=MentalActionResult,
    summary="Execute a mental action on target agent",
    description="Higher-level mental action modulating lower-level precision."
)
async def execute_mental_action(request: MentalActionRequest) -> MentalActionResult:
    """
    Execute a mental action that modulates lower-level parameters.

    Supports:
    - precision_delta: Adjust precision by delta amount
    - set_precision: Set precision to absolute value
    - focus_target: Direct attentional spotlight
    - spotlight_precision: Set spotlight precision

    FR-007: Validates that source agent is at a higher level than target.
    """
    from api.agents.metacognition_agent import MetacognitionAgent

    # FR-007: Validate hierarchy before executing action
    try:
        validate_hierarchy(request.source_agent, request.target_agent)
    except PermissionError as e:
        logger.warning(f"Hierarchy validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    async with MetacognitionAgent() as agent:
        try:
            result = await agent.mental_action(
                target_agent=request.target_agent,
                modulation=request.modulation
            )

            # T030: Log successful mental action execution
            logger.info(
                f"Mental action executed: {request.source_agent} -> {request.target_agent}, "
                f"type={request.action_type.value}, success={result.get('success', False)}, "
                f"modulations={result.get('modulations_applied', [])}"
            )

            return MentalActionResult(
                success=result.get("success", False),
                prior_state=result.get("prior_state", {}),
                new_state=result.get("new_state", {}),
                modulations_applied=result.get("modulations_applied", [])
            )
        except PermissionError as e:
            logger.warning(f"Mental action permission denied: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Hierarchy violation: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Mental action failed: {request.source_agent} -> {request.target_agent}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mental action failed: {str(e)}"
            )


# =============================================================================
# Endpoints - Phase 5 (US3: Agency)
# =============================================================================


@router.get(
    "/agency/{agent_id}",
    response_model=AgencyResult,
    summary="Get sense of agency strength for an agent",
    description="Computes KL divergence D_KL[Q(μ,a) | Q(μ)Q(a)] as agency measure."
)
async def get_agency_strength(agent_id: str) -> AgencyResult:
    """
    Compute sense of agency strength.

    Returns KL divergence between joint and independent distributions.
    - 0.0 = no agency (internal and active paths are independent)
    - Higher values = stronger sense of agency
    """
    from api.services.agency_service import AgencyService

    service = AgencyService()
    try:
        strength, has_agency, particle_type = await service.get_agent_agency(agent_id)
        return AgencyResult(
            agent_id=agent_id,
            agency_strength=strength,
            has_agency=has_agency,
            particle_type=particle_type
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    except Exception as e:
        logger.error(f"Agency computation failed for {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agency computation failed: {str(e)}"
        )


# =============================================================================
# Endpoints - Phase 6 (US4: Epistemic Gain)
# =============================================================================


@router.post(
    "/epistemic-gain/check",
    response_model=EpistemicGainCheckResult,
    summary="Check for epistemic gain event",
    description="Compares prior and posterior beliefs to detect 'Aha!' moments."
)
async def check_epistemic_gain(request: EpistemicGainCheckRequest) -> EpistemicGainCheckResult:
    """
    Check for significant learning ("Aha!" moment).

    Compares entropy reduction between prior and posterior beliefs.
    Returns event if reduction exceeds threshold.
    """
    from api.services.epistemic_gain_service import EpistemicGainService

    service = EpistemicGainService()
    try:
        prior = request.prior_belief.to_belief_state()
        posterior = request.posterior_belief.to_belief_state()

        event = await service.check_gain(
            prior_belief=prior,
            posterior_belief=posterior,
            threshold=request.threshold
        )

        if event:
            return EpistemicGainCheckResult(
                gain_detected=True,
                event=EpistemicGainEvent(
                    id=event.id,
                    magnitude=event.magnitude,
                    prior_entropy=event.prior_entropy,
                    posterior_entropy=event.posterior_entropy,
                    noetic_quality=event.noetic_quality
                )
            )
        return EpistemicGainCheckResult(gain_detected=False)
    except Exception as e:
        logger.error(f"Epistemic gain check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Epistemic gain check failed: {str(e)}"
        )


# =============================================================================
# Endpoints - Phase 8 (US6: Procedural Metacognition)
# =============================================================================


@router.get(
    "/monitoring/{agent_id}",
    response_model=CognitiveAssessment,
    summary="Get cognitive assessment for an agent",
    description="Non-invasive monitoring of cognitive state."
)
async def get_monitoring_assessment(agent_id: str) -> CognitiveAssessment:
    """
    Get cognitive assessment for monitoring.

    Returns progress, confidence, issues, and recommendations.
    """
    from api.services.procedural_metacognition import ProceduralMetacognition

    service = ProceduralMetacognition()
    try:
        assessment = await service.monitor(agent_id)
        return assessment
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    except Exception as e:
        logger.error(f"Monitoring failed for {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring failed: {str(e)}"
        )


@router.post(
    "/control",
    response_model=ControlResult,
    summary="Apply control action based on assessment",
    description="Takes cognitive assessment and returns recommended mental actions."
)
async def apply_control_action(request: ControlRequest) -> ControlResult:
    """
    Apply control action based on cognitive assessment.

    Analyzes issues and recommends mental actions to regulate cognition.
    """
    from api.services.procedural_metacognition import ProceduralMetacognition

    service = ProceduralMetacognition()
    try:
        actions = await service.control(request.assessment)
        # Convert dataclass instances to dicts for Pydantic response
        from dataclasses import asdict
        action_dicts = [asdict(a) for a in actions]
        return ControlResult(
            recommended_actions=action_dicts,
            rationale=f"Generated {len(actions)} control actions based on assessment"
        )
    except Exception as e:
        logger.error(f"Control action failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Control action failed: {str(e)}"
        )
