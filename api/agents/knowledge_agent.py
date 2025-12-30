import os
import json
from typing import Any, Dict, List, Optional
from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel
from api.agents.tools.avatar_tools import ingest_avatar_insight, query_avatar_graph, synthesize_avatar_profile
from api.agents.tools.wisdom_tools import ingest_wisdom_insight, query_wisdom_graph
from api.agents.tools.mosaeic_tools import mosaeic_capture
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.services.llm_service import get_router_model, GPT5_NANO
from api.models.bootstrap import BootstrapConfig

class KnowledgeAgent:
    """
    Specialized agent for Knowledge Base maintenance and Wisdom Extraction.
    Manages audiobook manuscripts, avatar research, and learning from archives.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        # T3.1: Use centralized LiteLLMRouterModel
        self.model = get_router_model(model_id=model_id)
        
        # T011: Initialize bootstrap recall service
        self.bootstrap_svc = BootstrapRecallService()
        
        # T3.1: Use router for sub-agents as well
        self.cheap_model = self.model
        
        from api.agents.audit import get_audit_callback
        audit = get_audit_callback()

        # Sub-agents with specialized tools use ToolCallingAgent (Phase 2)
        self.avatar_analyst = ToolCallingAgent(
            tools=[ingest_avatar_insight, query_avatar_graph],
            model=self.cheap_model,
            name="avatar_analyst",
            description="Extracts deep avatar insights (pain, desire, objections) and maps them to Neo4j.",
            max_steps=5,
            max_tool_threads=4,
            step_callbacks=audit.get_registry("avatar_analyst")
        )

        self.wisdom_analyst = ToolCallingAgent(
            tools=[ingest_wisdom_insight, query_wisdom_graph, mosaeic_capture],
            model=self.cheap_model,
            name="wisdom_analyst",
            description="Extracts user voice, processes, and conceptual evolution from archived conversations. Use mosaeic_capture for deep experiential states.",
            max_steps=5,
            max_tool_threads=4,
            step_callbacks=audit.get_registry("wisdom_analyst")
        )

        # (Docker sandboxing disabled for local Darwin environment stability)
        self.agent = CodeAgent(
            tools=[synthesize_avatar_profile, query_wisdom_graph, mosaeic_capture],
            model=self.model,
            managed_agents=[self.avatar_analyst, self.wisdom_analyst],
            name="knowledge_manager",
            description="Orchestrates the extraction of wisdom and avatar data from all available sources.",
            executor_type="local",
            use_structured_outputs_internally=True,
            additional_authorized_imports=["importlib.resources", "json", "datetime"],
            step_callbacks=audit.get_registry("knowledge_manager"),
            max_steps=10,
            planning_interval=3
        )

    async def map_avatar_data(self, raw_data: str, source: str = "unknown", project_id: str = "ias-knowledge-base") -> dict:
        """
        Orchestrate deep analysis of archives to learn voice, process, and avatar data.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        # T012: Perform Bootstrap Recall
        bootstrap_result = await self.bootstrap_svc.recall_context(
            query=f"Avatar wisdom voice extraction from {source}",
            project_id=project_id,
            config=BootstrapConfig(project_id=project_id)
        )

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
        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()
        
        # Run with timeout and gating (T0.3, Q4)
        result = await run_agent_with_timeout(
            self.agent, 
            prompt, 
            timeout_seconds=90, 
            use_ollama=is_ollama
        )
        
        return {
            "summary": str(result),
            "status": "completed",
            "confidence": 0.9
        }

    async def extract_wisdom_from_archive(self, content: str, session_id: str) -> dict:
        """
        T002: Use the /research.agent protocol to extract structured wisdom.
        Utilizes specialized tools for deep experiential and structural mapping.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = f"""
        You are the Dionysus /research.agent. Your mission is to perform DEEP WISDOM EXTRACTION from historical archives.
        
        SESSION_ID: {session_id}
        
        CRITICAL INSTRUCTIONS:
        1. MENTAL MODELS: Identify recurring principles, decision-making frameworks, and contrarian insights.
        2. OODA LOOPS: Identify successful strategies where Observation led to an effective Decision/Action.
        3. MOSAEIC MAPPING: Use your tools to capture deep experiential states (Senses, Actions, Emotions, Impulses, Cognitions) found in the text.
        4. ATTRACTOR BASINS: Map 'Energy Wells'—states of high momentum or recurring psychological patterns.
        5. PROVENANCE: Every insight must be tied to its origin in the CONTENT below.

        CONTENT:
        {content}
        
        OUTPUT:
        Respond with a JSON object containing:
        - 'wisdom_insights': list of [model, summary, importance]
        - 'attractors': list of [name, description, energy_level]
        - 'experiential_captures': output from your mosaeic_capture tool
        - 'reasoning': The 'Why' behind these extractions.
        """
        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()
        
        # Run with timeout and gating (T0.3, Q4)
        result = await run_agent_with_timeout(
            self.agent, 
            prompt, 
            timeout_seconds=120, # Wisdom extraction can be very heavy
            use_ollama=is_ollama
        )
        
        # Parse and return structured data
        try:
            cleaned = str(result).strip()
            if "```json" in cleaned: cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            return json.loads(cleaned)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to parse wisdom extraction JSON: {e}. Raw: {result}")
            return {"raw_output": str(result), "session_id": session_id}