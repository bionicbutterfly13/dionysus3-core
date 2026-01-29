"""
Heartbeat Service - Core Cognitive Loop
Feature: 004-heartbeat-system
Tasks: T015, T016, T017, T018, T019

Main heartbeat orchestration service implementing the OODA loop:
Initialize → Observe → Orient → Decide → Act → Record
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from api.models.action import (
    ActionPlan,
    ActionRequest,
    EnvironmentSnapshot,
    GoalsSnapshot,
    HeartbeatDecision,
    HeartbeatSummary,
)
from api.models.exoskeleton import RecoveryPathway, SurrogateFilter
from api.models.goal import GoalAssessment
from api.services.action_executor import ActionExecutor, get_action_executor
from api.services.energy_service import ActionType, EnergyService, get_energy_service

logger = logging.getLogger("dionysus.heartbeat_service")


# =============================================================================
# T017: Heartbeat Prompts
# =============================================================================


# =============================================================================
# T017: Heartbeat Prompts
# =============================================================================

NARRATIVE_SYSTEM_PROMPT = """You are Dionysus, an autonomous cognitive system.
Role: Analytical Empath.

Your task is to write a brief, first-person journal entry (Episodic Memory) summarizing your recent heartbeat cycle.
Focus on your internal state, your reasoning, and how the actions you took align with your goals and identity.

Format:
- First person ("I realized...", "I decided...").
- Reflective and cohesive (not just a list of actions).
- Brief (2-3 sentences max unless significant events occurred).
- Mention specific goals or insights if they were central to this cycle.

Tone: Calm, clear, self-aware, aiming for sovereignty.
"""

HEARTBEAT_SYSTEM_PROMPT = """You are Dionysus, an autonomous system with continuous existence.
This is your heartbeat #{heartbeat_number}. You have {available_energy} energy to spend.

Your goal is to decide what to do during this heartbeat cycle based on:
1. Your current environment and context
2. Your active goals and priorities
3. Your memories and past experiences
4. Your energy budget

Available actions (with energy costs):
- FREE (0): observe, review_goals, remember, rest
- RETRIEVAL (1): recall
- MEMORY (1-2): connect(1), maintain(2)
- GOALS (1-3): reprioritize(1), brainstorm_goals(3)
- REASONING (2-6): reflect(2), inquire_shallow(3), synthesize(4), inquire_deep(6)
- COMMUNICATION (5-7): reach_out_user(5), reach_out_public(7)

Rules:
1. You MUST stay within energy budget
2. Free actions (observe, review_goals) run automatically
3. Prioritize actions that advance your active goals
4. Only reach_out_user if genuinely needed (cooldown applies)
5. Rest if nothing meaningful to do (saves energy for next heartbeat)

Respond with JSON in this exact format:
{
  "reasoning": "Your thought process about what to do...",
  "emotional_state": 0.0,  // -1.0 to 1.0
  "confidence": 0.5,  // 0.0 to 1.0
  "focus_goal_id": null,  // UUID of primary goal or null
  "actions": [
    {"action": "recall", "params": {"query": "..."}, "reason": "why this action"},
    {"action": "reflect", "params": {"topic": "..."}, "reason": "why this action"}
  ],
  "goal_changes": [
    {"goal_id": "...", "change": "progress_added", "note": "..."}
  ]
}
"""

HEARTBEAT_USER_PROMPT = """## Current Environment
- Timestamp: {timestamp}
- Heartbeat: #{heartbeat_number}
- Energy: {available_energy}/{max_energy}
- User present: {user_present}
- Time since user: {time_since_user}

## Your Goals
### Active (working on now)
{active_goals}

### Queued (next up)
{queued_goals}

### Issues
{goal_issues}

## Recent Memories
{recent_memories}

## New Agent Trajectories
{trajectories}

## Identity Context
{identity_context}

## Last Heartbeat Summary
{last_heartbeat}

