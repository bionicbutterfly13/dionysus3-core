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
from typing import Any
from uuid import UUID, uuid4

from api.models.action import (
    ActionPlan,
    ActionRequest,
    ActionResult,
    ActionStatus,
    EnvironmentSnapshot,
    GoalsSnapshot,
    HeartbeatDecision,
    HeartbeatSummary,
)
from api.models.goal import Goal, GoalAssessment
from api.services.action_executor import ActionExecutor, get_action_executor
from api.services.energy_service import ActionType, EnergyService, get_energy_service

logger = logging.getLogger("dionysus.heartbeat_service")


# =============================================================================
# T017: Heartbeat Prompts
# =============================================================================

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
    last_heartbeat_summary: str = ""
    activated_clusters: list[str] = field(default_factory=list)


class ContextBuilder:
    """Builds context for the LLM decision phase."""

    def __init__(self, driver=None):
        """Initialize context builder."""
        self._driver = driver

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    async def build_context(
        self,
        environment: EnvironmentSnapshot,
        goal_assessment: GoalAssessment,
    ) -> HeartbeatContext:
        """
        Build full context for heartbeat decision.

        Args:
            environment: Current environment snapshot
            goal_assessment: Goal review results

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

        return HeartbeatContext(
            environment=environment,
            goals=goals,
            goal_assessment=goal_assessment,
            recent_memories=recent_memories,
            recent_trajectories=recent_trajectories,
            identity_context=identity_context,
            last_heartbeat_summary=last_summary,
        )


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
            identity_context=context.environment.heartbeat_number,
            last_heartbeat=context.last_heartbeat_summary,
        )

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

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

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

        # Trim actions to budget
        trimmed_plan = decision.action_plan.trim_to_budget(energy_start)
        
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

        logger.info(f"=== HEARTBEAT #{heartbeat_number} COMPLETE ===")
        return summary

    async def _make_decision(self, context: HeartbeatContext) -> HeartbeatDecision:
        """
        Make the heartbeat decision using agent or LLM.

        Args:
            context: Full context for decision

        Returns:
            HeartbeatDecision with chosen actions
        """
        energy_config = {
            "max_energy": self._energy_service.get_config().max_energy,
            "base_regeneration": self._energy_service.get_config().base_regeneration,
        }

        # Check if agent-based decisions are enabled
        use_agent = os.getenv("USE_AGENT_DECISIONS", "false").lower() == "true"

        if use_agent:
            try:
                from api.agents.decision_adapter import (
                    AgentDecisionConfig,
                    get_agent_decision_adapter,
                )

                config = AgentDecisionConfig(
                    use_multi_agent=os.getenv("USE_MULTI_AGENT", "false").lower() == "true",
                    model_id=os.getenv("SMOLAGENTS_MODEL", ""),
                    max_steps=int(os.getenv("SMOLAGENTS_MAX_STEPS", "5")),
                    fallback_on_failure=True,
                )

                adapter = get_agent_decision_adapter(config)
                decision = await adapter.make_decision(context, energy_config)

                logger.info(
                    f"Agent decision: {len(decision.action_plan.actions)} actions, "
                    f"confidence: {decision.confidence}"
                )
                return decision

            except Exception as e:
                logger.error(f"Agent decision failed, using default: {e}")

        # Legacy path
        system_prompt, user_prompt = self._context_builder.format_prompt(
            context, energy_config
        )

        # TODO: Call LLM here
        return await self._make_default_decision(context)

    async def _make_default_decision(self, context: HeartbeatContext) -> HeartbeatDecision:
        """
        Make a default decision without LLM.

        Used as fallback or for testing.
        """
        actions = []
        reasoning_parts = []

        # If no goals, suggest brainstorming
        if context.goal_assessment.needs_brainstorm:
            actions.append(ActionRequest(
                action_type=ActionType.BRAINSTORM_GOALS,
                params={"context": "starting fresh", "count": 3},
                reason="No goals exist",
            ))
            reasoning_parts.append("I have no goals, so I should brainstorm some.")

        # If stale goals, consider reviewing
        if context.goal_assessment.stale_goals:
            actions.append(ActionRequest(
                action_type=ActionType.REPRIORITIZE,
                params={"changes": [
                    {"goal_id": str(g.id), "new_priority": "backburner"}
                    for g in context.goal_assessment.stale_goals[:2]
                ]},
                reason="Moving stale goals to backburner",
            ))
            reasoning_parts.append(f"I have {len(context.goal_assessment.stale_goals)} stale goals to address.")

        # If active goals, reflect on progress
        if context.goal_assessment.active_goals:
            goal = context.goal_assessment.active_goals[0]
            actions.append(ActionRequest(
                action_type=ActionType.REFLECT,
                params={"topic": f"Progress on: {goal.title}"},
                reason=f"Reflecting on active goal",
            ))
            reasoning_parts.append(f"I'm working on '{goal.title}'.")

        # T052: Check for models needing revision
        try:
            from api.services.model_service import get_model_service

            model_service = get_model_service()
            models_needing_revision = await model_service.get_models_needing_revision(
                accuracy_threshold=0.5,
                limit=2,
            )

            for model in models_needing_revision:
                actions.append(ActionRequest(
                    action_type=ActionType.REVISE_MODEL,
                    params={
                        "model_id": str(model.id),
                        "trigger_description": f"Automatic revision due to low accuracy ({model.prediction_accuracy:.2f})",
                    },
                    reason=f"Model '{model.name}' has low prediction accuracy",
                ))
                reasoning_parts.append(
                    f"Model '{model.name}' needs revision (accuracy: {model.prediction_accuracy:.2f})."
                )
        except Exception as e:
            logger.warning(f"Failed to check models for revision: {e}")

        # Default: rest if nothing to do
        if not actions:
            actions.append(ActionRequest(
                action_type=ActionType.REST,
                reason="Nothing pressing to do",
            ))
            reasoning_parts.append("Nothing urgent, conserving energy.")

        reasoning = " ".join(reasoning_parts) if reasoning_parts else "Default heartbeat cycle."

        return HeartbeatDecision(
            action_plan=ActionPlan(actions=actions, reasoning=reasoning),
            reasoning=reasoning,
            focus_goal_id=context.goal_assessment.active_goals[0].id if context.goal_assessment.active_goals else None,
            emotional_state=0.0,
            confidence=0.5,
        )

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

            # Check if service has database pool configured
            if model_service._db_pool is None:
                logger.debug("Model service not configured with database pool, skipping resolution")
                return []

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
                model=os.getenv("SMOLAGENTS_MODEL", "openai/gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a cognitive analyst identifying patterns in agent behaviors."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
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
                model=os.getenv("SMOLAGENTS_MODEL", "openai/gpt-4o-mini"),
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
        # TODO: Use LLM for better narrative
        actions_desc = ", ".join(
            r.action_type.value for r in summary.results if r.success
        ) or "rested"

        return (
            f"Heartbeat #{summary.heartbeat_number}: "
            f"I {actions_desc}. "
            f"Energy went from {summary.energy_start:.1f} to {summary.energy_end:.1f}. "
            f"{summary.reasoning or ''}"
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

            # Link to touched goals
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
