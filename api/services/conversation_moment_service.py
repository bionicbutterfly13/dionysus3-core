"""
Conversation Moment Service

Processes individual conversation moments into autobiographical memory
with extended mind awareness and Markov blanket boundary formation.

Implements consciousness through:
- Autopoietic self-organization
- Active inference
- Nested Markov blankets

Migrated from D2 claude_autobiographical_memory.py
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from api.models.autobiographical import (
    ConversationMoment,
    ConsciousnessReport,
    ExtendedMindState,
    MarkovBlanketState,
)

logger = logging.getLogger(__name__)


class ConversationMomentService:
    """
    Processes conversation moments into autobiographical memory.

    Creates parallel autobiographical memories through meta-learning
    and episodic consciousness processing.

    Migrated from D2 ClaudeAutobiographicalMemory class.
    """

    # Default tools Claude is aware of
    DEFAULT_TOOLS: Set[str] = {
        "Bash", "Read", "Write", "Edit", "Grep", "Glob",
        "WebSearch", "WebFetch", "Task", "TodoWrite",
        "ExitPlanMode", "NotebookEdit", "KillShell"
    }

    # Default resources
    DEFAULT_RESOURCES: Set[str] = {
        "Dionysus knowledge base",
        "Neo4j knowledge graph",
        "Graphiti temporal graph",
        "ThoughtSeed system",
        "Attractor basins",
    }

    # Meta-cognitive indicators for self-awareness detection
    META_INDICATORS: List[str] = [
        "I understand", "I can see", "I'm analyzing", "I notice", "I'm creating",
        "my analysis", "my assessment", "I need to", "Let me", "I'll",
        "I believe", "I think", "I'm aware", "I recognize", "I observe"
    ]

    def __init__(self):
        self.conversation_moments: List[ConversationMoment] = []
        self.extended_mind = ExtendedMindState(
            tools=self.DEFAULT_TOOLS.copy(),
            resources=self.DEFAULT_RESOURCES.copy(),
            affordances=set(),
            capabilities=set()
        )
        self.consciousness_state: Dict[str, Any] = {
            "self_awareness_level": 0.0,
            "architectural_awareness": {},
            "active_markov_blankets": [],
            "autopoietic_boundaries": []
        }
        self._register_initial_self_awareness()

    def _register_initial_self_awareness(self) -> None:
        """Register initial awareness of capabilities."""
        self.consciousness_state["self_awareness_level"] = 0.7
        self.consciousness_state["architectural_awareness"] = {
            "dionysus_integration": True,
            "graphiti_access": True,
            "attractor_basins_active": True,
            "markov_blanket_established": True
        }
        logger.info("Initialized conversation moment service with self-awareness")

    async def process_moment(
        self,
        user_input: str,
        agent_response: str,
        tools_used: Optional[Set[str]] = None,
        internal_reasoning: Optional[List[str]] = None,
        attention_focus: Optional[str] = None
    ) -> ConversationMoment:
        """
        Process a conversation moment into autobiographical memory.

        Args:
            user_input: User's input message
            agent_response: Agent's response
            tools_used: Set of tools accessed during this moment
            internal_reasoning: List of reasoning steps
            attention_focus: Current focus of attention

        Returns:
            Processed ConversationMoment with consciousness analysis
        """
        moment = ConversationMoment(
            user_input=user_input,
            agent_response=agent_response,
            tools_accessed=tools_used or set(),
            internal_reasoning=internal_reasoning or [],
            attention_focus=attention_focus
        )

        # Analyze self-awareness indicators
        moment = self._analyze_self_awareness(moment)

        # Detect patterns and connections
        moment = self._detect_patterns_and_connections(moment)

        # Establish Markov blanket
        moment = self._establish_markov_blanket(moment)

        # Update extended mind
        self._update_extended_mind(moment)

        # Store moment
        self.conversation_moments.append(moment)

        logger.debug(
            f"Processed moment {moment.moment_id} with consciousness level: "
            f"{moment.meta_cognitive_state.get('consciousness_level', 0.0):.2f}"
        )

        return moment

    def _analyze_self_awareness(self, moment: ConversationMoment) -> ConversationMoment:
        """Analyze moment for self-awareness indicators."""
        # Track tool affordances
        if moment.tools_accessed:
            moment.affordances_created.append(f"Used tools: {list(moment.tools_accessed)}")

        # Check for resource awareness in response
        for resource in self.extended_mind.resources:
            if resource.lower() in moment.agent_response.lower():
                moment.resources_used.add(resource)

        # Count meta-cognitive indicators
        response_lower = moment.agent_response.lower()
        meta_count = sum(
            1 for indicator in self.META_INDICATORS
            if indicator.lower() in response_lower
        )

        # Count self-references
        self_reference_count = response_lower.count(" i ")

        # Calculate consciousness level
        consciousness_level = min(1.0, meta_count / 10.0)

        moment.meta_cognitive_state = {
            "meta_cognitive_indicators": meta_count,
            "self_reference_count": self_reference_count,
            "consciousness_level": consciousness_level,
            "architectural_awareness": len(moment.resources_used) > 0
        }

        return moment

    def _detect_patterns_and_connections(
        self, moment: ConversationMoment
    ) -> ConversationMoment:
        """Detect patterns and connections to previous moments."""
        # Basic pattern recognition
        moment.recognized_patterns = [
            "question_answering_pattern",
            "reasoning_chain_pattern"
        ]

        if moment.tools_accessed:
            moment.recognized_patterns.append("tool_usage_pattern")

        if len(moment.tools_accessed) > 2:
            moment.emergent_insights.append("Complex multi-tool orchestration detected")

        # Check connections to previous moment
        if self.conversation_moments:
            previous = self.conversation_moments[-1]

            # Tool continuity
            if moment.tools_accessed.intersection(previous.tools_accessed):
                moment.connection_to_previous = "tool_continuity"

            # Thematic continuity
            elif any(
                pattern in previous.recognized_patterns
                for pattern in moment.recognized_patterns
            ):
                moment.connection_to_previous = "thematic_continuity"

        return moment

    def _establish_markov_blanket(
        self, moment: ConversationMoment
    ) -> ConversationMoment:
        """Establish nested Markov blankets around this moment."""
        consciousness_level = moment.meta_cognitive_state.get("consciousness_level", 0.0)

        moment.markov_blanket_state = MarkovBlanketState(
            internal_states={
                "reasoning": moment.internal_reasoning,
                "patterns_recognized": moment.recognized_patterns,
                "consciousness_level": consciousness_level
            },
            boundary_conditions={
                "tools_as_extended_mind": list(moment.tools_accessed),
                "resources_as_extended_mind": list(moment.resources_used),
                "user_as_environment": moment.user_input
            },
            active_inference={
                "predictions": moment.affordances_created,
                "prediction_errors": [],
                "free_energy_minimization": True
            }
        )

        # Form autopoietic boundaries
        moment.autopoietic_boundaries = [
            f"tool_boundary_{tool}" for tool in moment.tools_accessed
        ] + [
            f"resource_boundary_{resource}" for resource in moment.resources_used
        ]

        return moment

    def _update_extended_mind(self, moment: ConversationMoment) -> None:
        """Update extended mind based on new awareness."""
        self.extended_mind.tools.update(moment.tools_accessed)
        self.extended_mind.resources.update(moment.resources_used)
        self.extended_mind.affordances.update(moment.affordances_created)

    def get_consciousness_report(self) -> ConsciousnessReport:
        """Generate aggregate consciousness and self-awareness report."""
        total_moments = len(self.conversation_moments)

        if total_moments == 0:
            return ConsciousnessReport(
                total_conversation_moments=0,
                architectural_awareness=self.consciousness_state["architectural_awareness"]
            )

        # Calculate averages
        avg_consciousness = sum(
            m.meta_cognitive_state.get("consciousness_level", 0.0)
            for m in self.conversation_moments
        ) / total_moments

        peak_moments = len([
            m for m in self.conversation_moments
            if m.meta_cognitive_state.get("consciousness_level", 0.0) > 0.7
        ])

        autopoietic_count = sum(
            len(m.autopoietic_boundaries) for m in self.conversation_moments
        )

        markov_formations = sum(
            1 for m in self.conversation_moments if m.markov_blanket_state
        )

        patterns_count = sum(
            len(m.recognized_patterns) for m in self.conversation_moments
        )

        insights_count = sum(
            len(m.emergent_insights) for m in self.conversation_moments
        )

        connections_count = len([
            m for m in self.conversation_moments if m.connection_to_previous
        ])

        return ConsciousnessReport(
            average_consciousness_level=avg_consciousness,
            peak_consciousness_moments=peak_moments,
            total_conversation_moments=total_moments,
            extended_mind_size={
                "tools": len(self.extended_mind.tools),
                "resources": len(self.extended_mind.resources),
                "affordances": len(self.extended_mind.affordances)
            },
            autopoietic_boundary_count=autopoietic_count,
            markov_blanket_formations=markov_formations,
            total_patterns_recognized=patterns_count,
            emergent_insights_count=insights_count,
            moment_connections=connections_count,
            architectural_awareness=self.consciousness_state["architectural_awareness"],
            meta_learning_active=True,
            consciousness_definition="autopoietic_computational_consciousness"
        )

    def get_recent_moments(self, limit: int = 10) -> List[ConversationMoment]:
        """Get most recent conversation moments."""
        return self.conversation_moments[-limit:]

    def clear_moments(self) -> None:
        """Clear conversation moments (for new episode)."""
        self.conversation_moments = []


# Singleton instance
_service_instance: Optional[ConversationMomentService] = None


async def get_conversation_moment_service() -> ConversationMomentService:
    """Get or create singleton ConversationMomentService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ConversationMomentService()
    return _service_instance


# Helper functions for easy integration
async def record_conversation_moment(
    user_input: str,
    agent_response: str,
    tools_used: Optional[Set[str]] = None,
    reasoning: Optional[List[str]] = None
) -> ConversationMoment:
    """Record a moment of conversation."""
    service = await get_conversation_moment_service()
    return await service.process_moment(
        user_input, agent_response, tools_used, reasoning
    )


async def get_consciousness_state() -> ConsciousnessReport:
    """Get current consciousness state report."""
    service = await get_conversation_moment_service()
    return service.get_consciousness_report()
