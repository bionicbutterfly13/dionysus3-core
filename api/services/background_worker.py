"""
Background Worker for Heartbeat System
Feature: 004-heartbeat-system
Tasks: T021, T022, T023, T024

Background maintenance daemon with no agency.
Handles neighborhood recomputation, episode summarization, and health monitoring.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger("dionysus.background_worker")


# =============================================================================
# Worker State
# =============================================================================


class WorkerState(str, Enum):
    """State of the background worker."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class WorkerHealth:
    """Health metrics for the background worker."""

    state: WorkerState = WorkerState.STOPPED
    last_cycle_at: datetime | None = None
    cycles_completed: int = 0
    errors_count: int = 0
    last_error: str | None = None
    last_error_at: datetime | None = None

    # Task-specific metrics
    neighborhoods_recomputed: int = 0
    episodes_summarized: int = 0
    stale_items_found: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state.value,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "cycles_completed": self.cycles_completed,
            "errors_count": self.errors_count,
            "last_error": self.last_error,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "neighborhoods_recomputed": self.neighborhoods_recomputed,
            "episodes_summarized": self.episodes_summarized,
            "stale_items_found": self.stale_items_found,
        }


@dataclass
class WorkerConfig:
    """Configuration for the background worker."""

    cycle_interval_seconds: float = 30.0
    neighborhood_stale_hours: float = 24.0
    episode_stale_hours: float = 48.0
    max_items_per_cycle: int = 10
    health_check_interval_cycles: int = 10


# =============================================================================
# T022: Neighborhood Recomputation
# =============================================================================


