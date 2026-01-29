"""
Energy Service for Heartbeat System
Feature: 004-heartbeat-system
Tasks: T009, T010

Service for managing AGI energy budget. Energy is a unified abstraction
over compute cost, network load, user attention, and cognitive coherence.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger("dionysus.energy_service")


# =============================================================================
# Action Types and Costs
# =============================================================================


class ActionType(str, Enum):
    """Types of actions the AGI can take during a heartbeat."""

    # Free actions (cost 0)
    OBSERVE = "observe"
    REVIEW_GOALS = "review_goals"
    REMEMBER = "remember"
    REST = "rest"

    # Retrieval (cost 1)
    RECALL = "recall"

    # Memory (cost 1-2)
    CONNECT = "connect"
    MAINTAIN = "maintain"

    # Goals (cost 1-3)
    REPRIORITIZE = "reprioritize"
    BRAINSTORM_GOALS = "brainstorm_goals"

    # Reasoning (cost 2-6)
    REFLECT = "reflect"
    INQUIRE_SHALLOW = "inquire_shallow"
    INQUIRE_DEEP = "inquire_deep"
    SYNTHESIZE = "synthesize"

    # Communication (cost 5-7)
    REACH_OUT_USER = "reach_out_user"
    REACH_OUT_PUBLIC = "reach_out_public"

    # Mental Models (cost 3)
    REVISE_MODEL = "revise_model"

    # MOSAEIC Memory Management (cost 1-3)
    REVISE_BELIEF = "revise_belief"      # Update/replace a belief
    PRUNE_EPISODIC = "prune_episodic"    # Apply episodic decay
    ARCHIVE_SEMANTIC = "archive_semantic"  # Archive low-confidence beliefs
    
    # ULTRATHINK: Psychological Actions
    EXOSKELETON_RECOVERY = "exoskeleton_recovery"  # Point of Performance grounding
    SURFACE_CONTEXT = "surface_context"  # Proactive Architecture Hunger
    VITAL_PAUSE = "vital_pause"  # Structured observation (Five Windows)


# Default action costs (can be overridden from Neo4j config)
DEFAULT_ACTION_COSTS: dict[ActionType, float] = {
    # Free
    ActionType.OBSERVE: 0.0,
    ActionType.REVIEW_GOALS: 0.0,
    ActionType.REMEMBER: 0.0,
    ActionType.REST: 0.0,
    # Retrieval
    ActionType.RECALL: 1.0,
    # Memory
    ActionType.CONNECT: 1.0,
    ActionType.MAINTAIN: 2.0,
    # Goals
    ActionType.REPRIORITIZE: 1.0,
    ActionType.BRAINSTORM_GOALS: 3.0,
    # Reasoning
    ActionType.REFLECT: 2.0,
    ActionType.INQUIRE_SHALLOW: 3.0,
    ActionType.INQUIRE_DEEP: 6.0,
    ActionType.SYNTHESIZE: 4.0,
    # Communication
    ActionType.REACH_OUT_USER: 5.0,
    ActionType.REACH_OUT_PUBLIC: 7.0,
    # Mental Models
    ActionType.REVISE_MODEL: 3.0,
    # MOSAEIC Memory Management
    ActionType.REVISE_BELIEF: 3.0,
    ActionType.PRUNE_EPISODIC: 2.0,
    ActionType.ARCHIVE_SEMANTIC: 1.0,
    # Psychological
    ActionType.EXOSKELETON_RECOVERY: 2.0,
    ActionType.SURFACE_CONTEXT: 1.0,
    ActionType.VITAL_PAUSE: 0.0,
}


# =============================================================================
# Energy Configuration
# =============================================================================


@dataclass
class EnergyConfig:
    """Configuration for the energy system."""

    base_regeneration: float = 10.0  # Energy gained per heartbeat
    max_energy: float = 20.0  # Maximum energy cap
    min_energy: float = 0.0  # Minimum energy floor (no debt)
    carry_over_rate: float = 1.0  # 100% carry-over by default


# =============================================================================
# Energy State
# =============================================================================


@dataclass
class EnergyState:
    """Current state of the energy system."""

    current_energy: float
    last_heartbeat_at: Optional[datetime]
    heartbeat_count: int
    paused: bool = False
    pause_reason: Optional[str] = None


# =============================================================================
# EnergyService
# =============================================================================


class EnergyService:
    """
    Service for managing AGI energy budget.

    Energy creates meaningful scarcity that forces the AGI to prioritize
    actions. A typical heartbeat uses 7-10 energy, with a budget of 10
    per heartbeat and max of 20 (allowing saving up).
    """

    def __init__(self, driver=None, config: Optional[EnergyConfig] = None):
        """
        Initialize EnergyService.

        Args:
            driver: Neo4j driver instance
            config: Energy configuration (uses defaults if not provided)
        """
        self._driver = driver
        self._config = config or EnergyConfig()
        self._action_costs = DEFAULT_ACTION_COSTS.copy()

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    # =========================================================================
    # T009: Energy State Management
    # =========================================================================

    async def get_state(self) -> EnergyState:
        """
        Get current energy state from Neo4j.

        Returns:
            EnergyState instance
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                RETURN s
                """
            )
            record = await result.single()

        if not record:
            # Create default state if not exists
            return await self._create_default_state()

        s = record["s"]
        return EnergyState(
            current_energy=s.get("current_energy", self._config.base_regeneration),
            last_heartbeat_at=s.get("last_heartbeat_at"),
            heartbeat_count=s.get("heartbeat_count", 0),
            paused=s.get("paused", False),
            pause_reason=s.get("pause_reason"),
        )

    async def _create_default_state(self) -> EnergyState:
        """Create default energy state in Neo4j."""
        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (s:HeartbeatState {singleton_id: 'main'})
                ON CREATE SET
                    s.current_energy = $energy,
                    s.last_heartbeat_at = null,
                    s.next_heartbeat_at = null,
                    s.heartbeat_count = 0,
                    s.paused = false,
                    s.pause_reason = null,
                    s.updated_at = datetime()
                """,
                energy=self._config.base_regeneration,
            )

        return EnergyState(
            current_energy=self._config.base_regeneration,
            last_heartbeat_at=None,
            heartbeat_count=0,
        )

    async def regenerate_energy(self) -> EnergyState:
        """
        Regenerate energy at start of heartbeat.

        Adds base_regeneration to current energy, capped at max_energy.

        Returns:
            Updated EnergyState
        """
        state = await self.get_state()

        new_energy = min(
            state.current_energy + self._config.base_regeneration,
            self._config.max_energy,
        )

        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                SET s.current_energy = $energy,
                    s.updated_at = datetime()
                """,
                energy=new_energy,
            )

        logger.info(
            f"Regenerated energy: {state.current_energy:.1f} + {self._config.base_regeneration:.1f} = {new_energy:.1f}"
        )

        state.current_energy = new_energy
        return state

    async def spend_energy(self, amount: float) -> tuple[bool, float]:
        """
        Spend energy on an action.

        Args:
            amount: Energy to spend

        Returns:
            Tuple of (success, remaining_energy)
        """
        state = await self.get_state()

        if amount > state.current_energy:
            logger.warning(
                f"Cannot spend {amount:.1f} energy (only {state.current_energy:.1f} available)"
            )
            return False, state.current_energy

        new_energy = max(state.current_energy - amount, self._config.min_energy)

        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                SET s.current_energy = $energy,
                    s.updated_at = datetime()
                """,
                energy=new_energy,
            )

        logger.debug(f"Spent {amount:.1f} energy, remaining: {new_energy:.1f}")
        return True, new_energy

    async def set_energy(self, amount: float) -> EnergyState:
        """
        Set energy to a specific value (for testing/admin).

        Args:
            amount: New energy value

        Returns:
            Updated EnergyState
        """
        clamped = max(self._config.min_energy, min(amount, self._config.max_energy))

        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                SET s.current_energy = $energy,
                    s.updated_at = datetime()
                """,
                energy=clamped,
            )

        logger.info(f"Set energy to {clamped:.1f}")
        return await self.get_state()

    async def increment_heartbeat_count(self) -> int:
        """
        Increment and return the heartbeat count.

        Returns:
            New heartbeat count
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                SET s.heartbeat_count = s.heartbeat_count + 1,
                    s.last_heartbeat_at = datetime(),
                    s.updated_at = datetime()
                RETURN s.heartbeat_count as count
                """
            )
            record = await result.single()

        count = record["count"]
        logger.info(f"Heartbeat #{count}")
        return count

    # =========================================================================
    # T010: Action Cost Tracking
    # =========================================================================

    def get_action_cost(self, action_type: ActionType) -> float:
        """
        Get the energy cost of an action.

        Args:
            action_type: Type of action

        Returns:
            Energy cost
        """
        return self._action_costs.get(action_type, 0.0)

    async def can_afford_action(self, action_type: ActionType) -> bool:
        """
        Check if we have enough energy for an action.

        Args:
            action_type: Type of action

        Returns:
            True if affordable
        """
        state = await self.get_state()
        cost = self.get_action_cost(action_type)
        return state.current_energy >= cost

    async def can_afford_actions(self, action_types: list[ActionType]) -> tuple[bool, float]:
        """
        Check if we have enough energy for a list of actions.

        Args:
            action_types: List of action types

        Returns:
            Tuple of (can_afford_all, total_cost)
        """
        state = await self.get_state()
        total_cost = sum(self.get_action_cost(a) for a in action_types)
        return state.current_energy >= total_cost, total_cost

    def trim_actions_to_budget(
        self, actions: list[ActionType], available_energy: float
    ) -> list[ActionType]:
        """
        Trim a list of actions to fit within energy budget.

        Args:
            actions: List of action types
            available_energy: Available energy

        Returns:
            Trimmed list that fits budget
        """
        result = []
        remaining = available_energy

        for action in actions:
            cost = self.get_action_cost(action)
            if cost <= remaining:
                result.append(action)
                remaining -= cost
            else:
                logger.debug(f"Trimmed action {action.value} (cost {cost:.1f}, only {remaining:.1f} left)")
                break

        return result

    async def execute_action_with_cost(
        self, action_type: ActionType
    ) -> tuple[bool, float, float]:
        """
        Attempt to execute an action, spending energy if affordable.

        Args:
            action_type: Type of action

        Returns:
            Tuple of (success, cost, remaining_energy)
        """
        cost = self.get_action_cost(action_type)

        if cost == 0:
            # Free action
            state = await self.get_state()
            return True, 0.0, state.current_energy

        success, remaining = await self.spend_energy(cost)
        return success, cost if success else 0.0, remaining

    async def load_costs_from_config(self) -> dict[ActionType, float]:
        """
        Load action costs from Neo4j HeartbeatConfig nodes.

        Returns:
            Dictionary of action costs
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (c:HeartbeatConfig)
                WHERE c.key STARTS WITH 'cost_'
                RETURN c.key as key, c.value as value
                """
            )
            records = await result.data()

        for r in records:
            key = r["key"].replace("cost_", "")
            try:
                action_type = ActionType(key)
                self._action_costs[action_type] = r["value"]
            except ValueError:
                logger.warning(f"Unknown action type in config: {key}")

        logger.info(f"Loaded {len(records)} action costs from config")
        return self._action_costs.copy()

    # =========================================================================
    # Pause/Resume
    # =========================================================================

    async def pause(self, reason: str) -> EnergyState:
        """
        Pause the heartbeat system.

        Args:
            reason: Reason for pausing

        Returns:
            Updated EnergyState
        """
        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                SET s.paused = true,
                    s.pause_reason = $reason,
                    s.updated_at = datetime()
                """,
                reason=reason,
            )

        logger.warning(f"Heartbeat paused: {reason}")
        return await self.get_state()

    async def resume(self) -> EnergyState:
        """
        Resume the heartbeat system.

        Returns:
            Updated EnergyState
        """
        driver = self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (s:HeartbeatState {singleton_id: 'main'})
                SET s.paused = false,
                    s.pause_reason = null,
                    s.updated_at = datetime()
                """
            )

        logger.info("Heartbeat resumed")
        return await self.get_state()

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_config(self) -> EnergyConfig:
        """Get current energy configuration."""
        return self._config

    def get_all_costs(self) -> dict[str, float]:
        """Get all action costs as a dictionary."""
        return {a.value: c for a, c in self._action_costs.items()}

    def estimate_turn_cost(self, actions: list[ActionType]) -> float:
        """
        Estimate total cost for a list of actions.

        Args:
            actions: List of action types

        Returns:
            Total energy cost
        """
        return sum(self.get_action_cost(a) for a in actions)


# =============================================================================
# Service Factory
# =============================================================================

_energy_service_instance: Optional[EnergyService] = None


def get_energy_service() -> EnergyService:
    """Get or create the EnergyService singleton."""
    global _energy_service_instance
    if _energy_service_instance is None:
        _energy_service_instance = EnergyService()
    return _energy_service_instance
