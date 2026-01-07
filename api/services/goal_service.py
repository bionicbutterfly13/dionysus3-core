"""
Goal Service for Heartbeat System
Feature: 004-heartbeat-system
Tasks: T005, T006, T007, T008

Service for AGI goal management with CRUD operations, lifecycle
management, review logic, and memory linkage.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from api.models.goal import (
    Goal,
    GoalAssessment,
    GoalBacklogSummary,
    GoalBlocker,
    GoalCreate,
    GoalMemoryLink,
    GoalMemoryLinkType,
    GoalPriority,
    GoalProgressNote,
    GoalSource,
    GoalUpdate,
)

logger = logging.getLogger("dionysus.goal_service")


# =============================================================================
# Configuration
# =============================================================================

MAX_ACTIVE_GOALS = 3
MAX_QUEUED_GOALS = 10
STALE_THRESHOLD_DAYS = 7


# =============================================================================
# GoalService
# =============================================================================


class GoalService:
    """
    Service for managing AGI goals.

    Provides CRUD operations, lifecycle management, and goal review
    logic for the heartbeat system.
    """

    def __init__(self, driver=None):
        """
        Initialize GoalService.

        Args:
            driver: Neo4j driver instance (optional, uses global if not provided)
        """
        self._driver = driver

    def _get_driver(self):
        """Get Neo4j driver, using global instance if not provided."""
        if self._driver:
            return self._driver
        # Import here to avoid circular dependency
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    # =========================================================================
    # T005: CRUD Operations
    # =========================================================================

    async def create_goal(self, goal_create: GoalCreate) -> Goal:
        """
        Create a new goal.

        Args:
            goal_create: Goal creation DTO

        Returns:
            Created Goal instance
        """
        goal = Goal(
            id=uuid4(),
            title=goal_create.title,
            description=goal_create.description,
            priority=goal_create.priority,
            source=goal_create.source,
            parent_goal_id=goal_create.parent_goal_id,
            emotional_valence=goal_create.emotional_valence,
            created_at=datetime.utcnow(),
            last_touched=datetime.utcnow(),
        )

        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                CREATE (g:Goal {
                    id: $id,
                    title: $title,
                    description: $description,
                    priority: $priority,
                    source: $source,
                    parent_goal_id: $parent_goal_id,
                    progress: $progress,
                    blocked_by: $blocked_by,
                    emotional_valence: $emotional_valence,
                    created_at: datetime($created_at),
                    last_touched: datetime($last_touched),
                    completed_at: $completed_at,
                    abandoned_at: $abandoned_at,
                    abandonment_reason: $abandonment_reason
                })
                """,
                id=str(goal.id),
                title=goal.title,
                description=goal.description,
                priority=goal.priority.value,
                source=goal.source.value,
                parent_goal_id=str(goal.parent_goal_id) if goal.parent_goal_id else None,
                progress=[],
                blocked_by=None,
                emotional_valence=goal.emotional_valence,
                created_at=goal.created_at.isoformat(),
                last_touched=goal.last_touched.isoformat(),
                completed_at=None,
                abandoned_at=None,
                abandonment_reason=None,
            )

        logger.info(f"Created goal: {goal.title} ({goal.id})")
        return goal

    async def get_goal(self, goal_id: UUID) -> Optional[Goal]:
        """
        Get a goal by ID.

        Args:
            goal_id: Goal UUID

        Returns:
            Goal instance or None if not found
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                RETURN g
                """,
                id=str(goal_id),
            )
            record = await result.single()

        if not record:
            return None

        return self._record_to_goal(record["g"])

    async def update_goal(self, goal_id: UUID, goal_update: GoalUpdate) -> Optional[Goal]:
        """
        Update a goal's basic properties.

        Args:
            goal_id: Goal UUID
            goal_update: Update DTO

        Returns:
            Updated Goal or None if not found
        """
        updates = {}
        if goal_update.title is not None:
            updates["title"] = goal_update.title
        if goal_update.description is not None:
            updates["description"] = goal_update.description
        if goal_update.emotional_valence is not None:
            updates["emotional_valence"] = goal_update.emotional_valence

        if not updates:
            return await self.get_goal(goal_id)

        updates["last_touched"] = datetime.utcnow().isoformat()

        set_clauses = ", ".join(f"g.{k} = ${k}" for k in updates.keys())

        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                f"""
                MATCH (g:Goal {{id: $id}})
                SET {set_clauses}
                RETURN g
                """,
                id=str(goal_id),
                **updates,
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Updated goal: {goal_id}")
        return self._record_to_goal(record["g"])

    async def delete_goal(self, goal_id: UUID) -> bool:
        """
        Delete a goal.

        Args:
            goal_id: Goal UUID

        Returns:
            True if deleted, False if not found
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                DETACH DELETE g
                RETURN count(g) as deleted
                """,
                id=str(goal_id),
            )
            record = await result.single()

        deleted = record["deleted"] > 0
        if deleted:
            logger.info(f"Deleted goal: {goal_id}")
        return deleted

    async def list_goals(
        self,
        priority: Optional[GoalPriority] = None,
        include_completed: bool = False,
        limit: int = 50,
    ) -> list[Goal]:
        """
        List goals with optional filtering.

        Args:
            priority: Filter by priority
            include_completed: Include completed/abandoned goals
            limit: Maximum results

        Returns:
            List of Goal instances
        """
        where_clauses = []
        params = {"limit": limit}

        if priority:
            where_clauses.append("g.priority = $priority")
            params["priority"] = priority.value
        elif not include_completed:
            where_clauses.append("g.priority IN ['active', 'queued', 'backburner']")

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                f"""
                MATCH (g:Goal)
                {where_str}
                RETURN g
                ORDER BY g.last_touched DESC
                LIMIT $limit
                """,
                **params,
            )
            records = await result.data()

        return [self._record_to_goal(r["g"]) for r in records]

    # =========================================================================
    # T006: Lifecycle Management
    # =========================================================================

    async def promote_goal(self, goal_id: UUID, reason: Optional[str] = None) -> Optional[Goal]:
        """
        Promote a goal to the next priority level.

        Transitions: backburner → queued → active

        Args:
            goal_id: Goal UUID
            reason: Optional reason for promotion

        Returns:
            Updated Goal or None if not found
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        promotion_map = {
            GoalPriority.BACKBURNER: GoalPriority.QUEUED,
            GoalPriority.QUEUED: GoalPriority.ACTIVE,
        }

        if goal.priority not in promotion_map:
            logger.warning(f"Cannot promote goal with priority {goal.priority}")
            return goal

        new_priority = promotion_map[goal.priority]

        # Check limits
        if new_priority == GoalPriority.ACTIVE:
            active_count = await self._count_goals_by_priority(GoalPriority.ACTIVE)
            if active_count >= MAX_ACTIVE_GOALS:
                logger.warning(f"Cannot promote: max active goals ({MAX_ACTIVE_GOALS}) reached")
                return goal

        return await self._change_priority(goal_id, new_priority, reason)

    async def demote_goal(self, goal_id: UUID, reason: Optional[str] = None) -> Optional[Goal]:
        """
        Demote a goal to the previous priority level.

        Transitions: active → queued → backburner

        Args:
            goal_id: Goal UUID
            reason: Optional reason for demotion

        Returns:
            Updated Goal or None if not found
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        demotion_map = {
            GoalPriority.ACTIVE: GoalPriority.QUEUED,
            GoalPriority.QUEUED: GoalPriority.BACKBURNER,
        }

        if goal.priority not in demotion_map:
            logger.warning(f"Cannot demote goal with priority {goal.priority}")
            return goal

        return await self._change_priority(goal_id, demotion_map[goal.priority], reason)

    async def complete_goal(self, goal_id: UUID) -> Optional[Goal]:
        """
        Mark a goal as completed.

        Args:
            goal_id: Goal UUID

        Returns:
            Updated Goal or None if not found
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                SET g.priority = 'completed',
                    g.completed_at = datetime($completed_at),
                    g.last_touched = datetime($last_touched)
                RETURN g
                """,
                id=str(goal_id),
                completed_at=datetime.utcnow().isoformat(),
                last_touched=datetime.utcnow().isoformat(),
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Completed goal: {goal_id}")
        return self._record_to_goal(record["g"])

    async def abandon_goal(self, goal_id: UUID, reason: str) -> Optional[Goal]:
        """
        Mark a goal as abandoned.

        Args:
            goal_id: Goal UUID
            reason: Reason for abandonment

        Returns:
            Updated Goal or None if not found
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                SET g.priority = 'abandoned',
                    g.abandoned_at = datetime($abandoned_at),
                    g.abandonment_reason = $reason,
                    g.last_touched = datetime($last_touched)
                RETURN g
                """,
                id=str(goal_id),
                abandoned_at=datetime.utcnow().isoformat(),
                reason=reason,
                last_touched=datetime.utcnow().isoformat(),
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Abandoned goal: {goal_id} - {reason}")
        return self._record_to_goal(record["g"])

    async def add_progress(
        self, goal_id: UUID, content: str, heartbeat_number: Optional[int] = None
    ) -> Optional[Goal]:
        """
        Add a progress note to a goal.

        Args:
            goal_id: Goal UUID
            content: Progress note content
            heartbeat_number: Optional heartbeat number when note was added

        Returns:
            Updated Goal or None if not found
        """
        note = GoalProgressNote(
            timestamp=datetime.utcnow(),
            content=content,
            heartbeat_number=heartbeat_number,
        )

        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                SET g.progress = g.progress + [$note],
                    g.last_touched = datetime($last_touched)
                RETURN g
                """,
                id=str(goal_id),
                note=note.model_dump(),
                last_touched=datetime.utcnow().isoformat(),
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Added progress to goal: {goal_id}")
        return self._record_to_goal(record["g"])

    async def set_blocked(self, goal_id: UUID, blocker: GoalBlocker) -> Optional[Goal]:
        """
        Mark a goal as blocked.

        Args:
            goal_id: Goal UUID
            blocker: Blocker description

        Returns:
            Updated Goal or None if not found
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                SET g.blocked_by = $blocker,
                    g.last_touched = datetime($last_touched)
                RETURN g
                """,
                id=str(goal_id),
                blocker=blocker.model_dump(),
                last_touched=datetime.utcnow().isoformat(),
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Marked goal as blocked: {goal_id}")
        return self._record_to_goal(record["g"])

    async def clear_blocked(self, goal_id: UUID) -> Optional[Goal]:
        """
        Clear blocker from a goal.

        Args:
            goal_id: Goal UUID

        Returns:
            Updated Goal or None if not found
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                SET g.blocked_by = null,
                    g.last_touched = datetime($last_touched)
                RETURN g
                """,
                id=str(goal_id),
                last_touched=datetime.utcnow().isoformat(),
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Cleared blocker from goal: {goal_id}")
        return self._record_to_goal(record["g"])

    # =========================================================================
    # T007: Goal Review Logic
    # =========================================================================

    async def review_goals(self) -> GoalAssessment:
        """
        Review all goals and produce an assessment.

        This is called during each heartbeat's free "Review Goals" action.

        Returns:
            GoalAssessment with categorized goals and issues
        """
        all_goals = await self.list_goals(include_completed=False)

        assessment = GoalAssessment()
        stale_threshold = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS)

        for goal in all_goals:
            # Categorize by priority
            if goal.priority == GoalPriority.ACTIVE:
                assessment.active_goals.append(goal)
            elif goal.priority == GoalPriority.QUEUED:
                assessment.queued_goals.append(goal)
            elif goal.priority == GoalPriority.BACKBURNER:
                assessment.backburner_goals.append(goal)

            # Check for blocked
            if goal.blocked_by:
                assessment.blocked_goals.append(goal)
                assessment.issues.append(f"Goal '{goal.title}' is blocked")

            # Check for stale
            if goal.last_touched < stale_threshold:
                assessment.stale_goals.append(goal)
                if goal.priority == GoalPriority.ACTIVE:
                    assessment.issues.append(
                        f"Active goal '{goal.title}' is stale (not touched in {STALE_THRESHOLD_DAYS}+ days)"
                    )

        # Check if we need more active goals
        if len(assessment.active_goals) < 1 and len(assessment.queued_goals) > 0:
            assessment.promotion_candidates = assessment.queued_goals[:3]
            assessment.issues.append("No active goals - consider promoting from queue")

        # Check if we need to brainstorm
        if len(all_goals) == 0:
            assessment.needs_brainstorm = True
            assessment.issues.append("No goals exist - brainstorming recommended")

        return assessment

    async def get_backlog_summary(self) -> GoalBacklogSummary:
        """
        Get a summary of the goal backlog.

        Returns:
            GoalBacklogSummary with counts
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal)
                RETURN
                    g.priority as priority,
                    count(g) as count,
                    sum(CASE WHEN g.blocked_by IS NOT NULL THEN 1 ELSE 0 END) as blocked
                """
            )
            records = await result.data()

        summary = GoalBacklogSummary()
        stale_threshold = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS)

        for r in records:
            priority = r["priority"]
            count = r["count"]
            summary.total_count += count

            if priority == "active":
                summary.active_count = count
            elif priority == "queued":
                summary.queued_count = count
            elif priority == "backburner":
                summary.backburner_count = count
            elif priority == "completed":
                summary.completed_count = count
            elif priority == "abandoned":
                summary.abandoned_count = count

            summary.blocked_count += r["blocked"]

        # Count stale goals
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal)
                WHERE g.priority IN ['active', 'queued', 'backburner']
                AND g.last_touched < datetime($threshold)
                RETURN count(g) as stale_count
                """,
                threshold=stale_threshold.isoformat(),
            )
            record = await result.single()
            summary.stale_count = record["stale_count"]

        return summary

    # =========================================================================
    # T008: Goal-Memory Linkage
    # =========================================================================

    async def link_memory_to_goal(
        self, goal_id: UUID, memory_id: UUID, link_type: GoalMemoryLinkType
    ) -> GoalMemoryLink:
        """
        Link a memory to a goal.

        Args:
            goal_id: Goal UUID
            memory_id: Memory UUID
            link_type: Type of link

        Returns:
            GoalMemoryLink instance
        """
        link = GoalMemoryLink(
            goal_id=goal_id,
            memory_id=memory_id,
            link_type=link_type,
            created_at=datetime.utcnow(),
        )

        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (g:Goal {id: $goal_id}), (m:Memory {id: $memory_id})
                MERGE (g)-[r:GOAL_MEMORY_LINK {link_type: $link_type}]->(m)
                SET r.created_at = datetime($created_at)
                """,
                goal_id=str(goal_id),
                memory_id=str(memory_id),
                link_type=link_type.value,
                created_at=link.created_at.isoformat(),
            )

        logger.info(f"Linked memory {memory_id} to goal {goal_id} ({link_type.value})")
        return link

    async def get_memories_for_goal(
        self, goal_id: UUID, link_type: Optional[GoalMemoryLinkType] = None
    ) -> list[dict]:
        """
        Get memories linked to a goal.

        Args:
            goal_id: Goal UUID
            link_type: Optional filter by link type

        Returns:
            List of memory dicts with link info
        """
        where_clause = ""
        params = {"goal_id": str(goal_id)}

        if link_type:
            where_clause = "AND r.link_type = $link_type"
            params["link_type"] = link_type.value

        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                f"""
                MATCH (g:Goal {{id: $goal_id}})-[r:GOAL_MEMORY_LINK]->(m:Memory)
                {where_clause}
                RETURN m, r.link_type as link_type, r.created_at as linked_at
                ORDER BY r.created_at DESC
                """,
                **params,
            )
            records = await result.data()

        return [
            {
                "memory": r["m"],
                "link_type": r["link_type"],
                "linked_at": r["linked_at"],
            }
            for r in records
        ]

    async def get_goals_for_memory(self, memory_id: UUID) -> list[dict]:
        """
        Get goals linked to a memory.

        Args:
            memory_id: Memory UUID

        Returns:
            List of goal dicts with link info
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal)-[r:GOAL_MEMORY_LINK]->(m:Memory {id: $memory_id})
                RETURN g, r.link_type as link_type, r.created_at as linked_at
                ORDER BY r.created_at DESC
                """,
                memory_id=str(memory_id),
            )
            records = await result.data()

        return [
            {
                "goal": self._record_to_goal(r["g"]),
                "link_type": r["link_type"],
                "linked_at": r["linked_at"],
            }
            for r in records
        ]

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _change_priority(
        self, goal_id: UUID, new_priority: GoalPriority, reason: Optional[str] = None
    ) -> Optional[Goal]:
        """Change a goal's priority."""
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {id: $id})
                SET g.priority = $priority,
                    g.last_touched = datetime($last_touched)
                RETURN g
                """,
                id=str(goal_id),
                priority=new_priority.value,
                last_touched=datetime.utcnow().isoformat(),
            )
            record = await result.single()

        if not record:
            return None

        logger.info(f"Changed goal {goal_id} priority to {new_priority.value}")
        return self._record_to_goal(record["g"])

    async def _count_goals_by_priority(self, priority: GoalPriority) -> int:
        """Count goals with a specific priority."""
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (g:Goal {priority: $priority})
                RETURN count(g) as count
                """,
                priority=priority.value,
            )
            record = await result.single()

        return record["count"]

    def _record_to_goal(self, record: dict) -> Goal:
        """Convert a Neo4j record to a Goal model."""
        return Goal(
            id=UUID(record["id"]),
            title=record["title"],
            description=record.get("description"),
            priority=GoalPriority(record["priority"]),
            source=GoalSource(record.get("source", "curiosity")),
            parent_goal_id=UUID(record["parent_goal_id"]) if record.get("parent_goal_id") else None,
            progress=[
                GoalProgressNote(**p) if isinstance(p, dict) else p
                for p in (record.get("progress") or [])
            ],
            blocked_by=GoalBlocker(**record["blocked_by"]) if record.get("blocked_by") else None,
            emotional_valence=record.get("emotional_valence", 0.0),
            created_at=record.get("created_at") or datetime.utcnow(),
            last_touched=record.get("last_touched") or datetime.utcnow(),
            completed_at=record.get("completed_at"),
            abandoned_at=record.get("abandoned_at"),
            abandonment_reason=record.get("abandonment_reason"),
        )


# =============================================================================
# Service Factory
# =============================================================================

_goal_service_instance: Optional[GoalService] = None


def get_goal_service() -> GoalService:
    """Get or create the GoalService singleton."""
    global _goal_service_instance
    if _goal_service_instance is None:
        _goal_service_instance = GoalService()
    return _goal_service_instance