class NeighborhoodRecomputeTask:
    """
    Recomputes stale memory neighborhoods.

    A neighborhood is stale when its neighbors haven't been updated
    in a while, possibly due to new memories being added.
    """

    def __init__(self, driver=None, config: WorkerConfig | None = None):
        """Initialize the task."""
        self._driver = driver
        self._config = config or WorkerConfig()

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    async def find_stale_neighborhoods(self) -> list[dict[str, Any]]:
        """
        Find memories with stale neighborhoods.

        Returns:
            List of memory IDs needing recomputation
        """
        driver = self._get_driver()
        stale_threshold = datetime.utcnow() - timedelta(hours=self._config.neighborhood_stale_hours)

        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (m:Memory)
                WHERE m.neighborhood_computed_at IS NULL
                   OR m.neighborhood_computed_at < datetime($threshold)
                RETURN m.id as id, m.content as content,
                       m.neighborhood_computed_at as last_computed
                ORDER BY m.neighborhood_computed_at ASC NULLS FIRST
                LIMIT $limit
                """,
                threshold=stale_threshold.isoformat(),
                limit=self._config.max_items_per_cycle,
            )
            records = await result.data()

        return records

    async def recompute_neighborhood(self, memory_id: str) -> bool:
        """
        Recompute neighborhood for a single memory.

        This includes:
        - Graph neighbors (directly connected)
        - Vector neighbors (semantically similar)
        - Temporal neighbors (created around same time)

        Args:
            memory_id: ID of memory to update

        Returns:
            True if successful
        """
        driver = self._get_driver()

        try:
            async with driver.session() as session:
                # Find graph neighbors (memories connected via relationships)
                graph_result = await session.run(
                    """
                    MATCH (m:Memory {id: $memory_id})-[r]-(neighbor:Memory)
                    WHERE type(r) <> 'TEMPORAL_NEAR'
                    RETURN neighbor.id as id, type(r) as relationship
                    LIMIT 20
                    """,
                    memory_id=memory_id,
                )
                graph_neighbors = await graph_result.data()

                # Find temporal neighbors (within 1 hour)
                temporal_result = await session.run(
                    """
                    MATCH (m:Memory {id: $memory_id})
                    MATCH (neighbor:Memory)
                    WHERE neighbor.id <> m.id
                      AND abs(duration.inSeconds(neighbor.created_at, m.created_at).seconds) < 3600
                    RETURN neighbor.id as id
                    LIMIT 10
                    """,
                    memory_id=memory_id,
                )
                temporal_neighbors = await temporal_result.data()

                # Update neighborhood metadata
                await session.run(
                    """
                    MATCH (m:Memory {id: $memory_id})
                    SET m.neighborhood_computed_at = datetime(),
                        m.graph_neighbor_count = $graph_count,
                        m.temporal_neighbor_count = $temporal_count
                    """,
                    memory_id=memory_id,
                    graph_count=len(graph_neighbors),
                    temporal_count=len(temporal_neighbors),
                )

                # Create/update temporal neighbor relationships
                for neighbor in temporal_neighbors:
                    await session.run(
                        """
                        MATCH (m:Memory {id: $memory_id})
                        MATCH (n:Memory {id: $neighbor_id})
                        MERGE (m)-[r:TEMPORAL_NEAR]-(n)
                        ON CREATE SET r.created_at = datetime()
                        """,
                        memory_id=memory_id,
                        neighbor_id=neighbor["id"],
                    )

            logger.debug(f"Recomputed neighborhood for {memory_id}: {len(graph_neighbors)} graph, {len(temporal_neighbors)} temporal")
            return True

        except Exception as e:
            logger.error(f"Failed to recompute neighborhood for {memory_id}: {e}")
            return False

    async def run(self) -> int:
        """
        Run the neighborhood recomputation task.

        Returns:
            Number of neighborhoods recomputed
        """
        stale = await self.find_stale_neighborhoods()
        if not stale:
            return 0

        count = 0
        for item in stale:
            if await self.recompute_neighborhood(item["id"]):
                count += 1

        logger.info(f"Recomputed {count} neighborhoods")
        return count


# =============================================================================
# T023: Episode Summarization
# =============================================================================


class EpisodeSummarizationTask:
    """
    Summarizes closed episodes.

    Episodes are collections of related memories over a time period.
    When an episode is closed, we generate a summary and embedding.
    """

    def __init__(self, driver=None, config: WorkerConfig | None = None):
        """Initialize the task."""
        self._driver = driver
        self._config = config or WorkerConfig()

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    async def find_unsummarized_episodes(self) -> list[dict[str, Any]]:
        """
        Find episodes that need summarization.

        Returns:
            List of episode data needing summarization
        """
        driver = self._get_driver()

        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (e:Episode)
                WHERE e.summary IS NULL
                  AND e.closed_at IS NOT NULL
                RETURN e.id as id, e.title as title, e.closed_at as closed_at
                ORDER BY e.closed_at ASC
                LIMIT $limit
                """,
                limit=self._config.max_items_per_cycle,
            )
            records = await result.data()

        return records

    async def summarize_episode(self, episode_id: str) -> bool:
        """
        Generate summary for an episode.

        Args:
            episode_id: ID of episode to summarize

        Returns:
            True if successful
        """
        driver = self._get_driver()

        try:
            async with driver.session() as session:
                # Get episode memories
                memory_result = await session.run(
                    """
                    MATCH (e:Episode {id: $episode_id})-[:CONTAINS]->(m:Memory)
                    RETURN m.content as content, m.memory_type as type
                    ORDER BY m.created_at
                    """,
                    episode_id=episode_id,
                )
                memories = await memory_result.data()

                if not memories:
                    logger.warning(f"Episode {episode_id} has no memories")
                    return False

                # TODO: Use LLM for actual summarization
                # For now, create a simple summary
                memory_count = len(memories)
                content_preview = " | ".join(m["content"][:50] for m in memories[:3])
                summary = f"Episode with {memory_count} memories: {content_preview}..."

                # Update episode with summary
                await session.run(
                    """
                    MATCH (e:Episode {id: $episode_id})
                    SET e.summary = $summary,
                        e.summarized_at = datetime(),
                        e.memory_count = $memory_count
                    """,
                    episode_id=episode_id,
                    summary=summary,
                    memory_count=memory_count,
                )

            logger.debug(f"Summarized episode {episode_id}: {memory_count} memories")
            return True

        except Exception as e:
            logger.error(f"Failed to summarize episode {episode_id}: {e}")
            return False

    async def run(self) -> int:
        """
        Run the episode summarization task.

        Returns:
            Number of episodes summarized
        """
        unsummarized = await self.find_unsummarized_episodes()
        if not unsummarized:
            return 0

        count = 0
        for item in unsummarized:
            if await self.summarize_episode(item["id"]):
                count += 1

        logger.info(f"Summarized {count} episodes")
        return count


# =============================================================================
# T024: Health Monitoring
# =============================================================================


