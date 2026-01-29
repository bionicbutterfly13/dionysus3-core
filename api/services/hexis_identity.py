"""
Hexis Identity Service
Feature: 101-hexis-core-migration

Aggregates identity context (worldview, goals, directives) for prompt injection.
Pulls from HexisService subconscious state and formats for LLM consumption.

Inlets:
    - HexisService.get_subconscious_state()
    - GoalService.list_goals() (optional fallback)
Outlets:
    - Formatted prompt context string
    - IdentityContext dataclass
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from api.services.hexis_service import get_hexis_service
from api.models.hexis_ontology import (
    Goal,
    GoalPriority,
    Worldview,
    SubconsciousState,
    MemoryBlock,
)

logger = logging.getLogger(__name__)


@dataclass
class IdentityContext:
    """Aggregated identity context for an agent."""
    goals: List[Goal] = field(default_factory=list)
    worldview: List[Worldview] = field(default_factory=list)
    directives: str = ""
    guidance: str = ""
    project_context: str = ""
    agent_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HexisIdentityService:
    """
    Aggregates and formats identity context for prompt injection.

    Pulls worldview, goals, and memory blocks from HexisService's
    subconscious state and formats them for LLM consumption.
    """

    def __init__(self):
        pass

    async def get_active_goals(self, agent_id: str) -> List[Goal]:
        """
        Get currently active goals for the agent.

        Args:
            agent_id: Agent/session identifier

        Returns:
            List of active Goal objects
        """
        try:
            hexis = get_hexis_service()
            state = await hexis.get_subconscious_state(agent_id)
            return state.active_goals or []
        except Exception as e:
            logger.error(f"get_active_goals() failed for {agent_id}: {e}")
            return []

    async def get_worldview(self, agent_id: str) -> List[Worldview]:
        """
        Get worldview beliefs for the agent.

        Args:
            agent_id: Agent/session identifier

        Returns:
            List of Worldview objects
        """
        try:
            hexis = get_hexis_service()
            state = await hexis.get_subconscious_state(agent_id)
            return state.worldview_snapshot or []
        except Exception as e:
            logger.error(f"get_worldview() failed for {agent_id}: {e}")
            return []

    async def get_identity_context(self, agent_id: str) -> IdentityContext:
        """
        Get full aggregated identity context.

        Args:
            agent_id: Agent/session identifier

        Returns:
            IdentityContext with goals, worldview, and directives
        """
        try:
            hexis = get_hexis_service()
            state = await hexis.get_subconscious_state(agent_id)

            # Extract blocks
            blocks = state.blocks or {}
            directives = self._get_block_value(blocks, "core_directives")
            guidance = self._get_block_value(blocks, "guidance")
            project_context = self._get_block_value(blocks, "project_context")

            return IdentityContext(
                goals=state.active_goals or [],
                worldview=state.worldview_snapshot or [],
                directives=directives,
                guidance=guidance,
                project_context=project_context,
                agent_id=agent_id
            )
        except Exception as e:
            logger.error(f"get_identity_context() failed for {agent_id}: {e}")
            return IdentityContext(agent_id=agent_id)

    async def get_prompt_context(self, agent_id: str) -> str:
        """
        Get formatted identity context string for LLM prompt injection.

        Args:
            agent_id: Agent/session identifier

        Returns:
            Formatted string suitable for system prompt injection
        """
        try:
            context = await self.get_identity_context(agent_id)
            return self._format_for_prompt(context)
        except Exception as e:
            logger.error(f"get_prompt_context() failed for {agent_id}: {e}")
            return ""

    def _get_block_value(self, blocks: Dict[str, Any], key: str) -> str:
        """Extract value from memory block dict."""
        block = blocks.get(key)
        if block is None:
            return ""
        if isinstance(block, MemoryBlock):
            return block.value or ""
        if isinstance(block, dict):
            return block.get("value", "")
        if hasattr(block, "value"):
            return getattr(block, "value", "")
        return str(block) if block else ""

    def _format_for_prompt(self, context: IdentityContext) -> str:
        """Format IdentityContext as LLM-ready string."""
        sections = []

        # Core Directives
        if context.directives and context.directives != "(Empty)":
            sections.append(f"## Core Directives\n{context.directives}")

        # Active Goals
        if context.goals:
            goal_lines = []
            for g in context.goals:
                priority = g.priority.value if hasattr(g.priority, "value") else str(g.priority)
                goal_lines.append(f"- [{priority.upper()}] {g.title}")
            if goal_lines:
                sections.append(f"## Active Goals\n" + "\n".join(goal_lines))

        # Worldview
        if context.worldview:
            belief_lines = [f"- {w.statement}" for w in context.worldview]
            if belief_lines:
                sections.append(f"## Worldview\n" + "\n".join(belief_lines))

        # Guidance
        if context.guidance and context.guidance != "(Empty)":
            sections.append(f"## Guidance\n{context.guidance}")

        # Project Context
        if context.project_context and context.project_context != "(Empty)":
            sections.append(f"## Project Context\n{context.project_context}")

        if not sections:
            return ""

        return "\n\n".join(sections)


# Singleton
_hexis_identity_service: Optional[HexisIdentityService] = None


def get_hexis_identity_service() -> HexisIdentityService:
    """Get singleton HexisIdentityService instance."""
    global _hexis_identity_service
    if _hexis_identity_service is None:
        _hexis_identity_service = HexisIdentityService()
    return _hexis_identity_service
