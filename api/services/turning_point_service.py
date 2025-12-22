"""
Turning Point Service
Feature: 008-mosaeic-memory

Manages "flashbulb memory" detection and preservation.
Turning Points are emotionally significant memories exempt from decay.

Detection triggers:
- HIGH_EMOTION: emotional_intensity >= 8.0
- SURPRISE: prediction_error > 0.8
- CONSEQUENCE: linked to severe maladaptive pattern
- MANUAL: explicitly flagged
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from api.models.mosaeic import (
    FiveWindowCapture,
    TurningPoint,
    TurningPointTrigger,
)
from api.services.db import get_db_pool

logger = logging.getLogger(__name__)


@dataclass
class TurningPointConfig:
    """Configuration for turning point detection."""
    # Emotional intensity threshold for HIGH_EMOTION trigger
    high_emotion_threshold: float = 8.0

    # Prediction error threshold for SURPRISE trigger
    surprise_threshold: float = 0.8

    # Pattern severity threshold for CONSEQUENCE trigger
    consequence_severity_threshold: float = 0.7

    # Default vividness score
    default_vividness: float = 0.8


@dataclass
class TurningPointDetectionResult:
    """Result of turning point detection."""
    is_turning_point: bool
    trigger_type: TurningPointTrigger | None
    trigger_description: str | None
    confidence: float  # 0.0 - 1.0


class TurningPointService:
    """
    Manages turning point detection and preservation.

    Turning Points are the MOSAEIC "flashbulb memories" that are
    marked "KEEP FOREVER" - exempt from time-based decay.
    """

    def __init__(self, config: TurningPointConfig | None = None):
        self.config = config or TurningPointConfig()

    def detect_from_emotion(
        self,
        capture: FiveWindowCapture,
    ) -> TurningPointDetectionResult:
        """
        Detect turning point based on emotional intensity.

        Args:
            capture: The episodic capture to evaluate

        Returns:
            Detection result
        """
        if capture.emotional_intensity >= self.config.high_emotion_threshold:
            intensity_excess = capture.emotional_intensity - self.config.high_emotion_threshold
            confidence = min(1.0, 0.7 + intensity_excess * 0.15)

            return TurningPointDetectionResult(
                is_turning_point=True,
                trigger_type=TurningPointTrigger.HIGH_EMOTION,
                trigger_description=f"Emotional intensity {capture.emotional_intensity:.1f}/10",
                confidence=confidence,
            )

        return TurningPointDetectionResult(
            is_turning_point=False,
            trigger_type=None,
            trigger_description=None,
            confidence=0.0,
        )

    def detect_from_surprise(
        self,
        capture: FiveWindowCapture,
        prediction_error: float,
    ) -> TurningPointDetectionResult:
        """
        Detect turning point based on prediction error (surprise).

        Large prediction errors indicate model revision needed,
        which often accompanies memorable moments.

        Args:
            capture: The episodic capture to evaluate
            prediction_error: Error magnitude (0.0 - 1.0)

        Returns:
            Detection result
        """
        if prediction_error > self.config.surprise_threshold:
            error_excess = prediction_error - self.config.surprise_threshold
            confidence = min(1.0, 0.6 + error_excess * 0.5)

            return TurningPointDetectionResult(
                is_turning_point=True,
                trigger_type=TurningPointTrigger.SURPRISE,
                trigger_description=f"Prediction error {prediction_error:.2f}",
                confidence=confidence,
            )

        return TurningPointDetectionResult(
            is_turning_point=False,
            trigger_type=None,
            trigger_description=None,
            confidence=0.0,
        )

    async def detect_from_consequence(
        self,
        capture: FiveWindowCapture,
    ) -> TurningPointDetectionResult:
        """
        Detect turning point based on linked maladaptive pattern severity.

        If a capture is linked to a high-severity pattern, it becomes
        a turning point for therapeutic intervention tracking.

        Args:
            capture: The episodic capture to evaluate

        Returns:
            Detection result
        """
        pool = await get_db_pool()

        # Check if capture is linked to severe patterns
        query = """
            SELECT
                mp.id,
                mp.severity_score,
                mp.severity_level,
                mp.belief_content
            FROM maladaptive_patterns mp
            WHERE $1 = ANY(mp.linked_capture_ids)
            AND mp.severity_score >= $2
            ORDER BY mp.severity_score DESC
            LIMIT 1
        """

        row = await pool.fetchrow(
            query,
            capture.id,
            self.config.consequence_severity_threshold,
        )

        if row:
            return TurningPointDetectionResult(
                is_turning_point=True,
                trigger_type=TurningPointTrigger.CONSEQUENCE,
                trigger_description=(
                    f"Linked to {row['severity_level']} pattern: "
                    f"{row['belief_content'][:50]}..."
                ),
                confidence=row["severity_score"],
            )

        return TurningPointDetectionResult(
            is_turning_point=False,
            trigger_type=None,
            trigger_description=None,
            confidence=0.0,
        )

    async def detect_turning_point(
        self,
        capture: FiveWindowCapture,
        prediction_error: float | None = None,
    ) -> TurningPointDetectionResult:
        """
        Detect if a capture should be marked as a Turning Point.

        Checks all trigger conditions in priority order:
        1. HIGH_EMOTION (immediate)
        2. SURPRISE (if prediction_error provided)
        3. CONSEQUENCE (requires DB lookup)

        Args:
            capture: The episodic capture to evaluate
            prediction_error: Optional prediction error for surprise detection

        Returns:
            Detection result with highest-confidence trigger
        """
        # Already a turning point?
        if capture.preserve_indefinitely:
            return TurningPointDetectionResult(
                is_turning_point=True,
                trigger_type=None,
                trigger_description="Already marked as turning point",
                confidence=1.0,
            )

        results: list[TurningPointDetectionResult] = []

        # Check emotion trigger (no DB needed)
        emotion_result = self.detect_from_emotion(capture)
        if emotion_result.is_turning_point:
            results.append(emotion_result)

        # Check surprise trigger if error provided
        if prediction_error is not None:
            surprise_result = self.detect_from_surprise(capture, prediction_error)
            if surprise_result.is_turning_point:
                results.append(surprise_result)

        # Check consequence trigger (requires DB)
        consequence_result = await self.detect_from_consequence(capture)
        if consequence_result.is_turning_point:
            results.append(consequence_result)

        # Return highest-confidence result
        if results:
            best = max(results, key=lambda r: r.confidence)
            return best

        return TurningPointDetectionResult(
            is_turning_point=False,
            trigger_type=None,
            trigger_description=None,
            confidence=0.0,
        )

    async def mark_as_turning_point(
        self,
        capture_id: UUID,
        trigger_type: TurningPointTrigger,
        trigger_description: str | None = None,
        vividness_score: float | None = None,
        narrative_thread_id: UUID | None = None,
        life_chapter_id: UUID | None = None,
    ) -> TurningPoint:
        """
        Mark a capture as a Turning Point.

        Creates turning_points record and sets preserve_indefinitely flag.

        Args:
            capture_id: The capture to mark
            trigger_type: What triggered the turning point
            trigger_description: Human-readable description
            vividness_score: Subjective recall vividness (0-1)
            narrative_thread_id: Link to autobiographical narrative
            life_chapter_id: Link to life chapter

        Returns:
            The created TurningPoint
        """
        pool = await get_db_pool()
        vividness = vividness_score or self.config.default_vividness

        async with pool.acquire() as conn:
            async with conn.transaction():
                # Update capture to preserve indefinitely
                await conn.execute(
                    """
                    UPDATE five_window_captures
                    SET preserve_indefinitely = TRUE
                    WHERE id = $1
                    """,
                    capture_id,
                )

                # Create turning point record
                row = await conn.fetchrow(
                    """
                    INSERT INTO turning_points (
                        capture_id,
                        trigger_type,
                        trigger_description,
                        vividness_score,
                        narrative_thread_id,
                        life_chapter_id
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (capture_id) DO UPDATE SET
                        trigger_type = EXCLUDED.trigger_type,
                        trigger_description = EXCLUDED.trigger_description,
                        vividness_score = EXCLUDED.vividness_score,
                        narrative_thread_id = EXCLUDED.narrative_thread_id,
                        life_chapter_id = EXCLUDED.life_chapter_id
                    RETURNING *
                    """,
                    capture_id,
                    trigger_type.value,
                    trigger_description,
                    vividness,
                    narrative_thread_id,
                    life_chapter_id,
                )

        turning_point = TurningPoint(
            id=row["id"],
            capture_id=row["capture_id"],
            trigger_type=TurningPointTrigger(row["trigger_type"]),
            trigger_description=row["trigger_description"],
            vividness_score=row["vividness_score"],
            narrative_thread_id=row["narrative_thread_id"],
            life_chapter_id=row["life_chapter_id"],
            created_at=row["created_at"],
        )

        logger.info(
            f"Marked capture {capture_id} as turning point "
            f"(trigger: {trigger_type.value})"
        )

        return turning_point

    async def link_to_narrative(
        self,
        turning_point_id: UUID,
        narrative_thread_id: UUID | None = None,
        life_chapter_id: UUID | None = None,
    ) -> bool:
        """
        Link a turning point to autobiographical narrative structures.

        From 005-mental-models spec:
        - narrative_thread_id: Links to narrative thread for story coherence
        - life_chapter_id: Links to life chapter for temporal organization

        Args:
            turning_point_id: The turning point to link
            narrative_thread_id: Optional narrative thread
            life_chapter_id: Optional life chapter

        Returns:
            True if updated successfully
        """
        if not narrative_thread_id and not life_chapter_id:
            return False

        pool = await get_db_pool()

        update_parts = []
        params = [turning_point_id]
        param_idx = 2

        if narrative_thread_id:
            update_parts.append(f"narrative_thread_id = ${param_idx}")
            params.append(narrative_thread_id)
            param_idx += 1

        if life_chapter_id:
            update_parts.append(f"life_chapter_id = ${param_idx}")
            params.append(life_chapter_id)

        query = f"""
            UPDATE turning_points
            SET {', '.join(update_parts)}
            WHERE id = $1
        """

        result = await pool.execute(query, *params)
        updated = result == "UPDATE 1"

        if updated:
            logger.info(
                f"Linked turning point {turning_point_id} to narrative"
            )

        return updated

    async def get_turning_point(
        self,
        turning_point_id: UUID,
    ) -> TurningPoint | None:
        """Get a turning point by ID."""
        pool = await get_db_pool()

        row = await pool.fetchrow(
            "SELECT * FROM turning_points WHERE id = $1",
            turning_point_id,
        )

        if not row:
            return None

        return TurningPoint(
            id=row["id"],
            capture_id=row["capture_id"],
            trigger_type=TurningPointTrigger(row["trigger_type"]),
            trigger_description=row["trigger_description"],
            vividness_score=row["vividness_score"],
            narrative_thread_id=row["narrative_thread_id"],
            life_chapter_id=row["life_chapter_id"],
            created_at=row["created_at"],
        )

    async def get_turning_point_for_capture(
        self,
        capture_id: UUID,
    ) -> TurningPoint | None:
        """Get turning point by capture ID."""
        pool = await get_db_pool()

        row = await pool.fetchrow(
            "SELECT * FROM turning_points WHERE capture_id = $1",
            capture_id,
        )

        if not row:
            return None

        return TurningPoint(
            id=row["id"],
            capture_id=row["capture_id"],
            trigger_type=TurningPointTrigger(row["trigger_type"]),
            trigger_description=row["trigger_description"],
            vividness_score=row["vividness_score"],
            narrative_thread_id=row["narrative_thread_id"],
            life_chapter_id=row["life_chapter_id"],
            created_at=row["created_at"],
        )

    async def get_turning_points(
        self,
        trigger_type: TurningPointTrigger | None = None,
        narrative_thread_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TurningPoint]:
        """
        Query turning points with optional filters.

        Args:
            trigger_type: Filter by trigger type
            narrative_thread_id: Filter by narrative thread
            limit: Max results
            offset: Pagination offset

        Returns:
            List of TurningPoint objects
        """
        pool = await get_db_pool()

        conditions = []
        params = []
        param_idx = 1

        if trigger_type:
            conditions.append(f"trigger_type = ${param_idx}")
            params.append(trigger_type.value)
            param_idx += 1

        if narrative_thread_id:
            conditions.append(f"narrative_thread_id = ${param_idx}")
            params.append(narrative_thread_id)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT * FROM turning_points
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        rows = await pool.fetch(query, *params)

        return [
            TurningPoint(
                id=row["id"],
                capture_id=row["capture_id"],
                trigger_type=TurningPointTrigger(row["trigger_type"]),
                trigger_description=row["trigger_description"],
                vividness_score=row["vividness_score"],
                narrative_thread_id=row["narrative_thread_id"],
                life_chapter_id=row["life_chapter_id"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_turning_point_statistics(self) -> dict[str, Any]:
        """Get statistics about turning points."""
        pool = await get_db_pool()

        stats = await pool.fetchrow("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE trigger_type = 'high_emotion') AS high_emotion_count,
                COUNT(*) FILTER (WHERE trigger_type = 'surprise') AS surprise_count,
                COUNT(*) FILTER (WHERE trigger_type = 'consequence') AS consequence_count,
                COUNT(*) FILTER (WHERE trigger_type = 'manual') AS manual_count,
                COUNT(*) FILTER (WHERE narrative_thread_id IS NOT NULL) AS linked_to_narrative,
                AVG(vividness_score) AS avg_vividness
            FROM turning_points
        """)

        return {
            "total": stats["total"],
            "by_trigger": {
                "high_emotion": stats["high_emotion_count"],
                "surprise": stats["surprise_count"],
                "consequence": stats["consequence_count"],
                "manual": stats["manual_count"],
            },
            "linked_to_narrative": stats["linked_to_narrative"],
            "average_vividness": float(stats["avg_vividness"]) if stats["avg_vividness"] else 0.0,
        }

    async def unmark_turning_point(
        self,
        capture_id: UUID,
    ) -> bool:
        """
        Remove turning point status from a capture.

        Deletes the turning_points record and clears preserve_indefinitely.

        Args:
            capture_id: The capture to unmark

        Returns:
            True if successfully unmarked
        """
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            async with conn.transaction():
                # Delete turning point record
                await conn.execute(
                    "DELETE FROM turning_points WHERE capture_id = $1",
                    capture_id,
                )

                # Clear preserve flag
                result = await conn.execute(
                    """
                    UPDATE five_window_captures
                    SET preserve_indefinitely = FALSE
                    WHERE id = $1
                    """,
                    capture_id,
                )

        unmarked = result == "UPDATE 1"

        if unmarked:
            logger.info(f"Unmarked turning point for capture {capture_id}")

        return unmarked


# Global service instance
_turning_point_service: TurningPointService | None = None


def get_turning_point_service() -> TurningPointService:
    """Get the global turning point service instance."""
    global _turning_point_service
    if _turning_point_service is None:
        _turning_point_service = TurningPointService()
    return _turning_point_service
