"""
ThoughtSeed Integration Service
Feature: 005-mental-models (Enhanced Integration)

Connects Mental Models to ThoughtSeed 5-layer hierarchy:
- Predictions → ThoughtSeeds at conceptual/abstract layers
- ThoughtSeed competition winners → Basin activation
- Prediction resolution → Basin strengthening (CLAUSE)

This creates bidirectional flow between Mental Models and ThoughtSeeds.
"""

import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger("dionysus.thoughtseed_integration")


# =============================================================================
# ThoughtSeed Layer Mapping
# =============================================================================

# Mental Model domains map to ThoughtSeed layers
DOMAIN_TO_LAYER = {
    "user": "conceptual",      # User model predictions → conceptual processing
    "self": "metacognitive",   # Self-model predictions → metacognitive layer
    "world": "abstract",       # World model predictions → abstract reasoning
    "task_specific": "perceptual",  # Task predictions → pattern recognition
}

# Prediction confidence maps to activation level
def confidence_to_activation(confidence: float) -> float:
    """Convert prediction confidence (0-1) to ThoughtSeed activation (0-1)."""
    # Slight boost to ensure predictions compete effectively
    return min(1.0, confidence * 1.2)


# =============================================================================
# ThoughtSeed Integration Service
# =============================================================================


