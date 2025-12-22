"""
Verification Service
Feature: 008-mosaeic-memory

Manages verification encounters - testing beliefs against reality.
During MOSAEIC Phase 5 (Verification), updated beliefs are tested
in new episodic contexts and outcomes are logged.

Verification flow:
1. Prediction made from belief → create_verification()
2. Observation made → resolve_verification()
3. Belief confidence updated based on prediction accuracy
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from api.models.mosaeic import VerificationEncounter
from api.services.db import get_db_pool

logger = logging.getLogger(__name__)


@dataclass
class VerificationConfig:
    """Configuration for verification service."""
    # Hours until unresolved verification expires
    default_ttl_hours: int = 24

    # Maximum pending verifications per belief
    max_pending_per_belief: int = 5

    # Batch size for expiration queries
    expiration_batch_size: int = 100

    # Whether to update belief confidence on resolution
    auto_update_confidence: bool = True


@dataclass
class VerificationResult:
    """Result of a verification resolution."""
    encounter_id: UUID
    belief_id: UUID
    prediction_correct: bool
    prediction_error: float
    belief_activated: str  # 'old' or 'new'


class VerificationService:
    """
    Manages verification encounters for belief testing.

    Verification encounters log when predictions are made and
    track whether they match observations. This feeds into
    the accuracy protocol for semantic memory.
    """

    def __init__(self, config: VerificationConfig | None = None):
        self.config = config or VerificationConfig()

    async def create_verification(
        self,
        belief_id: UUID,
        prediction_id: UUID,
        prediction_content: dict[str, Any],
        session_id: UUID,
        timestamp: datetime | None = None,
    ) -> VerificationEncounter:
        """
        Create a verification encounter.

        Called when a prediction is made from a belief. The encounter
        remains pending until an observation resolves it.

        Args:
            belief_id: The belief being tested
            prediction_id: The prediction ID
            prediction_content: The prediction details
            session_id: Current session
            timestamp: Optional explicit timestamp

        Returns:
            The created VerificationEncounter
        """
        pool = await get_db_pool()
        ts = timestamp or datetime.utcnow()

        # Check pending count limit
        pending_count = await pool.fetchval(
            """
            SELECT COUNT(*) FROM verification_encounters
            WHERE belief_id = $1 AND observation IS NULL
            """,
            belief_id,
        )

        if pending_count >= self.config.max_pending_per_belief:
            logger.warning(
                f"Belief {belief_id} has {pending_count} pending verifications, "
                f"limit is {self.config.max_pending_per_belief}"
            )

        row = await pool.fetchrow(
            """
            INSERT INTO verification_encounters (
                belief_id,
                prediction_id,
                prediction_content,
                session_id,
                timestamp
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            belief_id,
            prediction_id,
            prediction_content,
            session_id,
            ts,
        )

        encounter = self._row_to_encounter(row)

        logger.debug(
            f"Created verification {encounter.id} for belief {belief_id}"
        )

        return encounter

    async def resolve_verification(
        self,
        encounter_id: UUID,
        observation: dict[str, Any],
        belief_activated: str = "new",
        prediction_error: float | None = None,
    ) -> VerificationResult:
        """
        Resolve a verification encounter with an observation.

        Updates the encounter with the outcome and optionally
        updates the belief's confidence.

        Args:
            encounter_id: The encounter to resolve
            observation: The actual outcome observed
            belief_activated: 'old' or 'new' belief version activated
            prediction_error: Error magnitude (0.0 - 1.0)

        Returns:
            VerificationResult with outcome details
        """
        pool = await get_db_pool()

        # Get encounter and validate
        row = await pool.fetchrow(
            "SELECT * FROM verification_encounters WHERE id = $1",
            encounter_id,
        )

        if not row:
            raise ValueError(f"Verification {encounter_id} not found")

        if row["observation"] is not None:
            raise ValueError(f"Verification {encounter_id} already resolved")

        # Calculate prediction error if not provided
        if prediction_error is None:
            prediction_error = self._calculate_prediction_error(
                row["prediction_content"],
                observation,
            )

        # Determine if prediction was correct
        prediction_correct = prediction_error < 0.5

        # Update encounter
        await pool.execute(
            """
            UPDATE verification_encounters
            SET
                observation = $2,
                belief_activated = $3,
                prediction_error = $4
            WHERE id = $1
            """,
            encounter_id,
            observation,
            belief_activated,
            prediction_error,
        )

        # Update belief confidence if configured
        if self.config.auto_update_confidence:
            await self._update_belief_confidence(
                row["belief_id"],
                prediction_correct,
            )

        result = VerificationResult(
            encounter_id=encounter_id,
            belief_id=row["belief_id"],
            prediction_correct=prediction_correct,
            prediction_error=prediction_error,
            belief_activated=belief_activated,
        )

        logger.info(
            f"Resolved verification {encounter_id}: "
            f"correct={prediction_correct}, error={prediction_error:.3f}"
        )

        return result

    def _calculate_prediction_error(
        self,
        prediction: dict[str, Any],
        observation: dict[str, Any],
    ) -> float:
        """
        Calculate prediction error between predicted and observed.

        Simple implementation comparing shared keys.
        Override for domain-specific error calculation.

        Args:
            prediction: The prediction content
            observation: The observation content

        Returns:
            Error magnitude 0.0 - 1.0
        """
        # If explicit match field exists
        if "matches" in observation:
            return 0.0 if observation["matches"] else 1.0

        # If explicit error field exists
        if "error" in observation:
            return min(1.0, max(0.0, observation["error"]))

        # Compare shared keys
        shared_keys = set(prediction.keys()) & set(observation.keys())

        if not shared_keys:
            return 0.5  # Unknown

        matches = 0
        for key in shared_keys:
            if prediction[key] == observation[key]:
                matches += 1

        return 1.0 - (matches / len(shared_keys))

    async def _update_belief_confidence(
        self,
        belief_id: UUID,
        prediction_correct: bool,
    ) -> None:
        """Update belief confidence based on prediction outcome."""
        pool = await get_db_pool()

        if prediction_correct:
            await pool.execute(
                """
                UPDATE belief_rewrites
                SET
                    prediction_success_count = prediction_success_count + 1,
                    last_verified = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                belief_id,
            )
        else:
            await pool.execute(
                """
                UPDATE belief_rewrites
                SET
                    prediction_failure_count = prediction_failure_count + 1,
                    last_verified = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                belief_id,
            )

        # Recalculate adaptiveness score
        await pool.execute(
            """
            UPDATE belief_rewrites
            SET adaptiveness_score = CASE
                WHEN prediction_success_count + prediction_failure_count = 0 THEN 0.5
                ELSE prediction_success_count::FLOAT / (
                    prediction_success_count + prediction_failure_count
                )
            END
            WHERE id = $1
            """,
            belief_id,
        )

    async def get_pending_verifications(
        self,
        belief_id: UUID | None = None,
        session_id: UUID | None = None,
        limit: int = 50,
    ) -> list[VerificationEncounter]:
        """
        Get unresolved verification encounters.

        Args:
            belief_id: Optional filter by belief
            session_id: Optional filter by session
            limit: Max results

        Returns:
            List of pending VerificationEncounter objects
        """
        pool = await get_db_pool()

        conditions = ["observation IS NULL"]
        params = []
        param_idx = 1

        if belief_id:
            conditions.append(f"belief_id = ${param_idx}")
            params.append(belief_id)
            param_idx += 1

        if session_id:
            conditions.append(f"session_id = ${param_idx}")
            params.append(session_id)
            param_idx += 1

        query = f"""
            SELECT * FROM verification_encounters
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT ${param_idx}
        """
        params.append(limit)

        rows = await pool.fetch(query, *params)

        return [self._row_to_encounter(row) for row in rows]

    async def get_verification(
        self,
        encounter_id: UUID,
    ) -> VerificationEncounter | None:
        """Get a verification encounter by ID."""
        pool = await get_db_pool()

        row = await pool.fetchrow(
            "SELECT * FROM verification_encounters WHERE id = $1",
            encounter_id,
        )

        if not row:
            return None

        return self._row_to_encounter(row)

    async def get_verifications_for_belief(
        self,
        belief_id: UUID,
        include_pending: bool = True,
        limit: int = 50,
    ) -> list[VerificationEncounter]:
        """
        Get verification history for a belief.

        Args:
            belief_id: The belief ID
            include_pending: Include unresolved encounters
            limit: Max results

        Returns:
            List of VerificationEncounter objects
        """
        pool = await get_db_pool()

        if include_pending:
            query = """
                SELECT * FROM verification_encounters
                WHERE belief_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """
        else:
            query = """
                SELECT * FROM verification_encounters
                WHERE belief_id = $1 AND observation IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT $2
            """

        rows = await pool.fetch(query, belief_id, limit)

        return [self._row_to_encounter(row) for row in rows]

    async def expire_stale_verifications(
        self,
        ttl_hours: int | None = None,
    ) -> int:
        """
        Expire (delete) stale unresolved verifications.

        Verifications older than TTL that haven't been resolved
        are removed to prevent memory bloat.

        Args:
            ttl_hours: Hours until expiration (default: config value)

        Returns:
            Number of expired verifications
        """
        ttl = ttl_hours or self.config.default_ttl_hours
        pool = await get_db_pool()

        result = await pool.execute(
            """
            DELETE FROM verification_encounters
            WHERE observation IS NULL
            AND timestamp < (CURRENT_TIMESTAMP - ($1 || ' hours')::INTERVAL)
            """,
            str(ttl),
        )

        # Parse "DELETE N" to get count
        deleted = int(result.split()[-1]) if result else 0

        if deleted > 0:
            logger.info(f"Expired {deleted} stale verifications (TTL: {ttl}h)")

        return deleted

    async def get_stale_verifications(
        self,
        ttl_hours: int | None = None,
        limit: int | None = None,
    ) -> list[VerificationEncounter]:
        """
        Get verifications that would be expired.

        Args:
            ttl_hours: Hours until considered stale
            limit: Max results

        Returns:
            List of stale VerificationEncounter objects
        """
        ttl = ttl_hours or self.config.default_ttl_hours
        max_results = limit or self.config.expiration_batch_size
        pool = await get_db_pool()

        rows = await pool.fetch(
            """
            SELECT * FROM verification_encounters
            WHERE observation IS NULL
            AND timestamp < (CURRENT_TIMESTAMP - ($1 || ' hours')::INTERVAL)
            ORDER BY timestamp ASC
            LIMIT $2
            """,
            str(ttl),
            max_results,
        )

        return [self._row_to_encounter(row) for row in rows]

    async def get_verification_statistics(
        self,
        belief_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get verification statistics.

        Args:
            belief_id: Optional filter by belief

        Returns:
            Statistics dictionary
        """
        pool = await get_db_pool()

        if belief_id:
            stats = await pool.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE observation IS NULL) AS pending,
                    COUNT(*) FILTER (WHERE observation IS NOT NULL) AS resolved,
                    COUNT(*) FILTER (
                        WHERE prediction_error IS NOT NULL AND prediction_error < 0.5
                    ) AS correct,
                    COUNT(*) FILTER (
                        WHERE prediction_error IS NOT NULL AND prediction_error >= 0.5
                    ) AS incorrect,
                    AVG(prediction_error) FILTER (
                        WHERE prediction_error IS NOT NULL
                    ) AS avg_error
                FROM verification_encounters
                WHERE belief_id = $1
                """,
                belief_id,
            )
        else:
            stats = await pool.fetchrow("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE observation IS NULL) AS pending,
                    COUNT(*) FILTER (WHERE observation IS NOT NULL) AS resolved,
                    COUNT(*) FILTER (
                        WHERE prediction_error IS NOT NULL AND prediction_error < 0.5
                    ) AS correct,
                    COUNT(*) FILTER (
                        WHERE prediction_error IS NOT NULL AND prediction_error >= 0.5
                    ) AS incorrect,
                    AVG(prediction_error) FILTER (
                        WHERE prediction_error IS NOT NULL
                    ) AS avg_error
                FROM verification_encounters
            """)

        resolved = stats["resolved"] or 0
        correct = stats["correct"] or 0

        return {
            "total": stats["total"],
            "pending": stats["pending"],
            "resolved": resolved,
            "correct_predictions": correct,
            "incorrect_predictions": stats["incorrect"] or 0,
            "accuracy": correct / resolved if resolved > 0 else 0.0,
            "average_error": float(stats["avg_error"]) if stats["avg_error"] else 0.0,
            "config": {
                "default_ttl_hours": self.config.default_ttl_hours,
                "max_pending_per_belief": self.config.max_pending_per_belief,
            },
        }

    def _row_to_encounter(self, row) -> VerificationEncounter:
        """Convert database row to VerificationEncounter model."""
        return VerificationEncounter(
            id=row["id"],
            belief_id=row["belief_id"],
            prediction_id=row["prediction_id"],
            prediction_content=row["prediction_content"],
            observation=row["observation"],
            belief_activated=row["belief_activated"],
            prediction_error=row["prediction_error"],
            session_id=row["session_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
        )


# Global service instance
_verification_service: VerificationService | None = None


def get_verification_service() -> VerificationService:
    """Get the global verification service instance."""
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