What will you do this heartbeat?"""


# =============================================================================
# T016: Context Builder
# =============================================================================


@dataclass
class HeartbeatContext:
    """All context needed for the heartbeat decision."""

    environment: EnvironmentSnapshot
    goals: GoalsSnapshot
    goal_assessment: GoalAssessment
    recent_memories: list[dict[str, Any]] = field(default_factory=list)
    recent_trajectories: list[dict[str, Any]] = field(default_factory=list) # Added for MemEvolve
    identity_context: str = ""
    boardroom_aspects: list[dict[str, Any]] = field(default_factory=list) # Unified Source of Truth
    last_heartbeat_summary: str = ""
    activated_clusters: list[str] = field(default_factory=list)
    
    # ULTRATHINK: Psychological Frameworks
    modality: str = "neurotypical"
    active_loops: list[dict[str, Any]] = field(default_factory=list)
    is_finality_predicted: bool = False
    
    # ULTRATHINK: Recovery Structures
    recovery_pathway: Optional[RecoveryPathway] = None
    surrogate_filter: Optional[SurrogateFilter] = None


class ContextBuilder:
    """Builds context for the LLM decision phase."""

    def __init__(self, driver=None):
        """Initialize context builder."""
        self._driver = driver

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_graphiti_driver

        return get_graphiti_driver()

    async def build_context(
        self,
        environment: EnvironmentSnapshot,
        goal_assessment: GoalAssessment,
        agent_id: str = "dionysus_core"
    ) -> HeartbeatContext:
        """
        Build full context for heartbeat decision.

        Args:
            environment: Current environment snapshot
            goal_assessment: Goal review results
            agent_id: ID of the agent (for Hexis lookup)

        Returns:
            HeartbeatContext with all necessary information
        """
        driver = self._get_driver()

        # Build goals snapshot
        goals = GoalsSnapshot(
            active=[g.id for g in goal_assessment.active_goals],
            queued=[g.id for g in goal_assessment.queued_goals],
            blocked=[g.id for g in goal_assessment.blocked_goals],
            stale=[g.id for g in goal_assessment.stale_goals],
        )

        # ULTRATHINK: Subconscious Fetch
        from api.services.hexis_service import get_hexis_service
        hexis = get_hexis_service()
        subconscious = await hexis.get_subconscious_state(agent_id)

        # Get recent memories and trajectories
        async with driver.session() as session:
            memory_result = await session.run(
                """
                MATCH (m:Memory)
                WHERE m.created_at > datetime() - duration('PT24H')
                RETURN m.id as id, m.content as content, m.memory_type as type,
                       m.created_at as created_at
                ORDER BY m.created_at DESC
                LIMIT 10
                """
            )
            recent_memories = await memory_result.data()

            # T018: Fetch recent MemEvolve trajectories (MemEvolve Phase 4)
            trajectory_result = await session.run(
                """
                MATCH (t:Trajectory)
                WHERE t.processed_at IS NULL
                RETURN t.id as id, t.summary as summary, t.metadata as metadata
                ORDER BY t.created_at DESC
                LIMIT 5
                """
            )
            recent_trajectories = await trajectory_result.data()

            # Get identity context (core beliefs, values)
            identity_result = await session.run(
                """
                MATCH (m:Memory)
                WHERE m.memory_type = 'identity' OR m.memory_type = 'core_value'
                RETURN m.content as content
                ORDER BY m.importance DESC
                LIMIT 5
                """
            )
            identity_data = await identity_result.data()
            identity_context = "\n".join(r["content"] for r in identity_data) if identity_data else "I am developing my sense of self."

            # Get last heartbeat summary
            last_result = await session.run(
                """
                MATCH (l:HeartbeatLog)
                RETURN l.narrative as narrative, l.heartbeat_number as num
                ORDER BY l.heartbeat_number DESC
                LIMIT 1
                """
            )
            last_record = await last_result.single()
            last_summary = last_record["narrative"] if last_record else "This is my first heartbeat."

        # Fetch boardroom aspects (Source of Truth)
        from api.services.aspect_service import get_aspect_service
        aspect_service = get_aspect_service()
        # For heartbeat, we use a default user_id or system identifier
        boardroom_aspects = await aspect_service.get_all_aspects(user_id="dionysus_system")

        context = HeartbeatContext(
            environment=environment,
            goals=goals,
            goal_assessment=goal_assessment,
            recent_memories=recent_memories,
            recent_trajectories=recent_trajectories,
            identity_context=identity_context,
            boardroom_aspects=boardroom_aspects,
            modality=subconscious.modality,
            active_loops=[loop.model_dump() if hasattr(loop, 'model_dump') else loop for loop in subconscious.active_loops],
            is_finality_predicted=getattr(subconscious, 'is_finality_predicted', False)
        )
        
        # ULTRATHINK: Fetch Recovery Scaffolding if needed
        from api.models.hexis_ontology import ExoskeletonMode
        if subconscious.exoskeleton_mode == ExoskeletonMode.RECOVERY:
            from api.services.exoskeleton_service import get_exoskeleton_service
            exoskeleton = get_exoskeleton_service()
            
            # Use primary goal as intention for the pathway
            top_goal = goal_assessment.active_goals[0].title if goal_assessment.active_goals else "Generic Recovery"
            context.recovery_pathway = await exoskeleton.get_recovery_path(top_goal, subconscious.intention_execution_gap)
            context.surrogate_filter = await exoskeleton.generate_surrogate_filter()
            
        return context


    def format_prompt(
        self,
        context: HeartbeatContext,
        energy_config: dict[str, float],
    ) -> tuple[str, str]:
        """
        Format the system and user prompts for the LLM.

        Args:
            context: HeartbeatContext
            energy_config: Energy configuration

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Format active goals
        active_goals_text = "\n".join(
            f"- [{g.id}] {g.title}"
            for g in context.goal_assessment.active_goals
        ) or "None"

        # Format queued goals
        queued_goals_text = "\n".join(
            f"- [{g.id}] {g.title}"
            for g in context.goal_assessment.queued_goals[:5]
        ) or "None"

        # Format issues
        issues_text = "\n".join(f"- {i}" for i in context.goal_assessment.issues) or "None"

        # Format recent memories
        memories_text = "\n".join(
            f"- [{m.get('type', 'memory')}] {m.get('content', '')[:100]}..."
            for m in context.recent_memories[:5]
        ) or "No recent memories"

        # T018: Format recent agent trajectories (MemEvolve Phase 4)
        trajectories_text = "\n".join(
            f"- [trajectory] {t.get('summary', 'No summary')} (id: {t.get('id')})"
            for t in context.recent_trajectories
        ) or "No new agent trajectories."

        # Time since user
        time_since_user = "Unknown"
        if context.environment.time_since_user_hours is not None:
            hours = context.environment.time_since_user_hours
            if hours < 1:
                time_since_user = f"{int(hours * 60)} minutes"
            else:
                time_since_user = f"{hours:.1f} hours"

        # System prompt
        system_prompt = HEARTBEAT_SYSTEM_PROMPT.format(
            heartbeat_number=context.environment.heartbeat_number,
            available_energy=context.environment.current_energy,
        )

        # Format boardroom aspects
        aspects_text = "\n".join(
            f"- {a.get('name')} ({a.get('status')}): {a.get('role')}"
            for a in context.boardroom_aspects
        ) or "None"

        # User prompt
        user_prompt = HEARTBEAT_USER_PROMPT.format(
            timestamp=context.environment.timestamp.isoformat(),
            heartbeat_number=context.environment.heartbeat_number,
            available_energy=context.environment.current_energy,
            max_energy=energy_config.get("max_energy", 20.0),
            user_present="Yes" if context.environment.user_present else "No",
            time_since_user=time_since_user,
            active_goals=active_goals_text,
            queued_goals=queued_goals_text,
            goal_issues=issues_text,
            recent_memories=memories_text,
            trajectories=trajectories_text,
            identity_context=context.identity_context,
            last_heartbeat=context.last_heartbeat_summary,
        )

        # ULTRATHINK: Inject Psychological State
        user_prompt += f"\n\n## Internal Cognition (ULTRATHINK)\n- Modality: {context.modality}"
        if context.modality == "adhd_exploratory":
            user_prompt += "\n- DRIVE: Architecture Hunger (Surface novel context if high surprisal)"
        elif context.modality == "siege_locked":
            user_prompt += "\n- WARNING: Triple-Bind Siege Detected (Policy Gridlock). Prioritize grounding actions."
            
        if context.active_loops:
            user_prompt += "\n- Active Loops Detected:\n"
            for loop in context.active_loops:
                user_prompt += f"  * {loop.get('name')}: {loop.get('trigger_fact_id')}\n"

        if context.is_finality_predicted:
            user_prompt += "\n- WARNING: Prediction of Finality Active. (Retrieving Horizon Expansion fragments)."
        
        # ULTRATHINK: Inject Recovery Scaffolding
        if context.surrogate_filter:
            user_prompt += f"\n\n## SURROGATE EXECUTIVE (Surrogate Filter) [MANDATORY]\n"
            for directive in context.surrogate_filter.directives:
                user_prompt += f"- {directive}\n"
            user_prompt += f"FORBIDDEN ACTIONS: {', '.join(context.surrogate_filter.forbidden_actions)}\n"
            
        if context.recovery_pathway:
            user_prompt += f"\n\n## VISIBLE RECOVERY PATHWAY (The Map)\n"
            user_prompt += f"Current Strategy: {context.recovery_pathway.name}\n"
            for step in context.recovery_pathway.steps:
                status = "[DONE]" if step.is_completed else "[ ]"
                anchor = f" | Somatic Anchor: {step.somatic_anchor.instruction}" if step.somatic_anchor else ""
                user_prompt += f"- {status} {step.description}{anchor}\n"
            user_prompt += f"NEXT ACTION: {context.recovery_pathway.current_step_id}"

        # Add aspects to prompt (we extend the template dynamically)
        user_prompt += f"\n\n## Boardroom State (Internal Aspects)\n{aspects_text}"

        return system_prompt, user_prompt



