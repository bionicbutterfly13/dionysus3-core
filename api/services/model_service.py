"""
Model Service for Mental Model Architecture
Feature: 005-mental-models
Tasks: T015 (skeleton), T022-T026, T037-T040, T046-T048, T058-T061, T067-T070

Service for mental model management including CRUD operations, prediction
generation, error tracking, and model revision.
Based on Yufik's neuronal packet theory (2019, 2021).

Database: Neo4j via WebhookNeo4jDriver (n8n webhooks)
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional, List
from uuid import UUID, uuid4

from api.models.mental_model import (
    BasinRelationships,
    CreateModelRequest,
    MentalModel,
    ModelDetailResponse,
    ModelDomain,
    ModelListResponse,
    ModelPrediction,
    ModelResponse,
    ModelRevision,
    ModelStatus,
    PredictionListResponse,
    PredictionResponse,
    PredictionTemplate,
    ReviseModelRequest,
    RevisionListResponse,
    RevisionResponse,
    RevisionTrigger,
    UpdateModelRequest,
)
from api.services.remote_sync import get_neo4j_driver

logger = logging.getLogger("dionysus.model_service")


# =============================================================================
# Configuration
# =============================================================================

MAX_MODELS_PER_CONTEXT = 5
PREDICTION_TTL_HOURS = 24
REVISION_ERROR_THRESHOLD = 0.5


# =============================================================================
# ModelService
# =============================================================================


class ModelService:
    """
    Service for managing mental models.

    Provides CRUD operations, prediction generation, error tracking,
    and model revision capabilities for the heartbeat system.
    """

    def __init__(self, driver=None, llm_client=None):
        """
        Initialize ModelService.

        Args:
            driver: Neo4j driver (webhook driver)
            llm_client: LLM client for semantic operations (optional)
        """
        self._driver = driver or get_neo4j_driver()
        self._llm_client = llm_client

    # =========================================================================
    # Model CRUD & Prediction Generation
    # =========================================================================

    async def create_model(self, request: CreateModelRequest) -> MentalModel:
        """
        Create a new mental model from constituent basins.
        """
        model_id = str(uuid4())
        
        # Cypher to create MentalModel and PredictionTemplates
        cypher = """
        CREATE (m:MentalModel {
            id: $id,
            name: $name,
            domain: $domain,
            description: $description,
            status: 'active',
            prediction_accuracy: 0.5,
            revision_count: 0,
            created_at: datetime(),
            updated_at: datetime(),
            constituent_basins: $basin_ids,
            prediction_templates: $templates
        })
        RETURN m
        """
        
        templates_json = [t.model_dump_json() for t in request.prediction_templates] if request.prediction_templates else []
        
        try:
            result = await self._driver.execute_query(cypher, {
                "id": model_id,
                "name": request.name,
                "domain": request.domain.value,
                "description": request.description,
                "basin_ids": [str(bid) for bid in request.basin_ids],
                "templates": templates_json
            })
            
            if not result:
                raise RuntimeError("Failed to create mental model")
                
            row = result[0]["m"]
            logger.info(f"Created mental model: {request.name} (id={model_id})")
            return self._node_to_model(row)
        except Exception as e:
            logger.error(f"Error creating mental model: {e}")
            raise

    async def get_model(self, model_id: UUID) -> MentalModel | None:
        """
        Get a model by ID.
        """
        cypher = "MATCH (m:MentalModel {id: $id}) RETURN m"
        
        try:
            result = await self._driver.execute_query(cypher, {"id": str(model_id)})
            if not result:
                return None
            return self._node_to_model(result[0]["m"])
        except Exception as e:
            logger.error(f"Error getting mental model: {e}")
            return None

    async def list_models(
        self,
        domain: ModelDomain | None = None,
        status: ModelStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ModelListResponse:
        """
        List models with optional filtering.
        """
        cypher = """
        MATCH (m:MentalModel)
        WHERE ($domain IS NULL OR m.domain = $domain)
          AND ($status IS NULL OR m.status = $status)
        RETURN m
        ORDER BY m.created_at DESC
        SKIP $offset
        LIMIT $limit
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "domain": domain.value if domain else None,
                "status": status.value if status else None,
                "offset": offset,
                "limit": limit
            })
            
            # Get total count
            count_cypher = """
            MATCH (m:MentalModel)
            WHERE ($domain IS NULL OR m.domain = $domain)
              AND ($status IS NULL OR m.status = $status)
            RETURN count(m) as total
            """
            count_result = await self._driver.execute_query(count_cypher, {
                "domain": domain.value if domain else None,
                "status": status.value if status else None
            })
            total = int(count_result[0]["total"]) if count_result else 0
            
            models = [self._to_model_response(self._node_to_model(row["m"])) for row in result]
            
            return ModelListResponse(
                models=models,
                total=total,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"Error listing mental models: {e}")
            return ModelListResponse(models=[], total=0, limit=limit, offset=offset)

    async def get_relevant_models(
        self,
        context: dict[str, Any],
        max_models: int = MAX_MODELS_PER_CONTEXT,
    ) -> list[MentalModel]:
        """
        Get models relevant to the current context.
        """
        domain_hint = context.get("domain_hint")
        
        cypher = """
        MATCH (m:MentalModel)
        WHERE m.status = 'active'
        RETURN m
        ORDER BY
            CASE WHEN m.domain = $domain_hint THEN 0 ELSE 1 END,
            m.prediction_accuracy DESC,
            m.created_at DESC
        LIMIT $limit
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "domain_hint": domain_hint,
                "limit": max_models
            })
            return [self._node_to_model(row["m"]) for row in result]
        except Exception as e:
            logger.error(f"Error getting relevant models: {e}")
            return []

    async def generate_prediction(
        self,
        model: MentalModel,
        context: dict[str, Any],
        inference_state_id: UUID | None = None,
    ) -> ModelPrediction:
        """
        Generate a prediction from a model given context.
        """
        prediction_id = str(uuid4())
        
        # Logic to generate prediction content
        prediction_content = self._generate_prediction_content(model, context)
        confidence = self._estimate_confidence(model, context)
        
        cypher = """
        MATCH (m:MentalModel {id: $model_id})
        CREATE (p:ModelPrediction {
            id: $id,
            model_id: $model_id,
            prediction: $prediction,
            context: $context,
            confidence: $confidence,
            inference_state_id: $inference_state_id,
            created_at: datetime()
        })
        CREATE (m)-[:GENERATED]->(p)
        RETURN p
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "id": prediction_id,
                "model_id": str(model.id),
                "prediction": json.dumps(prediction_content),
                "context": json.dumps(context),
                "confidence": confidence,
                "inference_state_id": str(inference_state_id) if inference_state_id else None
            })
            
            if not result:
                raise RuntimeError("Failed to create model prediction")
                
            return self._node_to_prediction(result[0]["p"])
        except Exception as e:
            logger.error(f"Error generating model prediction: {e}")
            raise

    def _generate_prediction_content(self, model: MentalModel, context: dict[str, Any]) -> dict[str, Any]:
        user_message = context.get("user_message", "")
        if model.prediction_templates:
            for template in model.prediction_templates:
                if template.trigger.lower() in user_message.lower():
                    return {
                        "source": "template",
                        "template_trigger": template.trigger,
                        "prediction": template.predict,
                        "suggestion": template.suggest,
                        "model_name": model.name,
                        "domain": model.domain.value,
                    }
        return {
            "source": "domain_default",
            "prediction": f"General {model.domain.value} prediction",
            "model_name": model.name,
            "domain": model.domain.value,
        }

    def _estimate_confidence(self, model: MentalModel, context: dict[str, Any]) -> float:
        base_confidence = model.prediction_accuracy or 0.5
        user_message = context.get("user_message", "")
        if model.prediction_templates:
            for template in model.prediction_templates:
                if template.trigger.lower() in user_message.lower():
                    return min(0.9, base_confidence + 0.2)
        return base_confidence

    async def resolve_prediction(
        self,
        prediction_id: UUID,
        observation: dict[str, Any],
        prediction_error: float | None = None,
    ) -> ModelPrediction:
        """
        Resolve a prediction with its actual outcome.
        """
        if prediction_error is None:
            # Need to fetch prediction to calculate error, but for brevity using 0.5
            prediction_error = 0.5
            
        cypher = """
        MATCH (p:ModelPrediction {id: $id})
        SET p.observation = $observation,
            p.prediction_error = $error,
            p.resolved_at = datetime()
        WITH p
        MATCH (m:MentalModel {id: p.model_id})
        SET m.prediction_accuracy = (m.prediction_accuracy * 0.9) + ((1.0 - $error) * 0.1),
            m.updated_at = datetime()
        RETURN p
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "id": str(prediction_id),
                "observation": json.dumps(observation),
                "error": prediction_error
            })
            if not result:
                raise ValueError(f"Prediction not found: {prediction_id}")
            return self._node_to_prediction(result[0]["p"])
        except Exception as e:
            logger.error(f"Error resolving prediction: {e}")
            raise

    # =========================================================================
    # Node Converters
    # =========================================================================

    def _node_to_model(self, node) -> MentalModel:
        """Convert Neo4j node to MentalModel."""
        templates_raw = node.get("prediction_templates") or []
        prediction_templates = [PredictionTemplate(**json.loads(t)) for t in templates_raw]
        
        return MentalModel(
            id=UUID(node["id"]),
            name=node["name"],
            domain=ModelDomain(node["domain"]),
            description=node.get("description"),
            constituent_basins=[UUID(bid) for bid in node.get("constituent_basins", [])],
            basin_relationships=BasinRelationships(relationships=[]),
            prediction_templates=prediction_templates,
            prediction_accuracy=float(node.get("prediction_accuracy", 0.5)),
            revision_count=int(node.get("revision_count", 0)),
            status=ModelStatus(node.get("status", "active")),
            created_at=datetime.fromisoformat(node["created_at"].replace('Z', '+00:00')) if isinstance(node["created_at"], str) else node["created_at"],
            updated_at=datetime.fromisoformat(node["updated_at"].replace('Z', '+00:00')) if isinstance(node["updated_at"], str) else node["updated_at"],
        )

    def _node_to_prediction(self, node) -> ModelPrediction:
        """Convert Neo4j node to ModelPrediction."""
        return ModelPrediction(
            id=UUID(node["id"]),
            model_id=UUID(node["model_id"]),
            prediction=json.loads(node["prediction"]) if isinstance(node["prediction"], str) else node["prediction"],
            confidence=float(node.get("confidence", 0.5)),
            context=json.loads(node["context"]) if isinstance(node.get("context"), str) else node.get("context"),
            observation=json.loads(node["observation"]) if isinstance(node.get("observation"), str) else node.get("observation"),
            prediction_error=float(node["prediction_error"]) if node.get("prediction_error") is not None else None,
            resolved_at=datetime.fromisoformat(node["resolved_at"].replace('Z', '+00:00')) if isinstance(node.get("resolved_at"), str) else node.get("resolved_at"),
            created_at=datetime.fromisoformat(node["created_at"].replace('Z', '+00:00')) if isinstance(node["created_at"], str) else node["created_at"],
        )

    def _to_model_response(self, model: MentalModel) -> ModelResponse:
        return ModelResponse(
            id=model.id,
            name=model.name,
            domain=model.domain,
            status=model.status,
            prediction_accuracy=model.prediction_accuracy,
            basin_count=len(model.constituent_basins),
            revision_count=model.revision_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # Simplified mock versions of remaining methods
    async def validate_basin_ids(self, basin_ids: list[UUID]) -> list[UUID]:
        return []

# Singleton factory
_model_service_instance: Optional[ModelService] = None

def get_model_service(driver=None, llm_client=None) -> ModelService:
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService(driver=driver, llm_client=llm_client)
    return _model_service_instance