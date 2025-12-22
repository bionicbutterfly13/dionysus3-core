"""
Semantic Archive Service
Feature: 008-mosaeic-memory

Implements confidence-based preservation for semantic memories (accuracy protocol).
High-confidence beliefs persist indefinitely; low-confidence beliefs may be archived.

Archive criteria:
- Adaptiveness score below threshold (default 0.3)
- Not verified within stale period (default 365 days)
- Never delete - only archive for potential restoration
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from api.models.mosaeic import BeliefRewrite
from api.services.db import get_db_pool

logger = logging.getLogger(__name__)


@dataclass
class SemanticArchiveConfig:
    """Configuration for semantic archive behavior."""
    # Confidence threshold for archival
    archive_confidence_threshold: float = 0.3

    # Days without verification to be considered stale
    stale_days: int = 365

    # Minimum predictions before archival eligible
    min_predictions_for_archive: int = 5

    # Batch size for archive operations
    batch_size: int = 50

    # Whether to log each archived belief
    verbose_logging: bool = False


@dataclass
class ArchiveCandidate:
    """A belief eligible for archival."""
    id: UUID
    new_belief: str
    domain: str
    adaptiveness_score: float
    prediction_success_count: int
    prediction_failure_count: int
    last_verified: datetime | None
    days_since_verified: int
    created_at: datetime


@dataclass
class ArchiveResult:
    """Result of an archive operation."""
    candidates_found: int
    archived: int
    errors: list[str]
    duration_ms: float


class SemanticArchiveService:
    """
    Manages confidence-based archival for semantic beliefs.

    Implements the MOSAEIC accuracy protocol:
    - High-confidence beliefs are never archived
    - Low-confidence + stale beliefs are archived
    - Archived beliefs can be restored if accessed
    - Never delete - archive preserves for potential restoration
    """

    def __init__(self, config: SemanticArchiveConfig | None = None):
        self.config = config or SemanticArchiveConfig()

    async def get_archive_candidates(
        self,
        confidence_threshold: float | None = None,
        stale_days: int | None = None,
        limit: int | None = None,
    ) -> list[ArchiveCandidate]:
        """
        Query beliefs eligible for archival.

        Candidates are beliefs with:
        - adaptiveness_score < threshold
        - last_verified older than stale_days (or never verified)
        - Not already archived
        - Minimum prediction count met

        Args:
            confidence_threshold: Max score for archival eligibility
            stale_days: Days without verification to be stale
            limit: Maximum candidates to return

        Returns:
            List of ArchiveCandidate objects
        """
        threshold = confidence_threshold or self.config.archive_confidence_threshold
        stale = stale_days or self.config.stale_days
        max_results = limit or self.config.batch_size
        min_preds = self.config.min_predictions_for_archive

        pool = await get_db_pool()

        query = """
            SELECT
                id,
                new_belief,
                domain,
                adaptiveness_score,
                prediction_success_count,
                prediction_failure_count,
                last_verified,
                EXTRACT(DAY FROM (
                    CURRENT_TIMESTAMP - COALESCE(last_verified, created_at)
                ))::INTEGER AS days_since_verified,
                created_at
            FROM belief_rewrites
            WHERE archived = FALSE
            AND adaptiveness_score < $1
            AND (prediction_success_count + prediction_failure_count) >= $2
            AND COALESCE(last_verified, created_at) < (
                CURRENT_TIMESTAMP - ($3 || ' days')::INTERVAL
            )
            ORDER BY adaptiveness_score ASC
            LIMIT $4
        """

        rows = await pool.fetch(query, threshold, min_preds, str(stale), max_results)

        candidates = []
        for row in rows:
            candidates.append(ArchiveCandidate(
                id=row["id"],
                new_belief=row["new_belief"],
                domain=row["domain"],
                adaptiveness_score=row["adaptiveness_score"],
                prediction_success_count=row["prediction_success_count"],
                prediction_failure_count=row["prediction_failure_count"],
                last_verified=row["last_verified"],
                days_since_verified=row["days_since_verified"],
                created_at=row["created_at"],
            ))

        logger.info(
            f"Found {len(candidates)} archive candidates "
            f"(threshold: {threshold}, stale: {stale} days)"
        )
        return candidates

    async def archive_belief(self, belief_id: UUID) -> bool:
        """
        Archive a single belief.

        Args:
            belief_id: The belief to archive

        Returns:
            True if successfully archived
        """
        pool = await get_db_pool()

        result = await pool.execute(
            """
            UPDATE belief_rewrites
            SET archived = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND archived = FALSE
            """,
            belief_id,
        )

        archived = result == "UPDATE 1"

        if archived and self.config.verbose_logging:
            logger.debug(f"Archived belief {belief_id}")

        return archived

    async def apply_archival(
        self,
        confidence_threshold: float | None = None,
        stale_days: int | None = None,
    ) -> ArchiveResult:
        """
        Apply archival to all eligible beliefs.

        Args:
            confidence_threshold: Max score for archival eligibility
            stale_days: Days without verification to be stale

        Returns:
            ArchiveResult with statistics
        """
        start_time = datetime.utcnow()
        errors: list[str] = []
        archived_count = 0

        # Get candidates
        candidates = await self.get_archive_candidates(
            confidence_threshold=confidence_threshold,
            stale_days=stale_days,
        )

        for candidate in candidates:
            try:
                if await self.archive_belief(candidate.id):
                    archived_count += 1

            except Exception as e:
                error_msg = f"Error archiving belief {candidate.id}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = ArchiveResult(
            candidates_found=len(candidates),
            archived=archived_count,
            errors=errors,
            duration_ms=duration_ms,
        )

        logger.info(
            f"Archival complete: {archived_count} archived, "
            f"{len(errors)} errors, {duration_ms:.1f}ms"
        )

        return result

    async def restore_from_archive(
        self,
        belief_id: UUID,
    ) -> BeliefRewrite | None:
        """
        Restore a belief from archive.

        When archived beliefs are accessed/needed, they can be restored.
        This implements the "never delete" principle.

        Args:
            belief_id: The belief to restore

        Returns:
            The restored BeliefRewrite or None if not found
        """
        pool = await get_db_pool()

        row = await pool.fetchrow(
            """
            UPDATE belief_rewrites
            SET archived = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND archived = TRUE
            RETURNING *
            """,
            belief_id,
        )

        if not row:
            return None

        logger.info(f"Restored belief {belief_id} from archive")

        return self._row_to_belief(row)

    async def get_archived_beliefs(
        self,
        domain: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[BeliefRewrite]:
        """
        Query archived beliefs.

        Args:
            domain: Filter by domain
            limit: Max results
            offset: Pagination offset

        Returns:
            List of archived BeliefRewrite objects
        """
        pool = await get_db_pool()

        if domain:
            query = """
                SELECT * FROM belief_rewrites
                WHERE archived = TRUE AND domain = $1
                ORDER BY updated_at DESC
                LIMIT $2 OFFSET $3
            """
            rows = await pool.fetch(query, domain, limit, offset)
        else:
            query = """
                SELECT * FROM belief_rewrites
                WHERE archived = TRUE
                ORDER BY updated_at DESC
                LIMIT $1 OFFSET $2
            """
            rows = await pool.fetch(query, limit, offset)

        return [self._row_to_belief(row) for row in rows]

    async def get_belief(self, belief_id: UUID) -> BeliefRewrite | None:
        """Get a belief by ID."""
        pool = await get_db_pool()

        row = await pool.fetchrow(
            "SELECT * FROM belief_rewrites WHERE id = $1",
            belief_id,
        )

        if not row:
            return None

        return self._row_to_belief(row)

    async def update_confidence(
        self,
        belief_id: UUID,
        prediction_correct: bool,
    ) -> BeliefRewrite | None:
        """
        Update belief confidence based on prediction outcome.

        Args:
            belief_id: The belief to update
            prediction_correct: Whether the prediction was correct

        Returns:
            Updated BeliefRewrite or None if not found
        """
        pool = await get_db_pool()

        if prediction_correct:
            query = """
                UPDATE belief_rewrites
                SET
                    prediction_success_count = prediction_success_count + 1,
                    last_verified = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *
            """
        else:
            query = """
                UPDATE belief_rewrites
                SET
                    prediction_failure_count = prediction_failure_count + 1,
                    last_verified = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *
            """

        row = await pool.fetchrow(query, belief_id)

        if not row:
            return None

        # Update adaptiveness score based on new accuracy
        belief = self._row_to_belief(row)
        new_score = belief.accuracy

        await pool.execute(
            """
            UPDATE belief_rewrites
            SET adaptiveness_score = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            """,
            new_score,
            belief_id,
        )

        belief.adaptiveness_score = new_score

        logger.debug(
            f"Updated belief {belief_id} confidence: "
            f"correct={prediction_correct}, new_score={new_score:.3f}"
        )

        return belief

    async def flag_for_revision(
        self,
        belief_id: UUID,
    ) -> bool:
        """
        Check if a belief should be flagged for revision.

        Beliefs with accuracy < 50% after sufficient predictions
        should be revised.

        Args:
            belief_id: The belief to check

        Returns:
            True if belief needs revision
        """
        belief = await self.get_belief(belief_id)

        if not belief:
            return False

        return belief.needs_revision

    async def get_beliefs_needing_revision(
        self,
        limit: int = 20,
    ) -> list[BeliefRewrite]:
        """
        Get beliefs that need revision based on poor accuracy.

        Args:
            limit: Max results

        Returns:
            List of beliefs needing revision
        """
        pool = await get_db_pool()

        query = """
            SELECT * FROM belief_rewrites
            WHERE archived = FALSE
            AND (prediction_success_count + prediction_failure_count) >= 5
            AND prediction_success_count::FLOAT / NULLIF(
                prediction_success_count + prediction_failure_count, 0
            ) < 0.5
            ORDER BY adaptiveness_score ASC
            LIMIT $1
        """

        rows = await pool.fetch(query, limit)

        return [self._row_to_belief(row) for row in rows]

    async def get_archive_statistics(self) -> dict[str, Any]:
        """Get statistics about semantic archive state."""
        pool = await get_db_pool()

        stats = await pool.fetchrow("""
            SELECT
                COUNT(*) AS total_beliefs,
                COUNT(*) FILTER (WHERE archived = TRUE) AS archived_count,
                COUNT(*) FILTER (WHERE archived = FALSE) AS active_count,
                COUNT(*) FILTER (
                    WHERE archived = FALSE
                    AND adaptiveness_score < 0.3
                ) AS low_confidence_count,
                COUNT(*) FILTER (
                    WHERE archived = FALSE
                    AND (prediction_success_count + prediction_failure_count) >= 5
                    AND prediction_success_count::FLOAT / NULLIF(
                        prediction_success_count + prediction_failure_count, 0
                    ) < 0.5
                ) AS needs_revision_count,
                AVG(adaptiveness_score) FILTER (WHERE archived = FALSE) AS avg_confidence
            FROM belief_rewrites
        """)

        domain_stats = await pool.fetch("""
            SELECT
                domain,
                COUNT(*) AS count,
                AVG(adaptiveness_score) AS avg_confidence
            FROM belief_rewrites
            WHERE archived = FALSE
            GROUP BY domain
        """)

        return {
            "total_beliefs": stats["total_beliefs"],
            "archived_count": stats["archived_count"],
            "active_count": stats["active_count"],
            "low_confidence_count": stats["low_confidence_count"],
            "needs_revision_count": stats["needs_revision_count"],
            "average_confidence": float(stats["avg_confidence"]) if stats["avg_confidence"] else 0.0,
            "by_domain": {
                row["domain"]: {
                    "count": row["count"],
                    "avg_confidence": float(row["avg_confidence"]) if row["avg_confidence"] else 0.0,
                }
                for row in domain_stats
            },
            "config": {
                "archive_confidence_threshold": self.config.archive_confidence_threshold,
                "stale_days": self.config.stale_days,
                "min_predictions_for_archive": self.config.min_predictions_for_archive,
            },
        }

    def _row_to_belief(self, row) -> BeliefRewrite:
        """Convert database row to BeliefRewrite model."""
        from api.models.mosaeic import BasinInfluenceType

        return BeliefRewrite(
            id=row["id"],
            old_belief_id=row["old_belief_id"],
            new_belief=row["new_belief"],
            domain=row["domain"],
            adaptiveness_score=row["adaptiveness_score"],
            evidence_count=row["evidence_count"],
            last_verified=row["last_verified"],
            prediction_success_count=row["prediction_success_count"],
            prediction_failure_count=row["prediction_failure_count"],
            evolution_trigger=(
                BasinInfluenceType(row["evolution_trigger"])
                if row["evolution_trigger"]
                else None
            ),
            archived=row["archived"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# Global service instance
_semantic_archive_service: SemanticArchiveService | None = None


def get_semantic_archive_service() -> SemanticArchiveService:
    """Get the global semantic archive service instance."""
    global _semantic_archive_service
    if _semantic_archive_service is None:
        _semantic_archive_service = SemanticArchiveService()
    return _semantic_archive_service
