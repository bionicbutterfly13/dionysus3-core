"""
Pain Analyst Agent

Specialized smolagent for extracting and categorizing customer pain points.
Feature: 019-avatar-knowledge-graph
"""

import os
from smolagents import CodeAgent, LiteLLMModel

from api.agents.knowledge.tools import ingest_avatar_insight, query_avatar_graph


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
        model_id = model_id or os.getenv("SMOLAGENTS_MODEL", "openai/gpt-5-nano-2025-08-07")

        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        self.agent = CodeAgent(
            tools=[ingest_avatar_insight, query_avatar_graph],
            model=self.model,
            name="pain_analyst",
            description="Extracts and categorizes customer pain points from content. Expert at identifying hidden pains and their triggers.",
            max_steps=5,
        )

    async def analyze(self, content: str, source: str = "unknown") -> dict:
        """
        Analyze content for pain points.

        Args:
            content: Raw text to analyze
            source: Source document identifier

        Returns:
            Analysis results with extracted pain points
        """
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

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)

        return {
            "agent": "pain_analyst",
            "source": source,
            "analysis": str(result),
        }

    def run(self, task: str) -> str:
        """Run a custom task."""
        return self.agent.run(task)
