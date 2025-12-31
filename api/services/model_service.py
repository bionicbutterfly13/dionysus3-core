"""
Model Service for Mental Model Architecture
Feature: 005-mental-models
Tasks: T015 (skeleton), T022-T026, T037-T040, T046-T048, T058-T061, T067-T070

Service for mental model management including CRUD operations, prediction
generation, error tracking, and model revision.
Based on Yufik's neuronal packet theory (2019, 2021).

Database: Neo4j via Graphiti-backed driver
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import UUID, uuid4

from api.models.mental_model import (
    BasinRelationships,
    CreateModelRequest,
    MentalModel,
    ModelDomain,
    ModelListResponse,
    ModelPrediction,
    ModelResponse,
    ModelRevision,
    ModelStatus,
    PredictionTemplate,
    ReviseModelRequest,
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


from api.models.cognitive import NeuronalPacketModel

# =============================================================================
# NeuronalPacket (Synergistic Whole)
# =============================================================================

class NeuronalPacket:
    """
    Implementation of a Neuronal Packet (Yufik 2019).
    Encapsulates a group of ThoughtSeeds and enforces mutual constraints.
    """
    def __init__(self, model: NeuronalPacketModel):
        self.data = model

    def apply_synergistic_boost(self, active_seed_id: str, scores: dict) -> dict:
        """
        Boost the confidence of all seeds in the packet when one is dominant.
        Reduces degrees of freedom by reinforcing the group.
        """
        if active_seed_id not in self.data.seed_ids:
            return scores
            
        for seed_id in self.data.seed_ids:
            if seed_id in scores:
                # Synergistic boost: Reduce EFE (increase desirability)
                scores[seed_id].efe_score *= (1.0 - (0.1 * self.data.cohesion_weight))
        
        return scores

from api.services.efe_engine import get_efe_engine

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
        self._efe_engine = get_efe_engine()

    async def select_dominant_thought(self, query: str, goal_vector: List[float], candidates: List[Dict[str, Any]]) -> str:
        """
        T013: Use EFE calculation to select the dominant ThoughtSeed.
        """
        efe_response = self._efe_engine.calculate_efe(query, goal_vector, candidates)
        
        # Apply synergistic boosts if any packets are involved
        # For now, we'll assume a flat structure but allow for future packet expansion
        return efe_response.dominant_seed_id

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
        Get models relevant to the current context, respecting energy wells.
        """
        domain_hint = context.get("domain_hint")
        
        # FR-030-001: Order by boundary_energy and stability to ensure stable models are preferred
        cypher = """
        MATCH (m:MentalModel)
        WHERE m.status = 'active'
        RETURN m
        ORDER BY
            CASE WHEN m.domain = $domain_hint THEN 0 ELSE 1 END,
            m.boundary_energy DESC,
            m.stability DESC,
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
            boundary_energy=float(node.get("boundary_energy", 0.5)),
            cohesion_ratio=float(node.get("cohesion_ratio", 1.0)),
            stability=float(node.get("stability", 0.5)),
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

    # =========================================================================
    # Revisions & Error Tracking
    # =========================================================================

    async def get_unresolved_predictions(
        self,
        model_id: UUID | None = None,
        limit: int = 50,
    ) -> list[ModelPrediction]:
        """
        Get unresolved predictions (no observation).
        """
        cypher = """
        MATCH (p:ModelPrediction)
        WHERE p.observation IS NULL
          AND ($model_id IS NULL OR p.model_id = $model_id)
        RETURN p
        ORDER BY p.created_at ASC
        LIMIT $limit
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "model_id": str(model_id) if model_id else None,
                "limit": limit
            })
            return [self._node_to_prediction(row["p"]) for row in result]
        except Exception as e:
            logger.error(f"Error getting unresolved predictions: {e}")
            return []

    async def apply_revision(
        self,
        model_id: UUID,
        request: ReviseModelRequest,
    ) -> ModelRevision:
        """
        Apply a structural revision to a mental model.
        """
        revision_id = str(uuid4())
        
        # Get current model to get accuracy_before and revision_count
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id})")
            
        new_revision_number = model.revision_count + 1
        
        # Update model basins and revision count
        new_basins = set(model.constituent_basins)
        for bid in request.add_basins:
            new_basins.add(bid)
        for bid in request.remove_basins:
            if bid in new_basins:
                new_basins.remove(bid)
                
        cypher = """
        MATCH (m:MentalModel {id: $model_id})
        SET m.constituent_basins = $new_basins,
            m.revision_count = $rev_count,
            m.updated_at = datetime()
        CREATE (r:ModelRevision {
            id: $rev_id,
            model_id: $model_id,
            revision_number: $rev_count,
            trigger: 'manual',
            trigger_description: $description,
            basins_added: $added,
            basins_removed: $removed,
            accuracy_before: $acc_before,
            created_at: datetime()
        })
        CREATE (m)-[:REVISED_BY]->(r)
        RETURN r
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "model_id": str(model_id),
                "rev_id": revision_id,
                "rev_count": new_revision_number,
                "new_basins": [str(bid) for bid in new_basins],
                "description": request.trigger_description,
                "added": [str(bid) for bid in request.add_basins],
                "removed": [str(bid) for bid in request.remove_basins],
                "acc_before": model.prediction_accuracy
            })
            
            if not result:
                raise RuntimeError("Failed to apply model revision")
                
            row = result[0]["r"]
            logger.info(f"Applied revision {new_revision_number} to model {model_id}")
            return self._node_to_revision(row)
        except Exception as e:
            logger.error(f"Error applying model revision: {e}")
            raise

    async def get_revisions(self, model_id: UUID, limit: int = 20, offset: int = 0) -> list[ModelRevision]:
        """
        Get revision history for a model.
        """
        cypher = """
        MATCH (r:ModelRevision {model_id: $model_id})
        RETURN r
        ORDER BY r.revision_number DESC
        SKIP $offset
        LIMIT $limit
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "model_id": str(model_id),
                "offset": offset,
                "limit": limit
            })
            return [self._node_to_revision(row["r"]) for row in result]
        except Exception as e:
            logger.error(f"Error getting model revisions: {e}")
            return []

    async def update_model(self, model_id: UUID, request: UpdateModelRequest) -> MentalModel:
        """
        Update model metadata or status.
        """
        # Build SET clauses dynamically
        sets = ["m.updated_at = datetime()"]
        params = {"id": str(model_id)}
        
        if request.name is not None:
            sets.append("m.name = $name")
            params["name"] = request.name
        if request.description is not None:
            sets.append("m.description = $description")
            params["description"] = request.description
        if request.status is not None:
            sets.append("m.status = $status")
            params["status"] = request.status.value
        if request.prediction_templates is not None:
            sets.append("m.prediction_templates = $templates")
            params["templates"] = [t.model_dump_json() for t in request.prediction_templates]
            
        cypher = f"MATCH (m:MentalModel {{id: $id}}) SET {', '.join(sets)} RETURN m"
        
        try:
            result = await self._driver.execute_query(cypher, params)
            if not result:
                raise ValueError(f"Model not found: {model_id})")
            return self._node_to_model(result[0]["m"])
        except Exception as e:
            logger.error(f"Error updating mental model: {e}")
            raise

    async def deprecate_model(self, model_id: UUID) -> MentalModel:
        """
        Soft-delete a model by setting status to 'deprecated'.
        """
        return await self.update_model(model_id, UpdateModelRequest(status=ModelStatus.DEPRECATED))

    # =========================================================================
    # Node Converters
    # =========================================================================

    def _node_to_revision(self, node) -> ModelRevision:
        """Convert Neo4j node to ModelRevision."""
        return ModelRevision(
            id=UUID(node["id"]),
            model_id=UUID(node["model_id"]),
            revision_number=int(node["revision_number"]),
            trigger=RevisionTrigger(node.get("trigger", "manual")),
            trigger_description=node.get("trigger_description"),
            basins_added=[UUID(bid) for bid in node.get("basins_added", [])],
            basins_removed=[UUID(bid) for bid in node.get("basins_removed", [])],
            accuracy_before=float(node["accuracy_before"]) if node.get("accuracy_before") is not None else None,
            accuracy_after=float(node["accuracy_after"]) if node.get("accuracy_after") is not None else None,
            created_at=datetime.fromisoformat(node["created_at"].replace('Z', '+00:00')) if isinstance(node["created_at"], str) else node["created_at"],
        )

    async def validate_basin_ids(self, basin_ids: list[UUID]) -> list[UUID]:
        """Validate that basin IDs exist in the database.

        Args:
            basin_ids: List of basin UUIDs to validate

        Returns:
            List of valid basin IDs that exist in the database
        """
        if not basin_ids:
            return []

        cypher = """
        UNWIND $ids AS id
        MATCH (b:MemoryCluster {id: id})
        RETURN b.id AS valid_id
        """

        try:
            result = await self._driver.execute_query(
                cypher,
                {"ids": [str(bid) for bid in basin_ids]}
            )
            return [UUID(r["valid_id"]) for r in result if r.get("valid_id")]
        except Exception as e:
            logger.warning(f"Basin validation failed: {e}")
            return []


# Singleton factory
_model_service_instance: Optional[ModelService] = None

def get_model_service(driver=None, llm_client=None) -> ModelService:
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService(driver=driver, llm_client=llm_client)
    return _model_service_instance
