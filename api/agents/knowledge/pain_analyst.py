"""
Pain Analyst Agent

Specialized smolagent for extracting and categorizing customer pain points.
Feature: 019-avatar-knowledge-graph
"""

import os
from smolagents import ToolCallingAgent, LiteLLMModel

from api.agents.tools.avatar_tools import ingest_avatar_insight, query_avatar_graph


class PainAnalyst:
    """
    Specialized agent for pain point extraction and analysis.

    Capabilities:
    - Extract pain points from raw content
    - Categorize pain by domain (identity, achievement, relationship, health)
    - Identify triggers and intensity levels
    - Map relationships between pains
    """

    def __init__(self, model_id: str = None):
        model_id = model_id or os.getenv("SMOLAGENTS_MODEL", "openai/gpt-5-nano")

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
            name="pain_analyst",
            description="Extracts and categorizes customer pain points from content. Expert at identifying hidden pains and their triggers.",
            max_steps=5,
            max_tool_threads=4, # Enable parallel tool execution (T1.3)
            step_callbacks=audit.get_registry("pain_analyst")
        )

    async def analyze(self, content: str, source: str = "unknown") -> dict:
        """
        Analyze content for pain points.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = f"""Analyze this content for customer pain points.

Content from {source}:
{content}

Your task:
1. Identify ALL pain points (explicit and implicit)
2. For each pain point, use the ingest_avatar_insight tool with insight_type="pain_point"
3. After extraction, use query_avatar_graph to find related pains already in the system
4. Summarize your findings

Focus on:
- Identity pains (who they feel they are vs. who they want to be)
- Achievement pains (success that feels hollow)
- Relationship pains (disconnection despite connection)
- Health/energy pains (exhaustion, burnout)

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
            "agent": "pain_analyst",
            "source": source,
            "analysis": str(result),
        }

    def run(self, task: str) -> str:
        """Run a custom task."""
        return self.agent.run(task)
