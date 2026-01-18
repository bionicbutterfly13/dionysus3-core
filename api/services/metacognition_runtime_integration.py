"""
Metacognition Runtime Integration

Feature: 040-metacognitive-particles + 047-multi-tier-memory

Integrates procedural metacognition patterns with agent runtime execution.
Provides fast access to patterns during agent decision-making and control loops.

This service bridges:
1. HeartbeatAgent (OODA cycle)
2. ConsciousnessManager (Perception/Reasoning/Metacognition)
3. ProceduralMetacognition monitoring/control
4. Pattern storage (HOT tier)

AUTHOR: Mani Saint-Victor, MD
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from api.services.metacognition_patterns_storage import (
    get_metacognition_patterns_storage,
    ProceduralMetacognitionPatternsStorage,
    MonitoringPattern,
    ControlPattern,
    ThoughtseedCompetitionPattern,
    LoopPreventionPattern,
)
from api.services.procedural_metacognition import ProceduralMetacognition, CognitiveAssessment

logger = logging.getLogger("dionysus.metacognition_runtime_integration")


class MetacognitionRuntimeMonitor:
    """
    Monitoring runtime that checks surprise, confidence, basin stability
    at intervals specified by monitoring patterns.

    O(1) lookups via HOT patterns storage.
    """

    def __init__(self):
        self._patterns_storage = get_metacognition_patterns_storage()
        self._procedural_mc = ProceduralMetacognition()
        self._monitoring_state: Dict[str, Dict[str, Any]] = {}

    async def assess_cognitive_state(
        self,
        agent_id: str,
        metrics: Dict[str, float]
    ) -> Optional[CognitiveAssessment]:
        """
        Assess cognitive state using procedural metacognition.

        Args:
            agent_id: Agent being monitored
            metrics: Current cognitive metrics (surprise, confidence, basin_stability)

        Returns:
            CognitiveAssessment if issues detected, None otherwise
        """
        # Get monitoring pattern (HOT tier - O(1))
        monitor_pattern = self._patterns_storage.get_default_monitoring_pattern()
        if not monitor_pattern:
            logger.warning("No monitoring pattern available")
            return None

        # Get or initialize monitoring state for this agent
        if agent_id not in self._monitoring_state:
            self._monitoring_state[agent_id] = {
                "step_count": 0,
                "last_assessment": None,
            }

        state = self._monitoring_state[agent_id]
        state["step_count"] += 1

        # Check if it's time to assess (based on pattern interval)
        if state["step_count"] % monitor_pattern.check_interval != 0:
            return None

        # Perform assessment using procedural metacognition
        assessment = await self._procedural_mc.monitor(agent_id)

        # Update metrics from current state
        assessment.progress = metrics.get("progress", 0.0)
        assessment.confidence = metrics.get("confidence", 0.0)
        assessment.prediction_error = metrics.get("surprise", 0.0)

        state["last_assessment"] = assessment

        logger.debug(
            f"Assessment for {agent_id} (step {state['step_count']}): "
            f"issues={len(assessment.issues)}, recommendations={len(assessment.recommendations)}"
        )

        return assessment

    def reset_monitoring_state(self, agent_id: str):
        """Reset monitoring state for an agent."""
        if agent_id in self._monitoring_state:
            del self._monitoring_state[agent_id]


class MetacognitionRuntimeController:
    """
    Control runtime that generates control actions based on cognitive state.

    Maps surprise/confidence/free_energy to control actions.
    """

    def __init__(self):
        self._patterns_storage = get_metacognition_patterns_storage()
        self._procedural_mc = ProceduralMetacognition()

    async def generate_control_actions(
        self,
        agent_id: str,
        surprise: float,
        confidence: float,
        free_energy: float,
    ) -> List[Dict[str, Any]]:
        """
        Generate control actions based on cognitive state.

        Args:
            agent_id: Agent being controlled
            surprise: Current surprise metric
            confidence: Current confidence metric
            free_energy: Current free energy metric

        Returns:
            List of control action recommendations
        """
        # Get control pattern (HOT tier - O(1))
        control_pattern = self._patterns_storage.get_default_control_pattern()
        if not control_pattern:
            logger.warning("No control pattern available")
            return []

        control_actions = []

        # Get action for current state
        action = control_pattern.get_action_for_state(surprise, confidence, free_energy)
        if action:
            control_actions.append({
                "agent_id": agent_id,
                "action": action,
                "reason": self._get_reason(surprise, confidence, free_energy, control_pattern),
                "metrics": {
                    "surprise": surprise,
                    "confidence": confidence,
                    "free_energy": free_energy,
                },
                "thresholds": {
                    "surprise_threshold": control_pattern.surprise_threshold,
                    "confidence_threshold": control_pattern.confidence_threshold,
                    "free_energy_threshold": control_pattern.free_energy_threshold,
                },
            })

            logger.info(
                f"Control action for {agent_id}: {action} "
                f"(surprise={surprise:.2f}, confidence={confidence:.2f}, fe={free_energy:.2f})"
            )

        return control_actions

    def _get_reason(
        self,
        surprise: float,
        confidence: float,
        free_energy: float,
        pattern: ControlPattern,
    ) -> str:
        """Generate explanation for control action."""
        reasons = []

        if surprise > pattern.surprise_threshold:
            reasons.append(f"surprise {surprise:.2f} > {pattern.surprise_threshold:.2f}")
        if confidence < pattern.confidence_threshold:
            reasons.append(f"confidence {confidence:.2f} < {pattern.confidence_threshold:.2f}")
        if free_energy > pattern.free_energy_threshold:
            reasons.append(f"free_energy {free_energy:.2f} > {pattern.free_energy_threshold:.2f}")

        return " AND ".join(reasons) if reasons else "Threshold combination triggered"


class ThoughtseedCompetitionRuntime:
    """
    Manages thoughtseed competition using Active Inference Pattern.

    Determines winner thoughtseed based on minimum free energy.
    """

    def __init__(self):
        self._patterns_storage = get_metacognition_patterns_storage()

    def rank_thoughtseeds(
        self,
        thoughtseeds: List[Dict[str, Any]],
        selection_metrics: str = "free_energy"
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Rank thoughtseeds using competition pattern.

        Args:
            thoughtseeds: List of candidate thoughtseeds
            selection_metrics: Metric to rank by (free_energy, surprise, etc.)

        Returns:
            Tuple of (winner_thoughtseed, ranked_list)
        """
        pattern = self._patterns_storage.get_default_thoughtseed_pattern()
        if not pattern:
            logger.warning("No thoughtseed competition pattern available")
            return None, thoughtseeds

        # Sort by selection metric
        if selection_metrics == "free_energy":
            ranked = sorted(
                thoughtseeds,
                key=lambda ts: ts.get("free_energy", float("inf"))
            )
        else:
            ranked = thoughtseeds

        winner = ranked[0] if ranked else None

        logger.debug(
            f"Thoughtseed competition: {len(thoughtseeds)} candidates, "
            f"winner metric={winner.get(selection_metrics, 'N/A') if winner else 'N/A'}"
        )

        return winner, ranked

    def get_competition_config(self) -> Dict[str, Any]:
        """Get competition configuration from pattern."""
        pattern = self._patterns_storage.get_default_thoughtseed_pattern()
        if not pattern:
            return {}

        return {
            "algorithm": pattern.algorithm,
            "max_iterations": pattern.max_iterations,
            "winner_criterion": pattern.winner_criterion,
            "exploration_constant": pattern.exploration_constant,
            "simulation_count": pattern.simulation_count,
            "max_depth": pattern.max_depth,
        }


