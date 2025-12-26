import json
import os
from typing import Any, Dict

from smolagents import CodeAgent, LiteLLMModel, ToolCollection
from mcp import StdioServerParameters

class HeartbeatAgent:
    """
    Agent wrapper for the Heartbeat DECIDE phase.
    Uses smolagents CodeAgent with bridged MCP tools to reason about state.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        """
        Initialize the Heartbeat Agent with bridged MCP tools.
        """
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        # Bridge tools from local MCP server
        server_params = StdioServerParameters(
            command="python3",
            args=["-m", "dionysus_mcp.server"],
            env={**os.environ, "PYTHONPATH": "."}
        )
        
        try:
            self.tool_collection = ToolCollection.from_mcp(server_params, trust_remote_code=True)
            self.tools = [*self.tool_collection.tools]
        except Exception as e:
            # Fallback if bridge fails (e.g. during testing)
            from api.agents.tools.recall_tool import RecallTool
            self.tools = [RecallTool()]
            print(f"Warning: MCP Bridge failed, using local fallback: {e}")
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            max_steps=5,
            executor_type="local",
            verbosity_level=1
        )

    async def decide(self, context: Dict[str, Any]) -> str:
        """
        Execute the decision cycle.
        
        Args:
            context: Dictionary containing environment, goals, energy, etc.
        
        Returns:
            A string summary of the decision and actions taken.
        """
        # Construct the prompt from the context
        # We simplify the legacy prompt to focus on the CodeAgent's strengths
        
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
        
        If you take actions using tools (like recalling or reflecting), those count as part of your "Action Phase" for this heartbeat.
        
        Return a final summary of what you did and why, and what your plan is for the next cycle.
        """
        
        # Run the agent (CodeAgent.run is sync, so we wrap if needed, but here we can just call it
        # since we are likely in a thread pool or it handles it. 
        # Actually, smolagents.run IS sync. We should ideally run this in an executor if called from async code.)
        
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        
        return str(result)
