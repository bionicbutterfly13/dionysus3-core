"""
Belief Journey API Router

REST API endpoints for IAS belief transformation tracking.
Feature: 036-belief-avatar-system
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.models.belief_journey import (
    BeliefJourney,
    ExperimentOutcome,
    IASLesson,
)
from api.services.belief_tracking_service import get_belief_tracking_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/belief-journey", tags=["belief-journey"])


# =============================================================================
# Request Models
# =============================================================================


class CreateJourneyRequest(BaseModel):
    """Request to create a new belief journey."""
    participant_id: Optional[str] = Field(None, description="External participant identifier")


class AdvanceLessonRequest(BaseModel):
    """Request to advance to a lesson."""
    lesson: IASLesson = Field(..., description="Lesson to mark as completed")


class IdentifyLimitingBeliefRequest(BaseModel):
    """Request to identify a limiting belief."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    content: str = Field(..., description="The belief statement")
    pattern_name: Optional[str] = Field(None, description="Named pattern")
    origin_memory: Optional[str] = Field(None, description="Where belief came from")
    self_talk: Optional[List[str]] = Field(default_factory=list)
    mental_blocks: Optional[List[str]] = Field(default_factory=list)
    self_sabotage_behaviors: Optional[List[str]] = Field(default_factory=list)
    protects_from: Optional[str] = Field(None)


class MapBeliefRequest(BaseModel):
    """Request to map belief to behaviors."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    self_talk: List[str] = Field(..., description="Internal dialogue")
    mental_blocks: List[str] = Field(..., description="Created blocks")
    self_sabotage_behaviors: List[str] = Field(..., description="Driven behaviors")
    protects_from: str = Field(..., description="Emotional protection")


class AddEvidenceRequest(BaseModel):
    """Request to add evidence for/against belief."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    evidence: str = Field(..., description="Evidence statement")
    evidence_type: str = Field(default="for", description="'for' or 'against'")


class DissolveBeliefRequest(BaseModel):
    """Request to dissolve a limiting belief."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    replaced_by_id: Optional[UUID] = Field(None, description="Empowering belief that replaced this")


class ProposeEmpoweringBeliefRequest(BaseModel):
    """Request to propose an empowering belief."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    content: str = Field(..., description="The new belief statement")
    bridge_version: Optional[str] = Field(None, description="Softer version for testing")
    replaces_belief_id: Optional[UUID] = Field(None, description="Limiting belief this replaces")


class StrengthenBeliefRequest(BaseModel):
    """Request to strengthen an empowering belief."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    evidence: str = Field(..., description="Supporting evidence")
    embodiment_increase: float = Field(default=0.1, ge=0.0, le=1.0)


class AnchorBeliefRequest(BaseModel):
    """Request to anchor belief to habit."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    habit_stack: str = Field(..., description="Daily habit to stack with")
    checklist_items: List[str] = Field(..., description="Behavior checklist")


class DesignExperimentRequest(BaseModel):
    """Request to design an experiment."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    limiting_belief_id: Optional[UUID] = Field(None)
    empowering_belief_id: Optional[UUID] = Field(None)
    hypothesis: str = Field(..., description="What we expect to find")
    action_to_take: str = Field(..., description="Action to try")
    context: str = Field(default="low", description="Stakes: low/mid/high")


class RecordExperimentRequest(BaseModel):
    """Request to record experiment result."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    outcome: ExperimentOutcome = Field(..., description="Result type")
    actual_result: str = Field(..., description="What happened")
    emotional_response: Optional[str] = Field(None)
    belief_shift_observed: Optional[str] = Field(None)


class IdentifyLoopRequest(BaseModel):
    """Request to identify a replay loop."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    trigger_situation: str = Field(..., description="What triggers the replay")
    story_text: str = Field(..., description="The story behind the replay")
    emotion: str = Field(..., description="Primary emotion")
    fear_underneath: str = Field(..., description="The driving fear")
    pattern_name: Optional[str] = Field(None)
    fed_by_belief_id: Optional[UUID] = Field(None)


class InterruptLoopRequest(BaseModel):
    """Request to interrupt a replay loop."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    compassionate_reflection: str = Field(..., description="Self-compassion statement")


