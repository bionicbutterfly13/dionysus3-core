"""
Episodic Decay Service
Feature: 008-mosaeic-memory

Implements time-based decay for episodic memories (efficiency protocol).
Old captures are pruned unless marked as Turning Points (preserve_indefinitely=True).

Decay rates are differential by experiential dimension:
- Senses decay fastest (peripheral details)
- Mental content decays slowest (central gist)
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from api.models.mosaeic import (
    DEFAULT_DECAY_RATES,
    ExperientialDimension,
    FiveWindowCapture,
)
from api.services.db import get_db_pool

logger = logging.getLogger(__name__)


@dataclass
class EpisodicDecayConfig:
    """Configuration for episodic decay behavior."""
    # Age threshold for complete removal (days)
    full_decay_threshold_days: int = 180

    # Whether to apply differential dimension decay before removal
    apply_dimension_decay: bool = True

    # Minimum intensity to resist early dimension decay
    intensity_decay_resistance: float = 7.0

    # Batch size for decay operations
    batch_size: int = 100

    # Whether to log each decayed capture
    verbose_logging: bool = False


@dataclass
class DecayCandidate:
    """A capture eligible for decay."""
    id: UUID
    session_id: UUID
    age_days: int
    emotional_intensity: float
    preserve_indefinitely: bool
    created_at: datetime

    # Dimension values for differential decay
    mental: str | None = None
    observation: str | None = None
    senses: str | None = None
    actions: str | None = None
    emotions: str | None = None


@dataclass
class DecayResult:
    """Result of a decay operation."""
    candidates_found: int
    fully_decayed: int
    dimensions_decayed: int
    errors: list[str]
    duration_ms: float


class EpisodicDecayService:
    """
    Manages time-based decay for episodic memories.

    Implements the MOSAEIC efficiency protocol:
    - Captures older than threshold are candidates for decay
    - Turning Points (preserve_indefinitely=True) are exempt
    - High emotional intensity provides partial resistance
    - Differential decay rates apply to each dimension
    """

    def __init__(self, config: EpisodicDecayConfig | None = None):
        self.config = config or EpisodicDecayConfig()
        self._decay_rates = {
            rate.dimension: rate.half_life_days
            for rate in DEFAULT_DECAY_RATES
        }

    async def get_decay_candidates(
        self,
        threshold_days: int | None = None,
        limit: int | None = None,
    ) -> list[DecayCandidate]:
        """
        Query captures eligible for decay.

        Args:
            threshold_days: Age in days for decay eligibility (default: config value)
            limit: Maximum candidates to return

        Returns:
            List of DecayCandidate objects
        """
        threshold = threshold_days or self.config.full_decay_threshold_days
        max_results = limit or self.config.batch_size

        pool = await get_db_pool()

        query = """
            SELECT
                id,
                session_id,
                EXTRACT(DAY FROM (CURRENT_TIMESTAMP - created_at))::INTEGER AS age_days,
                emotional_intensity,
                preserve_indefinitely,
                created_at,
                mental,
                observation,
                senses,
                actions,
                emotions
            FROM five_window_captures
            WHERE preserve_indefinitely = FALSE
            AND created_at < (CURRENT_TIMESTAMP - ($1 || ' days')::INTERVAL)
            ORDER BY created_at ASC
            LIMIT $2
        """

        rows = await pool.fetch(query, str(threshold), max_results)

        candidates = []
        for row in rows:
            candidates.append(DecayCandidate(
                id=row["id"],
                session_id=row["session_id"],
                age_days=row["age_days"],
                emotional_intensity=row["emotional_intensity"],
                preserve_indefinitely=row["preserve_indefinitely"],
                created_at=row["created_at"],
                mental=row["mental"],
                observation=row["observation"],
                senses=row["senses"],
                actions=row["actions"],
                emotions=row["emotions"],
            ))

        logger.info(f"Found {len(candidates)} decay candidates older than {threshold} days")
        return candidates

    def calculate_dimension_decay(
        self,
        dimension: ExperientialDimension,
        age_days: int,
        emotional_intensity: float = 5.0,
    ) -> float:
        """
        Calculate decay factor for a specific dimension.

        Uses exponential decay based on half-life:
        decay_factor = 0.5 ^ (age_days / half_life_days)

        Higher emotional intensity provides resistance to decay.

        Args:
            dimension: The experiential dimension
            age_days: Age of the capture in days
            emotional_intensity: Emotional intensity (0-10)

        Returns:
            Decay factor between 0.0 (fully decayed) and 1.0 (no decay)
        """
        half_life = self._decay_rates.get(dimension, 30)

        # High intensity provides resistance (up to 2x half-life)
        intensity_factor = 1.0
        if emotional_intensity >= self.config.intensity_decay_resistance:
            intensity_factor = 1.0 + (emotional_intensity - 7.0) / 10.0

        effective_half_life = half_life * intensity_factor

        # Exponential decay formula: 0.5^(t/half_life)
        decay_factor = math.pow(0.5, age_days / effective_half_life)

        return max(0.0, min(1.0, decay_factor))

    def should_dimension_be_nulled(
        self,
        dimension: ExperientialDimension,
        age_days: int,
        emotional_intensity: float = 5.0,
        threshold: float = 0.1,
    ) -> bool:
        """
        Check if a dimension should be nulled due to decay.

        Args:
            dimension: The experiential dimension
            age_days: Age of the capture in days
            emotional_intensity: Emotional intensity (0-10)
            threshold: Below this decay factor, null the dimension

        Returns:
            True if dimension should be nulled
        """
        decay_factor = self.calculate_dimension_decay(
            dimension, age_days, emotional_intensity
        )
        return decay_factor < threshold

    async def apply_dimension_decay(
        self,
        candidate: DecayCandidate,
    ) -> list[ExperientialDimension]:
        """
        Apply differential decay to a capture's dimensions.

        Faster-decaying dimensions (senses, observation) are nulled first.
        This preserves central gist while losing peripheral details.

        Args:
            candidate: The decay candidate

        Returns:
            List of dimensions that were nulled
        """
        nulled_dimensions = []
        updates = {}

        for dimension in ExperientialDimension:
            current_value = getattr(candidate, dimension.value, None)
            if current_value is None:
                continue

            if self.should_dimension_be_nulled(
                dimension,
                candidate.age_days,
                candidate.emotional_intensity,
            ):
                updates[dimension.value] = None
                nulled_dimensions.append(dimension)

        if not updates:
            return []

        # Build dynamic UPDATE query
        set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(updates.keys())]
        query = f"""
            UPDATE five_window_captures
            SET {', '.join(set_clauses)}
            WHERE id = $1
        """

        pool = await get_db_pool()
        await pool.execute(query, candidate.id, *updates.values())

        if self.config.verbose_logging:
            logger.debug(
                f"Decay applied to capture {candidate.id}: "
                f"nulled {[d.value for d in nulled_dimensions]}"
            )

        return nulled_dimensions

    async def apply_full_decay(
        self,
        candidate: DecayCandidate,
    ) -> bool:
        """
        Fully remove a capture that has exceeded decay threshold.

        Args:
            candidate: The decay candidate

        Returns:
            True if successfully deleted
        """
        pool = await get_db_pool()

        # Delete the capture (cascades to turning_points if any existed)
        result = await pool.execute(
            "DELETE FROM five_window_captures WHERE id = $1",
            candidate.id,
        )

        deleted = result == "DELETE 1"

        if deleted and self.config.verbose_logging:
            logger.debug(
                f"Fully decayed capture {candidate.id} "
                f"(age: {candidate.age_days} days)"
            )

        return deleted

    async def apply_decay(
        self,
        threshold_days: int | None = None,
        full_removal_factor: float = 1.5,
    ) -> DecayResult:
        """
        Apply decay to all eligible captures.

        Two-stage decay:
        1. Dimension decay: Null individual dimensions based on their half-lives
        2. Full removal: Delete captures older than threshold * full_removal_factor

        Args:
            threshold_days: Age threshold for decay candidacy
            full_removal_factor: Multiplier for full removal (default 1.5x threshold)

        Returns:
            DecayResult with statistics
        """
        start_time = datetime.utcnow()
        threshold = threshold_days or self.config.full_decay_threshold_days
        full_removal_threshold = int(threshold * full_removal_factor)

        errors: list[str] = []
        fully_decayed = 0
        dimensions_decayed = 0

        # Get candidates
        candidates = await self.get_decay_candidates(threshold_days=threshold)

        for candidate in candidates:
            try:
                if candidate.age_days >= full_removal_threshold:
                    # Full removal for very old captures
                    if await self.apply_full_decay(candidate):
                        fully_decayed += 1
                elif self.config.apply_dimension_decay:
                    # Dimension decay for moderately old captures
                    nulled = await self.apply_dimension_decay(candidate)
                    dimensions_decayed += len(nulled)

            except Exception as e:
                error_msg = f"Error decaying capture {candidate.id}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = DecayResult(
            candidates_found=len(candidates),
            fully_decayed=fully_decayed,
            dimensions_decayed=dimensions_decayed,
            errors=errors,
            duration_ms=duration_ms,
        )

        logger.info(
            f"Decay complete: {fully_decayed} removed, "
            f"{dimensions_decayed} dimensions nulled, "
            f"{len(errors)} errors, {duration_ms:.1f}ms"
        )

        return result

    async def get_decay_statistics(self) -> dict[str, Any]:
        """
        Get statistics about current decay state.

        Returns:
            Dictionary with decay statistics
        """
        pool = await get_db_pool()

        stats_query = """
            SELECT
                COUNT(*) AS total_captures,
                COUNT(*) FILTER (WHERE preserve_indefinitely = TRUE) AS turning_points,
                COUNT(*) FILTER (
                    WHERE preserve_indefinitely = FALSE
                    AND created_at < (CURRENT_TIMESTAMP - '90 days'::INTERVAL)
                ) AS candidates_90_days,
                COUNT(*) FILTER (
                    WHERE preserve_indefinitely = FALSE
                    AND created_at < (CURRENT_TIMESTAMP - '180 days'::INTERVAL)
                ) AS candidates_180_days,
                AVG(emotional_intensity) AS avg_intensity,
                MIN(created_at) AS oldest_capture
            FROM five_window_captures
        """

        row = await pool.fetchrow(stats_query)

        return {
            "total_captures": row["total_captures"],
            "turning_points": row["turning_points"],
            "decay_candidates_90_days": row["candidates_90_days"],
            "decay_candidates_180_days": row["candidates_180_days"],
            "average_emotional_intensity": float(row["avg_intensity"]) if row["avg_intensity"] else 0.0,
            "oldest_capture": row["oldest_capture"].isoformat() if row["oldest_capture"] else None,
            "config": {
                "full_decay_threshold_days": self.config.full_decay_threshold_days,
                "apply_dimension_decay": self.config.apply_dimension_decay,
                "batch_size": self.config.batch_size,
            },
        }

    async def preview_decay(
        self,
        threshold_days: int | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Preview what would be decayed without actually applying changes.

        Args:
            threshold_days: Age threshold
            limit: Max previews to return

        Returns:
            List of dictionaries describing pending decay actions
        """
        threshold = threshold_days or self.config.full_decay_threshold_days
        full_removal_threshold = int(threshold * 1.5)

        candidates = await self.get_decay_candidates(
            threshold_days=threshold,
            limit=limit,
        )

        previews = []
        for candidate in candidates:
            preview = {
                "capture_id": str(candidate.id),
                "age_days": candidate.age_days,
                "emotional_intensity": candidate.emotional_intensity,
                "action": "full_removal" if candidate.age_days >= full_removal_threshold else "dimension_decay",
            }

            if preview["action"] == "dimension_decay":
                dimensions_to_null = []
                for dimension in ExperientialDimension:
                    if getattr(candidate, dimension.value) and self.should_dimension_be_nulled(
                        dimension,
                        candidate.age_days,
                        candidate.emotional_intensity,
                    ):
                        dimensions_to_null.append(dimension.value)
                preview["dimensions_to_null"] = dimensions_to_null

            previews.append(preview)

        return previews


# Global service instance
_episodic_decay_service: EpisodicDecayService | None = None


def get_episodic_decay_service() -> EpisodicDecayService:
    """Get the global episodic decay service instance."""
    global _episodic_decay_service
    if _episodic_decay_service is None:
        _episodic_decay_service = EpisodicDecayService()
    return _episodic_decay_service
