# Copyright 2025 Dionysus Project
# SPDX-License-Identifier: Apache-2.0

"""
Worldview Integration Service
Feature: 005-mental-models (US6 - Identity/Worldview Integration)
FRs: FR-014 through FR-020

Implements bidirectional flow between Mental Models and Identity/Worldview:
- Self-domain models inform identity_aspects
- World-domain models shape worldview_primitives
- Prediction errors update beliefs via precision-weighted accumulation
- Predictions are filtered by worldview alignment (Bayesian prior + gating)
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

logger = logging.getLogger("dionysus.worldview_integration")


class WorldviewIntegrationService:
    """
    Integrates Mental Models with Identity and Worldview systems.

    Based on Active Inference theory (Friston 2010):
    - Worldview = Generative Model priors
    - Prediction errors update beliefs (precision-weighted)
    - Beliefs filter/bias new predictions
    """

    def __init__(
        self,
        db_pool=None,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
        llm_client=None,
    ):
        self._db_pool = db_pool
        self._webhook_url = webhook_url
        self._webhook_secret = webhook_secret
        self._llm_client = llm_client

    # =========================================================================
    # FR-019: Prediction Filtering by Worldview
    # =========================================================================

    async def filter_prediction_by_worldview(
        self,
        prediction: dict,
        worldview_belief: str,
        base_confidence: float,
        alignment_threshold: float = 0.3,
        suppression_factor: float = 0.5,
    ) -> dict:
        """
        Apply Bayesian prior weighting and gating based on worldview alignment.

        FR-019: Flag predictions contradicting worldview (alignment < 0.3)

        Args:
            prediction: The prediction dict
            worldview_belief: The belief to check alignment against
            base_confidence: Original prediction confidence
            alignment_threshold: Below this, flag for review (default 0.3)
            suppression_factor: Multiply confidence by (1 - this) when flagged

        Returns:
            Dict with:
                - flagged_for_review: bool
                - suppression_factor: float (0.0 if not flagged)
                - alignment_score: float (0.0-1.0)
                - final_confidence: float (adjusted)
        """
        # Calculate alignment (semantic similarity)
        alignment_score = await self._calculate_alignment(prediction, worldview_belief)

        # Check if contradicting
        flagged = alignment_score < alignment_threshold

        # Calculate suppression
        actual_suppression = suppression_factor if flagged else 0.0

        # Bayesian prior weighting: base * worldview_confidence
        # For now, assume worldview_confidence would come from DB
        # Here we just apply the suppression
        final_confidence = base_confidence * (1 - actual_suppression)

        return {
            "flagged_for_review": flagged,
            "suppression_factor": actual_suppression,
            "alignment_score": alignment_score,
            "final_confidence": final_confidence,
        }

    async def _calculate_alignment(
        self, prediction: dict, worldview_belief: str
    ) -> float:
        """
        Calculate semantic alignment between prediction and worldview belief.

        Uses LLM if available, falls back to simple heuristics.
        """
        if self._llm_client:
            # Use LLM for semantic comparison
            prompt = f"""Rate the alignment between this prediction and belief on a scale of 0.0 to 1.0.
0.0 = completely contradicts, 0.5 = neutral/unrelated, 1.0 = strongly supports

Prediction: {json.dumps(prediction)}
Belief: {worldview_belief}

