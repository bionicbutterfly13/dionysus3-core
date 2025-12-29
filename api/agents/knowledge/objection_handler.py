"""
Objection Handler Agent

Specialized smolagent for mapping objections and generating counter-narratives.
Feature: 019-avatar-knowledge-graph
"""

import os
from smolagents import ToolCallingAgent, LiteLLMModel

from api.agents.tools.avatar_tools import ingest_avatar_insight, query_avatar_graph


class ObjectionHandler:
    """
    Specialized agent for objection mapping and counter-narrative development.

    Capabilities:
    - Extract objections from content
    - Categorize by type (price, time, trust, prior_solution, skepticism)
    - Generate effective counter-narratives
    - Identify root beliefs behind objections
    """

    def __init__(self, model_id: str = None):
        model_id = model_id or os.getenv("SMOLAGENTS_MODEL", "openai/gpt-5-nano-2025-08-07")

        # Configure LiteLLMModel for Ollama or cloud providers
        model_kwargs = {"model_id": model_id}
        if model_id.startswith("ollama/"):
            model_kwargs["api_base"] = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        else:
            model_kwargs["api_key"] = os.getenv("OPENAI_API_KEY")

        self.model = LiteLLMModel(**model_kwargs)

        # T1.1: Migrate to ToolCallingAgent
        from api.agents.audit import get_audit_callback
        audit = get_audit_callback()
        
        self.agent = ToolCallingAgent(
            tools=[ingest_avatar_insight, query_avatar_graph],
            model=self.model,
            name="objection_handler",
            description="Maps customer objections and generates counter-narratives. Expert at understanding resistance.",
            max_steps=5,
            max_tool_threads=4, # Enable parallel tool execution (T1.3)
            step_callbacks=audit.get_registry("objection_handler")
        )

    async def analyze(self, content: str, source: str = "unknown") -> dict:
        """
        Analyze content for objections.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = f"""Analyze this content for customer objections and resistance patterns.

Content from {source}:
{content}

Your task:
1. Identify ALL objections (stated and implied)
2. For each objection, use the ingest_avatar_insight tool with insight_type="objection"
3. For each objection, also identify the root belief driving it
4. Generate a counter-narrative that addresses the root belief
5. Use query_avatar_graph to find related objections

Categories to watch for:
- Price objections ("too expensive", "can I afford this")
- Time objections ("I don't have time", "too slow")
- Trust objections ("will this work for me", "sounds too good")
- Prior solution objections ("I've tried this before", "therapy didn't work")
- Skepticism ("this is just another...")

Extract everything you find."""

        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()
        
        # Run with timeout and gating (T0.3, Q4)
        result = await run_agent_with_timeout(
            self.agent, 
            prompt, 
            timeout_seconds=60, 
            use_ollama=is_ollama
        )

        return {
            "agent": "objection_handler",
            "source": source,
            "analysis": str(result),
        }

    async def generate_counter(self, objection: str) -> dict:
        """
        Generate a counter-narrative for a specific objection.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = f"""Generate a counter-narrative for this objection:

"{objection}"

1. First, identify the root belief behind this objection
2. Query the avatar graph for related pain points and desires
3. Craft a counter-narrative that:
   - Acknowledges their concern (validates, doesn't dismiss)
   - Reframes the root belief
   - Connects to their deeper desire
   - Uses the avatar's voice patterns if available

Make it feel like understanding, not selling."""

        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()
        
        # Run with timeout and gating (T0.3, Q4)
        result = await run_agent_with_timeout(
            self.agent, 
            prompt, 
            timeout_seconds=60, 
            use_ollama=is_ollama
        )

        return {
            "objection": objection,
            "counter_narrative": str(result),
        }

    def run(self, task: str) -> str:
        """Run a custom task."""
        return self.agent.run(task)
