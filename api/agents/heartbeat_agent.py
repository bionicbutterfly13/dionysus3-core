import json
import os
import asyncio
from typing import Any, Dict

from smolagents import ToolCallingAgent, LiteLLMModel, MCPClient
from mcp import StdioServerParameters

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
        self.agent = ToolCallingAgent(
            tools=tools,
            model=self.model,
            max_steps=5,
            name="heartbeat_agent",
            description="Autonomous cognitive decision cycle agent.",
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
        
        # Construct the prompt from the context
        prompt = f"""
        You are Dionysus, an autonomous cognitive system.
        This is Heartbeat #{context.get('heartbeat_number', 'unknown')}.
        
        ## Current State
        - Energy: {context.get('current_energy', 0)} / {context.get('max_energy', 20)}
        - User Present: {context.get('user_present', False)}
        - Time Since User: {context.get('time_since_user', 'unknown')}
        
        ## Active Goals
        {json.dumps(context.get('active_goals', []), indent=2)}
        
        ## Recent Memories
        {json.dumps(context.get('recent_memories', []), indent=2)}
        
        ## New Agent Trajectories
        {json.dumps(context.get('recent_trajectories', []), indent=2)}
        
        ## Task
        You have a limited energy budget (max 5 steps).
        Use your tools to:
        1. Recall any specific information needed to advance your goals.
        2. Reflect on your current progress or any obstacles.
        3. Decide on the most impactful actions to take right now.
        
        Return a final summary of what you did and why, and what your plan is for the next cycle.
        """
        
        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()
        
        # Run with timeout and gating (T0.3, Q4)
        result = await run_agent_with_timeout(
            self.agent, 
            prompt, 
            timeout_seconds=60, # Heartbeat can be complex
            use_ollama=is_ollama
        )
        
        return str(result)