class ThoughtSeedIntegrationService:
    """
    Integrates Mental Models with ThoughtSeed cognitive hierarchy.

    Key integration points:
    1. generate_thoughtseed_from_prediction: Create ThoughtSeed from model prediction
    2. activate_basins_from_winner: When ThoughtSeed wins, activate constituent basins
    3. strengthen_basins_from_resolution: Apply CLAUSE strengthening on resolution
    4. get_relevant_models_from_thoughtseeds: Find models matching active ThoughtSeeds
    """

    def __init__(self, db_pool=None):
        """Initialize with database connection pool."""
        self._db_pool = db_pool

    async def generate_thoughtseed_from_prediction(
        self,
        prediction_id: UUID,
        model_id: UUID,
        model_domain: str,
        prediction_content: dict,
        confidence: float,
        context: dict | None = None,
    ) -> dict:
        """
        Create a ThoughtSeed from a model prediction.

        This allows predictions to compete in the cognitive hierarchy,
        connecting Mental Models to the 5-layer ThoughtSeed system.

        Args:
            prediction_id: UUID of the model prediction
            model_id: UUID of the source mental model
            model_domain: Domain of the model (user/self/world/task_specific)
            prediction_content: The prediction dict
            confidence: Prediction confidence
            context: Optional context that triggered prediction

        Returns:
            Created ThoughtSeed dict with id, layer, activation_level
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        # Map domain to ThoughtSeed layer
        layer = DOMAIN_TO_LAYER.get(model_domain, "conceptual")

        # Build neuronal packet (cognitive content)
        neuronal_packet = {
            "source": "mental_model_prediction",
            "prediction_id": str(prediction_id),
            "model_id": str(model_id),
            "model_domain": model_domain,
            "prediction": prediction_content,
            "context": context,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Calculate activation level from confidence
        activation_level = confidence_to_activation(confidence)

        async with self._db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO thoughtseeds (
                    layer, neuronal_packet, activation_level, competition_status
                )
                VALUES ($1::thoughtseed_layer, $2, $3, 'pending')
                RETURNING id, layer, activation_level, competition_status
                """,
                layer,
                json.dumps(neuronal_packet),
                activation_level,
            )

        logger.info(
            f"Created ThoughtSeed from prediction | "
            f"thoughtseed_id={row['id']} | "
            f"layer={layer} | "
            f"activation={activation_level:.2f} | "
            f"model_id={model_id}"
        )

        return {
            "id": str(row["id"]),
            "layer": row["layer"],
            "activation_level": float(row["activation_level"]),
            "competition_status": row["competition_status"],
            "source_prediction_id": str(prediction_id),
            "source_model_id": str(model_id),
        }

    async def activate_basins_from_winner(
        self,
        thoughtseed_id: UUID,
        activation_strength: float = 0.5,
    ) -> list[dict]:
        """
        When a ThoughtSeed wins competition, activate its source model's basins.

        This connects ThoughtSeed winner selection back to basin activation,
        creating a feedback loop between cognitive layers and memory clusters.

        Args:
            thoughtseed_id: UUID of the winning ThoughtSeed
            activation_strength: Strength to apply to basin activation

        Returns:
            List of activated basins with new states
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get ThoughtSeed and extract model reference
            thoughtseed = await conn.fetchrow(
                """
                SELECT id, neuronal_packet, competition_status
                FROM thoughtseeds WHERE id = $1
                """,
                thoughtseed_id,
            )

            if not thoughtseed:
                raise ValueError(f"ThoughtSeed not found: {thoughtseed_id}")

            if thoughtseed["competition_status"] != "won":
                logger.debug(f"ThoughtSeed {thoughtseed_id} is not a winner, skipping activation")
                return []

            # Parse neuronal packet to get model_id
            packet = thoughtseed["neuronal_packet"]
            if isinstance(packet, str):
                packet = json.loads(packet)

            model_id_str = packet.get("model_id")
            if not model_id_str:
                logger.debug(f"ThoughtSeed {thoughtseed_id} has no source model")
                return []

            model_id = UUID(model_id_str)

            # Get model's constituent basins
            model = await conn.fetchrow(
                """
                SELECT constituent_basins FROM mental_models WHERE id = $1
                """,
                model_id,
            )

            if not model or not model["constituent_basins"]:
                logger.warning(f"Model {model_id} not found or has no basins")
                return []

            basin_ids = model["constituent_basins"]

            # Activate each basin using the activate_basin SQL function
            activated = []
            for basin_id in basin_ids:
                try:
                    result = await conn.fetchrow(
                        "SELECT * FROM activate_basin($1, $2)",
                        basin_id,
                        activation_strength,
                    )
                    activated.append({
                        "basin_id": str(basin_id),
                        "new_state": result["new_state"],
                        "new_activation": float(result["new_activation"]),
                        "clause_strength": float(result["new_clause_strength"]),
                    })
                except Exception as e:
                    logger.warning(f"Failed to activate basin {basin_id}: {e}")

        logger.info(
            f"Activated {len(activated)} basins from ThoughtSeed winner | "
            f"thoughtseed_id={thoughtseed_id} | "
            f"model_id={model_id}"
        )

        return activated

    async def strengthen_basins_from_resolution(
        self,
        prediction_id: UUID,
        prediction_error: float,
    ) -> list[dict]:
        """
        Apply CLAUSE strengthening to basins based on prediction accuracy.

        When a prediction is resolved:
        - Low error (accurate) → Strengthen basins (positive feedback)
        - High error (inaccurate) → Slightly weaken basins

        Args:
            prediction_id: UUID of the resolved prediction
            prediction_error: Error score (0.0 = perfect, 1.0 = completely wrong)

        Returns:
            List of basin updates with new CLAUSE strengths
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        # Calculate CLAUSE adjustment based on error
        # Low error → positive adjustment (strengthen)
        # High error → negative adjustment (weaken)
        clause_adjustment = (0.5 - prediction_error) * 0.2  # Range: -0.1 to +0.1

        async with self._db_pool.acquire() as conn:
            # Get prediction's model
            prediction = await conn.fetchrow(
                """
                SELECT model_id FROM model_predictions WHERE id = $1
                """,
                prediction_id,
            )

            if not prediction:
                raise ValueError(f"Prediction not found: {prediction_id}")

            model_id = prediction["model_id"]

            # Get model's constituent basins
            model = await conn.fetchrow(
                """
                SELECT constituent_basins FROM mental_models WHERE id = $1
                """,
                model_id,
            )

            if not model or not model["constituent_basins"]:
                return []

            basin_ids = model["constituent_basins"]

            # Adjust CLAUSE strength for each basin
            updated = []
            for basin_id in basin_ids:
                try:
                    result = await conn.fetchrow(
                        """
                        UPDATE memory_clusters
                        SET clause_strength = GREATEST(0.1, LEAST(2.0,
                            clause_strength + $2
                        )),
                        updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        RETURNING id, clause_strength
                        """,
                        basin_id,
                        clause_adjustment,
                    )
                    if result:
                        updated.append({
                            "basin_id": str(basin_id),
                            "new_clause_strength": float(result["clause_strength"]),
                            "adjustment": clause_adjustment,
                        })
                except Exception as e:
                    logger.warning(f"Failed to update CLAUSE for basin {basin_id}: {e}")

        if updated:
            logger.info(
                f"CLAUSE adjustment from prediction resolution | "
                f"prediction_id={prediction_id} | "
                f"error={prediction_error:.2f} | "
                f"adjustment={clause_adjustment:+.3f} | "
                f"basins_updated={len(updated)}"
            )

        return updated

    async def get_relevant_models_from_thoughtseeds(
        self,
        layer: str | None = None,
        competition_status: str = "won",
        limit: int = 5,
    ) -> list[dict]:
        """
        Find Mental Models associated with active/winning ThoughtSeeds.

        This allows the system to prioritize models whose predictions
        have won in ThoughtSeed competition.

        Args:
            layer: Optional ThoughtSeed layer filter
            competition_status: Filter by competition status (default: won)
            limit: Maximum models to return

        Returns:
            List of model info dicts with ThoughtSeed context
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Build query based on filters
            query_parts = [
                """
                SELECT DISTINCT ON (model_id)
                    t.id as thoughtseed_id,
                    t.layer,
                    t.activation_level,
                    t.neuronal_packet,
                    t.competition_status,
                    t.created_at
                FROM thoughtseeds t
                WHERE t.competition_status = $1
                  AND t.neuronal_packet->>'source' = 'mental_model_prediction'
                """
            ]
            params = [competition_status]
            param_idx = 2

            if layer:
                query_parts.append(f"AND t.layer = ${param_idx}::thoughtseed_layer")
                params.append(layer)
                param_idx += 1

            query_parts.append(f"ORDER BY model_id, t.activation_level DESC LIMIT ${param_idx}")
            params.append(limit)

            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)

            # Extract model info from each ThoughtSeed
            results = []
            for row in rows:
                packet = row["neuronal_packet"]
                if isinstance(packet, str):
                    packet = json.loads(packet)

                model_id_str = packet.get("model_id")
                if not model_id_str:
                    continue

                # Get model details
                model = await conn.fetchrow(
                    """
                    SELECT id, name, domain, status, prediction_accuracy
                    FROM mental_models WHERE id = $1
                    """,
                    UUID(model_id_str),
                )

                if model:
                    results.append({
                        "model_id": str(model["id"]),
                        "model_name": model["name"],
                        "model_domain": model["domain"],
                        "model_status": model["status"],
                        "prediction_accuracy": float(model["prediction_accuracy"] or 0.5),
                        "thoughtseed_id": str(row["thoughtseed_id"]),
                        "thoughtseed_layer": row["layer"],
                        "thoughtseed_activation": float(row["activation_level"]),
                    })

        return results

    async def run_prediction_competition(self, layer: str) -> dict | None:
        """
        Run ThoughtSeed competition for prediction-sourced ThoughtSeeds.

        This integrates Mental Model predictions into the cognitive hierarchy
        competition mechanism.

        Args:
            layer: ThoughtSeed layer to run competition for

        Returns:
            Competition result with winner, or None if no competitors
        """
        if not self._db_pool:
            raise RuntimeError("Database pool not configured")

        async with self._db_pool.acquire() as conn:
            # Get competing ThoughtSeeds at this layer
            competitors = await conn.fetch(
                """
                SELECT id, activation_level, neuronal_packet
                FROM thoughtseeds
                WHERE layer = $1::thoughtseed_layer
                  AND competition_status IN ('pending', 'competing')
                ORDER BY activation_level DESC
                """,
                layer,
            )

            if not competitors:
                return None

            # Winner is highest activation
            winner = competitors[0]
            loser_ids = [c["id"] for c in competitors[1:]]

            # Update statuses
            await conn.execute(
                "UPDATE thoughtseeds SET competition_status = 'won' WHERE id = $1",
                winner["id"],
            )

            if loser_ids:
                await conn.execute(
                    "UPDATE thoughtseeds SET competition_status = 'lost' WHERE id = ANY($1)",
                    loser_ids,
                )

            # Record competition
            competition_id = await conn.fetchval(
                """
                INSERT INTO thoughtseed_competitions (
                    competitor_ids, winner_id, layer, competition_energy
                )
                VALUES ($1, $2, $3::thoughtseed_layer, $4)
                RETURNING id
                """,
                [c["id"] for c in competitors],
                winner["id"],
                layer,
                sum(c["activation_level"] for c in competitors),
            )

            # Activate basins from winner (if it's from a mental model)
            activated_basins = await self.activate_basins_from_winner(
                winner["id"],
                activation_strength=0.3,  # Moderate activation from competition win
            )

        result = {
            "competition_id": str(competition_id),
            "layer": layer,
            "competitors": len(competitors),
            "winner": {
                "id": str(winner["id"]),
                "activation_level": float(winner["activation_level"]),
            },
            "activated_basins": len(activated_basins),
        }

        logger.info(
            f"Prediction competition completed | "
            f"layer={layer} | "
            f"winner={winner['id']} | "
            f"basins_activated={len(activated_basins)}"
        )

        return result


# =============================================================================
# Service Factory
# =============================================================================

_thoughtseed_integration_instance: ThoughtSeedIntegrationService | None = None


def get_thoughtseed_integration_service(db_pool=None) -> ThoughtSeedIntegrationService:
    """Get or create the ThoughtSeedIntegrationService singleton."""
    global _thoughtseed_integration_instance
    if _thoughtseed_integration_instance is None:
        _thoughtseed_integration_instance = ThoughtSeedIntegrationService(db_pool=db_pool)
    elif db_pool is not None and _thoughtseed_integration_instance._db_pool is None:
        _thoughtseed_integration_instance._db_pool = db_pool
    return _thoughtseed_integration_instance


def reset_thoughtseed_integration_service() -> None:
    """Reset the ThoughtSeedIntegrationService singleton (for testing)."""
    global _thoughtseed_integration_instance
    _thoughtseed_integration_instance = None