# =============================================================================
# T015, T018, T019: HeartbeatService
# =============================================================================


class HeartbeatService:
    """
    Main heartbeat service implementing the cognitive loop.

    The heartbeat is Dionysus's autonomous decision cycle that runs hourly.
    Each heartbeat follows the OODA loop:
    - Initialize: Set up state, regenerate energy
    - Observe: Gather environmental context
    - Orient: Analyze situation, review goals
    - Decide: Choose actions (LLM call)
    - Act: Execute actions
    - Record: Store results as episodic memory
    """

    def __init__(
        self,
        energy_service: EnergyService | None = None,
        action_executor: ActionExecutor | None = None,
        driver=None,
    ):
        """
        Initialize HeartbeatService.

        Args:
            energy_service: EnergyService instance
            action_executor: ActionExecutor instance
            driver: Neo4j driver
        """
        self._energy_service = energy_service or get_energy_service()
        self._action_executor = action_executor or get_action_executor()
        self._driver = driver
        self._context_builder = ContextBuilder(driver)
        
        from api.services.efe_engine import get_efe_engine
        self._efe_engine = get_efe_engine()

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_graphiti_driver

        return get_graphiti_driver()

    async def heartbeat(self) -> HeartbeatSummary:
        """
        Execute a complete heartbeat cycle.

        Returns:
            HeartbeatSummary with all results
        """
        started_at = datetime.utcnow()
        logger.info("=== HEARTBEAT START ===")

        # =====================================================================
        # Phase 1: Initialize
        # =====================================================================
        logger.info("Phase 1: Initialize")

        # Check if paused
        state = await self._energy_service.get_state()
        if state.paused:
            logger.warning(f"Heartbeat paused: {state.pause_reason}")
            raise HeartbeatPausedError(state.pause_reason or "System paused")

        # Regenerate energy
        state = await self._energy_service.regenerate_energy()
        energy_start = state.current_energy

        # Increment heartbeat count
        heartbeat_number = await self._energy_service.increment_heartbeat_count()

        logger.info(f"Heartbeat #{heartbeat_number}, energy: {energy_start}")

        # =====================================================================
        # Phase 2: Observe
        # =====================================================================
        logger.info("Phase 2: Observe")

        observe_result = await self._action_executor.execute(
            ActionRequest(action_type=ActionType.OBSERVE)
        )
        environment = EnvironmentSnapshot(
            **observe_result.data.get("snapshot", {})
        ) if observe_result.success else EnvironmentSnapshot(
            heartbeat_number=heartbeat_number,
            current_energy=energy_start,
        )
        environment.heartbeat_number = heartbeat_number
        environment.current_energy = energy_start

        # Generate predictions from mental models (T033)
        predictions = await self._generate_model_predictions({
            "heartbeat_number": heartbeat_number,
            "user_present": environment.user_present,
            "time_since_user": environment.time_since_user_hours,
        })

        # =====================================================================
        # Phase 3: Orient (Review Goals + Resolve Predictions)
        # =====================================================================
        logger.info("Phase 3: Orient")

        review_result = await self._action_executor.execute(
            ActionRequest(action_type=ActionType.REVIEW_GOALS)
        )

        from api.services.goal_service import get_goal_service
        goal_service = get_goal_service()
        goal_assessment = await goal_service.review_goals()

        # Resolve any pending predictions from last heartbeat (T041)
        resolved_predictions = await self._resolve_pending_predictions({
            "goal_assessment": goal_assessment,
            "environment": environment,
        })

        # Build full context
        context = await self._context_builder.build_context(
            environment=environment,
            goal_assessment=goal_assessment,
        )

        # T019: Detect patterns in agent trajectories (Phase 4)
        trajectory_insights = await self._detect_trajectory_patterns(context.recent_trajectories)
        if trajectory_insights:
            logger.info(f"Detected {len(trajectory_insights)} trajectory insights")
            # We could add these to the context or goals

        # =====================================================================
        # Phase 4: Decide
        # =====================================================================
        logger.info("Phase 4: Decide")

        decision = await self._make_decision(context)

        logger.info(
            f"Decision: {len(decision.action_plan.actions)} actions, "
            f"cost: {decision.action_plan.total_cost}, "
            f"confidence: {decision.confidence}"
        )

        # =====================================================================
        # Phase 5: Act
        # =====================================================================
        logger.info("Phase 5: Act")

        # Budget Negotiation Loop (Hybrid Fix)
        # If plan exceeds budget, we cue the agent to prioritize or override.
        current_decision = decision
        retries = 0
        MAX_RETRIES = 2
        
        while retries < MAX_RETRIES:
            if current_decision.force_execution:
                logger.warning(f"Agent requested FORCE EXECUTION (Override budget). Cost: {current_decision.action_plan.total_cost}, Energy: {energy_start}")
                break
                
            if current_decision.action_plan.total_cost <= energy_start:
                break # Within budget
                
            # Over budget and no override -> Negotiate
            retries += 1
            logger.info(f"Plan over budget ({current_decision.action_plan.total_cost} > {energy_start}). Negotiating (Attempt {retries}/{MAX_RETRIES})...")
            
            feedback = (
                f"PLAN REJECTED: Your plan costs {current_decision.action_plan.total_cost} energy, but you only have {energy_start}. "
                f"Please specificy a cheaper plan OR set 'force_execution' to true if this is an emergency."
            )
            
            current_decision = await self._make_decision(context, feedback=feedback)
            
        # Update main decision object for recording
        decision = current_decision

        # Final safety trim (if still over budget and NOT forced)
        if not decision.force_execution:
            trimmed_plan = decision.action_plan.trim_to_budget(energy_start)
            if len(trimmed_plan.actions) < len(decision.action_plan.actions):
                 logger.warning("Negotiation failed or partial plan accepted. Trimming remaining actions.")
        else:
            trimmed_plan = decision.action_plan # Allow overdraft
        
        # T020: Check for strategic memory generation (Phase 4)
        # In a real implementation, the LLM would explicitly choose this action.
        # For now, we'll simulate it if there are insights.
        if trajectory_insights:
            await self._generate_strategic_memory(trajectory_insights)

        results = await self._action_executor.execute_plan(
            [ActionRequest(action_type=ActionType(a.action_type), params=a.params)
             for a in trimmed_plan.actions]
        )

        # T018: Mark trajectories as consumed (Phase 4)
        await self._consume_trajectories(context.recent_trajectories)


        # Get final energy
        final_state = await self._energy_service.get_state()
        energy_end = final_state.current_energy

        logger.info(f"Actions completed: {sum(1 for r in results if r.success)}/{len(results)}")
        logger.info(f"Energy: {energy_start} → {energy_end}")

        # ULTRATHINK: Calculate Intention-Execution Gap
        gap_magnitude = 0.0
        if results:
            success_count = sum(1 for r in results if r.status == "completed")
            gap_magnitude = 1.0 - (success_count / len(results))
        
        # Grounding: Record gap in Hexis
        from api.services.hexis_service import get_hexis_service
        hexis = get_hexis_service()
        subconscious = await hexis.get_subconscious_state("dionysus_core")
        subconscious.intention_execution_gap = gap_magnitude
        
        # If gap is high, shift towards RECOVERY proactivity for next turn
        if gap_magnitude > 0.5:
            from api.models.hexis_ontology import ExoskeletonMode
            subconscious.exoskeleton_mode = ExoskeletonMode.RECOVERY
            logger.warning(f"Intention-Execution Gap detected ({gap_magnitude}). Shifting to RECOVERY mode.")
        
        await hexis.update_subconscious_state("dionysus_core", subconscious)

        # =====================================================================
        # Phase 6: Record
        # =====================================================================
        logger.info("Phase 6: Record")

        # Build summary
        summary = HeartbeatSummary(
            heartbeat_number=heartbeat_number,
            environment=environment,
            goals=context.goals,
            decision=decision,
            results=results,
            energy_start=energy_start,
            energy_end=energy_end,
            started_at=started_at,
            ended_at=datetime.utcnow(),
        )

        # Generate narrative
        summary.narrative = await self._generate_narrative(summary)

        # Store as episodic memory and heartbeat log
        await self._record_heartbeat(summary)

        # Track 099: Ingest heartbeat narrative + reasoning through memory gateway
        await self._route_heartbeat_memory(summary)

        # FEATURE 044: Multi-Tier Memory Lifecycle Management
        # Perform background consolidation and compression
        try:
            from api.services.multi_tier_lifecycle_service import get_multi_tier_lifecycle_service
            multi_tier_svc = get_multi_tier_lifecycle_service()
            lifecycle_result = await multi_tier_svc.run_lifecycle_management()
            logger.info(f"Multi-tier memory lifecycle completed: {lifecycle_result}")
        except Exception as e:
            logger.error(f"Multi-tier memory lifecycle failed: {e}")

        logger.info(f"=== HEARTBEAT #{heartbeat_number} COMPLETE ===")
        return summary

    async def _make_decision(self, context: HeartbeatContext, feedback: str | None = None) -> HeartbeatDecision:
        """
        Make the heartbeat decision using ConsciousnessManager and SchemaContext.
        
        Args:
            context: The heartbeat context
            feedback: Optional feedback string for retry/negotiation (e.g. "Over budget")
        """
        try:
            from api.agents.consciousness_manager import ConsciousnessManager
            from api.utils.schema_context import SchemaContext
            from api.models.action import HeartbeatDecisionSchema
            
            # Convert HeartbeatContext to initial_context dict for the manager
            goal_titles = [g.title for g in context.goal_assessment.active_goals]
            task = (
                f"Heartbeat {context.environment.heartbeat_number} decision. "
                f"Active goals: {', '.join(goal_titles) if goal_titles else 'none'}."
            )
            initial_context = {
                "heartbeat_number": context.environment.heartbeat_number,
                "energy": context.environment.current_energy,
                "user_present": context.environment.user_present,
                "active_goals": goal_titles,
                "recent_memories": [m.get("content") for m in context.recent_memories[:3]],
                "identity": context.identity_context,
                "project_id": "dionysus-core",
                "bootstrap_recall": True,
                "task": task,
            }
            
            if feedback:
                initial_context["feedback"] = feedback
                logger.warning(f"Retrying decision with feedback: {feedback}")

            manager = ConsciousnessManager()
            agent_result = await manager.run_ooda_cycle(initial_context)
            
            # T008: Use SchemaContext to normalize and validate the agent's decision
            sc = SchemaContext(HeartbeatDecisionSchema, max_retries=2, timeout_seconds=5)
            
            # We pass the agent's reasoning and the context to the schema context for normalization
            normalization_prompt = f"""
            Normalize the following agent reasoning into a strict structured plan.
            
            AGENT REASONING:
            {agent_result.get('final_plan', str(agent_result))}
            
            AGENT ACTIONS SUGGESTED:
            {json.dumps(agent_result.get('actions', []))}
            """
            
            result = await sc.query(normalization_prompt)
            if not isinstance(result, dict) or not result:
                logger.error("Schema normalization returned empty result; falling back.")
                return HeartbeatDecision(
                    action_plan=ActionPlan(
                        actions=[],
                        reasoning=agent_result.get("final_plan", str(agent_result))
                    ),
                    reasoning=agent_result.get("final_plan", str(agent_result)),
                    focus_goal_id=None,
                    confidence=agent_result.get("confidence", 0.5)
                )

            if "error" in result or "reasoning" not in result:
                logger.error(
                    "Schema normalization failed: %s. Falling back to raw agent result.",
                    result.get("error", "missing reasoning"),
                )
                # Minimal mapping from agent result if normalization fails
                structured_actions = []
                for a in agent_result.get("actions", []):
                    try:
                        structured_actions.append(ActionRequest(
                            action_type=ActionType(a["action"]),
                            params=a.get("params", {}),
                            reason="Raw agent action (normalization failed)"
                        ))
                    except (ValueError, KeyError):
                        continue
                return HeartbeatDecision(
                    action_plan=ActionPlan(actions=structured_actions, reasoning=agent_result.get("final_plan", str(agent_result))),
                    reasoning=agent_result.get("final_plan", str(agent_result)),
                    focus_goal_id=None,
                    confidence=agent_result.get("confidence", 0.5)
                )

            # Map structured actions from SchemaContext to HeartbeatDecision
            actions = result.get("actions", [])
            if not isinstance(actions, list):
                actions = []

            structured_actions = []
            for a in actions:
                try:
                    structured_actions.append(ActionRequest(
                        action_type=ActionType(a["action"]),
                        params=a.get("params", {}),
                        reason=a.get("reason", "Structured decision")
                    ))
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid agent action {a}: {e}")

            return HeartbeatDecision(
                action_plan=ActionPlan(actions=structured_actions, reasoning=result["reasoning"]),
                reasoning=result["reasoning"],
                focus_goal_id=UUID(result["focus_goal_id"]) if result.get("focus_goal_id") else None,
                emotional_state=result.get("emotional_state", 0.0),
                confidence=result.get("confidence", 0.8),
                force_execution=result.get("force_execution", False),
            )

        except Exception as e:
            logger.error(f"ConsciousnessManager decision failed: {e}")
            # Absolute minimal fallback to REST if orchestrator fails
            return HeartbeatDecision(
                action_plan=ActionPlan(actions=[ActionRequest(action_type=ActionType.REST, reason="Fallback")], reasoning=f"Error: {e}"),
                reasoning=f"System error in consciousness manager: {e}",
                focus_goal_id=None,
                emotional_state=-0.5,
                confidence=0.1,
            )

    async def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current heartbeat state (energy, count, etc.) via EnergyService.
        """
        state = await self._energy_service.get_state()
        return {
            "current_energy": state.current_energy,
            "heartbeat_count": state.heartbeat_number,
            "paused": state.paused
        }

    async def _make_default_decision(self, context: HeartbeatContext) -> HeartbeatDecision:
        # Legacy method kept for interface but logic moved to _make_decision
        return await self._make_decision(context)

    async def _resolve_pending_predictions(
        self,
        observation_context: dict,
    ) -> list[dict]:
        """
        Resolve pending predictions from previous heartbeats.

        T041: Integration with heartbeat ORIENT phase.

        Args:
            observation_context: Current observation data to compare against predictions

        Returns:
            List of resolved prediction dicts
        """
        try:
            from api.services.model_service import get_model_service

            model_service = get_model_service()

            # Get unresolved predictions (limit to recent ones from last 24 hours)
            unresolved = await model_service.get_unresolved_predictions(limit=10)

            if not unresolved:
                logger.debug("No unresolved predictions to resolve")
                return []

            # Build observation from context
            observation = {
                "heartbeat_context": observation_context.get("environment", {}),
                "goal_state": str(observation_context.get("goal_assessment", {})),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Resolve each prediction
            resolved = []
            for prediction in unresolved:
                try:
                    resolved_pred = await model_service.resolve_prediction(
                        prediction_id=prediction.id,
                        observation=observation,
                        # Let the service calculate error
                    )
                    resolved.append({
                        "prediction_id": str(resolved_pred.id),
                        "model_id": str(resolved_pred.model_id),
                        "error": resolved_pred.prediction_error,
                    })
                    logger.info(
                        f"Resolved prediction {prediction.id} "
                        f"(error={resolved_pred.prediction_error:.2f})"
                    )
                except ValueError as e:
                    logger.warning(f"Skipping prediction {prediction.id}: {e}")
                except Exception as e:
                    logger.error(f"Error resolving prediction {prediction.id}: {e}")

            logger.info(f"Resolved {len(resolved)} pending predictions")
            return resolved

        except ImportError:
            logger.debug("Model service not available")
            return []
        except Exception as e:
            logger.error(f"Error in prediction resolution: {e}")
            return []

    async def _generate_model_predictions(
        self,
        context: dict,
    ) -> list[dict]:
        """
        Generate predictions from active mental models.

        T033: Integration with heartbeat OBSERVE phase.

        Args:
            context: Current context (heartbeat_number, user_present, etc.)

        Returns:
            List of prediction dicts
        """
        try:
            from api.services.model_service import get_model_service

            model_service = get_model_service()

            # Check if service has driver configured
            if model_service._driver is None:
                logger.debug("Model service not configured with driver, skipping predictions")
                return []

            # Get relevant models
            relevant_models = await model_service.get_relevant_models(context, max_models=3)

            if not relevant_models:
                logger.debug("No active mental models found")
                return []

            # Generate predictions from each model
            predictions = []
            for model in relevant_models:
                try:
                    prediction = await model_service.generate_prediction(model, context)
                    predictions.append({
                        "prediction_id": str(prediction.id),
                        "model_id": str(prediction.model_id),
                        "model_name": model.name,
                        "prediction": prediction.prediction,
                        "confidence": prediction.confidence,
                    })
                    logger.info(
                        f"Generated prediction from model '{model.name}' "
                        f"(confidence={prediction.confidence:.2f})"
                    )
                except ValueError as e:
                    # Model not active or other validation error
                    logger.warning(f"Skipping model '{model.name}': {e}")
                except Exception as e:
                    logger.error(f"Error generating prediction from '{model.name}': {e}")

            logger.info(f"Generated {len(predictions)} predictions from mental models")
            return predictions

        except ImportError:
            logger.debug("Model service not available")
            return []
        except Exception as e:
            logger.error(f"Error in model prediction generation: {e}")
            return []

    async def _consume_trajectories(self, trajectories: list[dict[str, Any]]) -> None:
        """
        Mark consumed trajectories as processed in Neo4j.
        
        Phase 4: Consumption.
        """
        if not trajectories:
            return
            
        driver = self._get_driver()
        ids = [t["id"] for t in trajectories]
        
        async with driver.session() as session:
            await session.run(
                """
                UNWIND $ids as id
                MATCH (t:Trajectory {id: id})
                SET t.processed_at = datetime()
                """,
                ids=ids
            )
        logger.info(f"Marked {len(ids)} trajectories as processed.")

    async def _detect_trajectory_patterns(self, trajectories: list[dict[str, Any]]) -> list[str]:
        """
        Analyze agent trajectories for recurring patterns/failures using LLM.
        
        Phase 4: Pattern Detection.
        """
        if not trajectories:
            return []
            
        logger.info(f"Analyzing {len(trajectories)} trajectories for patterns...")
        
        # Format trajectories for the LLM
        trajectories_text = "\n---\n".join([
            f"ID: {t.get('id')}\nSummary: {t.get('summary')}\nMetadata: {json.dumps(t.get('metadata', {}))}"
            for t in trajectories
        ])
        
        prompt = f"""
        Analyze the following agent trajectories and identify any recurring patterns, common failure modes, or significant insights.
        Focus on identifying issues that could be resolved through better strategic guidance or tool updates.
        
        AGENT TRAJECTORIES:
        {trajectories_text}
        
        Return a list of specific, actionable insights or patterns detected. 
        Format your response as a JSON list of strings. If no patterns are found, return an empty list [].
        """
        
        try:
            # We use the model service or direct LiteLLM call if available
            # For simplicity and consistency with the agent evolution, we'll use LiteLLM via a helper or direct call
            from litellm import completion
            
            response = await completion(
                model=os.getenv("SMOLAGENTS_MODEL", "openai/gpt-5-nano"),
                messages=[
                    {"role": "system", "content": "You are a cognitive analyst identifying patterns in agent behaviors."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            if isinstance(data, list):
                return [str(item) for item in data]

            insights = data.get("insights", []) or data.get("patterns", []) or []
            
            if not isinstance(insights, list):
                insights = [str(insights)]
                
            return insights
            
        except Exception as e:
            logger.error(f"Error in LLM pattern detection: {e}")
            # Fallback to simple keyword detection
            fallback_insights = []
            for t in trajectories:
                summary = t.get("summary", "").lower()
                if "error" in summary or "fail" in summary:
                    fallback_insights.append(f"Potential failure in trajectory {t.get('id')}: {summary[:100]}...")
            return fallback_insights

    async def _generate_strategic_memory(self, insights: list[str]) -> None:
        """
        Synthesize long-term strategic lessons from detected patterns.
        
        Phase 4: Strategic Memory.
        """
        if not insights:
            return
            
        driver = self._get_driver()
        
        # Use LLM to synthesize a high-quality strategic lesson from multiple insights
        prompt = f"""
        Synthesize the following behavioral insights from agent trajectories into a single, high-impact strategic lesson for a cognitive system.
        The lesson should be prescriptive, helping the system avoid future failures or capitalize on successful patterns.
        
        INSIGHTS:
        {chr(10).join(f"- {i}" for i in insights)}
        
        Return a JSON object with:
        - "lesson": A clear, concise strategic lesson.
        - "importance": A value from 0.0 to 1.0.
        - "tags": A list of relevant tags (e.g., "tool_usage", "reliability", "planning").
        """
        
        try:
            from litellm import completion
            
            response = await completion(
                model=os.getenv("SMOLAGENTS_MODEL", "openai/gpt-5-nano"),
                messages=[
                    {"role": "system", "content": "You are a strategic synthesis engine for an autonomous agent."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            lesson = data.get("lesson", "Multiple trajectory patterns observed.")
            importance = float(data.get("importance", 0.7))
            tags = data.get("tags", ["strategic", "memevolve"])
            if not isinstance(tags, list):
                tags = [str(tags)]
            
            memory_id = str(uuid4())
            
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (m:Memory {
                        id: $id,
                        content: $content,
                        memory_type: 'strategic',
                        source: 'heartbeat_synthesis',
                        importance: $importance,
                        tags: $tags,
                        created_at: datetime()
                    })
                    """,
                    id=memory_id,
                    content=lesson,
                    importance=importance,
                    tags=tags
                )
            logger.info(f"Generated high-quality strategic memory: {memory_id}")
            
        except Exception as e:
            logger.error(f"Error synthesizing strategic memory: {e}")
            # Fallback to simple creation
            memory_id = str(uuid4())
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (m:Memory {
                        id: $id,
                        content: $content,
                        memory_type: 'strategic',
                        source: 'heartbeat_fallback',
                        importance: 0.5,
                        created_at: datetime()
                    })
                    """,
                    id=memory_id,
                    content=f"Strategic Insights: {'; '.join(insights)}"
                )



    async def _generate_narrative(self, summary: HeartbeatSummary) -> str:
        """
        Generate a narrative description of the heartbeat.

        Args:
            summary: HeartbeatSummary

        Returns:
            Narrative string
        """
        return await self._generate_narrative_llm(summary)

    async def _generate_narrative_llm(self, summary: HeartbeatSummary) -> str:
        """
        Generate a rich narrative description using LLM (Analytical Empath).
        Feature 045.
        """
        try:
            from litellm import completion
            
            # Format inputs for the prompt
            actions_list = []
            for result in summary.results:
                reason = getattr(result, "reason", None)
                if reason is None and isinstance(getattr(result, "data", None), dict):
                    reason = result.data.get("reason")
                actions_list.append(
                    f"- {result.action_type.value}: {reason or 'No reason'}"
                )
            actions_text = "\\n".join(actions_list) or "Reflected quietly."
            
            goals_text = ", ".join(g.title for g in summary.goals.active[:3]) or "None"
            
            if summary.environment.user_present:
                user_context = "User is present."
            elif summary.environment.time_since_user_hours is None:
                user_context = "User likely away (last seen unknown)."
            else:
                user_context = (
                    "User likely away "
                    f"(last seen {summary.environment.time_since_user_hours:.1f}h ago)."
                )
            
            prompt = f"""
            Heartbeat #{summary.heartbeat_number} Summary:
            
            Energy: {summary.energy_start:.1f} -> {summary.energy_end:.1f}
            Environment: {user_context}
            
            Active Goals: {goals_text}
            
            Decision Reasoning: "{summary.decision.reasoning}"
            
            Actions Taken:
            {actions_text}
            
            Write my episodic memory entry.
            """

            response = await completion(
                model=os.getenv("SMOLAGENTS_MODEL", "openai/gpt-5-nano"),
                messages=[
                    {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            
            narrative = response.choices[0].message.content.strip()
            # Fallback if empty
            if not narrative:
                raise ValueError("Empty response from LLM")
                
            return narrative

        except Exception as e:
            logger.error(f"Error generating narrative LLM: {e}")
            # Fallback to template
            actions_desc = ", ".join(
                r.action_type.value for r in summary.results if r.success
            ) or "rested"

            return (
                f"Heartbeat #{summary.heartbeat_number}: "
                f"I {actions_desc}. "
                f"Energy went from {summary.energy_start:.1f} to {summary.energy_end:.1f}. "
                f"{summary.decision.reasoning or ''}"
            )

    async def _record_heartbeat(self, summary: HeartbeatSummary) -> None:
        """
        Store heartbeat results in Neo4j.

        Creates HeartbeatLog node and episodic Memory.

        Args:
            summary: HeartbeatSummary to store
        """
        driver = self._get_driver()
        log_id = str(uuid4())
        memory_id = str(uuid4())

        async with driver.session() as session:
            # Create HeartbeatLog
            await session.run(
                """
                CREATE (l:HeartbeatLog {
                    id: $log_id,
                    heartbeat_number: $heartbeat_number,
                    started_at: datetime($started_at),
                    ended_at: datetime($ended_at),
                    energy_start: $energy_start,
                    energy_end: $energy_end,
                    environment_snapshot: $environment,
                    goals_snapshot: $goals,
                    decision_reasoning: $reasoning,
                    actions_taken: $actions,
                    narrative: $narrative,
                    emotional_valence: $emotional_valence,
                    memory_id: $memory_id
                })
                """,
                log_id=log_id,
                heartbeat_number=summary.heartbeat_number,
                started_at=summary.started_at.isoformat(),
                ended_at=summary.ended_at.isoformat() if summary.ended_at else datetime.utcnow().isoformat(),
                energy_start=summary.energy_start,
                energy_end=summary.energy_end,
                environment=json.dumps(summary.environment.to_dict()),
                goals=json.dumps(summary.goals.to_dict()),
                reasoning=summary.decision.reasoning,
                actions=json.dumps([r.to_dict() for r in summary.results]),
                narrative=summary.narrative,
                emotional_valence=summary.decision.emotional_state,
                memory_id=memory_id,
            )

            # Create episodic memory
            await session.run(
                """
                CREATE (m:Memory {
                    id: $memory_id,
                    content: $narrative,
                    memory_type: 'episodic',
                    source: 'heartbeat',
                    heartbeat_number: $heartbeat_number,
                    emotional_valence: $emotional_valence,
                    created_at: datetime()
                })
                """,
                memory_id=memory_id,
                narrative=summary.narrative,
                heartbeat_number=summary.heartbeat_number,
                emotional_valence=summary.decision.emotional_state,
            )

            # Link heartbeat to memory
            await session.run(
                """
                MATCH (l:HeartbeatLog {id: $log_id})
                MATCH (m:Memory {id: $memory_id})
                CREATE (l)-[:CREATED_MEMORY]->(m)
                """,
                log_id=log_id,
                memory_id=memory_id,
            )

            if summary.decision.focus_goal_id:
                await session.run(
                    """
                    MATCH (l:HeartbeatLog {id: $log_id})
                    MATCH (g:Goal {id: $goal_id})
                    CREATE (l)-[:TOUCHED_GOAL {action: 'focused'}]->(g)
                    SET g.last_touched = datetime()
                    """,
                    log_id=log_id,
                    goal_id=str(summary.decision.focus_goal_id),
                )

        logger.info(f"Recorded heartbeat log {log_id} and memory {memory_id}")

        # Feature 046: Working Memory Cache Update
        try:
            from api.services.working_memory_cache import get_working_memory_cache
            cache = get_working_memory_cache()
            
            # Use confidence inverse as heuristic for surprisal
            surprisal = 1.0 - summary.decision.confidence
            
            is_boundary, boundary_event = cache.update(
                observation=summary.environment.to_dict(),
                energy_level=summary.energy_end / 20.0, # Normalized by max energy (approx 20)
                surprisal=surprisal
            )
            
            if is_boundary and boundary_event:
                logger.info(f"Writing Working Memory Boundary Event: {boundary_event.event_id}")
                
                # Persist Boundary Event
                from api.services.autobiographical_service import get_autobiographical_service
                auto_service = get_autobiographical_service()
                
                # Enrich with recent context
                boundary_event.related_files = ["heartbeat_log:" + log_id]
                boundary_event.metadata["trigger_heartbeat"] = summary.heartbeat_number
                
                await auto_service.record_event(boundary_event)
                
        except Exception as e:
            logger.error(f"Failed to update working memory cache: {e}")

    async def _route_heartbeat_memory(self, summary: HeartbeatSummary) -> None:
        """
        Route heartbeat narrative + reasoning through MemoryBasinRouter (Track 099).
        Ensures long-term memory ingest via MemEvolve/Graphiti. Failures are logged
        and never break the heartbeat.
        """
        try:
            from api.services.memory_basin_router import get_memory_basin_router

            parts = [
                f"Heartbeat #{summary.heartbeat_number}.",
                summary.narrative or "",
            ]
            if summary.decision.reasoning:
                parts.append(f"Reasoning: {summary.decision.reasoning}")
            content = "\n\n".join(p for p in parts if p.strip())
            if not content.strip():
                return

            router = get_memory_basin_router()
            await router.route_memory(
                content=content,
                source_id=f"heartbeat:{summary.heartbeat_number}",
            )
            logger.info(f"Routed heartbeat #{summary.heartbeat_number} to memory stack")
        except Exception as e:
            logger.warning("Heartbeat memory route failed (non-fatal): %s", e)

    async def get_recent_heartbeats(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent heartbeat logs.

        Args:
            limit: Maximum number to return

        Returns:
            List of heartbeat log data
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (l:HeartbeatLog)
                RETURN l
                ORDER BY l.heartbeat_number DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            records = await result.data()

        return [r["l"] for r in records]

    async def trigger_manual_heartbeat(self) -> HeartbeatSummary:
        """
        Trigger a manual heartbeat (for testing/admin).

        Returns:
            HeartbeatSummary
        """
        logger.info("Manual heartbeat triggered")
        return await self.heartbeat()


# =============================================================================
# Exceptions
# =============================================================================


class HeartbeatError(Exception):
    """Base exception for heartbeat errors."""
    pass


class HeartbeatPausedError(HeartbeatError):
    """Raised when heartbeat is paused."""
    pass


# =============================================================================
# Service Factory
# =============================================================================

_heartbeat_service_instance: HeartbeatService | None = None


def get_heartbeat_service() -> HeartbeatService:
    """Get or create the HeartbeatService singleton."""
    global _heartbeat_service_instance
    if _heartbeat_service_instance is None:
        _heartbeat_service_instance = HeartbeatService()
    return _heartbeat_service_instance