class ResolveLoopRequest(BaseModel):
    """Request to resolve a replay loop."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    lesson_found: str = Field(..., description="Genuine lesson extracted")
    comfort_offered: str = Field(..., description="Self-comfort statement")
    next_step_taken: Optional[str] = Field(None)
    time_to_resolution_minutes: Optional[float] = Field(None)


class CaptureMosaeicRequest(BaseModel):
    """Request to capture MOSAEIC observation."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    high_pressure_context: str = Field(..., description="The situation")
    sensations: Optional[List[str]] = Field(default_factory=list)
    actions: Optional[List[str]] = Field(default_factory=list)
    emotions: Optional[List[str]] = Field(default_factory=list)
    impulses: Optional[List[str]] = Field(default_factory=list)
    cognitions: Optional[List[str]] = Field(default_factory=list)
    narrative_identified: Optional[str] = Field(None)
    connects_to_belief_id: Optional[UUID] = Field(None)


class AddVisionRequest(BaseModel):
    """Request to add a vision element."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    description: str = Field(..., description="Vision described")
    category: str = Field(default="general")
    values_aligned: Optional[List[str]] = Field(default_factory=list)
    first_step: Optional[str] = Field(None)
    requires_dissolution_of: Optional[List[UUID]] = Field(default_factory=list)


class CreateCircleRequest(BaseModel):
    """Request to create support circle."""
    journey_id: UUID = Field(..., description="Parent journey ID")


class AddMemberRequest(BaseModel):
    """Request to add circle member."""
    journey_id: UUID = Field(..., description="Parent journey ID")
    role: str = Field(..., description="mentor/peer/mentee")
    name: Optional[str] = Field(None)
    check_in_frequency: str = Field(default="monthly")
    value_provided: Optional[str] = Field(None)


# =============================================================================
# Response Models
# =============================================================================


class SuccessResponse(BaseModel):
    """Generic success response wrapper."""
    success: bool = True
    data: dict


class MetricsData(BaseModel):
    """Journey metrics data."""
    journey_id: str
    current_phase: str
    current_lesson: str
    lessons_completed: int
    limiting_beliefs: dict
    empowering_beliefs: dict
    experiments: dict
    replay_loops: dict
    support_circle: dict


class MetricsResponse(BaseModel):
    """Metrics endpoint response."""
    success: bool = True
    data: MetricsData


# =============================================================================
# Helper Functions
# =============================================================================


async def get_journey_or_404(journey_id: UUID) -> BeliefJourney:
    """Get journey by ID or raise 404."""
    service = get_belief_tracking_service()
    journey = await service.get_journey(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")
    return journey


def get_belief_or_400(journey: BeliefJourney, belief_id: UUID, belief_type: str = "limiting"):
    """Get belief from journey or raise 400."""
    if belief_type == "limiting":
        belief = next((b for b in journey.limiting_beliefs if b.id == belief_id), None)
    else:
        belief = next((b for b in journey.empowering_beliefs if b.id == belief_id), None)

    if not belief:
        raise HTTPException(
            status_code=400,
            detail=f"Belief {belief_id} not found in journey {journey.id}"
        )
    return belief


# =============================================================================
# Health Endpoint
# =============================================================================


@router.get("/health")
async def health_check():
    """Health check for belief journey router."""
    service = get_belief_tracking_service()
    ingestion_health = service.get_ingestion_health()
    
    # Status is degraded if ingestion is failing
    status = "healthy" if ingestion_health["healthy"] else "degraded"
    
    return {
        "status": status,
        "service": "belief-journey",
        "journeys_in_memory": len(service._journeys),
        "ingestion": ingestion_health
    }


# =============================================================================
# Journey Endpoints (User Story 1)
# =============================================================================


@router.post("/journey/create", response_model=SuccessResponse)
async def create_journey(request: CreateJourneyRequest):
    """Create a new belief journey for a participant."""
    service = get_belief_tracking_service()
    journey = await service.create_journey(participant_id=request.participant_id)
    return SuccessResponse(
        data={
            "id": str(journey.id),
            "participant_id": journey.participant_id,
            "current_phase": journey.current_phase.value,
            "current_lesson": journey.current_lesson.value
        }
    )


@router.get("/journey/{journey_id}", response_model=SuccessResponse)
async def get_journey(journey_id: UUID):
    """Get a journey by ID."""
    journey = await get_journey_or_404(journey_id)
    return SuccessResponse(
        data={
            "id": str(journey.id),
            "participant_id": journey.participant_id,
            "current_phase": journey.current_phase.value,
            "current_lesson": journey.current_lesson.value,
            "lessons_completed": [l.value for l in journey.lessons_completed],
            "limiting_beliefs_count": len(journey.limiting_beliefs),
            "empowering_beliefs_count": len(journey.empowering_beliefs),
            "experiments_count": len(journey.experiments),
            "replay_loops_count": len(journey.replay_loops),
            "started_at": journey.started_at.isoformat(),
            "last_activity_at": journey.last_activity_at.isoformat()
        }
    )


@router.post("/journey/{journey_id}/advance", response_model=SuccessResponse)
async def advance_lesson(journey_id: UUID, request: AdvanceLessonRequest):
    """Advance journey to the next lesson."""
    service = get_belief_tracking_service()
    await get_journey_or_404(journey_id)  # Verify exists

    updated = await service.advance_lesson(journey_id, request.lesson)
    return SuccessResponse(
        data={
            "id": str(updated.id),
            "current_phase": updated.current_phase.value,
            "current_lesson": updated.current_lesson.value,
            "lessons_completed": [l.value for l in updated.lessons_completed]
        }
    )


# =============================================================================
# Limiting Belief Endpoints (User Story 1)
# =============================================================================


@router.post("/beliefs/limiting/identify", response_model=SuccessResponse)
async def identify_limiting_belief(request: IdentifyLimitingBeliefRequest):
    """Identify a new limiting belief."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    belief = await service.identify_limiting_belief(
        journey_id=request.journey_id,
        content=request.content,
        pattern_name=request.pattern_name,
        origin_memory=request.origin_memory,
        self_talk=request.self_talk or [],
        mental_blocks=request.mental_blocks or [],
        self_sabotage_behaviors=request.self_sabotage_behaviors or [],
        protects_from=request.protects_from
    )
    return SuccessResponse(
        data={
            "id": str(belief.id),
            "journey_id": str(belief.journey_id),
            "content": belief.content,
            "status": belief.status.value,
            "identified_at": belief.identified_at.isoformat()
        }
    )


