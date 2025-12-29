"""
Network State Service - Observable W/T/H state management.

Part of 034-network-self-modeling feature.
Provides network state observation, snapshotting, and delta calculation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, Union

import numpy as np

from api.models.network_state import (
    NetworkState,
    NetworkStateDiff,
    NetworkStateConfig,
    SnapshotTrigger,
    ValueChange,
    get_network_state_config,
)
from api.services.webhook_neo4j_driver import WebhookNeo4jDriver, get_neo4j_driver

logger = logging.getLogger(__name__)


class NetworkStateService:
    """Service for network state observation and management.

    Implements:
    - T004: state_to_vector() for L2 norm delta calculation
    - T006: Webhook persistence helper for Neo4j storage
    - T014-T017: Core service methods
    """

    DELTA_THRESHOLD = 0.05  # 5% change triggers snapshot

    def __init__(
        self,
        driver: Optional[WebhookNeo4jDriver] = None,
        config: Optional[NetworkStateConfig] = None,
    ):
        self.driver = driver or get_neo4j_driver()
        self.config = config or get_network_state_config()
        self._cache: dict[str, NetworkState] = {}

    def state_to_vector(
        self,
        state: Union[NetworkState, dict]
    ) -> np.ndarray:
        """Convert network state to numpy vector for delta calculation (T004).

        Creates a flattened vector of all W, T, H values for L2 norm comparison.

        Args:
            state: NetworkState model or dict with connection_weights, thresholds, speed_factors

        Returns:
            numpy array of all state values
        """
        if isinstance(state, NetworkState):
            weights = state.connection_weights
            thresholds = state.thresholds
            speeds = state.speed_factors
        else:
            weights = state.get("connection_weights", {})
            thresholds = state.get("thresholds", {})
            speeds = state.get("speed_factors", {})

        # Combine all values in consistent order (sorted keys)
        values = (
            [weights[k] for k in sorted(weights.keys())] +
            [thresholds[k] for k in sorted(thresholds.keys())] +
            [speeds[k] for k in sorted(speeds.keys())]
        )

        return np.array(values) if values else np.array([0.0])

    def calculate_delta(
        self,
        old_state: Union[NetworkState, dict],
        new_state: Union[NetworkState, dict]
    ) -> float:
        """Calculate L2 norm delta between two states.

        Args:
            old_state: Previous network state
            new_state: New network state

        Returns:
            Relative delta (||new - old|| / ||old||)
        """
        old_vec = self.state_to_vector(old_state)
        new_vec = self.state_to_vector(new_state)

        # Handle dimension mismatch (state structure changed)
        if old_vec.shape != new_vec.shape:
            logger.warning(
                f"State dimension mismatch: {old_vec.shape} vs {new_vec.shape}"
            )
            return 1.0  # Force snapshot on structure change

        old_norm = np.linalg.norm(old_vec)
        if old_norm == 0:
            return 1.0  # Force snapshot from zero state

        return float(np.linalg.norm(new_vec - old_vec) / old_norm)

    async def get_current(self, agent_id: str) -> Optional[NetworkState]:
        """Get most recent network state for agent (T014).

        Args:
            agent_id: Agent identifier

        Returns:
            Most recent NetworkState or None if no state exists
        """
        if not self.config.network_state_enabled:
            return None

        # Check cache first
        if agent_id in self._cache:
            return self._cache[agent_id]

        # Query Neo4j via webhook
        cypher = """
        MATCH (s:NetworkState {agent_id: $agent_id})
        RETURN s
        ORDER BY s.timestamp DESC
        LIMIT 1
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, {"agent_id": agent_id})
                data = await result.single()

                if data and "s" in data:
                    state = self._parse_neo4j_state(data["s"])
                    self._cache[agent_id] = state
                    return state
        except Exception as e:
            logger.error(f"Failed to get network state for {agent_id}: {e}")

        return None

    async def should_snapshot(
        self,
        agent_id: str,
        new_state: dict
    ) -> bool:
        """Check if state change exceeds threshold (T015).

        Args:
            agent_id: Agent identifier
            new_state: New state dict with W/T/H values

        Returns:
            True if snapshot should be created
        """
        if not self.config.network_state_enabled:
            return False

        current = await self.get_current(agent_id)
        if not current:
            return True  # Always snapshot if no previous state

        delta = self.calculate_delta(current, new_state)
        return delta > self.config.delta_threshold

    async def create_snapshot(
        self,
        agent_id: str,
        trigger: SnapshotTrigger,
        connection_weights: dict[str, float],
        thresholds: dict[str, float],
        speed_factors: dict[str, float],
    ) -> Optional[NetworkState]:
        """Create and persist network state snapshot (T016).

        Args:
            agent_id: Agent identifier
            trigger: Reason for snapshot
            connection_weights: W values
            thresholds: T values
            speed_factors: H values

        Returns:
            Created NetworkState or None if disabled
        """
        if not self.config.network_state_enabled:
            return None

        # Get previous state for delta calculation
        previous = await self.get_current(agent_id)

        state = NetworkState(
            agent_id=agent_id,
            trigger=trigger,
            connection_weights=connection_weights,
            thresholds=thresholds,
            speed_factors=speed_factors,
        )

        # Calculate delta if previous exists
        if previous:
            state.delta_from_previous = self.calculate_delta(previous, state)

        # Compute checksum
        state.checksum = state.compute_checksum()

        # Persist to Neo4j via webhook (T006)
        await self._persist_snapshot(state)

        # Update cache
        self._cache[agent_id] = state

        logger.info(
            f"Created network state snapshot for {agent_id}: "
            f"trigger={trigger.value}, delta={state.delta_from_previous}"
        )

        return state

    async def get_history(
        self,
        agent_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[NetworkState]:
        """Get network state history for agent (T017).

        Args:
            agent_id: Agent identifier
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of snapshots (max 1000)

        Returns:
            List of NetworkState snapshots
        """
        if not self.config.network_state_enabled:
            return []

        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()

        limit = min(limit, 1000)

        cypher = """
        MATCH (s:NetworkState {agent_id: $agent_id})
        WHERE s.timestamp >= $start_time AND s.timestamp <= $end_time
        RETURN s
        ORDER BY s.timestamp DESC
        LIMIT $limit
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    cypher,
                    {
                        "agent_id": agent_id,
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "limit": limit,
                    }
                )
                data = await result.data()
                return [self._parse_neo4j_state(row["s"]) for row in data if "s" in row]
        except Exception as e:
            logger.error(f"Failed to get history for {agent_id}: {e}")
            return []

    async def get_diff(
        self,
        agent_id: str,
        from_snapshot_id: str,
        to_snapshot_id: str,
    ) -> Optional[NetworkStateDiff]:
        """Get diff between two snapshots (T021).

        Args:
            agent_id: Agent identifier
            from_snapshot_id: Source snapshot ID
            to_snapshot_id: Target snapshot ID

        Returns:
            NetworkStateDiff or None if snapshots not found
        """
        if not self.config.network_state_enabled:
            return None

        cypher = """
        MATCH (from:NetworkState {id: $from_id, agent_id: $agent_id})
        MATCH (to:NetworkState {id: $to_id, agent_id: $agent_id})
        RETURN from, to
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    cypher,
                    {
                        "from_id": from_snapshot_id,
                        "to_id": to_snapshot_id,
                        "agent_id": agent_id,
                    }
                )
                data = await result.single()

                if not data:
                    return None

                from_state = self._parse_neo4j_state(data["from"])
                to_state = self._parse_neo4j_state(data["to"])

                return self._calculate_diff(from_state, to_state)
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return None

    async def _persist_snapshot(self, state: NetworkState) -> None:
        """Persist network state to Neo4j via webhook (T006).

        Args:
            state: NetworkState to persist
        """
        cypher = """
        CREATE (s:NetworkState {
            id: $id,
            agent_id: $agent_id,
            timestamp: $timestamp,
            trigger: $trigger,
            connection_weights: $connection_weights,
            thresholds: $thresholds,
            speed_factors: $speed_factors,
            delta_from_previous: $delta_from_previous,
            checksum: $checksum
        })
        RETURN s
        """

        try:
            async with self.driver.session() as session:
                await session.run(
                    cypher,
                    {
                        "id": state.id,
                        "agent_id": state.agent_id,
                        "timestamp": state.timestamp.isoformat(),
                        "trigger": state.trigger.value,
                        "connection_weights": state.connection_weights,
                        "thresholds": state.thresholds,
                        "speed_factors": state.speed_factors,
                        "delta_from_previous": state.delta_from_previous,
                        "checksum": state.checksum,
                    },
                    mode="write"
                )
        except Exception as e:
            logger.error(f"Failed to persist network state: {e}")
            raise

    def _parse_neo4j_state(self, data: dict) -> NetworkState:
        """Parse Neo4j node data to NetworkState model.

        Args:
            data: Neo4j node properties

        Returns:
            NetworkState model
        """
        return NetworkState(
            id=data.get("id", ""),
            agent_id=data.get("agent_id", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            trigger=SnapshotTrigger(data.get("trigger", "MANUAL")),
            connection_weights=data.get("connection_weights", {}),
            thresholds=data.get("thresholds", {}),
            speed_factors=data.get("speed_factors", {}),
            delta_from_previous=data.get("delta_from_previous"),
            checksum=data.get("checksum"),
        )

    def _calculate_diff(
        self,
        from_state: NetworkState,
        to_state: NetworkState
    ) -> NetworkStateDiff:
        """Calculate diff between two states.

        Args:
            from_state: Source state
            to_state: Target state

        Returns:
            NetworkStateDiff with all changes
        """
        weight_changes = {}
        threshold_changes = {}
        speed_changes = {}

        # Weight changes
        all_weight_keys = set(from_state.connection_weights.keys()) | set(to_state.connection_weights.keys())
        for key in all_weight_keys:
            old = from_state.connection_weights.get(key, 0.0)
            new = to_state.connection_weights.get(key, 0.0)
            if old != new:
                weight_changes[key] = ValueChange(old=old, new=new, delta=new - old)

        # Threshold changes
        all_threshold_keys = set(from_state.thresholds.keys()) | set(to_state.thresholds.keys())
        for key in all_threshold_keys:
            old = from_state.thresholds.get(key, 0.0)
            new = to_state.thresholds.get(key, 0.0)
            if old != new:
                threshold_changes[key] = ValueChange(old=old, new=new, delta=new - old)

        # Speed factor changes
        all_speed_keys = set(from_state.speed_factors.keys()) | set(to_state.speed_factors.keys())
        for key in all_speed_keys:
            old = from_state.speed_factors.get(key, 0.0)
            new = to_state.speed_factors.get(key, 0.0)
            if old != new:
                speed_changes[key] = ValueChange(old=old, new=new, delta=new - old)

        return NetworkStateDiff(
            from_snapshot_id=from_state.id,
            to_snapshot_id=to_state.id,
            weight_changes=weight_changes,
            threshold_changes=threshold_changes,
            speed_factor_changes=speed_changes,
            total_delta=self.calculate_delta(from_state, to_state),
        )


# Singleton instance
_service: Optional[NetworkStateService] = None


def get_network_state_service() -> NetworkStateService:
    """Get or create the network state service singleton."""
    global _service
    if _service is None:
        _service = NetworkStateService()
    return _service