class HealthMonitorTask:
    """
    Monitors system health and detects issues.

    Checks:
    - Stale counts exceeding thresholds
    - Queue backlogs
    - Error rates
    """

    def __init__(self, driver=None, config: WorkerConfig | None = None):
        """Initialize the task."""
        self._driver = driver
        self._config = config or WorkerConfig()
        self._thresholds = {
            "stale_goals": 5,
            "blocked_goals": 3,
            "orphan_memories": 100,
            "error_rate_percent": 10,
        }

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    async def check_health(self) -> dict[str, Any]:
        """
        Run health checks.

        Returns:
            Dict with health check results
        """
        driver = self._get_driver()
        issues = []
        metrics = {}

        async with driver.session() as session:
            # Check stale goals
            stale_result = await session.run(
                """
                MATCH (g:Goal)
                WHERE g.priority IN ['active', 'queued']
                  AND g.last_touched < datetime() - duration('P7D')
                RETURN count(g) as count
                """
            )
            stale_record = await stale_result.single()
            metrics["stale_goals"] = stale_record["count"] if stale_record else 0

            if metrics["stale_goals"] > self._thresholds["stale_goals"]:
                issues.append(f"High stale goal count: {metrics['stale_goals']}")

            # Check blocked goals
            blocked_result = await session.run(
                """
                MATCH (g:Goal)
                WHERE g.blocked_by IS NOT NULL
                RETURN count(g) as count
                """
            )
            blocked_record = await blocked_result.single()
            metrics["blocked_goals"] = blocked_record["count"] if blocked_record else 0

            if metrics["blocked_goals"] > self._thresholds["blocked_goals"]:
                issues.append(f"High blocked goal count: {metrics['blocked_goals']}")

            # Check orphan memories (no relationships)
            orphan_result = await session.run(
                """
                MATCH (m:Memory)
                WHERE NOT (m)-[]-()
                RETURN count(m) as count
                """
            )
            orphan_record = await orphan_result.single()
            metrics["orphan_memories"] = orphan_record["count"] if orphan_record else 0

            if metrics["orphan_memories"] > self._thresholds["orphan_memories"]:
                issues.append(f"High orphan memory count: {metrics['orphan_memories']}")

            # Check heartbeat state
            hb_result = await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                RETURN s.current_energy as energy, s.paused as paused,
                       s.heartbeat_count as count
                """
            )
            hb_record = await hb_result.single()
            if hb_record:
                metrics["current_energy"] = hb_record["energy"]
                metrics["heartbeat_paused"] = hb_record["paused"]
                metrics["heartbeat_count"] = hb_record["count"]

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "metrics": metrics,
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def run(self) -> dict[str, Any]:
        """
        Run health monitoring.

        Returns:
            Health check results
        """
        health = await self.check_health()

        if not health["healthy"]:
            logger.warning(f"Health issues detected: {health['issues']}")
        else:
            logger.debug("Health check passed")

        return health


# =============================================================================
# T021: Background Worker
# =============================================================================


class BackgroundWorker:
    """
    Background maintenance daemon.

    Runs on a 30-second cycle, executing maintenance tasks:
    - Neighborhood recomputation (for stale memories)
    - Episode summarization (for closed episodes)
    - Health monitoring (periodic checks)

    This worker has NO agency - it only performs maintenance.
    """

    def __init__(self, config: WorkerConfig | None = None, driver=None):
        """
        Initialize the background worker.

        Args:
            config: Worker configuration
            driver: Neo4j driver
        """
        self._config = config or WorkerConfig()
        self._driver = driver
        self._state = WorkerState.STOPPED
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._health = WorkerHealth()

        # Initialize tasks
        self._neighborhood_task = NeighborhoodRecomputeTask(driver, self._config)
        self._episode_task = EpisodeSummarizationTask(driver, self._config)
        self._health_task = HealthMonitorTask(driver, self._config)

    @property
    def state(self) -> WorkerState:
        """Get worker state."""
        return self._state

    @property
    def health(self) -> WorkerHealth:
        """Get worker health metrics."""
        return self._health

    async def start(self) -> None:
        """Start the background worker."""
        if self._state == WorkerState.RUNNING:
            logger.warning("Worker already running")
            return

        self._state = WorkerState.RUNNING
        self._health.state = WorkerState.RUNNING
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Background worker started")

    async def stop(self) -> None:
        """Stop the background worker."""
        if self._state == WorkerState.STOPPED:
            logger.warning("Worker already stopped")
            return

        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._state = WorkerState.STOPPED
        self._health.state = WorkerState.STOPPED
        logger.info("Background worker stopped")

    async def pause(self) -> None:
        """Pause the background worker."""
        if self._state != WorkerState.RUNNING:
            return

        self._state = WorkerState.PAUSED
        self._health.state = WorkerState.PAUSED
        logger.info("Background worker paused")

    async def resume(self) -> None:
        """Resume the background worker."""
        if self._state != WorkerState.PAUSED:
            return

        self._state = WorkerState.RUNNING
        self._health.state = WorkerState.RUNNING
        logger.info("Background worker resumed")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        logger.info("Worker loop started")
        cycle_count = 0

        while not self._stop_event.is_set():
            try:
                # Wait for next cycle
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._config.cycle_interval_seconds,
                    )
                    # Stop requested
                    break
                except asyncio.TimeoutError:
                    pass

                # Skip if paused
                if self._state == WorkerState.PAUSED:
                    continue

                cycle_count += 1
                logger.debug(f"Worker cycle {cycle_count}")

                # Run maintenance tasks
                try:
                    from api.utils.event_bus import get_event_bus
                    bus = get_event_bus()

                    # Neighborhood recomputation
                    neighborhoods = await self._neighborhood_task.run()
                    self._health.neighborhoods_recomputed += neighborhoods
                    self._health.stale_items_found += neighborhoods
                    
                    if neighborhoods > 0:
                        await bus.emit_system_event(
                            source="background_worker",
                            event_type="neighborhood_recompute",
                            summary=f"Recomputed {neighborhoods} memory neighborhoods.",
                            metadata={"count": neighborhoods}
                        )

                    # Episode summarization
                    episodes = await self._episode_task.run()
                    self._health.episodes_summarized += episodes
                    
                    if episodes > 0:
                        await bus.emit_system_event(
                            source="background_worker",
                            event_type="episode_summarization",
                            summary=f"Summarized {episodes} closed memory episodes.",
                            metadata={"count": episodes}
                        )

                    # FEATURE 047: Unified Multi-Tier Memory Lifecycle
                    try:
                        from api.services.multi_tier_service import get_multi_tier_service
                        multi_tier_svc = get_multi_tier_service()
                        await multi_tier_svc.run_lifecycle_management()
                    except Exception as e:
                        logger.error(f"Multi-tier memory lifecycle error in background worker: {e}")

                    # FEATURE 049: Continuous Self-Monitoring (System Moments)
                    # Run every cycle (30s) or controlled by config
                    try:
                        from api.services.meta_evolution_service import get_meta_evolution_service
                        evo_svc = get_meta_evolution_service()
                        await evo_svc.capture_system_moment()
                    except Exception as e:
                        logger.error(f"Failed to capture system moment: {e}")

                    # FEATURE 049: Meta-Evolutionary Cycle
                    # Run every 100 cycles (~50 minutes) or controlled by config
                    if cycle_count % 100 == 0:
                        try:
                            await evo_svc.run_evolution_cycle()
                        except Exception as e:
                            logger.error(f"Meta-evolution cycle failed: {e}")

                    # Periodic health check
                    if cycle_count % self._config.health_check_interval_cycles == 0:
                        await self._health_task.run()

                    self._health.cycles_completed += 1
                    self._health.last_cycle_at = datetime.utcnow()

                except Exception as e:
                    self._health.errors_count += 1
                    self._health.last_error = str(e)
                    self._health.last_error_at = datetime.utcnow()
                    logger.error(f"Worker cycle error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(60)

        logger.info("Worker loop ended")

    def get_status(self) -> dict[str, Any]:
        """Get worker status."""
        return {
            "state": self._state.value,
            "config": {
                "cycle_interval_seconds": self._config.cycle_interval_seconds,
                "max_items_per_cycle": self._config.max_items_per_cycle,
            },
            "health": self._health.to_dict(),
        }


# =============================================================================
# Service Factory
# =============================================================================

_worker_instance: BackgroundWorker | None = None


def get_background_worker() -> BackgroundWorker:
    """Get or create the BackgroundWorker singleton."""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = BackgroundWorker()
    return _worker_instance


async def start_background_worker() -> BackgroundWorker:
    """
    Start the background worker.

    Returns:
        Running BackgroundWorker instance
    """
    worker = get_background_worker()
    await worker.start()
    return worker
