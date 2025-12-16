# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Mental Models REST API Router
Feature: 005-mental-models
Tasks: T030-T032

REST endpoints for mental model management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.models.mental_model import (
    CreateModelRequest,
    ModelDomain,
    ModelStatus,
    PredictionTemplate,
)

router = APIRouter(prefix="/api/models", tags=["mental-models"])


# =============================================================================
# Request/Response Models (REST-specific)
# =============================================================================


class CreateModelRestRequest(BaseModel):
    """REST request for creating a mental model."""

    name: str = Field(min_length=1, max_length=200)
    domain: str = Field(pattern="^(user|self|world|task_specific)$")
    basin_ids: list[str] = Field(min_length=1)
    description: Optional[str] = Field(None, max_length=2000)
    prediction_templates: Optional[list[dict]] = None


class ModelSummaryResponse(BaseModel):
    """Summary of a mental model for list responses."""

    id: str
    name: str
    domain: str
    status: str
    prediction_accuracy: Optional[float]
    basin_count: int
    revision_count: int
    created_at: str
    updated_at: str


class ModelListResponse(BaseModel):
    """List of models response."""

    models: list[ModelSummaryResponse]
    total: int


class ModelDetailResponse(BaseModel):
    """Detailed model response."""

    id: str
    name: str
    domain: str
    status: str
    description: Optional[str]
    constituent_basins: list[str]
    basin_relationships: dict
    prediction_templates: list[dict]
    prediction_accuracy: Optional[float]
    revision_count: int
    created_at: str
    updated_at: str


class CreateModelResponse(BaseModel):
    """Response from creating a model."""

    success: bool
    model_id: Optional[str]
    message: str


# =============================================================================
# Model Management Endpoints
# =============================================================================


@router.post("/", response_model=CreateModelResponse)
async def create_model(request: CreateModelRestRequest):
    """
    Create a new mental model.

    Mental models combine memory basins (attractor basins) to generate
    predictions about user behavior, self-state, world state, or tasks.

    Args:
        request: Model creation parameters

    Returns:
        Success status with model_id
    """
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        # Convert REST request to internal request
        templates = []
        if request.prediction_templates:
            for t in request.prediction_templates:
                templates.append(PredictionTemplate(**t))

        internal_request = CreateModelRequest(
            name=request.name,
            domain=ModelDomain(request.domain),
            basin_ids=[UUID(bid) for bid in request.basin_ids],
            description=request.description,
            prediction_templates=templates,
        )

        model = await service.create_model(internal_request)

        return CreateModelResponse(
            success=True,
            model_id=str(model.id),
            message=f"Model '{request.name}' created with {len(request.basin_ids)} basins",
        )

    except ValueError as e:
        return CreateModelResponse(
            success=False,
            model_id=None,
            message=str(e),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ModelListResponse)