@router.post("/beliefs/limiting/{belief_id}/map", response_model=SuccessResponse)
async def map_limiting_belief(belief_id: UUID, request: MapBeliefRequest):
    """Map a limiting belief to behaviors and blocks."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)
    get_belief_or_400(journey, belief_id, "limiting")  # Verify exists

    # Update belief mapping via service
    belief = await service.map_belief_to_behaviors(
        journey_id=request.journey_id,
        belief_id=belief_id,
        self_talk=request.self_talk,
        mental_blocks=request.mental_blocks,
        self_sabotage_behaviors=request.self_sabotage_behaviors,
        protects_from=request.protects_from
    )

    return SuccessResponse(
        data={
            "id": str(belief.id),
            "status": belief.status.value,
            "self_talk": belief.self_talk,
            "mental_blocks": belief.mental_blocks,
            "self_sabotage_behaviors": belief.self_sabotage_behaviors,
            "protects_from": belief.protects_from
        }
    )


@router.post("/beliefs/limiting/{belief_id}/evidence", response_model=SuccessResponse)
async def add_belief_evidence(belief_id: UUID, request: AddEvidenceRequest):
    """Add evidence for or against a limiting belief."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)
    get_belief_or_400(journey, belief_id, "limiting")  # Verify exists

    belief = await service.add_evidence_for_belief(
        journey_id=request.journey_id,
        belief_id=belief_id,
        evidence=request.evidence,
        evidence_type=request.evidence_type
    )

    return SuccessResponse(
        data={
            "id": str(belief.id),
            "evidence_for": belief.evidence_for,
            "evidence_against": belief.evidence_against
        }
    )


