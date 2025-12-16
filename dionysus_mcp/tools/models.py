# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Mental Model MCP Tools
Feature: 005-mental-models
Tasks: T019-T020

MCP tools for mental model management.
"""

from typing import Any, Optional
from uuid import UUID

__all__ = [
    "create_mental_model_tool",
    "list_mental_models_tool",
    "get_mental_model_tool",
    "revise_mental_model_tool",
    "run_prediction_competition_tool",
    "get_models_by_winners_tool",
    "generate_prediction_tool",
]


async def get_pool():
    """Get database pool from server."""
    from dionysus_mcp.server import get_pool as _get_pool
    return await _get_pool()


async def create_mental_model_tool(
    name: str,
    domain: str,
    basin_ids: list[str],
    description: Optional[str] = None,
    prediction_templates: Optional[list[dict]] = None
) -> dict:
    """
    Create a new mental model from constituent basins.

    Args:
        name: Model name (unique)
        domain: One of user, self, world, task_specific
        basin_ids: List of memory cluster UUIDs
        description: Optional description
        prediction_templates: Optional list of prediction templates

    Returns:
        CreateModelToolResponse as dict
    """
    from api.models.mental_model import (
        CreateModelRequest,
        ModelDomain,
        PredictionTemplate,
    )
    from api.services.model_service import get_model_service

    try:
        pool = await get_pool()
        service = get_model_service(db_pool=pool)

        # Convert basin_ids from strings to UUIDs
        basin_uuids = [UUID(bid) for bid in basin_ids]

        # Convert prediction templates
        templates = []
        if prediction_templates:
            for t in prediction_templates:
                templates.append(PredictionTemplate(**t))

        request = CreateModelRequest(
            name=name,
            domain=ModelDomain(domain),
            basin_ids=basin_uuids,
            description=description,
            prediction_templates=templates,
        )

        model = await service.create_model(request)

        return {
            "success": True,
            "model_id": str(model.id),
            "message": f"Model '{name}' created with {len(basin_uuids)} basins",
        }

    except ValueError as e:
        return {
            "success": False,
            "model_id": None,
            "message": str(e),
        }
    except Exception as e:
        return {
            "success": False,
            "model_id": None,
            "message": f"Failed to create model: {str(e)}",
        }


async def list_mental_models_tool(
    domain: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """
    List mental models with optional filtering.

    Args:
        domain: Filter by domain (user, self, world, task_specific)
        status: Filter by status (draft, active, deprecated)
        limit: Maximum results (default: 20)
        offset: Pagination offset

    Returns:
        ListModelsToolResponse as dict
    """
    from api.models.mental_model import ModelDomain, ModelStatus
    from api.services.model_service import get_model_service

    try:
        pool = await get_pool()
        service = get_model_service(db_pool=pool)

        domain_filter = ModelDomain(domain) if domain else None
        status_filter = ModelStatus(status) if status else None

        response = await service.list_models(
            domain=domain_filter,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        return {
            "models": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "domain": m.domain.value,
                    "status": m.status.value,
                    "prediction_accuracy": m.prediction_accuracy,
                    "basin_count": m.basin_count,
                    "revision_count": m.revision_count,
                    "created_at": m.created_at.isoformat(),
                    "updated_at": m.updated_at.isoformat(),
                }
                for m in response.models
            ],
            "total": response.total,
        }

    except Exception as e:
        return {
            "models": [],
            "total": 0,
            "error": str(e),
        }


async def get_mental_model_tool(
    model_id: str,
    include_predictions: bool = False,
    include_revisions: bool = False
) -> dict:
    """
    Get details for a specific mental model.

    Args:
        model_id: UUID of the model
        include_predictions: Include recent predictions
        include_revisions: Include revision history

    Returns:
        GetModelToolResponse as dict
    """
    from api.services.model_service import get_model_service

    try:
        pool = await get_pool()
        service = get_model_service(db_pool=pool)

        model = await service.get_model(UUID(model_id))

        if not model:
            return {
                "model": None,
                "error": f"Model not found: {model_id}",
            }

        result = {
            "model": {
                "id": str(model.id),
                "name": model.name,
                "domain": model.domain.value,
                "status": model.status.value,
                "description": model.description,
                "constituent_basins": [str(b) for b in model.constituent_basins],
                "basin_relationships": model.basin_relationships.model_dump(),
                "prediction_templates": [t.model_dump() for t in model.prediction_templates],
                "prediction_accuracy": model.prediction_accuracy,
                "revision_count": model.revision_count,
                "created_at": model.created_at.isoformat(),
                "updated_at": model.updated_at.isoformat(),
            },
            "predictions": None,
            "revisions": None,
        }

        # TODO: Add predictions and revisions when methods are implemented
        # if include_predictions:
        #     predictions = await service.get_predictions_for_model(model.id)
        #     result["predictions"] = [...]

        return result

    except Exception as e:
        return {
            "model": None,
            "error": str(e),
        }


async def revise_mental_model_tool(
    model_id: str,
    trigger_description: str,
    add_basins: Optional[list[str]] = None,
    remove_basins: Optional[list[str]] = None
) -> dict:
    """
    Revise a mental model's structure.

    Args:
        model_id: UUID of the model
        trigger_description: Why this revision is being made
        add_basins: Basin UUIDs to add
        remove_basins: Basin UUIDs to remove

    Returns:
        ReviseModelToolResponse as dict
    """
    from api.models.mental_model import ReviseModelRequest, RevisionTrigger
    from api.services.model_service import get_model_service

    try:
        pool = await get_pool()
        service = get_model_service(db_pool=pool)

        request = ReviseModelRequest(
            trigger_description=trigger_description,
            add_basins=[UUID(b) for b in (add_basins or [])],
            remove_basins=[UUID(b) for b in (remove_basins or [])],
        )

        revision = await service.apply_revision(UUID(model_id), request)

        # Get updated model for accuracy
        model = await service.get_model(UUID(model_id))

        return {
            "success": True,
            "revision_id": str(revision.id),
            "message": f"Model revised successfully",
            "new_accuracy": model.prediction_accuracy if model else None,
        }

    except ValueError as e:
        return {
            "success": False,
            "revision_id": None,
            "message": str(e),
            "new_accuracy": None,
        }
    except NotImplementedError:
        return {
            "success": False,
            "revision_id": None,
            "message": "Revision functionality not yet implemented",
            "new_accuracy": None,
        }
    except Exception as e:
        return {
            "success": False,
            "revision_id": None,
            "message": f"Failed to revise model: {str(e)}",
            "new_accuracy": None,
        }


async def generate_prediction_tool(
    model_id: str,
    context: dict,
    inference_state_id: Optional[str] = None
) -> dict:
    """
    Generate a prediction from a mental model.

    Creates a ThoughtSeed in the cognitive hierarchy for competition.
    Domain mapping: user→conceptual, self→metacognitive, world→abstract.

    Args:
        model_id: UUID of the mental model
        context: Context dict (user_message, domain_hint, etc.)
        inference_state_id: Optional link to active inference state

    Returns:
        Prediction with thoughtseed reference
    """
    from api.services.model_service import get_model_service

    try:
        pool = await get_pool()
        service = get_model_service(db_pool=pool)

        model = await service.get_model(UUID(model_id))
        if not model:
            return {
                "success": False,
                "prediction": None,
                "thoughtseed_id": None,
                "message": f"Model not found: {model_id}",
            }

        prediction = await service.generate_prediction(
            model=model,
            context=context,
            inference_state_id=UUID(inference_state_id) if inference_state_id else None,
        )

        return {
            "success": True,
            "prediction_id": str(prediction.id),
            "model_id": str(prediction.model_id),
            "prediction": prediction.prediction,
            "confidence": prediction.confidence,
            "message": f"Prediction generated from model '{model.name}' (confidence={prediction.confidence:.2f})",
        }

    except ValueError as e:
        return {
            "success": False,
            "prediction": None,
            "message": str(e),
        }
    except Exception as e:
        return {
            "success": False,
            "prediction": None,
            "message": f"Failed to generate prediction: {str(e)}",
        }


async def run_prediction_competition_tool(
    layer: str
) -> dict:
    """
    Run ThoughtSeed competition for predictions at a given cognitive layer.

    Layer mapping from ModelDomain:
    - user → conceptual (abstract concepts)
    - self → metacognitive (self-monitoring)
    - world → abstract (reasoning)
    - task_specific → perceptual (pattern recognition)

    Winner's constituent basins are activated via CLAUSE strengthening.

    Args:
        layer: ThoughtSeed layer (sensorimotor, perceptual, conceptual, abstract, metacognitive)

    Returns:
        Competition result with winner and activated basins
    """
    try:
        pool = await get_pool()

        from api.services.thoughtseed_integration import (
            get_thoughtseed_integration_service,
        )

        integration = get_thoughtseed_integration_service(db_pool=pool)
        result = await integration.run_prediction_competition(layer)

        if not result:
            return {
                "success": True,
                "message": f"No competing ThoughtSeeds at layer '{layer}'",
                "competition": None,
            }

        return {
            "success": True,
            "competition_id": result["competition_id"],
            "layer": result["layer"],
            "competitors": result["competitors"],
            "winner": result["winner"],
            "basins_activated": result["activated_basins"],
            "message": f"Competition completed: {result['competitors']} competitors, winner activation={result['winner']['activation_level']:.2f}",
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Competition failed: {str(e)}",
            "competition": None,
        }


async def get_models_by_winners_tool(
    layer: Optional[str] = None,
    limit: int = 5
) -> dict:
    """
    Get Mental Models associated with winning ThoughtSeeds.

    Models whose predictions have won in ThoughtSeed competition are
    cognitively relevant and should be prioritized.

    Args:
        layer: Optional filter by ThoughtSeed layer
        limit: Maximum models to return

    Returns:
        List of models with their ThoughtSeed context
    """
    try:
        pool = await get_pool()

        from api.services.model_service import get_model_service

        service = get_model_service(db_pool=pool)
        models = await service.get_models_by_thoughtseed_winners(
            layer=layer,
            limit=limit,
        )

        return {
            "success": True,
            "models": models,
            "count": len(models),
            "message": f"Found {len(models)} models with winning ThoughtSeeds",
        }

    except Exception as e:
        return {
            "success": False,
            "models": [],
            "message": f"Query failed: {str(e)}",
        }
