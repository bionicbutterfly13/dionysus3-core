"""
Voice Extractor Agent

Specialized smolagent for extracting linguistic patterns and voice characteristics.
Feature: 019-avatar-knowledge-graph
"""

import os
from smolagents import ToolCallingAgent, LiteLLMModel

from api.agents.knowledge.tools import ingest_avatar_insight, query_avatar_graph


class VoiceExtractor:
    """
    Specialized agent for voice pattern extraction.

    Capabilities:
    - Extract distinctive phrases and expressions
    - Identify emotional tones and contexts
    - Map vocabulary preferences
    - Detect linguistic patterns that indicate psychological states
    """

    def __init__(self, model_id: str = None):
        model_id = model_id or os.getenv("SMOLAGENTS_MODEL", "openai/gpt-4o-mini")

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
            name="voice_extractor",
            description="Extracts voice patterns, phrases, and emotional tones from content. Expert at capturing authentic avatar language.",
            max_steps=5,
            max_tool_threads=4, # Enable parallel tool execution (T1.3)
            step_callbacks=audit.get_registry("voice_extractor")
        )

    async def analyze(self, content: str, source: str = "unknown") -> dict:
        """
        Analyze content for voice patterns.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = f"""Analyze this content for voice patterns and linguistic characteristics.

Content from {source}:
{content}

Your task:
1. Identify distinctive phrases the avatar uses
2. For each pattern, use the ingest_avatar_insight tool with insight_type="voice_pattern"
3. Note the emotional tone of each phrase
4. Identify the context where they'd use this language

Watch for:
- Self-talk phrases ("I should be...", "Why can't I...")
- Emotional markers (frustration, resignation, hope)
- Professional jargon they use
- Metaphors and frameworks they naturally employ
- Words they avoid vs. words they gravitate toward

This is about capturing HOW they speak, not just WHAT they say."""

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
            "agent": "voice_extractor",
            "source": source,
            "analysis": str(result),
        }

    async def generate_voice_guide(self) -> dict:
        """
        Generate a comprehensive voice guide from all extracted patterns.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = """Generate a comprehensive voice guide for writing to this avatar.

1. Query the avatar graph for all voice_pattern insights
2. Also query for pain points and beliefs to understand emotional context
3. Synthesize into a voice guide with:
   - Phrases TO USE (with examples)
   - Phrases TO AVOID (with alternatives)
   - Emotional tone guidance
   - Vocabulary preferences
   - Sample sentences that sound like them

Make this actionable for copywriters."""

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
            "voice_guide": str(result),
        }

    def run(self, task: str) -> str:
        """Run a custom task."""
        return self.agent.run(task)