@router.post("/beliefs/limiting/{belief_id}/dissolve", response_model=SuccessResponse)
async def dissolve_limiting_belief(belief_id: UUID, request: DissolveBeliefRequest):
    """Dissolve a limiting belief."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)
    get_belief_or_400(journey, belief_id, "limiting")  # Verify exists

    dissolved = await service.dissolve_belief(
        journey_id=request.journey_id,
        belief_id=belief_id,
        replaced_by_id=request.replaced_by_id
    )
    return SuccessResponse(
        data={
            "id": str(dissolved.id),
            "status": dissolved.status.value,
            "dissolved_at": dissolved.dissolved_at.isoformat() if dissolved.dissolved_at else None,
            "replaced_by": str(dissolved.replaced_by) if dissolved.replaced_by else None
        }
    )


# =============================================================================
# Empowering Belief Endpoints (User Story 1)
# =============================================================================


@router.post("/beliefs/empowering/propose", response_model=SuccessResponse)
async def propose_empowering_belief(request: ProposeEmpoweringBeliefRequest):
    """Propose a new empowering belief."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    belief = await service.propose_empowering_belief(
        journey_id=request.journey_id,
        content=request.content,
        bridge_version=request.bridge_version,
        replaces_belief_id=request.replaces_belief_id
    )
    return SuccessResponse(
        data={
            "id": str(belief.id),
            "journey_id": str(belief.journey_id),
            "content": belief.content,
            "bridge_version": belief.bridge_version,
            "status": belief.status.value,
            "proposed_at": belief.proposed_at.isoformat()
        }
    )


@router.post("/beliefs/empowering/{belief_id}/strengthen", response_model=SuccessResponse)
async def strengthen_empowering_belief(belief_id: UUID, request: StrengthenBeliefRequest):
    """Strengthen an empowering belief with evidence."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)
    get_belief_or_400(journey, belief_id, "empowering")  # Verify exists

    strengthened = await service.strengthen_empowering_belief(
        journey_id=request.journey_id,
        belief_id=belief_id,
        evidence=request.evidence,
        embodiment_increase=request.embodiment_increase
    )
    return SuccessResponse(
        data={
            "id": str(strengthened.id),
            "embodiment_level": strengthened.embodiment_level,
            "status": strengthened.status.value,
            "evidence_collected": strengthened.evidence_collected
        }
    )


@router.post("/beliefs/empowering/{belief_id}/anchor", response_model=SuccessResponse)
async def anchor_empowering_belief(belief_id: UUID, request: AnchorBeliefRequest):
    """Anchor an empowering belief to a daily habit."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)
    get_belief_or_400(journey, belief_id, "empowering")  # Verify exists

    belief = await service.anchor_belief_to_habit(
        journey_id=request.journey_id,
        belief_id=belief_id,
        habit_stack=request.habit_stack,
        checklist_items=request.checklist_items
    )

    return SuccessResponse(
        data={
            "id": str(belief.id),
            "habit_stack": belief.habit_stack,
            "daily_checklist_items": belief.daily_checklist_items
        }
    )


# =============================================================================
# Experiment Endpoints (User Story 1 / Phase 9)
# =============================================================================


@router.post("/experiments/design", response_model=SuccessResponse)
async def design_experiment(request: DesignExperimentRequest):
    """Design a new belief experiment."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    experiment = await service.design_experiment(
        journey_id=request.journey_id,
        limiting_belief_id=request.limiting_belief_id,
        empowering_belief_id=request.empowering_belief_id,
        hypothesis=request.hypothesis,
        action_to_take=request.action_to_take,
        context=request.context
    )
    return SuccessResponse(
        data={
            "id": str(experiment.id),
            "journey_id": str(experiment.journey_id),
            "hypothesis": experiment.hypothesis,
            "action_taken": experiment.action_taken,
            "context": experiment.context,
            "designed_at": experiment.designed_at.isoformat()
        }
    )


@router.post("/experiments/{experiment_id}/record", response_model=SuccessResponse)
async def record_experiment_result(experiment_id: UUID, request: RecordExperimentRequest):
    """Record the result of an experiment."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)

    # Find experiment in journey
    experiment = next((e for e in journey.experiments if e.id == experiment_id), None)
    if not experiment:
        raise HTTPException(
            status_code=400,
            detail=f"Experiment {experiment_id} not found in journey {journey.id}"
        )

    recorded = await service.record_experiment_result(
        journey_id=request.journey_id,
        experiment_id=experiment_id,
        outcome=request.outcome,
        actual_result=request.actual_result,
        emotional_response=request.emotional_response,
        belief_shift_observed=request.belief_shift_observed
    )
    return SuccessResponse(
        data={
            "id": str(recorded.id),
            "outcome": recorded.outcome.value if recorded.outcome else None,
            "actual_result": recorded.actual_result,
            "executed_at": recorded.executed_at.isoformat() if recorded.executed_at else None
        }
    )


