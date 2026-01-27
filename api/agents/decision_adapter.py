"""
Decision Adapter for Smolagents Integration

Bridges HeartbeatAgent/ConsciousnessManager to HeartbeatDecision format.
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from api.services.heartbeat_service import HeartbeatContext

from api.models.action import ActionRequest, ActionPlan, HeartbeatDecision
from api.services.energy_service import ActionType

logger = logging.getLogger(__name__)


@dataclass
class AgentDecisionConfig:
    """Configuration for agent-based decision making."""

    use_multi_agent: bool = False
    model_id: str = ""
    timeout_seconds: float = 30.0


class AgentDecisionAdapter:
    """
    Adapts smolagents output to HeartbeatDecision format.

    Supports both single-agent (HeartbeatAgent) and multi-agent
    (ConsciousnessManager) configurations.
    """

    def __init__(self, config: AgentDecisionConfig):
        self.config = config
        self._agent = None
        self._manager = None

    def _get_model_id(self) -> str:
        """Get the model ID from config or environment."""
        if self.config.model_id:
            return self.config.model_id
        return os.getenv("SMOLAGENTS_MODEL", "anthropic/claude-sonnet-4-20250514")

    def _init_single_agent(self):
        """Initialize single HeartbeatAgent."""
        if self._agent is None:
            from api.agents.heartbeat_agent import HeartbeatAgent
            self._agent = HeartbeatAgent(model_id=self._get_model_id())
        return self._agent

    def _init_multi_agent(self):
        """Initialize ConsciousnessManager with sub-agents."""
        if self._manager is None:
            from api.agents.consciousness_manager import ConsciousnessManager
            self._manager = ConsciousnessManager(model_id=self._get_model_id())
        return self._manager

    def _context_to_dict(self, context: "HeartbeatContext", energy_config: Dict) -> Dict[str, Any]:
        """Convert HeartbeatContext to agent-friendly dictionary."""
        return {
            "heartbeat_number": context.heartbeat_number,
            "current_energy": context.current_energy,
            "max_energy": energy_config.get("max_energy", 20),
            "base_regeneration": energy_config.get("base_regeneration", 2),
            "user_present": context.user_present,
            "time_since_user": str(context.time_since_user) if context.time_since_user else "unknown",
            "active_goals": [
                {"id": str(g.goal_id), "description": g.description, "priority": g.priority}
                for g in context.active_goals
            ],
            "recent_memories": [
                {"id": str(m.memory_id), "content": m.content[:200], "importance": m.importance}
                for m in context.recent_memories[:10]
            ],
            "pending_actions": [
                {"type": a.action_type, "payload": a.payload}
                for a in context.pending_actions
            ],
        }

    def _parse_action_type(self, type_str: str) -> ActionType:
        """Parse string to ActionType enum, with fallback."""
        type_str = type_str.upper().strip()
        try:
            return ActionType(type_str)
        except ValueError:
            # Map common variations
            mappings = {
                "REFLECT": ActionType.REFLECT,
                "RECALL": ActionType.RECALL,
                "REVISE_MODEL": ActionType.REVISE_MODEL,
                "QUERY": ActionType.RECALL,
                "THINK": ActionType.REFLECT,
            }
            return mappings.get(type_str, ActionType.REFLECT)

    def _parse_actions_from_output(self, output: str) -> List[ActionRequest]:
        """
        Parse agent output to extract ActionRequests.

        Looks for action patterns like:
        - ACTION: type=reflect, params={...}
        - [ACTION] RECALL: query="..."
        - Structured JSON blocks
        """
        actions = []

        # Try to find JSON action blocks
        json_pattern = r'\{[^{}]*"action_type"[^{}]*\}'
        json_matches = re.findall(json_pattern, output, re.DOTALL)

        for match in json_matches:
            try:
                data = json.loads(match)
                action_type = self._parse_action_type(data.get("action_type", "REFLECT"))
                actions.append(ActionRequest(
                    action_type=action_type,
                    params=data.get("params", data.get("payload", {})),
                    priority=data.get("priority", 5),
                    reason=data.get("reason", "Agent-generated action"),
                ))
            except (json.JSONDecodeError, ValueError):
                continue

        # If no JSON actions found, create a default REFLECT action
        if not actions:
            actions.append(ActionRequest(
                action_type=ActionType.REFLECT,
                params={"summary": output[:500] if output else "Agent completed without explicit actions"},
                priority=5,
                reason="Default agent reflection",
            ))

        return actions

    def _create_decision(
        self,
        output: str,
        actions: List[ActionRequest],
        context: "HeartbeatContext",
    ) -> HeartbeatDecision:
        """Create HeartbeatDecision from parsed output."""
        action_plan = ActionPlan(
            actions=actions,
            reasoning=output[:1000] if output else "Agent decision",
        )

        return HeartbeatDecision(
            action_plan=action_plan,
            reasoning=output[:1000] if output else "Agent decision",
            confidence=0.8,  # Default confidence for agent decisions
        )

    async def make_decision(
        self,
        context: "HeartbeatContext",
        energy_config: Dict,
    ) -> HeartbeatDecision:
        """
        Make a decision using smolagents.

        Args:
            context: The HeartbeatContext with current state
            energy_config: Energy configuration dict

        Returns:
            HeartbeatDecision with selected actions
        """
        context_dict = self._context_to_dict(context, energy_config)

        try:
            if self.config.use_multi_agent:
                manager = self._init_multi_agent()
                output = await asyncio.wait_for(
                    manager.run_ooda_cycle(context_dict),
                    timeout=self.config.timeout_seconds,
                )
            else:
                agent = self._init_single_agent()
                output = await asyncio.wait_for(
                    agent.decide(context_dict),
                    timeout=self.config.timeout_seconds,
                )

            actions = self._parse_actions_from_output(output)
            return self._create_decision(output, actions, context)

        except asyncio.TimeoutError:
            logger.warning(f"Agent decision timed out after {self.config.timeout_seconds}s")
            raise
        except Exception as e:
            logger.error(f"Agent decision failed: {e}")
            raise


# Singleton pattern for adapter reuse
_adapter_instance: Optional[AgentDecisionAdapter] = None


def get_agent_decision_adapter(config: Optional[AgentDecisionConfig] = None) -> AgentDecisionAdapter:
    """Get or create the agent decision adapter."""
    global _adapter_instance

    if config is not None:
        _adapter_instance = AgentDecisionAdapter(config)
    elif _adapter_instance is None:
        _adapter_instance = AgentDecisionAdapter(AgentDecisionConfig())

    return _adapter_instance
