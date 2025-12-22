"""
Pattern Detection Service
Feature: 008-mosaeic-memory

Detects and tracks maladaptive patterns for intervention.
Patterns are recurring negative beliefs or behaviors that warrant attention.

Severity escalation:
- LOW: recurrence < 3
- MODERATE: recurrence 3-4
- HIGH: recurrence 5-9
- CRITICAL: recurrence >= 10

Intervention triggers when severity_score >= 0.7 and recurrence >= 3.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from api.models.mosaeic import (
    MaladaptivePattern,
    PatternSeverity,
)
from api.services.db import get_db_pool

logger = logging.getLogger(__name__)


@dataclass
class PatternDetectionConfig:
    """Configuration for pattern detection."""
    # Minimum similarity for pattern matching
    similarity_threshold: float = 0.7

    # Recurrence thresholds for severity levels
    moderate_threshold: int = 3
    high_threshold: int = 5
    critical_threshold: int = 10

    # Severity score for intervention
    intervention_severity_threshold: float = 0.7

    # Minimum recurrence for intervention
    intervention_recurrence_threshold: int = 3

    # Base severity increment per recurrence
    severity_increment: float = 0.05


@dataclass
class PatternMatch:
    """A detected pattern match."""
    pattern_id: UUID
    belief_content: str
    similarity_score: float
    recurrence_count: int
    severity_level: PatternSeverity


class PatternDetectionService:
    """
    Detects and tracks maladaptive patterns.

    Key responsibilities:
    - Detect recurring negative patterns in beliefs/captures
    - Track recurrence and escalate severity
    - Trigger intervention when thresholds met
    - Link patterns to related entities
    """

    def __init__(self, config: PatternDetectionConfig | None = None):
        self.config = config or PatternDetectionConfig()

    def calculate_text_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        Calculate similarity between two text strings.

        Uses Jaccard similarity on word sets.
        In production, consider using embeddings for semantic similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0.0 - 1.0
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    async def detect_pattern(
        self,
        belief_content: str,
        domain: str,
        capture_id: UUID | None = None,
    ) -> PatternMatch | None:
        """
        Detect if content matches an existing maladaptive pattern.

        Args:
            belief_content: The belief text to match
            domain: The belief domain
            capture_id: Optional capture to link

        Returns:
            PatternMatch if found, None otherwise
        """
        pool = await get_db_pool()

        # Get existing patterns in same domain
        rows = await pool.fetch(
            """
            SELECT
                id,
                belief_content,
                domain,
                severity_score,
                severity_level,
                recurrence_count
            FROM maladaptive_patterns
            WHERE domain = $1
            AND intervention_triggered = FALSE
            """,
            domain,
        )

        best_match: PatternMatch | None = None
        best_similarity = 0.0

        for row in rows:
            similarity = self.calculate_text_similarity(
                belief_content,
                row["belief_content"],
            )

            if similarity >= self.config.similarity_threshold:
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = PatternMatch(
                        pattern_id=row["id"],
                        belief_content=row["belief_content"],
                        similarity_score=similarity,
                        recurrence_count=row["recurrence_count"],
                        severity_level=PatternSeverity(row["severity_level"]),
                    )

        if best_match:
            logger.debug(
                f"Pattern match found: {best_match.pattern_id} "
                f"(similarity: {best_similarity:.2f})"
            )

        return best_match

    async def create_pattern(
        self,
        belief_content: str,
        domain: str,
        capture_id: UUID | None = None,
        model_id: UUID | None = None,
        initial_severity: float = 0.1,
    ) -> MaladaptivePattern:
        """
        Create a new maladaptive pattern.

        Args:
            belief_content: The maladaptive belief text
            domain: The belief domain
            capture_id: Optional linked capture
            model_id: Optional linked mental model
            initial_severity: Starting severity score

        Returns:
            The created MaladaptivePattern
        """
        pool = await get_db_pool()

        linked_captures = [str(capture_id)] if capture_id else []
        linked_models = [str(model_id)] if model_id else []

        row = await pool.fetchrow(
            """
            INSERT INTO maladaptive_patterns (
                belief_content,
                domain,
                severity_score,
                severity_level,
                recurrence_count,
                linked_capture_ids,
                linked_model_ids
            ) VALUES ($1, $2, $3, $4, 1, $5, $6)
            RETURNING *
            """,
            belief_content,
            domain,
            initial_severity,
            PatternSeverity.LOW.value,
            linked_captures,
            linked_models,
        )

        pattern = self._row_to_pattern(row)

        logger.info(f"Created maladaptive pattern {pattern.id} in domain {domain}")

        return pattern

    async def update_recurrence(
        self,
        pattern_id: UUID,
        capture_id: UUID | None = None,
        model_id: UUID | None = None,
    ) -> MaladaptivePattern:
        """
        Update pattern recurrence count and severity.

        Each recurrence:
        - Increments count
        - Increases severity score
        - May escalate severity level

        Args:
            pattern_id: The pattern to update
            capture_id: Optional new linked capture
            model_id: Optional new linked model

        Returns:
            Updated MaladaptivePattern
        """
        pool = await get_db_pool()

        # First, get current pattern
        current = await pool.fetchrow(
            "SELECT * FROM maladaptive_patterns WHERE id = $1",
            pattern_id,
        )

        if not current:
            raise ValueError(f"Pattern {pattern_id} not found")

        # Calculate new values
        new_count = current["recurrence_count"] + 1
        new_severity_score = min(
            1.0,
            current["severity_score"] + self.config.severity_increment,
        )
        new_level = self._calculate_severity_level(new_count)

        # Update linked arrays
        linked_captures = list(current["linked_capture_ids"] or [])
        linked_models = list(current["linked_model_ids"] or [])

        if capture_id and str(capture_id) not in linked_captures:
            linked_captures.append(str(capture_id))

        if model_id and str(model_id) not in linked_models:
            linked_models.append(str(model_id))

        # Update pattern
        row = await pool.fetchrow(
            """
            UPDATE maladaptive_patterns
            SET
                recurrence_count = $2,
                severity_score = $3,
                severity_level = $4,
                linked_capture_ids = $5,
                linked_model_ids = $6,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """,
            pattern_id,
            new_count,
            new_severity_score,
            new_level.value,
            linked_captures,
            linked_models,
        )

        pattern = self._row_to_pattern(row)

        logger.info(
            f"Updated pattern {pattern_id}: "
            f"recurrence={new_count}, severity={new_level.value}"
        )

        return pattern

    def _calculate_severity_level(self, recurrence_count: int) -> PatternSeverity:
        """Calculate severity level based on recurrence count."""
        if recurrence_count >= self.config.critical_threshold:
            return PatternSeverity.CRITICAL
        elif recurrence_count >= self.config.high_threshold:
            return PatternSeverity.HIGH
        elif recurrence_count >= self.config.moderate_threshold:
            return PatternSeverity.MODERATE
        else:
            return PatternSeverity.LOW

    def assess_severity(
        self,
        pattern: MaladaptivePattern,
    ) -> dict[str, Any]:
        """
        Assess pattern severity and intervention need.

        Args:
            pattern: The pattern to assess

        Returns:
            Assessment dictionary with recommendations
        """
        needs_intervention = (
            pattern.severity_score >= self.config.intervention_severity_threshold
            and pattern.recurrence_count >= self.config.intervention_recurrence_threshold
            and not pattern.intervention_triggered
        )

        return {
            "pattern_id": str(pattern.id),
            "severity_level": pattern.severity_level.value,
            "severity_score": pattern.severity_score,
            "recurrence_count": pattern.recurrence_count,
            "needs_intervention": needs_intervention,
            "thresholds": {
                "severity_threshold": self.config.intervention_severity_threshold,
                "recurrence_threshold": self.config.intervention_recurrence_threshold,
            },
            "linked_captures": len(pattern.linked_capture_ids),
            "linked_models": len(pattern.linked_model_ids),
        }

    async def trigger_intervention(
        self,
        pattern_id: UUID,
    ) -> MaladaptivePattern:
        """
        Trigger intervention for a pattern.

        Marks the pattern as having intervention triggered.

        Args:
            pattern_id: The pattern requiring intervention

        Returns:
            Updated MaladaptivePattern
        """
        pool = await get_db_pool()

        row = await pool.fetchrow(
            """
            UPDATE maladaptive_patterns
            SET
                intervention_triggered = TRUE,
                last_intervention = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """,
            pattern_id,
        )

        if not row:
            raise ValueError(f"Pattern {pattern_id} not found")

        pattern = self._row_to_pattern(row)

        logger.warning(
            f"INTERVENTION TRIGGERED for pattern {pattern_id}: "
            f"{pattern.belief_content[:50]}..."
        )

        return pattern

    async def get_patterns_requiring_intervention(
        self,
        limit: int = 20,
    ) -> list[MaladaptivePattern]:
        """
        Get patterns that meet intervention criteria.

        Args:
            limit: Max results

        Returns:
            List of patterns needing intervention
        """
        pool = await get_db_pool()

        query = """
            SELECT * FROM maladaptive_patterns
            WHERE intervention_triggered = FALSE
            AND severity_score >= $1
            AND recurrence_count >= $2
            ORDER BY severity_score DESC, recurrence_count DESC
            LIMIT $3
        """

        rows = await pool.fetch(
            query,
            self.config.intervention_severity_threshold,
            self.config.intervention_recurrence_threshold,
            limit,
        )

        return [self._row_to_pattern(row) for row in rows]

    async def get_pattern(self, pattern_id: UUID) -> MaladaptivePattern | None:
        """Get a pattern by ID."""
        pool = await get_db_pool()

        row = await pool.fetchrow(
            "SELECT * FROM maladaptive_patterns WHERE id = $1",
            pattern_id,
        )

        if not row:
            return None

        return self._row_to_pattern(row)

    async def get_patterns(
        self,
        domain: str | None = None,
        severity_level: PatternSeverity | None = None,
        include_intervened: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MaladaptivePattern]:
        """
        Query patterns with optional filters.

        Args:
            domain: Filter by domain
            severity_level: Filter by severity
            include_intervened: Include patterns with intervention triggered
            limit: Max results
            offset: Pagination offset

        Returns:
            List of MaladaptivePattern objects
        """
        pool = await get_db_pool()

        conditions = []
        params = []
        param_idx = 1

        if not include_intervened:
            conditions.append("intervention_triggered = FALSE")

        if domain:
            conditions.append(f"domain = ${param_idx}")
            params.append(domain)
            param_idx += 1

        if severity_level:
            conditions.append(f"severity_level = ${param_idx}")
            params.append(severity_level.value)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT * FROM maladaptive_patterns
            {where_clause}
            ORDER BY severity_score DESC, recurrence_count DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        rows = await pool.fetch(query, *params)

        return [self._row_to_pattern(row) for row in rows]

    async def link_capture_to_pattern(
        self,
        pattern_id: UUID,
        capture_id: UUID,
    ) -> bool:
        """
        Link a capture to a pattern.

        Args:
            pattern_id: The pattern
            capture_id: The capture to link

        Returns:
            True if updated
        """
        pool = await get_db_pool()

        result = await pool.execute(
            """
            UPDATE maladaptive_patterns
            SET
                linked_capture_ids = array_append(
                    linked_capture_ids,
                    $2::TEXT
                ),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            AND NOT ($2::TEXT = ANY(linked_capture_ids))
            """,
            pattern_id,
            str(capture_id),
        )

        return result == "UPDATE 1"

    async def get_pattern_statistics(self) -> dict[str, Any]:
        """Get statistics about patterns."""
        pool = await get_db_pool()

        stats = await pool.fetchrow("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE severity_level = 'low') AS low_count,
                COUNT(*) FILTER (WHERE severity_level = 'moderate') AS moderate_count,
                COUNT(*) FILTER (WHERE severity_level = 'high') AS high_count,
                COUNT(*) FILTER (WHERE severity_level = 'critical') AS critical_count,
                COUNT(*) FILTER (WHERE intervention_triggered = TRUE) AS intervened_count,
                COUNT(*) FILTER (
                    WHERE intervention_triggered = FALSE
                    AND severity_score >= 0.7
                    AND recurrence_count >= 3
                ) AS needs_intervention,
                AVG(recurrence_count) AS avg_recurrence,
                AVG(severity_score) AS avg_severity
            FROM maladaptive_patterns
        """)

        domain_stats = await pool.fetch("""
            SELECT
                domain,
                COUNT(*) AS count,
                AVG(severity_score) AS avg_severity
            FROM maladaptive_patterns
            GROUP BY domain
        """)

        return {
            "total": stats["total"],
            "by_severity": {
                "low": stats["low_count"],
                "moderate": stats["moderate_count"],
                "high": stats["high_count"],
                "critical": stats["critical_count"],
            },
            "intervened_count": stats["intervened_count"],
            "needs_intervention": stats["needs_intervention"],
            "average_recurrence": float(stats["avg_recurrence"]) if stats["avg_recurrence"] else 0.0,
            "average_severity": float(stats["avg_severity"]) if stats["avg_severity"] else 0.0,
            "by_domain": {
                row["domain"]: {
                    "count": row["count"],
                    "avg_severity": float(row["avg_severity"]) if row["avg_severity"] else 0.0,
                }
                for row in domain_stats
            },
        }

    def _row_to_pattern(self, row) -> MaladaptivePattern:
        """Convert database row to MaladaptivePattern model."""
        return MaladaptivePattern(
            id=row["id"],
            belief_content=row["belief_content"],
            domain=row["domain"],
            severity_score=row["severity_score"],
            severity_level=PatternSeverity(row["severity_level"]),
            recurrence_count=row["recurrence_count"],
            intervention_triggered=row["intervention_triggered"],
            last_intervention=row["last_intervention"],
            linked_capture_ids=[
                UUID(cid) for cid in (row["linked_capture_ids"] or [])
            ],
            linked_model_ids=[
                UUID(mid) for mid in (row["linked_model_ids"] or [])
            ],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# Global service instance
_pattern_detection_service: PatternDetectionService | None = None


def get_pattern_detection_service() -> PatternDetectionService:
    """Get the global pattern detection service instance."""
    global _pattern_detection_service
    if _pattern_detection_service is None:
        _pattern_detection_service = PatternDetectionService()
    return _pattern_detection_service
