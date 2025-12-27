import os
import json
from typing import Any, Dict, List, Optional
from smolagents import CodeAgent, LiteLLMModel
from api.agents.knowledge.tools import ingest_avatar_insight, query_avatar_graph, synthesize_avatar_profile
from api.agents.knowledge.wisdom_tools import ingest_wisdom_insight, query_wisdom_graph
from api.agents.tools.mosaeic_tools import mosaeic_capture
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.models.bootstrap import BootstrapConfig

class KnowledgeAgent:
    """
    Specialized agent for Knowledge Base maintenance and Wisdom Extraction.
    Manages audiobook manuscripts, avatar research, and learning from archives.
    """

    def __init__(self, model_id: Optional[str] = None):
        # Default model for management/writing tasks
        if model_id is None:
            model_id = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5-20251101")
            
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # T011: Initialize bootstrap recall service
        self.bootstrap_svc = BootstrapRecallService()
        
        # Use the cheap model for heavy analytical extraction tasks
        self.cheap_model = LiteLLMModel(
            model_id=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Sub-agents with specialized tools use the cheap model
        self.avatar_analyst = CodeAgent(
            tools=[ingest_avatar_insight, query_avatar_graph],
            model=self.cheap_model,
            name="avatar_analyst",
            description="Extracts deep avatar insights (pain, desire, objections) and maps them to Neo4j."
        )

        self.wisdom_analyst = CodeAgent(
            tools=[ingest_wisdom_insight, query_wisdom_graph, mosaeic_capture],
            model=self.cheap_model,
            name="wisdom_analyst",
            description="Extracts user voice, processes, and conceptual evolution from archived conversations. Use mosaeic_capture for deep experiential states."
        )

        self.agent = CodeAgent(
            tools=[synthesize_avatar_profile, query_wisdom_graph, mosaeic_capture],
            model=self.model,
            managed_agents=[self.avatar_analyst, self.wisdom_analyst],
            name="knowledge_manager",
            description="Orchestrates the extraction of wisdom and avatar data from all available sources."
        )

    async def map_avatar_data(self, raw_data: str, source: str = "unknown", project_id: str = "ias-knowledge-base") -> dict:
        """
        Orchestrate deep analysis of archives to learn voice, process, and avatar data.
        """
        # T012: Perform Bootstrap Recall
        bootstrap_result = await self.bootstrap_svc.recall_context(
            query=f"Avatar wisdom voice extraction from {source}",
            project_id=project_id,
            config=BootstrapConfig(project_id=project_id)
        )

        from api.services.aspect_service import get_aspect_service
        aspect_service = get_aspect_service()
        
        prompt = f"""
        Analyze this raw archival data to extract CURRENTLY RELEVANT wisdom.
        
        {bootstrap_result.formatted_context}

        DATA:
        {raw_data}
        
        SOURCE: {source}
        
        TASKS:
        1. Extract AVATAR insights (pain, objections, desires) for the 'Analytical Empath' True Model.
        2. Extract VOICE patterns (how the user speaks) and store them.
        3. Extract PROCESS insights (how the Conviction Gauntlet or MOSAEIC works) and store them.
        4. Extract EVOLUTION reasoning (why we moved from old concepts to the True Model).
        
        Use your sub-agents (avatar_analyst, wisdom_analyst) to perform these extractions.
        Discard outdated definitions that contradict the True Model, but preserve the underlying psychological 'richness'.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        
        return {
            "summary": str(result),
            "status": "completed",
            "confidence": 0.9
        }

    async def review_manuscript(self, text: str, target_word_count: int = 13500) -> Dict[str, Any]:
        prompt = f"Review this manuscript for IAS consistency and target {target_word_count} words:\n\n{text[:5000]}"
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        return {"result": str(result)}