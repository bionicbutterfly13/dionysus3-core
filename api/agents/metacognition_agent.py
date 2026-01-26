import os
import logging
from typing import Dict, Any, Optional
from smolagents import ToolCallingAgent, MCPClient
from mcp import StdioServerParameters

logger = logging.getLogger("dionysus.metacognition")


# Attentional spotlight registry - tracks focus targets per agent
# Keys: agent_name -> {"focus_target": str, "spotlight_precision": float}
_attentional_spotlight_registry: Dict[str, Dict[str, Any]] = {}


class MetacognitionAgent:
    """
    Specialized agent for the DECIDE phase of the OODA loop.
    Reviews goal states, assesses model accuracy, and revises mental models via MCP tools.
    Uses ToolCallingAgent for efficient, parallel self-reflection and goal management.
    
    ABM Alignment (Chapter 22, Anderson 2014):
    - Autonomy: Exercises top-down control via 'mental actions'.
    - Local Rules: Modulates lower-level agent parameters (precision, attention).
    - Proactivity: Actively corrects prediction errors to maintain system integrity.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        from api.services.llm_service import get_router_model
        self.model = get_router_model(model_id=model_id)
        self.server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        self.mcp_client = None
        self.agent = None
        self.name = "metacognition"
        self.description = """
            Specialized in self-reflection, goal management, and mental model revision.
            Uses ToolCallingAgent to evaluate system performance and adjust internal models.
            Supports FRACTAL METACOGNITION: can create hierarchical thoughts by linking 
            ThoughtSeeds as children of higher-order reflections.
            """

    def __enter__(self):
        from api.agents.audit import get_audit_callback
        self.mcp_client = MCPClient(self.server_params, structured_output=True)
        tools = self.mcp_client.__enter__()
        
        audit = get_audit_callback()
        
        # T1.1: Migrate to ToolCallingAgent
        # T039-002: Enable planning_interval for OODA agents
        self.agent = ToolCallingAgent(
            tools=tools,
            model=self.model,
            name=self.name,
            description=self.description,
            max_steps=5,
            planning_interval=2,  # Re-plan every 2 steps (FR-039-002)
            max_tool_threads=4,  # Enable parallel tool execution (T1.3)
            step_callbacks=audit.get_registry("metacognition")
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mcp_client:
            self.mcp_client.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        self.__exit__(None, None, None)

    async def run(self, task: str):
        """Run the metacognition cycle with River Metaphor and Fractal integration."""
        if not self.agent:
            with self:
                return await self._run(task)
        return await self._run(task)

    async def _run(self, task: str):
        from api.services.context_stream import get_context_stream_service
        from api.models.cognitive import FlowState

        # 1. Check current River Flow (T027)
        stream_svc = get_context_stream_service()
        flow = await stream_svc.analyze_current_flow(project_id="default")

        # 2. Adjust max_steps based on state (SC-002)
        if flow.state == FlowState.TURBULENT:
            # Slow down, be more careful
            self.agent.max_steps = 3
        elif flow.state == FlowState.FLOWING:
            # Productive, can do more
            self.agent.max_steps = 8

        # 3. Inject flow context and FRACTAL instructions into task for LLM awareness
        fractal_instructions = """
        FRACTAL METACOGNITION ENABLED:
        When creating ThoughtSeeds, you can now link them hierarchically. 
        - If a thought is a reflection on a previous thought, provide the parent_thought_id.
        - You can also provide a list of child_thought_ids to establish containment.
        - Use this to build deep, recursive models of system behavior.
        """

        task_with_flow = f"CURRENT RIVER STATUS: {flow.summary}\n\n{fractal_instructions}\n\n{task}"

        return self.agent.run(task_with_flow)

    # =========================================================================
    # ACTIVE METACOGNITION: Mental Actions
    # Per Metacognitive Particles paper: higher-level active paths (a^2) modulate
    # lower-level belief parameters. Mental actions target precision/attention,
    # NOT belief content directly.
    # =========================================================================

    async def mental_action(
        self,
        target_agent: str,
        modulation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a mental action that modulates lower-level agent parameters.

        Mental actions are the mechanism by which metacognition ACTIVELY influences
        cognition, rather than passively observing. Per the Metacognitive Particles
        paper, mental actions modulate:
        - Precision (inverse variance / confidence)
        - Attention allocation (spotlight focus)
        - Working memory maintenance

        Args:
            target_agent: Name of the agent to modulate (e.g., "perception", "reasoning")
            modulation: Dict containing modulation parameters:
                - "precision_delta": float - Adjust precision by this amount
                - "set_precision": float - Set precision to this absolute value
                - "focus_target": str - Direct attentional spotlight to this target
                - "spotlight_precision": float - Precision of the spotlight (0.0-1.0)

        Returns:
            Dict with status and resulting state
        """
        from api.services.efe_engine import (
            get_agent_precision,
            set_agent_precision
        )

        result = {
            "target_agent": target_agent,
            "action": "mental_action",
            "success": True,
            "modulations_applied": [],
            "prior_state": {},
            "new_state": {}
        }

        # Record prior state
        result["prior_state"]["precision"] = get_agent_precision(target_agent)
        result["prior_state"]["spotlight"] = _attentional_spotlight_registry.get(target_agent, {})

        try:
            # Apply precision modulation
            if "precision_delta" in modulation:
                delta = float(modulation["precision_delta"])
                new_precision = await self._adjust_agent_precision(target_agent, delta)
                result["modulations_applied"].append(f"precision_delta={delta:+.4f}")
                result["new_state"]["precision"] = new_precision

            elif "set_precision" in modulation:
                precision = float(modulation["set_precision"])
                set_agent_precision(target_agent, precision)
                result["modulations_applied"].append(f"set_precision={precision:.4f}")
                result["new_state"]["precision"] = get_agent_precision(target_agent)

            # Apply attentional spotlight modulation
            if "focus_target" in modulation or "spotlight_precision" in modulation:
                focus = modulation.get("focus_target")
                spotlight_prec = modulation.get("spotlight_precision", 0.5)
                await self._adjust_attentional_spotlight(
                    target_agent,
                    {"focus_target": focus, "spotlight_precision": spotlight_prec}
                )
                result["modulations_applied"].append(
                    f"spotlight(target={focus}, precision={spotlight_prec:.2f})"
                )
                result["new_state"]["spotlight"] = _attentional_spotlight_registry.get(target_agent, {})

            logger.info(
                f"Mental action executed on '{target_agent}': "
                f"{', '.join(result['modulations_applied'])}"
            )

        except Exception as e:
            logger.error(f"Mental action failed for '{target_agent}': {e}")
            result["success"] = False
            result["error"] = str(e)

        return result

    async def _adjust_agent_precision(
        self,
        agent_name: str,
        delta: float
    ) -> float:
        """
        Modulate precision of a target agent.

        Per Active Inference: precision = inverse variance = confidence.
        Higher precision means the agent's predictions are weighted more heavily.

        When prediction error is high:
        - DECREASE precision to make the agent more open to new information
        - This is "loosening" attention / increasing uncertainty tolerance

        When prediction error is low:
        - INCREASE precision to make the agent more confident
        - This is "tightening" attention / decreasing uncertainty tolerance

        Args:
            agent_name: Target agent (e.g., "perception", "reasoning")
            delta: Amount to adjust precision (positive = increase, negative = decrease)

        Returns:
            New precision value
        """
        from api.services.efe_engine import adjust_agent_precision, get_agent_precision

        prior_precision = get_agent_precision(agent_name)
        new_precision = adjust_agent_precision(agent_name, delta)

        logger.info(
            f"Precision modulation for '{agent_name}': "
            f"{prior_precision:.4f} -> {new_precision:.4f} (delta={delta:+.4f})"
        )

        return new_precision

    async def _adjust_attentional_spotlight(
        self,
        agent_name: str,
        focus: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust attentional spotlight for a target agent.

        The attentional spotlight determines WHERE the agent focuses and
        with what precision (how tightly focused). This is a core mechanism
        of active metacognition - directing lower-level processing.

        Args:
            agent_name: Target agent (e.g., "perception", "reasoning")
            focus: Dict containing:
                - "focus_target": str - What to focus on (concept, domain, etc.)
                - "spotlight_precision": float - How tightly focused (0.0=diffuse, 1.0=laser)

        Returns:
            Updated spotlight configuration
        """
        prior_spotlight = _attentional_spotlight_registry.get(agent_name, {})

        # Update spotlight
        new_spotlight = {
            "focus_target": focus.get("focus_target") or prior_spotlight.get("focus_target"),
            "spotlight_precision": focus.get("spotlight_precision", 0.5),
            "updated_by": "metacognition",
        }

        _attentional_spotlight_registry[agent_name] = new_spotlight

        logger.info(
            f"Attentional spotlight for '{agent_name}': "
            f"focus={new_spotlight['focus_target']}, "
            f"precision={new_spotlight['spotlight_precision']:.2f}"
        )

        return new_spotlight

    async def active_correction(
        self,
        agent_name: str,
        prediction_error: float,
        error_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute active correction when prediction error exceeds threshold.

        This is the core ACTIVE metacognition loop:
        1. Observe prediction error (from self_modeling_callback)
        2. If error > threshold, trigger mental action
        3. Mental action adjusts precision to improve future predictions

        Strategy per Active Inference:
        - High prediction error -> DECREASE precision (be more open to surprise)
        - This allows the system to update beliefs more readily
        - Gradually increase precision as errors decrease (stabilize beliefs)

        Args:
            agent_name: Agent that produced the prediction error
            prediction_error: Magnitude of prediction error (0.0 - 1.0+)
            error_context: Optional context about the error

        Returns:
            Dict with correction actions taken
        """
        # Thresholds for precision adjustment
        HIGH_ERROR_THRESHOLD = 0.15
        CRITICAL_ERROR_THRESHOLD = 0.30

        result = {
            "agent_name": agent_name,
            "prediction_error": prediction_error,
            "correction_type": "none",
            "actions_taken": []
        }

        if prediction_error < HIGH_ERROR_THRESHOLD:
            # Error acceptable, no correction needed
            # Optionally: slowly increase precision (stabilize)
            result["correction_type"] = "none"
            return result

        if prediction_error >= CRITICAL_ERROR_THRESHOLD:
            # Critical error: aggressive precision decrease
            delta = -0.3
            result["correction_type"] = "critical"
            logger.warning(
                f"CRITICAL prediction error ({prediction_error:.2%}) for '{agent_name}' - "
                f"aggressive precision decrease"
            )
        else:
            # Moderate error: gentle precision decrease
            delta = -0.15
            result["correction_type"] = "moderate"
            logger.info(
                f"High prediction error ({prediction_error:.2%}) for '{agent_name}' - "
                f"moderate precision decrease"
            )

        # Execute precision modulation
        precision_result = await self.mental_action(
            target_agent=agent_name,
            modulation={"precision_delta": delta}
        )
        result["actions_taken"].append(precision_result)

        # If context suggests a specific focus area, adjust spotlight
        if error_context and "focus_suggestion" in error_context:
            spotlight_result = await self.mental_action(
                target_agent=agent_name,
                modulation={
                    "focus_target": error_context["focus_suggestion"],
                    "spotlight_precision": 0.7  # Moderately focused
                }
            )
            result["actions_taken"].append(spotlight_result)

        return result

    # =========================================================================
    # SOFAI ARBITRATION (Track 101)
    # =========================================================================

    async def arbitrate_decision(
        self,
        proposal: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decide whether to accept the S1 (Fast) proposal or trigger S2 (Slow) reasoning.
        
        Args:
            proposal: The initial fast result from the perception/heartbeat pass.
            context: Current cognitive and environmental state.
        
        Returns:
            Dict containing arbitration decision and rationale.
        """
        from api.services.arbitration_service import get_arbitration_service
        service = get_arbitration_service()
        
        # Extract metrics
        confidence = proposal.get("confidence", 0.5)
        success_rate = context.get("historical_success", 0.8) # Placeholder
        energy = context.get("energy", 1.0)
        complexity = context.get("complexity", 0.5)
        
        result = service.arbitrate(
            s1_confidence=confidence,
            success_rate=success_rate,
            current_energy=energy,
            complexity_estimate=complexity
        )
        
        logger.info(f"SOFAI Arbitration for decision: use_s2={result.use_s2}, reason='{result.reason}'")
        
        return {
            "use_s2": result.use_s2,
            "reason": result.reason,
            "trust_score": float(result.trust_score),
            "risk_aversion": float(result.risk_aversion)
        }


def get_attentional_spotlight(agent_name: str) -> Dict[str, Any]:
    """Get current attentional spotlight for an agent."""
    return _attentional_spotlight_registry.get(agent_name, {
        "focus_target": None,
        "spotlight_precision": 0.5
    })