# =============================================================================
# Replay Loop Endpoints (User Story 5)
# =============================================================================


@router.post("/loops/identify", response_model=SuccessResponse)
async def identify_replay_loop(request: IdentifyLoopRequest):
    """Identify a new replay loop."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    loop = await service.identify_replay_loop(
        journey_id=request.journey_id,
        trigger_situation=request.trigger_situation,
        story_text=request.story_text,
        emotion=request.emotion,
        fear_underneath=request.fear_underneath,
        pattern_name=request.pattern_name,
        fed_by_belief_id=request.fed_by_belief_id
    )
    return SuccessResponse(
        data={
            "id": str(loop.id),
            "journey_id": str(loop.journey_id),
            "trigger_situation": loop.trigger_situation,
            "emotion": loop.emotion,
            "status": loop.status.value,
            "first_identified_at": loop.first_identified_at.isoformat()
        }
    )


@router.post("/loops/{loop_id}/interrupt", response_model=SuccessResponse)
async def interrupt_replay_loop(loop_id: UUID, request: InterruptLoopRequest):
    """Interrupt an active replay loop with compassion."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    interrupted = await service.interrupt_replay_loop(
        journey_id=request.journey_id,
        loop_id=loop_id,
        compassionate_reflection=request.compassionate_reflection
    )
    return SuccessResponse(
        data={
            "id": str(interrupted.id),
            "status": interrupted.status.value,
            "compassionate_reflection": interrupted.compassionate_reflection
        }
    )


@router.post("/loops/{loop_id}/resolve", response_model=SuccessResponse)
async def resolve_replay_loop(loop_id: UUID, request: ResolveLoopRequest):
    """Resolve a replay loop by extracting the lesson."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    resolved = await service.resolve_replay_loop(
        journey_id=request.journey_id,
        loop_id=loop_id,
        lesson_found=request.lesson_found,
        comfort_offered=request.comfort_offered,
        next_step_taken=request.next_step_taken,
        time_to_resolution_minutes=request.time_to_resolution_minutes
    )
    return SuccessResponse(
        data={
            "id": str(resolved.id),
            "status": resolved.status.value,
            "lesson_found": resolved.lesson_found,
            "resolved_at": resolved.resolved_at.isoformat() if resolved.resolved_at else None,
            "time_to_resolution_minutes": resolved.time_to_resolution_minutes
        }
    )


# =============================================================================
# MOSAEIC Capture Endpoint (Phase 9)
# =============================================================================


@router.post("/mosaeic/capture", response_model=SuccessResponse)
async def capture_mosaeic(request: CaptureMosaeicRequest):
    """Capture a MOSAEIC observation under pressure."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    capture = await service.capture_mosaeic(
        journey_id=request.journey_id,
        high_pressure_context=request.high_pressure_context,
        sensations=request.sensations or [],
        actions=request.actions or [],
        emotions=request.emotions or [],
        impulses=request.impulses or [],
        cognitions=request.cognitions or [],
        narrative_identified=request.narrative_identified,
        connects_to_belief_id=request.connects_to_belief_id
    )
    return SuccessResponse(
        data={
            "id": str(capture.id),
            "journey_id": str(capture.journey_id),
            "high_pressure_context": capture.high_pressure_context,
            "timestamp": capture.timestamp.isoformat()
        }
    )