async def list_models(
    domain: Optional[str] = Query(
        None,
        pattern="^(user|self|world|task_specific)$",
        description="Filter by domain",
    ),
    status: Optional[str] = Query(
        None,
        pattern="^(draft|active|deprecated)$",
        description="Filter by status",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List mental models with optional filtering.

    Args:
        domain: Filter by domain (user, self, world, task_specific)
        status: Filter by status (draft, active, deprecated)
        limit: Maximum results to return
        offset: Pagination offset

    Returns:
        List of model summaries with total count
    """
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        domain_filter = ModelDomain(domain) if domain else None
        status_filter = ModelStatus(status) if status else None

        response = await service.list_models(
            domain=domain_filter,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        return ModelListResponse(
            models=[
                ModelSummaryResponse(
                    id=str(m.id),
                    name=m.name,
                    domain=m.domain.value,
                    status=m.status.value,
                    prediction_accuracy=m.prediction_accuracy,
                    basin_count=m.basin_count,
                    revision_count=m.revision_count,
                    created_at=m.created_at.isoformat(),
                    updated_at=m.updated_at.isoformat(),
                )
                for m in response.models
            ],
            total=response.total,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=ModelDetailResponse)
async def get_model(model_id: UUID):
    """
    Get details for a specific mental model.

    Args:
        model_id: UUID of the model

    Returns:
        Full model details including basins and templates
    """
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        model = await service.get_model(model_id)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        return ModelDetailResponse(
            id=str(model.id),
            name=model.name,
            domain=model.domain.value,
            status=model.status.value,
            description=model.description,
            constituent_basins=[str(b) for b in model.constituent_basins],
            basin_relationships=model.basin_relationships.model_dump(),
            prediction_templates=[t.model_dump() for t in model.prediction_templates],
            prediction_accuracy=model.prediction_accuracy,
            revision_count=model.revision_count,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Prediction Endpoints (T042)
# =============================================================================


class PredictionSummaryResponse(BaseModel):
    """Summary of a model prediction."""

    id: str
    model_id: str
    prediction: dict
    confidence: float
    context: Optional[dict]
    observation: Optional[dict]
    prediction_error: Optional[float]
    resolved_at: Optional[str]
    created_at: str


class PredictionListResponse(BaseModel):
    """List of predictions response."""

    predictions: list[PredictionSummaryResponse]
    total: int


@router.get("/{model_id}/predictions", response_model=PredictionListResponse)
async def get_model_predictions(
    model_id: UUID,
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Get predictions for a specific model.

    Args:
        model_id: UUID of the model
        resolved: Filter by resolution status (true=resolved, false=unresolved, null=all)
        limit: Maximum results to return
        offset: Pagination offset

    Returns:
        List of predictions with total count
    """
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        # Verify model exists
        model = await service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        # Get predictions based on filter
        if resolved is False:
            predictions = await service.get_unresolved_predictions(
                model_id=model_id,
                limit=limit,
            )
            # Apply offset manually for now
            predictions = predictions[offset:offset + limit]
            total = len(predictions)
        else:
            # For resolved=True or None, we need to implement get_predictions_for_model
            # For now, just get all predictions via direct query
            predictions = await service.get_unresolved_predictions(
                model_id=model_id,
                limit=limit + offset,
            )
            if resolved is True:
                predictions = [p for p in predictions if p.resolved_at is not None]
            predictions = predictions[offset:offset + limit]
            total = len(predictions)

        return PredictionListResponse(
            predictions=[
                PredictionSummaryResponse(
                    id=str(p.id),
                    model_id=str(p.model_id),
                    prediction=p.prediction if isinstance(p.prediction, dict) else {},
                    confidence=p.confidence,
                    context=p.context if isinstance(p.context, dict) else None,
                    observation=p.observation if isinstance(p.observation, dict) else None,
                    prediction_error=p.prediction_error,
                    resolved_at=p.resolved_at.isoformat() if p.resolved_at else None,
                    created_at=p.created_at.isoformat(),
                )
                for p in predictions
            ],
            total=total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Revision Endpoints (T053-T054)
# =============================================================================


class RevisionSummaryResponse(BaseModel):
    """Summary of a model revision."""

    id: str
    model_id: str
    revision_number: int
    trigger: str
    trigger_description: Optional[str]
    basins_added: list[str]
    basins_removed: list[str]
    accuracy_before: Optional[float]
    accuracy_after: Optional[float]
    created_at: str


class RevisionListResponse(BaseModel):
    """List of revisions response."""

    revisions: list[RevisionSummaryResponse]
    total: int


class CreateRevisionRequest(BaseModel):
    """Request to create a model revision."""

    trigger_description: str = Field(min_length=1, max_length=2000)
    add_basins: Optional[list[str]] = None
    remove_basins: Optional[list[str]] = None


class CreateRevisionResponse(BaseModel):
    """Response from creating a revision."""

    success: bool
    revision_id: Optional[str]
    message: str
    new_accuracy: Optional[float]


@router.post("/{model_id}/revisions", response_model=CreateRevisionResponse)
async def create_revision(model_id: UUID, request: CreateRevisionRequest):
    """
    Create a revision for a mental model.

    Revisions modify a model's constituent basins and track the changes
    for audit and rollback purposes.

    Args:
        model_id: UUID of the model to revise
        request: Revision parameters (add/remove basins)

    Returns:
        Success status with revision_id and new accuracy
    """
    from api.models.mental_model import ReviseModelRequest
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        # Verify model exists
        model = await service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        # Create revision request
        internal_request = ReviseModelRequest(
            trigger_description=request.trigger_description,
            add_basins=[UUID(b) for b in (request.add_basins or [])],
            remove_basins=[UUID(b) for b in (request.remove_basins or [])],
        )

        # Apply revision
        revision = await service.apply_revision(model_id, internal_request)

        # Get updated model for accuracy
        updated_model = await service.get_model(model_id)

        return CreateRevisionResponse(
            success=True,
            revision_id=str(revision.id),
            message=f"Revision {revision.revision_number} applied successfully",
            new_accuracy=updated_model.prediction_accuracy if updated_model else None,
        )

    except ValueError as e:
        return CreateRevisionResponse(
            success=False,
            revision_id=None,
            message=str(e),
            new_accuracy=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/revisions", response_model=RevisionListResponse)
async def get_model_revisions(
    model_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Get revision history for a mental model.

    Args:
        model_id: UUID of the model
        limit: Maximum results to return
        offset: Pagination offset

    Returns:
        List of revisions with total count
    """
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        # Verify model exists
        model = await service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        # Get revisions via direct query (service method returns list)
        async with service._db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM model_revisions
                WHERE model_id = $1
                ORDER BY revision_number DESC
                LIMIT $2 OFFSET $3
                """,
                model_id,
                limit,
                offset,
            )
            total_row = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM model_revisions WHERE model_id = $1",
                model_id,
            )
            total = total_row["count"] if total_row else 0

        return RevisionListResponse(
            revisions=[
                RevisionSummaryResponse(
                    id=str(row["id"]),
                    model_id=str(row["model_id"]),
                    revision_number=row["revision_number"],
                    trigger=row["trigger"],
                    trigger_description=row["trigger_description"],
                    basins_added=[str(b) for b in (row["basins_added"] or [])],
                    basins_removed=[str(b) for b in (row["basins_removed"] or [])],
                    accuracy_before=row["accuracy_before"],
                    accuracy_after=row["accuracy_after"],
                    created_at=row["created_at"].isoformat(),
                )
                for row in rows
            ],
            total=total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Model Management Endpoints (T062-T063)
# =============================================================================


class UpdateModelRestRequest(BaseModel):
    """Request to update a mental model."""

    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(draft|active|deprecated)$")
    prediction_templates: Optional[list[dict]] = None


class UpdateModelResponse(BaseModel):
    """Response from updating a model."""

    success: bool
    message: str


class DeprecateModelResponse(BaseModel):
    """Response from deprecating a model."""

    success: bool
    message: str


@router.put("/{model_id}", response_model=UpdateModelResponse)
async def update_model(model_id: UUID, request: UpdateModelRestRequest):
    """
    Update a mental model's properties.

    Args:
        model_id: UUID of the model to update
        request: Fields to update (name, description, status, prediction_templates)

    Returns:
        Success status with message
    """
    from api.models.mental_model import (
        UpdateModelRequest,
        ModelStatus,
        PredictionTemplate,
    )
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        # Verify model exists
        model = await service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        # Convert to internal request
        templates = None
        if request.prediction_templates is not None:
            templates = [PredictionTemplate(**t) for t in request.prediction_templates]

        internal_request = UpdateModelRequest(
            name=request.name,
            description=request.description,
            status=ModelStatus(request.status) if request.status else None,
            prediction_templates=templates,
        )

        await service.update_model(model_id, internal_request)

        return UpdateModelResponse(
            success=True,
            message=f"Model '{model_id}' updated successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}", response_model=DeprecateModelResponse)
async def deprecate_model(model_id: UUID):
    """
    Deprecate (soft-delete) a mental model.

    Sets the model status to 'deprecated'. Only active models can be deprecated.

    Args:
        model_id: UUID of the model to deprecate

    Returns:
        Success status with message
    """
    from api.services.model_service import get_model_service

    service = get_model_service()

    try:
        # Verify model exists
        model = await service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        await service.deprecate_model(model_id)

        return DeprecateModelResponse(
            success=True,
            message=f"Model '{model_id}' deprecated successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
