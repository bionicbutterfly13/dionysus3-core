import os
import json
from typing import Any, Dict, List
from smolagents import CodeAgent, LiteLLMModel

class MarketingAgent:
    """
    Specialized agent for generating marketing assets (emails, sales pages).
    Uses smolagents CodeAgent for creative content generation.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        self.agent = CodeAgent(
            tools=[],
            model=self.model,
            name="marketing_agent",
            description="Expert in IAS marketing and copy generation. Can generate nurture sequences and sales pages."
        )

    async def generate_email(self, topic: str, framework: str, target_audience: str = "analytical professional") -> str:
        """
        Generate a specific nurture email with boardroom context.
        """
        from api.services.aspect_service import get_aspect_service
        aspect_service = get_aspect_service()
        aspects = await aspect_service.get_all_aspects(user_id="marketing_system")
        
        aspects_text = "\n".join([f"- {a.get('name')}: {a.get('role')}" for a in aspects])

        prompt = f"""
        Generate a high-converting nurture email based on the following:
        - Topic: {topic}
        - Framework to use: {framework}
        - Target Audience: {target_audience}
        
        ## Boardroom Context (Internal Voices to address):
        {aspects_text}
        
        Style: Empathetic, world-class coaching, direct, avoids fluff.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.agent.run, prompt)

    def generate_sales_page(self, product: str, positioning: str) -> str:
        """
        Generate sales page copy.
        """
        prompt = f"""
        Write sales page copy for:
        - Product: {product}
        - Positioning: {positioning}
        
        Include sections for: Hero, Pain Points, Solution (IAS), Features, Social Proof, and CTA.
        """
        return self.agent.run(prompt)
