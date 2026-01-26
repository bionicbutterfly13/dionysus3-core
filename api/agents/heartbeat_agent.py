import json
import os
from typing import Any, Dict

from smolagents import ToolCallingAgent, MCPClient
from mcp import StdioServerParameters
from api.agents.tools.active_inference_tools import compute_policy_efe, update_belief_precision

class HeartbeatAgent:
    """
    Agent wrapper for the Heartbeat DECIDE phase.
    Uses smolagents ToolCallingAgent with bridged MCP tools to reason about state.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the Heartbeat Agent with bridged MCP tools.
        """
        from api.services.llm_service import get_router_model
        self.model = get_router_model(model_id=model_id)
        self.server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        self.mcp_client = None
        self.agent = None

    def __enter__(self):
        from api.agents.audit import get_audit_callback
        # T0.1: trust_remote_code=False (default)
        self.mcp_client = MCPClient(self.server_params, structured_output=True)
        tools = self.mcp_client.__enter__()
        
        audit = get_audit_callback()
        
        # T1.1: Migrate to ToolCallingAgent
        # T039-001: Enable planning_interval for periodic replanning
        # T101-01: Inject formal Active Inference tools
        all_tools = tools + [compute_policy_efe, update_belief_precision]
        
        self.agent = ToolCallingAgent(
            tools=all_tools,
            model=self.model,
            max_steps=10,
            planning_interval=3,
            name="heartbeat_agent",
            description="Autonomous cognitive decision cycle agent equipped with formal Active Inference G-selection.",
            verbosity_level=1,
            step_callbacks=audit.get_registry("heartbeat_agent")
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mcp_client:
            self.mcp_client.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        """Terminate the MCP bridge session."""
        self.__exit__(None, None, None)

    async def decide(self, context: Dict[str, Any]) -> str:
        """
        Execute the decision cycle with timeout and resource gating (T0.3).
        """
        if not self.agent:
            with self:
                return await self._run_decide(context)
        return await self._run_decide(context)

    async def _run_decide(self, context: Dict[str, Any]) -> str:
        from api.agents.resource_gate import run_agent_with_timeout
        from api.agents.managed.metacognition import ManagedMetacognitionAgent
        from api.services.hexis_service import get_hexis_service
        
        # Hexis Consent Check (Gateway Mandate)
        try:
             hexis = get_hexis_service()
             # We assume agent_id is stable. Using a default for now or extracting from context if available.
             # Ideally context['agent_id'] is populated.
             agent_id = context.get('agent_id', 'dionysus_core') 
             has_consent = await hexis.check_consent(agent_id)
             if not has_consent:
                 return f"HEXIS_CONSENT_REQUIRED: Agent {agent_id} has not completed the Hexis Handshake."
        except Exception as e:
             # Fail open or closed? Closed for safety.
             return f"HEXIS_CHECK_FAILED: {str(e)}"
        
        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()

        # 1. System 1: Fast Heuristic Pass (OODA - Observe/Orient)
        # Constrained pass to gather initial intent.
        s1_prompt = f"OODA System 1 (Fast Pass): Briefly summarize recent state and suggest the most obvious next step. Heartbeat #{context.get('heartbeat_number', 'unknown')}."
        
        s1_result = await run_agent_with_timeout(
            self.agent, 
            s1_prompt,
            timeout_seconds=15, 
            use_ollama=is_ollama
        )

        # 2. Metacognitive Arbitration (SOFAI)
        # Use ManagedMetacognitionAgent to decide if System 2 (Slow Thinking) is needed.
        with ManagedMetacognitionAgent() as managed:
             arbitration = await managed.arbitrate_decision(
                 proposal={"output": str(s1_result), "confidence": 0.6}, # S1 confidence is heuristic
                 context={
                     "energy": context.get('current_energy', 0) / context.get('max_energy', 20),
                     "complexity": 0.7 if context.get('active_goals') else 0.3,
                     "historical_success": 0.85 
                 }
             )
             
        if not arbitration.get("use_s2"):
            return f"SYSTEM 1 ACCEPTED\nReason: {arbitration.get('reason')}\nResult: {s1_result}"

        # 3. System 2: Slow Reasoning Cascade (OODA - Decide/Act)
        # Trigger full planning cycle with formal Active Inference tools.
        prompt = f"""
        SOFAI System 2 (Slow Reasoning) ACTIVATED.
        Reason for S2: {arbitration.get('reason')}
        
        You are Dionysus, an autonomous cognitive system.
        This is Heartbeat #{context.get('heartbeat_number', 'unknown')}.
        
        ## Current State
        - Energy: {context.get('current_energy', 0)} / {context.get('max_energy', 20)}
        - User Present: {context.get('user_present', False)}
        
        ## Active Goals
        {json.dumps(context.get('active_goals', []), indent=2)}
        
        ## New Agent Trajectories
        {json.dumps(context.get('recent_trajectories', []), indent=2)}
        
        ## Task
        Perform a Deep Planning cycle using Formal Active Inference:
        1. RECALL: Gather necessary information for goal advancement.
        2. SIMULATE: For candidate action plans, use 'compute_policy_efe' to get their G-scores.
        3. DECIDE: Select the policy with the minimum G-score and execute its first step.
        4. REFLECT: If results are surprising, use 'update_belief_precision' to adjust focus.
        
        Return a final summary including the G-scores of plans you evaluated and your rationale for the selection.
        """
        
        result = await run_agent_with_timeout(
            self.agent, 
            prompt, 
            timeout_seconds=60, 
            use_ollama=is_ollama
        )
        
        return f"SYSTEM 2 COMPLETED\nReason for S2: {arbitration.get('reason')}\nResult: {result}"
