"""
Model Service for Mental Model Architecture
Feature: 005-mental-models
Tasks: T015 (skeleton), T022-T026, T037-T040, T046-T048, T058-T061, T067-T070

Service for mental model management including CRUD operations, prediction
generation, error tracking, and model revision.
Based on Yufik's neuronal packet theory (2019, 2021).
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

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

    def __init__(self, db_pool=None, llm_client=None):
        """
        Initialize ModelService.

        Args:
            db_pool: PostgreSQL connection pool (asyncpg)
            llm_client: LLM client for semantic operations (optional)
        """
        self._db_pool = db_pool
        self._llm_client = llm_client

    # =========================================================================
    # US1: Model CRUD & Prediction Generation
    # =========================================================================

    async def create_model(self, request: CreateModelRequest) -> MentalModel:
        """
        Create a new mental model from constituent basins.

        T022: Implementation
        T058: Basin existence validation (US4)

        Args:
            request: CreateModelRequest with name, domain, basin_ids

        Returns:
            Created MentalModel

        Raises:
            ValueError: If basin IDs don't exist or name is duplicate
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        # T058: Validate basin IDs exist
        invalid_basins = await self.validate_basin_ids(request.basin_ids)
        if invalid_basins:
            raise ValueError(f"Invalid basin IDs: {invalid_basins}")

        # Convert prediction templates to JSONB array
        templates_jsonb = [
            json.dumps(t.model_dump()) for t in request.prediction_templates
        ] if request.prediction_templates else []

        async with self._db_pool.acquire() as conn:
            try:
                # Call SQL function create_mental_model
                model_id = await conn.fetchval(
                    """
                    SELECT create_mental_model($1, $2::model_domain, $3, $4, $5::jsonb[])
                    """,
                    request.name,
                    request.domain.value,
                    request.basin_ids,
                    request.description,
                    templates_jsonb,
                )

                # Fetch the created model
                row = await conn.fetchrow(
                    """
                    SELECT * FROM mental_models WHERE id = $1
                    """,
                    model_id,
                )

                logger.info(f"Created mental model: {request.name} (id={model_id})")
                return self._row_to_model(row)

            except Exception as e:
                error_msg = str(e)
                if "basin IDs do not exist" in error_msg:
                    raise ValueError(error_msg)
                if "mental_models_name_unique" in error_msg:
                    raise ValueError(f"A model with name '{request.name}' already exists")
                raise

    async def get_model(self, model_id: UUID) -> MentalModel | None:
        """
        Get a model by ID.

        T023: Implementation

        Args:
            model_id: UUID of the model

        Returns:
            MentalModel if found, None otherwise
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM mental_models WHERE id = $1
                """,
                model_id,
            )

        if not row:
            return None

        return self._row_to_model(row)

    async def list_models(
        self,
        domain: ModelDomain | None = None,
        status: ModelStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ModelListResponse:
        """
        List models with optional filtering.

        T024: Implementation
        T068: Domain-based filtering (US5)

        Args:
            domain: Filter by domain type
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            ModelListResponse with matching models
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        # Build query with optional filters
        query_parts = ["SELECT * FROM mental_models WHERE 1=1"]
        count_parts = ["SELECT COUNT(*) FROM mental_models WHERE 1=1"]
        params = []
        param_idx = 1

        if domain is not None:
            query_parts.append(f"AND domain = ${param_idx}::model_domain")
            count_parts.append(f"AND domain = ${param_idx}::model_domain")
            params.append(domain.value)
            param_idx += 1

        if status is not None:
            query_parts.append(f"AND status = ${param_idx}::model_status")
            count_parts.append(f"AND status = ${param_idx}::model_status")
            params.append(status.value)
            param_idx += 1

        query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}")
        params.extend([limit, offset])

        query = " ".join(query_parts)
        count_query = " ".join(count_parts)

        async with self._db_pool.acquire() as conn:
            # Get total count (without limit/offset params)
            count_params = params[:-2] if params else []
            total = await conn.fetchval(count_query, *count_params)

            # Get models
            rows = await conn.fetch(query, *params)

        models = [self._to_model_response(self._row_to_model(row)) for row in rows]

        return ModelListResponse(
            models=models,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_relevant_models(
        self,
        context: dict[str, Any],
        max_models: int = MAX_MODELS_PER_CONTEXT,
    ) -> list[MentalModel]:
        """
        Get models relevant to the current context.

        T025: Implementation
        T069: Domain-based context matching (US5)
        T070: Domain prioritization (US5)
        T078: Performance optimized (<500ms target)

        Args:
            context: Current context (user message, domain hints, etc.)
            max_models: Maximum models to return

        Returns:
            List of relevant MentalModel instances
        """
        start_time = time.perf_counter()

        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        # Extract domain hint from context
        domain_hint = context.get("domain_hint")
        domain_filter = None
        if domain_hint:
            try:
                domain_filter = ModelDomain(domain_hint)
            except ValueError:
                pass  # Invalid domain hint, ignore

        async with self._db_pool.acquire() as conn:
            if domain_filter:
                # Get models matching domain hint first, then others
                rows = await conn.fetch(
                    """
                    SELECT * FROM mental_models
                    WHERE status = 'active'
                    ORDER BY
                        CASE WHEN domain = $1::model_domain THEN 0 ELSE 1 END,
                        prediction_accuracy DESC,
                        created_at DESC
                    LIMIT $2
                    """,
                    domain_filter.value,
                    max_models,
                )
            else:
                # No domain hint - get by accuracy
                rows = await conn.fetch(
                    """
                    SELECT * FROM mental_models
                    WHERE status = 'active'
                    ORDER BY prediction_accuracy DESC, created_at DESC
                    LIMIT $1
                    """,
                    max_models,
                )

        models = [self._row_to_model(row) for row in rows]

        # T078: Performance monitoring
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if elapsed_ms > 500:
            logger.warning(
                f"PERF: get_relevant_models exceeded 500ms | "
                f"elapsed={elapsed_ms:.1f}ms | models_found={len(models)}"
            )
        else:
            logger.debug(f"PERF: get_relevant_models | elapsed={elapsed_ms:.1f}ms")

        return models

    async def generate_prediction(
        self,
        model: MentalModel,
        context: dict[str, Any],
        inference_state_id: UUID | None = None,
    ) -> ModelPrediction:
        """
        Generate a prediction from a model given context.

        T026: Implementation
        T078: Performance optimized (<500ms target)
        Called during heartbeat OBSERVE phase (T033).

        Args:
            model: The mental model to use
            context: Context triggering the prediction
            inference_state_id: Optional link to active inference state

        Returns:
            Generated ModelPrediction

        Raises:
            ValueError: If model is not active
        """
        start_time = time.perf_counter()

        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        if model.status != ModelStatus.ACTIVE:
            raise ValueError(f"Model '{model.name}' is not active (status: {model.status.value})")

        # Generate prediction content using templates or basic logic
        prediction_content = self._generate_prediction_content(model, context)
        confidence = self._estimate_confidence(model, context)

        async with self._db_pool.acquire() as conn:
            try:
                # Call SQL function generate_model_prediction
                prediction_id = await conn.fetchval(
                    """
                    SELECT generate_model_prediction($1, $2, $3, $4, $5)
                    """,
                    model.id,
                    json.dumps(prediction_content),
                    json.dumps(context),
                    confidence,
                    inference_state_id,
                )

                # Fetch the created prediction
                row = await conn.fetchrow(
                    """
                    SELECT * FROM model_predictions WHERE id = $1
                    """,
                    prediction_id,
                )

                prediction = self._row_to_prediction(row)

                # ThoughtSeed Integration: Create ThoughtSeed from prediction
                await self._create_thoughtseed_from_prediction(
                    prediction=prediction,
                    model=model,
                    context=context,
                )

                # T078: Performance monitoring
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                if elapsed_ms > 500:
                    logger.warning(
                        f"PERF: generate_prediction exceeded 500ms | "
                        f"elapsed={elapsed_ms:.1f}ms | model={model.name}"
                    )
                else:
                    logger.info(
                        f"Generated prediction from model '{model.name}' "
                        f"(confidence={confidence:.2f}, elapsed={elapsed_ms:.1f}ms)"
                    )

                return prediction

            except Exception as e:
                error_msg = str(e)
                if "not active" in error_msg:
                    raise ValueError(error_msg)
                raise

    def _generate_prediction_content(
        self,
        model: MentalModel,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate prediction content from model templates.

        Uses template matching if templates exist, otherwise generates
        a basic prediction based on model domain.
        """
        user_message = context.get("user_message", "")

        # Try matching prediction templates
        if model.prediction_templates:
            for template in model.prediction_templates:
                trigger = template.trigger.lower()
                if trigger in user_message.lower():
                    return {
                        "source": "template",
                        "template_trigger": template.trigger,
                        "prediction": template.predict,
                        "suggestion": template.suggest,
                        "model_name": model.name,
                        "domain": model.domain.value,
                    }

        # No template match - generate basic prediction based on domain
        domain_predictions = {
            ModelDomain.USER: "User state prediction based on behavioral patterns",
            ModelDomain.SELF: "Internal state prediction based on self-model",
            ModelDomain.WORLD: "Environmental prediction based on world model",
            ModelDomain.TASK_SPECIFIC: "Task-related prediction based on context",
        }

        return {
            "source": "domain_default",
            "prediction": domain_predictions.get(model.domain, "General prediction"),
            "model_name": model.name,
            "domain": model.domain.value,
            "context_summary": user_message[:100] if user_message else None,
        }

    def _estimate_confidence(
        self,
        model: MentalModel,
        context: dict[str, Any],
    ) -> float:
        """
        Estimate confidence for a prediction.

        Based on model's historical accuracy and template matching.
        """
        base_confidence = model.prediction_accuracy or 0.5

        # Boost confidence if we have a template match
        user_message = context.get("user_message", "")
        if model.prediction_templates:
            for template in model.prediction_templates:
                if template.trigger.lower() in user_message.lower():
                    # Template match increases confidence
                    return min(0.9, base_confidence + 0.2)

        return base_confidence

    # =========================================================================
    # US2: Prediction Error Tracking
    # =========================================================================

    async def get_unresolved_predictions(
        self,
        model_id: UUID | None = None,
        limit: int = 50,
    ) -> list[ModelPrediction]:
        """
        Get predictions that haven't been resolved yet.

        T037: Implementation

        Args:
            model_id: Filter by specific model (optional)
            limit: Maximum results

        Returns:
            List of unresolved ModelPrediction instances
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            if model_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM model_predictions
                    WHERE model_id = $1 AND resolved_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    model_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM model_predictions
                    WHERE resolved_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )

        return [self._row_to_prediction(row) for row in rows]

    async def calculate_error(
        self,
        prediction: dict[str, Any],
        observation: dict[str, Any],
    ) -> float:
        """
        Calculate semantic error between prediction and observation.

        T038: Implementation (uses LLM for semantic comparison)

        Args:
            prediction: What the model predicted
            observation: What actually happened

        Returns:
            Error score between 0.0 (perfect) and 1.0 (completely wrong)
        """
        # Use LLM if available for semantic comparison
        if self._llm_client:
            try:
                return await self._calculate_error_with_llm(prediction, observation)
            except Exception as e:
                logger.warning(f"LLM error calculation failed, using heuristic: {e}")

        # Fall back to heuristic error calculation
        return self._calculate_error_heuristic(prediction, observation)

    async def _calculate_error_with_llm(
        self,
        prediction: dict[str, Any],
        observation: dict[str, Any],
    ) -> float:
        """Calculate error using LLM semantic comparison."""
        prompt = f"""Compare this prediction with the actual observation and rate the error.

Prediction: {json.dumps(prediction)}
Observation: {json.dumps(observation)}

Rate the prediction error from 0.0 to 1.0:
- 0.0 = perfect match (prediction exactly matched observation)
- 0.5 = partially correct (some aspects matched)
- 1.0 = completely wrong (nothing matched)

Respond with ONLY a number between 0.0 and 1.0."""

        # This would call the LLM client - placeholder for now
        # response = await self._llm_client.complete(prompt)
        # return float(response.strip())
        raise NotImplementedError("LLM client not implemented")

    def _calculate_error_heuristic(
        self,
        prediction: dict[str, Any],
        observation: dict[str, Any],
    ) -> float:
        """
        Calculate error using heuristic comparison.

        Simple comparison based on:
        - Exact key/value matches
        - String similarity for text values
        """
        if not prediction or not observation:
            return 0.5  # No data to compare

        # Get prediction and observation text
        pred_text = str(prediction.get("prediction", prediction))
        obs_text = str(observation.get("actual", observation.get("observation", observation)))

        # Check for explicit accuracy markers
        if observation.get("was_accurate") is True:
            return 0.1
        if observation.get("was_accurate") is False:
            return 0.9

        # Simple word overlap calculation
        pred_words = set(pred_text.lower().split())
        obs_words = set(obs_text.lower().split())

        if not pred_words or not obs_words:
            return 0.5

        overlap = len(pred_words & obs_words)
        total = len(pred_words | obs_words)

        if total == 0:
            return 0.5

        similarity = overlap / total
        error = 1.0 - similarity

        # Clamp to valid range
        return max(0.0, min(1.0, error))

    async def resolve_prediction(
        self,
        prediction_id: UUID,
        observation: dict[str, Any],
        prediction_error: float | None = None,
    ) -> ModelPrediction:
        """
        Resolve a prediction with its actual outcome.

        T039: Implementation
        Called during heartbeat ORIENT phase (T041).

        Args:
            prediction_id: UUID of the prediction to resolve
            observation: The actual outcome
            prediction_error: Pre-calculated error (if not provided, calculated)

        Returns:
            Updated ModelPrediction

        Raises:
            ValueError: If prediction not found or already resolved
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get the prediction first to get its content for error calculation
            row = await conn.fetchrow(
                """
                SELECT * FROM model_predictions WHERE id = $1
                """,
                prediction_id,
            )

            if not row:
                raise ValueError(f"Prediction not found: {prediction_id}")

            if row["resolved_at"] is not None:
                raise ValueError(f"Prediction already resolved: {prediction_id}")

            prediction_content = row["prediction"]
            if isinstance(prediction_content, str):
                prediction_content = json.loads(prediction_content)

            # Calculate error if not provided
            if prediction_error is None:
                prediction_error = await self.calculate_error(prediction_content, observation)

            # Call SQL function resolve_prediction
            try:
                await conn.execute(
                    """
                    SELECT resolve_prediction($1, $2, $3)
                    """,
                    prediction_id,
                    json.dumps(observation),
                    prediction_error,
                )
            except Exception as e:
                error_msg = str(e)
                if "already resolved" in error_msg:
                    raise ValueError(error_msg)
                raise

            # Fetch updated prediction
            updated_row = await conn.fetchrow(
                """
                SELECT * FROM model_predictions WHERE id = $1
                """,
                prediction_id,
            )

            prediction = self._row_to_prediction(updated_row)

            # T055: Enhanced audit logging for prediction resolution
            logger.info(
                f"AUDIT: Prediction resolved | "
                f"prediction_id={prediction_id} | "
                f"model_id={row['model_id']} | "
                f"prediction_error={prediction_error:.4f} | "
                f"confidence={prediction.confidence}"
            )

            # ThoughtSeed Integration: Apply CLAUSE strengthening to basins
            await self._strengthen_basins_from_resolution(
                prediction_id=prediction_id,
                prediction_error=prediction_error,
            )

            return prediction

    async def get_model_accuracy(self, model_id: UUID) -> float:
        """
        Get the current rolling accuracy for a model.

        T040: Implementation

        Args:
            model_id: UUID of the model

        Returns:
            Accuracy score between 0.0 and 1.0

        Raises:
            ValueError: If model not found
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT prediction_accuracy FROM mental_models WHERE id = $1
                """,
                model_id,
            )

            if not row:
                raise ValueError(f"Model not found: {model_id}")

            return row["prediction_accuracy"] or 0.5

    async def get_stale_predictions(
        self,
        ttl_hours: int = PREDICTION_TTL_HOURS,
        limit: int = 100,
    ) -> list[ModelPrediction]:
        """
        Get unresolved predictions that have exceeded the TTL.

        T076: Prediction timeout handling

        Args:
            ttl_hours: Hours after which a prediction is considered stale
            limit: Maximum predictions to return

        Returns:
            List of stale ModelPrediction instances
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        cutoff_time = datetime.utcnow() - timedelta(hours=ttl_hours)

        async with self._db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM model_predictions
                WHERE resolved_at IS NULL
                  AND created_at < $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                cutoff_time,
                limit,
            )

        return [self._row_to_prediction(row) for row in rows]

    async def expire_stale_predictions(
        self,
        ttl_hours: int = PREDICTION_TTL_HOURS,
        limit: int = 100,
    ) -> int:
        """
        Expire (auto-resolve) stale predictions that have exceeded TTL.

        T076: Prediction timeout handling

        Marks stale predictions as resolved with:
        - observation: {"status": "expired", "reason": "TTL exceeded"}
        - prediction_error: 0.5 (neutral - no impact on model accuracy)

        Args:
            ttl_hours: Hours after which a prediction is considered stale
            limit: Maximum predictions to expire in one call

        Returns:
            Number of predictions expired
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        cutoff_time = datetime.utcnow() - timedelta(hours=ttl_hours)
        expiration_observation = json.dumps({
            "status": "expired",
            "reason": "TTL exceeded",
            "ttl_hours": ttl_hours,
        })

        async with self._db_pool.acquire() as conn:
            # Update stale predictions to mark them as expired
            result = await conn.execute(
                """
                UPDATE model_predictions
                SET resolved_at = CURRENT_TIMESTAMP,
                    observation = $1::jsonb,
                    prediction_error = 0.5
                WHERE resolved_at IS NULL
                  AND created_at < $2
                LIMIT $3
                """,
                expiration_observation,
                cutoff_time,
                limit,
            )

            # Parse "UPDATE N" result
            expired_count = int(result.split()[-1]) if result else 0

        if expired_count > 0:
            logger.info(
                f"AUDIT: Expired {expired_count} stale predictions | "
                f"ttl_hours={ttl_hours} | cutoff={cutoff_time.isoformat()}"
            )

        return expired_count

    # =========================================================================
    # US3: Model Revision
    # =========================================================================

    async def flag_for_revision(
        self,
        model_id: UUID,
        trigger_type: RevisionTrigger,
        trigger_description: str | None = None,
        trigger_memory_id: UUID | None = None,
    ) -> ModelRevision:
        """
        Flag a model for revision due to errors or new evidence.

        T046: Implementation

        Args:
            model_id: UUID of the model
            trigger_type: What triggered the revision
            trigger_description: Human-readable description
            trigger_memory_id: Memory that triggered this (if applicable)

        Returns:
            Created ModelRevision record

        Raises:
            ValueError: If model not found
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            try:
                # Call SQL function flag_model_revision (creates revision record)
                revision_id = await conn.fetchval(
                    """
                    SELECT flag_model_revision($1, $2::revision_trigger, $3, $4, NULL, NULL)
                    """,
                    model_id,
                    trigger_type.value,
                    trigger_description,
                    trigger_memory_id,
                )

                # Fetch the created revision
                row = await conn.fetchrow(
                    """
                    SELECT * FROM model_revisions WHERE id = $1
                    """,
                    revision_id,
                )

                revision = self._row_to_revision(row)

                # T055: Enhanced audit logging for revision flagging
                logger.info(
                    f"AUDIT: Model flagged for revision | "
                    f"model_id={model_id} | "
                    f"revision_id={revision.id} | "
                    f"revision_number={revision.revision_number} | "
                    f"trigger={trigger_type.value} | "
                    f"trigger_description={trigger_description} | "
                    f"trigger_memory_id={trigger_memory_id}"
                )
                return revision

            except Exception as e:
                error_msg = str(e)
                if "Model not found" in error_msg:
                    raise ValueError(error_msg)
                raise

    async def get_models_needing_revision(self) -> list[MentalModel]:
        """
        Get models with high error rates that need revision.

        T047: Implementation
        Uses models_needing_revision view.

        Returns:
            List of MentalModel instances needing revision
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Use the models_needing_revision view (>50% avg error in last 7 days)
            view_rows = await conn.fetch(
                """
                SELECT id FROM models_needing_revision
                ORDER BY recent_avg_error DESC
                """
            )

            if not view_rows:
                return []

            # Fetch full model data for each
            model_ids = [row["id"] for row in view_rows]
            rows = await conn.fetch(
                """
                SELECT * FROM mental_models
                WHERE id = ANY($1)
                ORDER BY prediction_accuracy ASC
                """,
                model_ids,
            )

        return [self._row_to_model(row) for row in rows]

    async def apply_revision(
        self,
        model_id: UUID,
        request: ReviseModelRequest,
    ) -> ModelRevision:
        """
        Apply a revision to a model (add/remove basins).

        T048: Implementation

        Args:
            model_id: UUID of the model
            request: ReviseModelRequest with basin changes

        Returns:
            Created ModelRevision record

        Raises:
            ValueError: If model not found or would become empty
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            try:
                # Call SQL function flag_model_revision with basin changes
                revision_id = await conn.fetchval(
                    """
                    SELECT flag_model_revision(
                        $1,
                        'manual'::revision_trigger,
                        $2,
                        NULL,
                        $3,
                        $4
                    )
                    """,
                    model_id,
                    request.trigger_description,
                    list(request.add_basins) if request.add_basins else None,
                    list(request.remove_basins) if request.remove_basins else None,
                )

                # Fetch the created revision
                row = await conn.fetchrow(
                    """
                    SELECT * FROM model_revisions WHERE id = $1
                    """,
                    revision_id,
                )

                revision = self._row_to_revision(row)

                # T055: Enhanced audit logging for revision trail
                logger.info(
                    f"AUDIT: Model revision applied | "
                    f"model_id={model_id} | "
                    f"revision_id={revision.id} | "
                    f"revision_number={revision.revision_number} | "
                    f"trigger={revision.trigger} | "
                    f"basins_added={len(request.add_basins or [])} | "
                    f"basins_removed={len(request.remove_basins or [])} | "
                    f"accuracy_before={revision.accuracy_before} | "
                    f"accuracy_after={revision.accuracy_after}"
                )
                return revision

            except Exception as e:
                error_msg = str(e)
                if "Model not found" in error_msg:
                    raise ValueError(error_msg)
                if "Cannot remove all basins" in error_msg:
                    raise ValueError("Cannot remove all basins from model")
                raise

    # =========================================================================
    # US4: Model Management
    # =========================================================================

    async def update_model(
        self,
        model_id: UUID,
        request: UpdateModelRequest,
    ) -> MentalModel:
        """
        Update a model's properties.

        T060: Implementation
        T064: Status transition validation

        Args:
            model_id: UUID of the model
            request: UpdateModelRequest with changes

        Returns:
            Updated MentalModel

        Raises:
            ValueError: If model not found or invalid status transition
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get current model
            row = await conn.fetchrow(
                "SELECT * FROM mental_models WHERE id = $1",
                model_id,
            )

            if not row:
                raise ValueError(f"Model not found: {model_id}")

            current_status = ModelStatus(row["status"])

            # T064: Validate status transition if status is being changed
            if request.status and request.status != current_status:
                if not self.validate_status_transition(current_status, request.status):
                    raise ValueError(
                        f"Invalid status transition: {current_status.value} -> {request.status.value}"
                    )

            # Build update query dynamically
            updates = []
            params = [model_id]
            param_idx = 2

            if request.name is not None:
                updates.append(f"name = ${param_idx}")
                params.append(request.name)
                param_idx += 1

            if request.description is not None:
                updates.append(f"description = ${param_idx}")
                params.append(request.description)
                param_idx += 1

            if request.status is not None:
                updates.append(f"status = ${param_idx}::model_status")
                params.append(request.status.value)
                param_idx += 1

            if request.prediction_templates is not None:
                templates_jsonb = [
                    json.dumps(t.model_dump()) for t in request.prediction_templates
                ]
                updates.append(f"prediction_templates = ${param_idx}::jsonb[]")
                params.append(templates_jsonb)
                param_idx += 1

            if not updates:
                # No changes, return current model
                return self._row_to_model(row)

            updates.append("updated_at = CURRENT_TIMESTAMP")

            query = f"""
                UPDATE mental_models
                SET {", ".join(updates)}
                WHERE id = $1
                RETURNING *
            """

            updated_row = await conn.fetchrow(query, *params)

            logger.info(
                f"AUDIT: Model updated | "
                f"model_id={model_id} | "
                f"fields_updated={[u.split('=')[0].strip() for u in updates if 'updated_at' not in u]}"
            )
            return self._row_to_model(updated_row)

    async def deprecate_model(self, model_id: UUID) -> MentalModel:
        """
        Soft-delete a model by setting status to deprecated.

        T061: Implementation

        Args:
            model_id: UUID of the model

        Returns:
            Updated MentalModel with deprecated status

        Raises:
            ValueError: If model not found or cannot be deprecated
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get current model
            row = await conn.fetchrow(
                "SELECT * FROM mental_models WHERE id = $1",
                model_id,
            )

            if not row:
                raise ValueError(f"Model not found: {model_id}")

            current_status = ModelStatus(row["status"])

            # Only active models can be deprecated
            if current_status != ModelStatus.ACTIVE:
                raise ValueError(
                    f"Cannot deprecate model with status '{current_status.value}'. "
                    f"Only active models can be deprecated."
                )

            # Update status to deprecated
            updated_row = await conn.fetchrow(
                """
                UPDATE mental_models
                SET status = 'deprecated'::model_status, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *
                """,
                model_id,
            )

            logger.info(
                f"AUDIT: Model deprecated | "
                f"model_id={model_id} | "
                f"previous_status={current_status.value}"
            )
            return self._row_to_model(updated_row)

    async def check_model_health(self, model_id: UUID) -> tuple[bool, list[UUID]]:
        """
        Check if a model's constituent basins still exist.

        T077: Degraded model handling

        Args:
            model_id: UUID of the model to check

        Returns:
            Tuple of (is_healthy, missing_basin_ids)
            - is_healthy: True if all basins exist
            - missing_basin_ids: List of basin IDs that no longer exist
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT constituent_basins FROM mental_models WHERE id = $1",
                model_id,
            )

            if not row:
                raise ValueError(f"Model not found: {model_id}")

            basin_ids = row["constituent_basins"] or []

            if not basin_ids:
                return True, []

            # Check which basins still exist
            existing = await conn.fetch(
                "SELECT id FROM memory_clusters WHERE id = ANY($1)",
                basin_ids,
            )
            existing_ids = {r["id"] for r in existing}
            missing_ids = [bid for bid in basin_ids if bid not in existing_ids]

            return len(missing_ids) == 0, missing_ids

    async def get_degraded_models(self) -> list[tuple[MentalModel, list[UUID]]]:
        """
        Get all active models that have missing constituent basins.

        T077: Degraded model handling

        Returns:
            List of (model, missing_basin_ids) tuples
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get all active models
            model_rows = await conn.fetch(
                """
                SELECT * FROM mental_models
                WHERE status = 'active'
                """
            )

            # Get all memory_clusters IDs in one query
            all_basin_ids = []
            for row in model_rows:
                all_basin_ids.extend(row["constituent_basins"] or [])

            existing = await conn.fetch(
                "SELECT id FROM memory_clusters WHERE id = ANY($1)",
                list(set(all_basin_ids)),
            )
            existing_ids = {r["id"] for r in existing}

        degraded = []
        for row in model_rows:
            basin_ids = row["constituent_basins"] or []
            missing = [bid for bid in basin_ids if bid not in existing_ids]
            if missing:
                degraded.append((self._row_to_model(row), missing))

        return degraded

    async def deprecate_degraded_models(self) -> list[UUID]:
        """
        Find and deprecate models with missing constituent basins.

        T077: Degraded model handling

        Returns:
            List of model IDs that were deprecated
        """
        degraded_models = await self.get_degraded_models()
        deprecated_ids = []

        for model, missing_basins in degraded_models:
            try:
                await self.deprecate_model(model.id)
                deprecated_ids.append(model.id)

                logger.warning(
                    f"AUDIT: Model auto-deprecated due to missing basins | "
                    f"model_id={model.id} | "
                    f"model_name={model.name} | "
                    f"missing_basins={len(missing_basins)} | "
                    f"missing_basin_ids={[str(b) for b in missing_basins[:5]]}"
                )
            except ValueError:
                # Model already not active, skip
                pass

        if deprecated_ids:
            logger.info(
                f"AUDIT: Auto-deprecated {len(deprecated_ids)} degraded models"
            )

        return deprecated_ids

    # =========================================================================
    # Query Helpers
    # =========================================================================

    async def get_predictions_for_model(
        self,
        model_id: UUID,
        resolved: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PredictionListResponse:
        """
        Get predictions for a specific model.

        Args:
            model_id: UUID of the model
            resolved: Filter by resolution status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            PredictionListResponse with matching predictions
        """
        # TODO: Implement for T042
        raise NotImplementedError("get_predictions_for_model not yet implemented")

    async def get_revisions_for_model(
        self,
        model_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> RevisionListResponse:
        """
        Get revision history for a specific model.

        Args:
            model_id: UUID of the model
            limit: Maximum results
            offset: Pagination offset

        Returns:
            RevisionListResponse with revision history
        """
        # TODO: Implement for T054
        raise NotImplementedError("get_revisions_for_model not yet implemented")

    async def get_model_detail(self, model_id: UUID) -> ModelDetailResponse | None:
        """
        Get detailed model information including basins and templates.

        Args:
            model_id: UUID of the model

        Returns:
            ModelDetailResponse if found, None otherwise
        """
        # TODO: Implement for T032
        raise NotImplementedError("get_model_detail not yet implemented")

    # =========================================================================
    # Validation Helpers
    # =========================================================================

    async def validate_basin_ids(self, basin_ids: list[UUID]) -> list[UUID]:
        """
        Validate that all basin IDs exist in memory_clusters.

        T058: Basin existence validation

        Args:
            basin_ids: List of basin UUIDs to validate

        Returns:
            List of invalid basin IDs (empty if all valid)
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        if not basin_ids:
            return []

        async with self._db_pool.acquire() as conn:
            # Check which basin IDs exist in memory_clusters
            existing = await conn.fetch(
                """
                SELECT id FROM memory_clusters WHERE id = ANY($1)
                """,
                list(basin_ids),
            )

            existing_ids = {row["id"] for row in existing}
            invalid_ids = [bid for bid in basin_ids if bid not in existing_ids]

            return invalid_ids

    def validate_status_transition(
        self,
        current: ModelStatus,
        target: ModelStatus,
    ) -> bool:
        """
        Validate a status transition is allowed.

        T064: Status transition validation

        Valid transitions:
            draft -> active
            active -> deprecated
            deprecated -> active

        Args:
            current: Current model status
            target: Target status

        Returns:
            True if transition is valid
        """
        valid_transitions = {
            (ModelStatus.DRAFT, ModelStatus.ACTIVE),
            (ModelStatus.ACTIVE, ModelStatus.DEPRECATED),
            (ModelStatus.DEPRECATED, ModelStatus.ACTIVE),
        }
        return (current, target) in valid_transitions

    # =========================================================================
    # ThoughtSeed Integration
    # =========================================================================

    async def _create_thoughtseed_from_prediction(
        self,
        prediction: ModelPrediction,
        model: MentalModel,
        context: dict[str, Any],
    ) -> None:
        """
        Create a ThoughtSeed from a model prediction.

        Integrates predictions into the 5-layer ThoughtSeed hierarchy,
        allowing them to compete in the cognitive system.
        """
        try:
            from api.services.thoughtseed_integration import (
                get_thoughtseed_integration_service,
            )

            integration = get_thoughtseed_integration_service(self._db_pool)
            await integration.generate_thoughtseed_from_prediction(
                prediction_id=prediction.id,
                model_id=model.id,
                model_domain=model.domain.value,
                prediction_content=prediction.prediction,
                confidence=prediction.confidence,
                context=context,
            )
        except ImportError:
            logger.debug("ThoughtSeed integration not available")
        except Exception as e:
            # Don't fail prediction on integration error
            logger.warning(f"ThoughtSeed integration failed: {e}")

    async def _strengthen_basins_from_resolution(
        self,
        prediction_id: UUID,
        prediction_error: float,
    ) -> None:
        """
        Apply CLAUSE strengthening to constituent basins based on prediction accuracy.

        Low prediction error → Strengthen basins (positive feedback)
        High prediction error → Weaken basins slightly
        """
        try:
            from api.services.thoughtseed_integration import (
                get_thoughtseed_integration_service,
            )

            integration = get_thoughtseed_integration_service(self._db_pool)
            await integration.strengthen_basins_from_resolution(
                prediction_id=prediction_id,
                prediction_error=prediction_error,
            )
        except ImportError:
            logger.debug("ThoughtSeed integration not available")
        except Exception as e:
            # Don't fail resolution on integration error
            logger.warning(f"Basin strengthening failed: {e}")

    async def get_models_by_thoughtseed_winners(
        self,
        layer: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get Mental Models associated with winning ThoughtSeeds.

        This prioritizes models whose predictions have won in
        ThoughtSeed competition, indicating cognitive relevance.

        Args:
            layer: Optional ThoughtSeed layer filter
            limit: Maximum models to return

        Returns:
            List of model info dicts with ThoughtSeed context
        """
        try:
            from api.services.thoughtseed_integration import (
                get_thoughtseed_integration_service,
            )

            integration = get_thoughtseed_integration_service(self._db_pool)
            return await integration.get_relevant_models_from_thoughtseeds(
                layer=layer,
                competition_status="won",
                limit=limit,
            )
        except ImportError:
            logger.debug("ThoughtSeed integration not available")
            return []
        except Exception as e:
            logger.warning(f"ThoughtSeed model lookup failed: {e}")
            return []

    # =========================================================================
    # Database Row Converters
    # =========================================================================

    def _row_to_model(self, row) -> MentalModel:
        """Convert database row to MentalModel."""
        # Parse basin relationships from JSONB
        basin_rels_data = row.get("basin_relationships") or {"relationships": []}
        if isinstance(basin_rels_data, str):
            basin_rels_data = json.loads(basin_rels_data)
        basin_relationships = BasinRelationships(**basin_rels_data)

        # Parse prediction templates from JSONB array
        templates_raw = row.get("prediction_templates") or []
        prediction_templates = []
        for t in templates_raw:
            if isinstance(t, str):
                t = json.loads(t)
            prediction_templates.append(PredictionTemplate(**t))

        # Parse temporal_horizon interval to timedelta
        temporal_horizon = None
        if row.get("temporal_horizon"):
            # PostgreSQL intervals are returned as timedelta by asyncpg
            temporal_horizon = row["temporal_horizon"]

        return MentalModel(
            id=row["id"],
            name=row["name"],
            domain=ModelDomain(row["domain"]),
            description=row.get("description"),
            constituent_basins=row["constituent_basins"],
            basin_relationships=basin_relationships,
            prediction_templates=prediction_templates,
            explanatory_scope=row.get("explanatory_scope") or [],
            requires_sensory_input=row.get("requires_sensory_input", False),
            temporal_horizon=temporal_horizon,
            evidence_memories=row.get("evidence_memories") or [],
            prediction_accuracy=row.get("prediction_accuracy", 0.5),
            last_validated=row.get("last_validated"),
            revision_count=row.get("revision_count", 0),
            status=ModelStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_prediction(self, row) -> ModelPrediction:
        """Convert database row to ModelPrediction."""
        return ModelPrediction(
            id=row["id"],
            model_id=row["model_id"],
            prediction=row["prediction"],
            confidence=row.get("confidence", 0.5),
            context=row.get("context"),
            observation=row.get("observation"),
            prediction_error=row.get("prediction_error"),
            resolved_at=row.get("resolved_at"),
            inference_state_id=row.get("inference_state_id"),
            created_at=row["created_at"],
        )

    def _row_to_revision(self, row) -> ModelRevision:
        """Convert database row to ModelRevision."""
        return ModelRevision(
            id=row["id"],
            model_id=row["model_id"],
            trigger_type=RevisionTrigger(row["trigger_type"]),
            trigger_memory_id=row.get("trigger_memory_id"),
            trigger_description=row.get("trigger_description"),
            old_structure=row.get("old_structure"),
            new_structure=row.get("new_structure"),
            basins_added=row.get("basins_added") or [],
            basins_removed=row.get("basins_removed") or [],
            change_description=row.get("change_description"),
            prediction_error_before=row.get("prediction_error_before"),
            prediction_error_after=row.get("prediction_error_after"),
            created_at=row["created_at"],
        )

    # =========================================================================
    # Response Converters
    # =========================================================================

    def _to_model_response(self, model: MentalModel) -> ModelResponse:
        """Convert MentalModel to ModelResponse."""
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

    def _to_prediction_response(self, prediction: ModelPrediction) -> PredictionResponse:
        """Convert ModelPrediction to PredictionResponse."""
        return PredictionResponse(
            id=prediction.id,
            model_id=prediction.model_id,
            prediction=prediction.prediction,
            confidence=prediction.confidence,
            context=prediction.context,
            observation=prediction.observation,
            prediction_error=prediction.prediction_error,
            resolved_at=prediction.resolved_at,
            created_at=prediction.created_at,
        )

    def _to_revision_response(self, revision: ModelRevision) -> RevisionResponse:
        """Convert ModelRevision to RevisionResponse."""
        return RevisionResponse(
            id=revision.id,
            model_id=revision.model_id,
            trigger_type=revision.trigger_type,
            trigger_description=revision.trigger_description,
            basins_added=revision.basins_added,
            basins_removed=revision.basins_removed,
            change_description=revision.change_description,
            prediction_error_before=revision.prediction_error_before,
            prediction_error_after=revision.prediction_error_after,
            created_at=revision.created_at,
        )


# =============================================================================
# Service Factory
# =============================================================================

_model_service_instance: Optional[ModelService] = None


def get_model_service(db_pool=None, llm_client=None) -> ModelService:
    """Get or create the ModelService singleton."""
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService(db_pool=db_pool, llm_client=llm_client)
    elif db_pool is not None and _model_service_instance._db_pool is None:
        # Update pool if not set
        _model_service_instance._db_pool = db_pool
    return _model_service_instance


def reset_model_service() -> None:
    """Reset the ModelService singleton (for testing)."""
    global _model_service_instance
    _model_service_instance = None