class LoopPreventionRuntime:
    """
    Loop prevention runtime using pattern-based depth/diminishing returns checks.

    Prevents infinite recursion in meta-reasoning.
    """

    def __init__(self):
        self._patterns_storage = get_metacognition_patterns_storage()
        self._recursion_stacks: Dict[str, LoopPreventionPattern] = {}

    def create_recursion_context(self, context_id: str) -> LoopPreventionPattern:
        """Create a new recursion context."""
        pattern = self._patterns_storage.get_default_loop_prevention_pattern()
        if not pattern:
            logger.error("No loop prevention pattern available")
            # Create default if missing
            pattern = LoopPreventionPattern()

        # Create a copy for this context
        new_pattern = LoopPreventionPattern(
            max_recursion_depth=pattern.max_recursion_depth,
            diminishing_returns_threshold=pattern.diminishing_returns_threshold,
            improvement_window=pattern.improvement_window,
            force_execution_after_steps=pattern.force_execution_after_steps,
        )

        self._recursion_stacks[context_id] = new_pattern
        logger.debug(f"Created recursion context: {context_id}")

        return new_pattern

    def enter_recursion(self, context_id: str) -> bool:
        """
        Try to enter a deeper recursion level.

        Returns:
            True if recursion should continue, False otherwise
        """
        if context_id not in self._recursion_stacks:
            self.create_recursion_context(context_id)

        pattern = self._recursion_stacks[context_id]
        pattern.recursion_depth += 1

        can_continue = pattern.should_continue_recursion()

        logger.debug(
            f"Recursion check for {context_id}: "
            f"depth={pattern.recursion_depth}, continue={can_continue}"
        )

        return can_continue

    def exit_recursion(self, context_id: str, improvement: float = 0.0):
        """
        Exit a recursion level and record improvement.

        Args:
            context_id: Recursion context
            improvement: Improvement metric for this level
        """
        if context_id not in self._recursion_stacks:
            return

        pattern = self._recursion_stacks[context_id]
        pattern.record_improvement(improvement)
        pattern.increment_step()
        pattern.recursion_depth = max(0, pattern.recursion_depth - 1)

    def reset_recursion_context(self, context_id: str):
        """Reset a recursion context."""
        if context_id in self._recursion_stacks:
            self._recursion_stacks[context_id].reset_for_new_context()

    def cleanup_context(self, context_id: str):
        """Clean up a recursion context."""
        if context_id in self._recursion_stacks:
            del self._recursion_stacks[context_id]

    def get_context_status(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a recursion context."""
        pattern = self._recursion_stacks.get(context_id)
        if not pattern:
            return None

        return {
            "recursion_depth": pattern.recursion_depth,
            "step_counter": pattern.step_counter,
            "force_execution_after_steps": pattern.force_execution_after_steps,
            "max_recursion_depth": pattern.max_recursion_depth,
            "last_improvements": pattern.last_improvements[-5:],  # Last 5
        }


class MetacognitionRuntimeIntegration:
    """
    Main integration service for metacognition runtime.

    Coordinates monitoring, control, thoughtseed competition, and loop prevention.
    """

    def __init__(self):
        self._patterns_storage = get_metacognition_patterns_storage()
        self._monitor = MetacognitionRuntimeMonitor()
        self._controller = MetacognitionRuntimeController()
        self._thoughtseed_comp = ThoughtseedCompetitionRuntime()
        self._loop_prevention = LoopPreventionRuntime()

    async def execute_metacognition_cycle(
        self,
        agent_id: str,
        metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Execute full metacognition cycle: monitoring -> assessment -> control.

        Args:
            agent_id: Agent executing
            metrics: Current metrics (surprise, confidence, basin_stability, progress)

        Returns:
            Result with assessment and control actions
        """
        result = {
            "agent_id": agent_id,
            "assessment": None,
            "control_actions": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Phase 1: Monitor (check every N steps)
        assessment = await self._monitor.assess_cognitive_state(agent_id, metrics)
        if assessment:
            result["assessment"] = assessment.to_dict()

        # Phase 2: Control (if issues detected)
        if assessment and len(assessment.issues) > 0:
            control_actions = await self._controller.generate_control_actions(
                agent_id,
                surprise=metrics.get("surprise", 0.0),
                confidence=metrics.get("confidence", 0.5),
                free_energy=metrics.get("free_energy", 0.0),
            )
            result["control_actions"] = control_actions

        return result

    def get_patterns_summary(self) -> Dict[str, Any]:
        """Get summary of all loaded patterns."""
        storage = self._patterns_storage
        patterns = storage.list_all_patterns()
        stats = storage.get_stats()

        return {
            "patterns": patterns,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def cleanup_storage(self) -> Dict[str, Any]:
        """Clean up expired patterns from storage."""
        expired = self._patterns_storage.cleanup_expired_patterns()
        return {
            "expired_patterns": expired,
            "remaining_stats": self._patterns_storage.get_stats(),
        }


# Singleton instance
_runtime_integration_instance: Optional[MetacognitionRuntimeIntegration] = None


def get_metacognition_runtime_integration() -> MetacognitionRuntimeIntegration:
    """Get or create the singleton runtime integration instance."""
    global _runtime_integration_instance
    if _runtime_integration_instance is None:
        _runtime_integration_instance = MetacognitionRuntimeIntegration()
    return _runtime_integration_instance
