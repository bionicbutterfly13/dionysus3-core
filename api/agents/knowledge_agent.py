import os
import json
from typing import Any, Dict, List
from smolagents import CodeAgent, LiteLLMModel

class KnowledgeAgent:
    """
    Specialized agent for Knowledge Base maintenance.
    Manages audiobook manuscripts and knowledge graph entity mapping.
    """

    def __init__(self, model_id: str = "anthropic/claude-3-5-sonnet-20241022"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        self.agent = CodeAgent(
            tools=[], # Tools will be bridged via MCP if needed
            model=self.model,
            name="knowledge_agent",
            description="Expert in IAS conceptual content, audiobook production, and avatar research."
        )

    async def review_manuscript(self, text: str, target_word_count: int = 13500) -> Dict[str, Any]:
        """
        Review and suggest updates for the audiobook manuscript with self-reported confidence.
        """
        prompt = f"""
        Review this manuscript section. Target: {target_word_count} words.
        Ensure IAS consistency and authoritative tone.
        
        Manuscript:
        {text[:5000]}
        
        Respond with a JSON object:
        {{
            "suggestions": "...",
            "word_count_estimate": <int>,
            "confidence": <float>,
            "reasoning": "..."
        }}
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
            return json.loads(cleaned)
        except:
            return {"raw_result": result, "confidence": 0.5}

    async def map_avatar_data(self, raw_data: str) -> dict:
        """
        Extract structured avatar research data from raw text.
        """
        from api.services.aspect_service import get_aspect_service
        aspect_service = get_aspect_service()
        aspects = await aspect_service.get_all_aspects(user_id="knowledge_system")
        aspects_text = "\n".join([f"- {a.get('name')}: {a.get('role')}" for a in aspects])

        prompt = f"""
        Extract structured avatar research (pain points, objections, goals) from this raw data:
        {raw_data}
        
        ## Existing Boardroom Aspects (Reference for mapping):
        {aspects_text}
        
        Respond with a JSON object.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
            return json.loads(cleaned)
        except:
            # Low confidence - add to human review
            await aspect_service.add_to_human_review("Failed Avatar Extraction", {"raw": raw_data, "result": result})
            return {"raw_result": result, "status": "human_review_queued"}