# =============================================================================
# Vision Element Endpoint (Phase 9)
# =============================================================================


@router.post("/vision/add", response_model=SuccessResponse)
async def add_vision_element(request: AddVisionRequest):
    """Add a vision element to the journey."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    vision = await service.add_vision_element(
        journey_id=request.journey_id,
        description=request.description,
        category=request.category,
        values_aligned=request.values_aligned or [],
        first_step=request.first_step,
        requires_dissolution_of=request.requires_dissolution_of or []
    )
    return SuccessResponse(
        data={
            "id": str(vision.id),
            "journey_id": str(vision.journey_id),
            "description": vision.description,
            "category": vision.category,
            "status": vision.status
        }
    )


# =============================================================================
# Support Circle Endpoints (Phase 9)
# =============================================================================


@router.post("/support/circle/create", response_model=SuccessResponse)
async def create_support_circle(request: CreateCircleRequest):
    """Create a support circle for the journey."""
    service = get_belief_tracking_service()
    await get_journey_or_404(request.journey_id)  # Verify exists

    circle = await service.create_support_circle(journey_id=request.journey_id)
    return SuccessResponse(
        data={
            "id": str(circle.id),
            "journey_id": str(circle.journey_id),
            "total_members": circle.total_members,
            "created_at": circle.created_at.isoformat()
        }
    )


@router.post("/support/circle/{circle_id}/member", response_model=SuccessResponse)
async def add_circle_member(circle_id: UUID, request: AddMemberRequest):
    """Add a member to the support circle."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(request.journey_id)

    if not journey.support_circle or journey.support_circle.id != circle_id:
        raise HTTPException(
            status_code=400,
            detail=f"Support circle {circle_id} not found in journey {journey.id}"
        )

    circle = await service.add_circle_member(
        journey_id=request.journey_id,
        role=request.role,
        name=request.name,
        check_in_frequency=request.check_in_frequency,
        value_provided=request.value_provided
    )
    return SuccessResponse(
        data={
            "role": request.role,
            "name": request.name,
            "check_in_frequency": request.check_in_frequency,
            "circle_total_members": circle.total_members
        }
    )


# =============================================================================
# Metrics Endpoint (User Story 2)
# =============================================================================


@router.get("/journey/{journey_id}/metrics", response_model=MetricsResponse)
async def get_journey_metrics(journey_id: UUID):
    """Get comprehensive metrics for a journey."""
    service = get_belief_tracking_service()
    journey = await get_journey_or_404(journey_id)

    metrics = service.get_journey_metrics(journey_id)  # sync method

    return MetricsResponse(
        data=MetricsData(
            journey_id=str(journey.id),
            current_phase=journey.current_phase.value,
            current_lesson=journey.current_lesson.value,
            lessons_completed=len(journey.lessons_completed),
            limiting_beliefs={
                "total": metrics.get("limiting_beliefs", {}).get("total", 0),
                "dissolved": metrics.get("limiting_beliefs", {}).get("dissolved", 0),
                "dissolution_rate": metrics.get("limiting_beliefs", {}).get("dissolution_rate", 0.0)
            },
            empowering_beliefs={
                "total": metrics.get("empowering_beliefs", {}).get("total", 0),
                "embodied": metrics.get("empowering_beliefs", {}).get("embodied", 0),
                "embodiment_rate": metrics.get("empowering_beliefs", {}).get("embodiment_rate", 0.0)
            },
            experiments={
                "total": metrics.get("experiments", {}).get("total", 0),
                "success_rate": metrics.get("experiments", {}).get("success_rate", 0.0)
            },
            replay_loops={
                "total": metrics.get("replay_loops", {}).get("total", 0),
                "resolved": metrics.get("replay_loops", {}).get("resolved", 0),
                "avg_resolution_time_minutes": metrics.get("replay_loops", {}).get("avg_resolution_time_minutes", 0.0)
            },
            support_circle={
                "total_members": metrics.get("support_circle", {}).get("total_members", 0),
                "active_members": metrics.get("support_circle", {}).get("active_members", 0)
            }
        )
    )
