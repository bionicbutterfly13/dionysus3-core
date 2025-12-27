import os
import json
from typing import Any, Dict, List
from smolagents import CodeAgent, LiteLLMModel

class MarketingAgent:
    """
    Specialized agent for generating marketing assets (emails, sales pages).
    Uses smolagents CodeAgent for creative content generation.
    """

    def __init__(self, model_id: Optional[str] = None):
        if model_id is None:
            model_id = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
            
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.agent = CodeAgent(
            tools=[],
            model=self.model,
            name="marketing_agent",
            description="Expert in IAS marketing and copy generation. Can generate nurture sequences and sales pages."
        )

    async def generate_email(self, topic: str, framework: str, target_audience: str = "analytical professional") -> Dict[str, Any]:
        """
        Generate a high-converting nurture email with self-reported confidence.
        """
        from api.services.aspect_service import get_aspect_service
        aspect_service = get_aspect_service()
        aspects = await aspect_service.get_all_aspects(user_id="marketing_system")
        
        aspects_text = "\n".join([f"- {a.get('name')}: {a.get('role')}" for a in aspects])

        prompt = f"""
        Generate a high-converting nurture email.
        - Topic: {topic}
        - Framework: {framework}
        - Target: {target_audience}
        - Boardroom Context: {aspects_text}
        
        Style: Empathetic, coaching, direct.
        
        Respond with a JSON object:
        {{
            "email_text": "...",
            "subject_line": "...",
            "confidence": <float 0.0-1.0>,
            "reasoning": "..."
        }}
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
            data = json.loads(cleaned)
            
            # FR-004: Divert to review if confidence is low
            if data.get("confidence", 0.0) < 0.7:
                await aspect_service.add_to_human_review("Low Confidence Email", data, data.get("confidence", 0.0))
                
            return data
        except Exception as e:
            # Divert to review on parse failure
            await aspect_service.add_to_human_review("Email Parse Failure", {"raw": result, "error": str(e)})
            return {"status": "human_review_queued", "raw": result}

    async def generate_sales_page(self, product: str, positioning: str) -> Dict[str, Any]:
        """
        Generate sales page copy with self-reported confidence.
        """
        prompt = f"""
        Write sales page copy for:
        - Product: {product}
        - Positioning: {positioning}
        
        Include sections: Hero, Pain, Solution, Features, Social Proof, CTA.
        
        Respond with a JSON object containing 'copy_text', 'confidence', and 'reasoning'.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
            data = json.loads(cleaned)
            return data
        except:
            return {"raw": result, "confidence": 0.5}
