# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
MOSAEIC Dual Memory REST API Router
Feature: 008-mosaeic-memory
Tasks: T008

REST endpoints for MOSAEIC dual memory architecture:
- Episodic captures with 5 experiential dimensions
- Turning point detection and management
- Semantic beliefs with confidence scoring
- Maladaptive pattern tracking
- Verification encounters
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.models.mosaeic import (
    BeliefRewrite,
    CreateBeliefRequest,
    CreateCaptureRequest,
    FiveWindowCapture,
    MaladaptivePattern,
    PatternSeverity,
    TurningPoint,
    TurningPointTrigger,
    VerificationEncounter,
)

router = APIRouter(prefix="/api/mosaeic", tags=["mosaeic-memory"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CaptureListResponse(BaseModel):
    """List of captures response."""
    captures: list[dict]
    total: int


class TurningPointListResponse(BaseModel):
    """List of turning points response."""
    turning_points: list[dict]
    total: int


class BeliefListResponse(BaseModel):
    """List of beliefs response."""
    beliefs: list[dict]
    total: int


class PatternListResponse(BaseModel):
    """List of patterns response."""
    patterns: list[dict]
    total: int


class VerificationListResponse(BaseModel):
    """List of verifications response."""
    verifications: list[dict]
    total: int


class DecayPreviewResponse(BaseModel):
    """Preview of decay operations."""
    previews: list[dict]
    threshold_days: int


class StatisticsResponse(BaseModel):
    """Statistics response."""
    statistics: dict


class CreatePatternRequest(BaseModel):
    """Request to create a maladaptive pattern."""
    belief_content: str = Field(min_length=1)
    domain: str
    capture_id: str | None = None
    model_id: str | None = None
    initial_severity: float = Field(default=0.1, ge=0.0, le=1.0)


class CreateVerificationRequest(BaseModel):
    """Request to create a verification encounter."""
    belief_id: str
    prediction_id: str
    prediction_content: dict[str, Any]
    session_id: str


class ResolveVerificationRequest(BaseModel):
    """Request to resolve a verification."""
    observation: dict[str, Any]
    belief_activated: str = Field(default="new", pattern="^(old|new)$")
    prediction_error: float | None = Field(default=None, ge=0.0, le=1.0)


class MarkTurningPointRequest(BaseModel):
    """Request to mark a capture as turning point."""
    trigger_type: str = Field(pattern="^(high_emotion|surprise|consequence|manual)$")
    trigger_description: str | None = None
    vividness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    narrative_thread_id: str | None = None
    life_chapter_id: str | None = None


# =============================================================================
# Captures Endpoints
# =============================================================================


@router.post("/captures", response_model=dict)
async def create_capture(request: CreateCaptureRequest):
    """
    Create a new FiveWindowCapture.

    Automatically detects if capture is a turning point candidate
    based on emotional intensity.
    """
    from api.services.db import get_db_pool
    from api.services.turning_point_service import get_turning_point_service

    pool = await get_db_pool()

    # Create capture
    row = await pool.fetchrow(
        """
        INSERT INTO five_window_captures (
            session_id, mental, observation, senses, actions, emotions,
            emotional_intensity, context, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """,
        request.session_id,
        request.mental,
        request.observation,
        request.senses,
        request.actions,
        request.emotions,
        request.emotional_intensity,
        request.context,
        datetime.utcnow(),
    )

    capture = FiveWindowCapture(
        id=row["id"],
        session_id=row["session_id"],
        mental=row["mental"],
        observation=row["observation"],
        senses=row["senses"],
        actions=row["actions"],
        emotions=row["emotions"],
        emotional_intensity=row["emotional_intensity"],
        preserve_indefinitely=row["preserve_indefinitely"],
        context=row["context"],
        timestamp=row["timestamp"],
        created_at=row["created_at"],
    )

    # Check for turning point
    turning_point_service = get_turning_point_service()
    detection = await turning_point_service.detect_turning_point(capture)

    return {
        "id": str(capture.id),
        "session_id": str(capture.session_id),
        "emotional_intensity": capture.emotional_intensity,
        "is_turning_point_candidate": detection.is_turning_point,
        "preserve_indefinitely": capture.preserve_indefinitely,
        "created_at": capture.created_at.isoformat(),
    }


@router.get("/captures", response_model=CaptureListResponse)
async def list_captures(
    session_id: str | None = Query(None),
    preserve_indefinitely: bool | None = Query(None),
    min_intensity: float | None = Query(None, ge=0.0, le=10.0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List episodic captures with optional filters."""
    from api.services.db import get_db_pool

    pool = await get_db_pool()

    conditions = []
    params = []
    param_idx = 1

    if session_id:
        conditions.append(f"session_id = ${param_idx}")
        params.append(UUID(session_id))
        param_idx += 1

    if preserve_indefinitely is not None:
        conditions.append(f"preserve_indefinitely = ${param_idx}")
        params.append(preserve_indefinitely)
        param_idx += 1

    if min_intensity is not None:
        conditions.append(f"emotional_intensity >= ${param_idx}")
        params.append(min_intensity)
        param_idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT * FROM five_window_captures
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])

    rows = await pool.fetch(query, *params)

    count_query = f"SELECT COUNT(*) FROM five_window_captures {where_clause}"
    total = await pool.fetchval(count_query, *params[:-2]) if conditions else await pool.fetchval(count_query)

    captures = [
        {
            "id": str(row["id"]),
            "session_id": str(row["session_id"]),
            "emotional_intensity": row["emotional_intensity"],
            "preserve_indefinitely": row["preserve_indefinitely"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]

    return CaptureListResponse(captures=captures, total=total or 0)


@router.get("/captures/{capture_id}")
async def get_capture(capture_id: str):
    """Get a specific capture by ID."""
    from api.services.db import get_db_pool

    pool = await get_db_pool()

    row = await pool.fetchrow(
        "SELECT * FROM five_window_captures WHERE id = $1",
        UUID(capture_id),
    )

    if not row:
        raise HTTPException(status_code=404, detail="Capture not found")

    return {
        "id": str(row["id"]),
        "session_id": str(row["session_id"]),
        "mental": row["mental"],
        "observation": row["observation"],
        "senses": row["senses"],
        "actions": row["actions"],
        "emotions": row["emotions"],
        "emotional_intensity": row["emotional_intensity"],
        "preserve_indefinitely": row["preserve_indefinitely"],
        "context": row["context"],
        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
        "created_at": row["created_at"].isoformat(),
    }


@router.get("/captures/decay/preview", response_model=DecayPreviewResponse)
async def preview_decay(
    threshold_days: int = Query(180, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """Preview what would be decayed without applying."""
    from api.services.episodic_decay_service import get_episodic_decay_service

    service = get_episodic_decay_service()
    previews = await service.preview_decay(threshold_days=threshold_days, limit=limit)

    return DecayPreviewResponse(previews=previews, threshold_days=threshold_days)


@router.post("/captures/decay/apply")
async def apply_decay(threshold_days: int = Query(180, ge=1)):
    """Apply episodic decay to old captures."""
    from api.services.episodic_decay_service import get_episodic_decay_service

    service = get_episodic_decay_service()
    result = await service.apply_decay(threshold_days=threshold_days)

    return {
        "candidates_found": result.candidates_found,
        "fully_decayed": result.fully_decayed,
        "dimensions_decayed": result.dimensions_decayed,
        "errors": result.errors,
        "duration_ms": result.duration_ms,
    }


@router.get("/captures/statistics", response_model=StatisticsResponse)
async def get_decay_statistics():
    """Get decay statistics."""
    from api.services.episodic_decay_service import get_episodic_decay_service

    service = get_episodic_decay_service()
    stats = await service.get_decay_statistics()

    return StatisticsResponse(statistics=stats)


# =============================================================================
# Turning Points Endpoints
# =============================================================================


@router.post("/turning-points", response_model=dict)
async def mark_turning_point(capture_id: str, request: MarkTurningPointRequest):
    """Mark a capture as a turning point."""
    from api.services.turning_point_service import get_turning_point_service

    service = get_turning_point_service()

    tp = await service.mark_as_turning_point(
        capture_id=UUID(capture_id),
        trigger_type=TurningPointTrigger(request.trigger_type),
        trigger_description=request.trigger_description,
        vividness_score=request.vividness_score,
        narrative_thread_id=UUID(request.narrative_thread_id) if request.narrative_thread_id else None,
        life_chapter_id=UUID(request.life_chapter_id) if request.life_chapter_id else None,
    )

    return {
        "id": str(tp.id),
        "capture_id": str(tp.capture_id),
        "trigger_type": tp.trigger_type.value,
        "vividness_score": tp.vividness_score,
        "created_at": tp.created_at.isoformat(),
    }


@router.get("/turning-points", response_model=TurningPointListResponse)
async def list_turning_points(
    trigger_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List turning points with optional filters."""
    from api.services.turning_point_service import get_turning_point_service

    service = get_turning_point_service()

    tps = await service.get_turning_points(
        trigger_type=TurningPointTrigger(trigger_type) if trigger_type else None,
        limit=limit,
        offset=offset,
    )

    return TurningPointListResponse(
        turning_points=[
            {
                "id": str(tp.id),
                "capture_id": str(tp.capture_id),
                "trigger_type": tp.trigger_type.value,
                "trigger_description": tp.trigger_description,
                "vividness_score": tp.vividness_score,
                "created_at": tp.created_at.isoformat(),
            }
            for tp in tps
        ],
        total=len(tps),
    )


@router.get("/turning-points/{turning_point_id}")
async def get_turning_point(turning_point_id: str):
    """Get a specific turning point."""
    from api.services.turning_point_service import get_turning_point_service

    service = get_turning_point_service()
    tp = await service.get_turning_point(UUID(turning_point_id))

    if not tp:
        raise HTTPException(status_code=404, detail="Turning point not found")

    return {
        "id": str(tp.id),
        "capture_id": str(tp.capture_id),
        "trigger_type": tp.trigger_type.value,
        "trigger_description": tp.trigger_description,
        "vividness_score": tp.vividness_score,
        "narrative_thread_id": str(tp.narrative_thread_id) if tp.narrative_thread_id else None,
        "life_chapter_id": str(tp.life_chapter_id) if tp.life_chapter_id else None,
        "created_at": tp.created_at.isoformat(),
    }


@router.delete("/turning-points/capture/{capture_id}")
async def unmark_turning_point(capture_id: str):
    """Remove turning point status from a capture."""
    from api.services.turning_point_service import get_turning_point_service

    service = get_turning_point_service()
    unmarked = await service.unmark_turning_point(UUID(capture_id))

    if not unmarked:
        raise HTTPException(status_code=404, detail="No turning point found for capture")

    return {"unmarked": True, "capture_id": capture_id}


@router.get("/turning-points/statistics", response_model=StatisticsResponse)
async def get_turning_point_statistics():
    """Get turning point statistics."""
    from api.services.turning_point_service import get_turning_point_service

    service = get_turning_point_service()
    stats = await service.get_turning_point_statistics()

    return StatisticsResponse(statistics=stats)


# =============================================================================
# Beliefs Endpoints
# =============================================================================


@router.post("/beliefs", response_model=dict)
async def create_belief(request: CreateBeliefRequest):
    """Create a new semantic belief."""
    from api.services.db import get_db_pool

    pool = await get_db_pool()

    row = await pool.fetchrow(
        """
        INSERT INTO belief_rewrites (
            new_belief, domain, old_belief_id, evidence_count
        ) VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        request.new_belief,
        request.domain,
        request.old_belief_id,
        request.evidence_count,
    )

    return {
        "id": str(row["id"]),
        "new_belief": row["new_belief"],
        "domain": row["domain"],
        "adaptiveness_score": row["adaptiveness_score"],
        "created_at": row["created_at"].isoformat(),
    }


@router.get("/beliefs", response_model=BeliefListResponse)
async def list_beliefs(
    domain: str | None = Query(None),
    archived: bool = Query(False),
    needs_revision: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List beliefs with optional filters."""
    from api.services.semantic_archive_service import get_semantic_archive_service

    if needs_revision:
        service = get_semantic_archive_service()
        beliefs = await service.get_beliefs_needing_revision(limit=limit)
        return BeliefListResponse(
            beliefs=[
                {
                    "id": str(b.id),
                    "new_belief": b.new_belief,
                    "domain": b.domain,
                    "adaptiveness_score": b.adaptiveness_score,
                    "accuracy": b.accuracy,
                    "needs_revision": b.needs_revision,
                    "archived": b.archived,
                    "created_at": b.created_at.isoformat(),
                }
                for b in beliefs
            ],
            total=len(beliefs),
        )

    if archived:
        service = get_semantic_archive_service()
        beliefs = await service.get_archived_beliefs(domain=domain, limit=limit, offset=offset)
        return BeliefListResponse(
            beliefs=[
                {
                    "id": str(b.id),
                    "new_belief": b.new_belief,
                    "domain": b.domain,
                    "adaptiveness_score": b.adaptiveness_score,
                    "accuracy": b.accuracy,
                    "archived": b.archived,
                    "created_at": b.created_at.isoformat(),
                }
                for b in beliefs
            ],
            total=len(beliefs),
        )

    # Standard list
    from api.services.db import get_db_pool

    pool = await get_db_pool()

    conditions = ["archived = FALSE"]
    params = []
    param_idx = 1

    if domain:
        conditions.append(f"domain = ${param_idx}")
        params.append(domain)
        param_idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}"

    query = f"""
        SELECT * FROM belief_rewrites
        {where_clause}
        ORDER BY updated_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])

    rows = await pool.fetch(query, *params)

    count_query = f"SELECT COUNT(*) FROM belief_rewrites {where_clause}"
    total = await pool.fetchval(count_query, *params[:-2])

    return BeliefListResponse(
        beliefs=[
            {
                "id": str(row["id"]),
                "new_belief": row["new_belief"],
                "domain": row["domain"],
                "adaptiveness_score": row["adaptiveness_score"],
                "archived": row["archived"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ],
        total=total or 0,
    )


@router.get("/beliefs/{belief_id}")
async def get_belief(belief_id: str):
    """Get a specific belief."""
    from api.services.semantic_archive_service import get_semantic_archive_service

    service = get_semantic_archive_service()
    belief = await service.get_belief(UUID(belief_id))

    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")

    return {
        "id": str(belief.id),
        "new_belief": belief.new_belief,
        "domain": belief.domain,
        "old_belief_id": str(belief.old_belief_id) if belief.old_belief_id else None,
        "adaptiveness_score": belief.adaptiveness_score,
        "evidence_count": belief.evidence_count,
        "prediction_success_count": belief.prediction_success_count,
        "prediction_failure_count": belief.prediction_failure_count,
        "accuracy": belief.accuracy,
        "needs_revision": belief.needs_revision,
        "evolution_trigger": belief.evolution_trigger.value if belief.evolution_trigger else None,
        "archived": belief.archived,
        "last_verified": belief.last_verified.isoformat() if belief.last_verified else None,
        "created_at": belief.created_at.isoformat(),
        "updated_at": belief.updated_at.isoformat(),
    }


@router.post("/beliefs/{belief_id}/update-confidence")
async def update_belief_confidence(belief_id: str, prediction_correct: bool):
    """Update belief confidence based on prediction outcome."""
    from api.services.semantic_archive_service import get_semantic_archive_service

    service = get_semantic_archive_service()
    belief = await service.update_confidence(UUID(belief_id), prediction_correct)

    if not belief:
        raise HTTPException(status_code=404, detail="Belief not found")

    return {
        "id": str(belief.id),
        "adaptiveness_score": belief.adaptiveness_score,
        "accuracy": belief.accuracy,
        "needs_revision": belief.needs_revision,
    }


@router.post("/beliefs/{belief_id}/restore")
async def restore_belief(belief_id: str):
    """Restore an archived belief."""
    from api.services.semantic_archive_service import get_semantic_archive_service

    service = get_semantic_archive_service()
    belief = await service.restore_from_archive(UUID(belief_id))

    if not belief:
        raise HTTPException(status_code=404, detail="Archived belief not found")

    return {
        "id": str(belief.id),
        "restored": True,
        "archived": belief.archived,
    }


@router.post("/beliefs/archive/apply")
async def apply_archive(
    confidence_threshold: float = Query(0.3, ge=0.0, le=1.0),
    stale_days: int = Query(365, ge=1),
):
    """Apply archival to low-confidence beliefs."""
    from api.services.semantic_archive_service import get_semantic_archive_service

    service = get_semantic_archive_service()
    result = await service.apply_archival(
        confidence_threshold=confidence_threshold,
        stale_days=stale_days,
    )

    return {
        "candidates_found": result.candidates_found,
        "archived": result.archived,
        "duration_ms": result.duration_ms,
        "errors": result.errors,
    }


@router.get("/beliefs/statistics", response_model=StatisticsResponse)
async def get_belief_statistics():
    """Get belief statistics."""
    from api.services.semantic_archive_service import get_semantic_archive_service

    service = get_semantic_archive_service()
    stats = await service.get_archive_statistics()

    return StatisticsResponse(statistics=stats)


# =============================================================================
# Patterns Endpoints
# =============================================================================


@router.post("/patterns", response_model=dict)
async def create_pattern(request: CreatePatternRequest):
    """Create a new maladaptive pattern."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()

    pattern = await service.create_pattern(
        belief_content=request.belief_content,
        domain=request.domain,
        capture_id=UUID(request.capture_id) if request.capture_id else None,
        model_id=UUID(request.model_id) if request.model_id else None,
        initial_severity=request.initial_severity,
    )

    return {
        "id": str(pattern.id),
        "belief_content": pattern.belief_content,
        "domain": pattern.domain,
        "severity_level": pattern.severity_level.value,
        "recurrence_count": pattern.recurrence_count,
        "created_at": pattern.created_at.isoformat(),
    }


@router.get("/patterns", response_model=PatternListResponse)
async def list_patterns(
    domain: str | None = Query(None),
    severity_level: str | None = Query(None),
    include_intervened: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List patterns with optional filters."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()

    patterns = await service.get_patterns(
        domain=domain,
        severity_level=PatternSeverity(severity_level) if severity_level else None,
        include_intervened=include_intervened,
        limit=limit,
        offset=offset,
    )

    return PatternListResponse(
        patterns=[
            {
                "id": str(p.id),
                "belief_content": p.belief_content,
                "domain": p.domain,
                "severity_level": p.severity_level.value,
                "severity_score": p.severity_score,
                "recurrence_count": p.recurrence_count,
                "should_intervene": p.should_intervene,
                "intervention_triggered": p.intervention_triggered,
                "created_at": p.created_at.isoformat(),
            }
            for p in patterns
        ],
        total=len(patterns),
    )


@router.get("/patterns/requiring-intervention", response_model=PatternListResponse)
async def get_patterns_requiring_intervention(limit: int = Query(20, ge=1, le=100)):
    """Get patterns that meet intervention criteria."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()
    patterns = await service.get_patterns_requiring_intervention(limit=limit)

    return PatternListResponse(
        patterns=[
            {
                "id": str(p.id),
                "belief_content": p.belief_content,
                "domain": p.domain,
                "severity_level": p.severity_level.value,
                "severity_score": p.severity_score,
                "recurrence_count": p.recurrence_count,
                "should_intervene": True,
                "created_at": p.created_at.isoformat(),
            }
            for p in patterns
        ],
        total=len(patterns),
    )


@router.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get a specific pattern."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()
    pattern = await service.get_pattern(UUID(pattern_id))

    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    assessment = service.assess_severity(pattern)

    return {
        "id": str(pattern.id),
        "belief_content": pattern.belief_content,
        "domain": pattern.domain,
        "severity_level": pattern.severity_level.value,
        "severity_score": pattern.severity_score,
        "recurrence_count": pattern.recurrence_count,
        "intervention_triggered": pattern.intervention_triggered,
        "last_intervention": pattern.last_intervention.isoformat() if pattern.last_intervention else None,
        "linked_captures": len(pattern.linked_capture_ids),
        "linked_models": len(pattern.linked_model_ids),
        "assessment": assessment,
        "created_at": pattern.created_at.isoformat(),
        "updated_at": pattern.updated_at.isoformat(),
    }


@router.post("/patterns/{pattern_id}/increment")
async def increment_pattern(
    pattern_id: str,
    capture_id: str | None = Query(None),
    model_id: str | None = Query(None),
):
    """Increment pattern recurrence."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()

    pattern = await service.update_recurrence(
        pattern_id=UUID(pattern_id),
        capture_id=UUID(capture_id) if capture_id else None,
        model_id=UUID(model_id) if model_id else None,
    )

    return {
        "id": str(pattern.id),
        "recurrence_count": pattern.recurrence_count,
        "severity_level": pattern.severity_level.value,
        "severity_score": pattern.severity_score,
        "should_intervene": pattern.should_intervene,
    }


@router.post("/patterns/{pattern_id}/trigger-intervention")
async def trigger_intervention(pattern_id: str):
    """Trigger intervention for a pattern."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()
    pattern = await service.trigger_intervention(UUID(pattern_id))

    return {
        "id": str(pattern.id),
        "intervention_triggered": True,
        "last_intervention": pattern.last_intervention.isoformat() if pattern.last_intervention else None,
    }


@router.get("/patterns/statistics", response_model=StatisticsResponse)
async def get_pattern_statistics():
    """Get pattern statistics."""
    from api.services.pattern_detection_service import get_pattern_detection_service

    service = get_pattern_detection_service()
    stats = await service.get_pattern_statistics()

    return StatisticsResponse(statistics=stats)


# =============================================================================
# Verifications Endpoints
# =============================================================================


@router.post("/verifications", response_model=dict)
async def create_verification(request: CreateVerificationRequest):
    """Create a new verification encounter."""
    from api.services.verification_service import get_verification_service

    service = get_verification_service()

    encounter = await service.create_verification(
        belief_id=UUID(request.belief_id),
        prediction_id=UUID(request.prediction_id),
        prediction_content=request.prediction_content,
        session_id=UUID(request.session_id),
    )

    return {
        "id": str(encounter.id),
        "belief_id": str(encounter.belief_id),
        "prediction_id": str(encounter.prediction_id),
        "is_resolved": encounter.is_resolved,
        "created_at": encounter.created_at.isoformat(),
    }


@router.get("/verifications", response_model=VerificationListResponse)
async def list_verifications(
    belief_id: str | None = Query(None),
    session_id: str | None = Query(None),
    pending_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
):
    """List verifications with optional filters."""
    from api.services.verification_service import get_verification_service

    service = get_verification_service()

    if pending_only:
        verifications = await service.get_pending_verifications(
            belief_id=UUID(belief_id) if belief_id else None,
            session_id=UUID(session_id) if session_id else None,
            limit=limit,
        )
    elif belief_id:
        verifications = await service.get_verifications_for_belief(
            belief_id=UUID(belief_id),
            limit=limit,
        )
    else:
        # Fall back to pending for general list
        verifications = await service.get_pending_verifications(limit=limit)

    return VerificationListResponse(
        verifications=[
            {
                "id": str(v.id),
                "belief_id": str(v.belief_id),
                "prediction_id": str(v.prediction_id),
                "is_resolved": v.is_resolved,
                "prediction_error": v.prediction_error,
                "belief_activated": v.belief_activated,
                "timestamp": v.timestamp.isoformat(),
            }
            for v in verifications
        ],
        total=len(verifications),
    )


@router.get("/verifications/{encounter_id}")
async def get_verification(encounter_id: str):
    """Get a specific verification encounter."""
    from api.services.verification_service import get_verification_service

    service = get_verification_service()
    encounter = await service.get_verification(UUID(encounter_id))

    if not encounter:
        raise HTTPException(status_code=404, detail="Verification not found")

    return {
        "id": str(encounter.id),
        "belief_id": str(encounter.belief_id),
        "prediction_id": str(encounter.prediction_id),
        "prediction_content": encounter.prediction_content,
        "observation": encounter.observation,
        "belief_activated": encounter.belief_activated,
        "prediction_error": encounter.prediction_error,
        "is_resolved": encounter.is_resolved,
        "session_id": str(encounter.session_id),
        "timestamp": encounter.timestamp.isoformat(),
        "created_at": encounter.created_at.isoformat(),
    }


@router.post("/verifications/{encounter_id}/resolve")
async def resolve_verification(encounter_id: str, request: ResolveVerificationRequest):
    """Resolve a verification encounter with observation."""
    from api.services.verification_service import get_verification_service

    service = get_verification_service()

    try:
        result = await service.resolve_verification(
            encounter_id=UUID(encounter_id),
            observation=request.observation,
            belief_activated=request.belief_activated,
            prediction_error=request.prediction_error,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "encounter_id": str(result.encounter_id),
        "belief_id": str(result.belief_id),
        "prediction_correct": result.prediction_correct,
        "prediction_error": result.prediction_error,
        "belief_activated": result.belief_activated,
    }


@router.post("/verifications/expire")
async def expire_stale_verifications(ttl_hours: int = Query(24, ge=1)):
    """Expire stale unresolved verifications."""
    from api.services.verification_service import get_verification_service

    service = get_verification_service()
    expired = await service.expire_stale_verifications(ttl_hours=ttl_hours)

    return {
        "expired": expired,
        "ttl_hours": ttl_hours,
    }


@router.get("/verifications/statistics", response_model=StatisticsResponse)
async def get_verification_statistics(belief_id: str | None = Query(None)):
    """Get verification statistics."""
    from api.services.verification_service import get_verification_service

    service = get_verification_service()
    stats = await service.get_verification_statistics(
        belief_id=UUID(belief_id) if belief_id else None
    )

    return StatisticsResponse(statistics=stats)