Return only a number between 0.0 and 1.0."""

            try:
                response = await self._llm_client.complete(prompt)
                score = float(response.strip())
                return max(0.0, min(1.0, score))
            except Exception as e:
                logger.warning(f"LLM alignment calculation failed: {e}")

        # Fallback: simple keyword overlap
        pred_text = json.dumps(prediction).lower()
        belief_lower = worldview_belief.lower()

        # Check for contradiction keywords
        contradiction_pairs = [
            ("crash", "efficient"),
            ("fail", "succeed"),
            ("never", "always"),
            ("impossible", "possible"),
        ]

        for neg, pos in contradiction_pairs:
            if neg in pred_text and pos in belief_lower:
                return 0.1  # Strong contradiction
            if pos in pred_text and neg in belief_lower:
                return 0.1

        # Check for overlap
        pred_words = set(pred_text.split())
        belief_words = set(belief_lower.split())
        overlap = len(pred_words & belief_words)

        if overlap > 3:
            return 0.7  # Good alignment
        elif overlap > 0:
            return 0.5  # Neutral
        else:
            return 0.4  # Unknown alignment

    # =========================================================================
    # FR-016: Record Prediction Errors
    # =========================================================================

    async def record_prediction_error(
        self,
        model_id: UUID,
        prediction_id: UUID,
        prediction_error: float,
        auto_update: bool = False,
    ) -> dict:
        """
        Record prediction error for linked worldviews.

        FR-016: Accumulate errors per worldview primitive

        Args:
            model_id: The mental model that made the prediction
            prediction_id: The resolved prediction
            prediction_error: Error score (0.0 = perfect, 1.0 = wrong)
            auto_update: If True, immediately check for worldview updates

        Returns:
            Dict with worldviews_affected and worldviews_updated counts
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT * FROM record_worldview_prediction_error($1, $2, $3, $4)
                """,
                model_id,
                prediction_id,
                prediction_error,
                auto_update,
            )

        logger.info(
            f"Recorded prediction error | "
            f"model_id={model_id} | "
            f"error={prediction_error:.2f} | "
            f"worldviews_affected={result['worldviews_affected']}"
        )

        return {
            "worldviews_affected": result["worldviews_affected"],
            "worldviews_updated": result["worldviews_updated"],
        }

    # =========================================================================
    # FR-017/FR-018: Precision-Weighted Updates
    # =========================================================================

    async def check_worldview_update(self, worldview_id: UUID) -> dict:
        """
        Check if a worldview primitive should be updated.

        FR-017: Uses precision-weighted error formula
        FR-018: Learning rate based on belief stability

        Returns:
            Dict with should_update, new_confidence, evidence_count
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM calculate_worldview_update($1)",
                worldview_id,
            )

        return {
            "should_update": result["should_update"],
            "new_confidence": float(result["new_confidence"]),
            "evidence_count": result["evidence_count"],
        }

    async def apply_worldview_update(self, worldview_id: UUID) -> dict:
        """
        Apply calculated update to worldview confidence.

        Returns:
            Dict with updated, old_confidence, new_confidence
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM apply_worldview_update($1)",
                worldview_id,
            )

        if result["updated"]:
            logger.info(
                f"Updated worldview confidence | "
                f"worldview_id={worldview_id} | "
                f"old={result['old_confidence']:.3f} → new={result['new_confidence']:.3f}"
            )

        return {
            "updated": result["updated"],
            "old_confidence": float(result["old_confidence"]),
            "new_confidence": float(result["new_confidence"]),
        }

    # =========================================================================
    # FR-020: Webhook Sync to Neo4j
    # =========================================================================

    async def send_prediction_resolved_webhook(
        self,
        model_id: UUID,
        model_domain: str,
        prediction_id: UUID,
        prediction_error: float,
        linked_worldview_ids: list[UUID] | None = None,
        linked_identity_ids: list[UUID] | None = None,
    ) -> bool:
        """
        Send webhook to n8n for Neo4j sync.

        FR-020: Sync model-identity/worldview relationships via webhooks

        Returns:
            True if webhook sent successfully
        """
        if not self._webhook_url:
            logger.debug("Webhook URL not configured, skipping sync")
            return False

        payload = {
            "event": "prediction_resolved",
            "model_id": str(model_id),
            "model_domain": model_domain,
            "prediction_id": str(prediction_id),
            "prediction_error": prediction_error,
            "linked_worldview_ids": [str(w) for w in (linked_worldview_ids or [])],
            "linked_identity_ids": [str(i) for i in (linked_identity_ids or [])],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Sign payload with HMAC-SHA256
        headers = {}
        if self._webhook_secret:
            signature = hmac.new(
                self._webhook_secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._webhook_url}/webhook/model-prediction-resolved",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

            logger.info(
                f"Sent prediction_resolved webhook | "
                f"model_id={model_id} | "
                f"domain={model_domain}"
            )
            return True

        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            return False

    # =========================================================================
    # Combined: Resolve with Propagation
    # =========================================================================

    async def resolve_prediction_with_propagation(
        self,
        prediction_id: UUID,
        observation: dict,
        prediction_error: float,
    ) -> dict:
        """
        Resolve a prediction and propagate error to linked worldviews/identity.

        Combines:
        - Recording error in PostgreSQL (FR-016)
        - Sending webhook to n8n (FR-020)

        This is the main entry point for prediction resolution.
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get prediction and model info
            prediction = await conn.fetchrow(
                """
                SELECT mp.*, mm.domain as model_domain
                FROM model_predictions mp
                JOIN mental_models mm ON mp.model_id = mm.id
                WHERE mp.id = $1
                """,
                prediction_id,
            )

            if not prediction:
                raise ValueError(f"Prediction not found: {prediction_id}")

            model_id = prediction["model_id"]
            model_domain = prediction["model_domain"]

            # Update prediction with resolution
            await conn.execute(
                """
                UPDATE model_predictions
                SET observation = $2,
                    prediction_error = $3,
                    resolved_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                prediction_id,
                json.dumps(observation),
                prediction_error,
            )

            # Update model accuracy (EMA)
            await conn.execute(
                """
                UPDATE mental_models
                SET prediction_accuracy = 0.9 * prediction_accuracy + 0.1 * (1 - $2),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                model_id,
                prediction_error,
            )

            # Get linked worldviews/identity
            linked_worldviews = await conn.fetch(
                "SELECT worldview_id FROM model_worldview_links WHERE model_id = $1",
                model_id,
            )
            linked_identity = await conn.fetch(
                "SELECT identity_aspect_id FROM model_identity_links WHERE model_id = $1",
                model_id,
            )

        # Record error for worldviews (FR-016)
        error_result = await self.record_prediction_error(
            model_id=model_id,
            prediction_id=prediction_id,
            prediction_error=prediction_error,
            auto_update=True,  # Immediately check for updates
        )

        # Send webhook for Neo4j sync (FR-020)
        webhook_sent = await self.send_prediction_resolved_webhook(
            model_id=model_id,
            model_domain=model_domain,
            prediction_id=prediction_id,
            prediction_error=prediction_error,
            linked_worldview_ids=[r["worldview_id"] for r in linked_worldviews],
            linked_identity_ids=[r["identity_aspect_id"] for r in linked_identity],
        )

        return {
            "prediction_id": str(prediction_id),
            "model_id": str(model_id),
            "prediction_error": prediction_error,
            "worldviews_affected": error_result["worldviews_affected"],
            "worldviews_updated": error_result["worldviews_updated"],
            "webhook_sent": webhook_sent,
        }


# =============================================================================
# Service Factory
# =============================================================================

_worldview_integration_instance: WorldviewIntegrationService | None = None


def get_worldview_integration_service(
    db_pool=None,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    llm_client=None,
) -> WorldviewIntegrationService:
    """Get or create the WorldviewIntegrationService singleton."""
    global _worldview_integration_instance
    if _worldview_integration_instance is None:
        _worldview_integration_instance = WorldviewIntegrationService(
            db_pool=db_pool,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
            llm_client=llm_client,
        )
    elif db_pool is not None and _worldview_integration_instance._db_pool is None:
        _worldview_integration_instance._db_pool = db_pool
    return _worldview_integration_instance


def reset_worldview_integration_service() -> None:
    """Reset the service singleton (for testing)."""
    global _worldview_integration_instance
    _worldview_integration_instance = None
