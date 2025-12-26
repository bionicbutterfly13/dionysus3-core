"""
Avatar Researcher - Orchestrating Manager Agent

Multi-agent coordinator for comprehensive avatar research using smolagents.
Feature: 019-avatar-knowledge-graph
"""

import os
import logging
from typing import List, Optional, Dict, Any

from smolagents import CodeAgent, LiteLLMModel

from api.agents.knowledge.tools import (
    ingest_avatar_insight,
    query_avatar_graph,
    synthesize_avatar_profile,
    bulk_ingest_document,
)
from api.agents.knowledge.pain_analyst import PainAnalyst
from api.agents.knowledge.objection_handler import ObjectionHandler
from api.agents.knowledge.voice_extractor import VoiceExtractor

logger = logging.getLogger(__name__)


class AvatarResearcher:
    """
    Orchestrating manager agent for avatar research.

    Coordinates specialized sub-agents:
    - PainAnalyst: Extracts and categorizes pain points
    - ObjectionHandler: Maps objections and generates counter-narratives
    - VoiceExtractor: Captures linguistic patterns and voice characteristics

    Uses Graphiti-backed tools for knowledge graph persistence.
    """

    def __init__(self, model_id: str = None):
        """
        Initialize the Avatar Researcher with sub-agents.

        Args:
            model_id: LiteLLM model identifier (default: from env or gpt-4o-mini)
        """
        model_id = model_id or os.getenv("SMOLAGENTS_MODEL", "openai/gpt-4o-mini")

        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Initialize sub-agents
        self.pain_analyst = PainAnalyst(model_id=model_id)
        self.objection_handler = ObjectionHandler(model_id=model_id)
        self.voice_extractor = VoiceExtractor(model_id=model_id)

        # Manager agent with access to all tools and sub-agents
        self.agent = CodeAgent(
            tools=[
                ingest_avatar_insight,
                query_avatar_graph,
                synthesize_avatar_profile,
                bulk_ingest_document,
            ],
            model=self.model,
            name="avatar_researcher",
            description="""Master avatar research coordinator. Orchestrates specialized agents
to build comprehensive customer avatar profiles from raw content. Expert at synthesizing
insights across pain points, objections, desires, beliefs, behaviors, and voice patterns.""",
            max_steps=10,
            managed_agents=[
                self.pain_analyst.agent,
                self.objection_handler.agent,
                self.voice_extractor.agent,
            ],
        )

    async def analyze_document(self, file_path: str, document_type: str = "copy_brief") -> Dict[str, Any]:
        """
        Analyze a document comprehensively using all sub-agents.

        Args:
            file_path: Path to the document to analyze
            document_type: Type of document (copy_brief, email, interview, review)

        Returns:
            Comprehensive analysis results from all agents
        """
        prompt = f"""Analyze this document comprehensively for avatar research.

Document: {file_path}
Type: {document_type}

Your task:
1. First, use bulk_ingest_document to extract and store all insights from the file
2. Then delegate to your specialized agents:
   - Ask pain_analyst to analyze the content for pain points
   - Ask objection_handler to identify objections and counter-narratives
   - Ask voice_extractor to capture linguistic patterns
3. After all agents complete, use synthesize_avatar_profile to create a unified view
4. Summarize the key findings

Be thorough - this document may be our "Ground Truth" for the avatar."""

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)

        return {
            "document": file_path,
            "document_type": document_type,
            "analysis": str(result),
        }

    async def analyze_content(self, content: str, source: str = "unknown") -> Dict[str, Any]:
        """
        Analyze raw content using all sub-agents in parallel.

        Args:
            content: Raw text content to analyze
            source: Source identifier

        Returns:
            Combined analysis from all agents
        """
        import asyncio

        # Run all sub-agents in parallel
        results = await asyncio.gather(
            self.pain_analyst.analyze(content, source),
            self.objection_handler.analyze(content, source),
            self.voice_extractor.analyze(content, source),
            return_exceptions=True,
        )

        return {
            "source": source,
            "pain_analysis": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
            "objection_analysis": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
            "voice_analysis": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
        }

    async def research_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a research question about the avatar using the knowledge graph.

        Args:
            question: Natural language question about the avatar

        Returns:
            Research findings with supporting evidence
        """
        prompt = f"""Answer this research question about our avatar using the knowledge graph.

Question: {question}

Your approach:
1. Use query_avatar_graph to search for relevant insights
2. If needed, delegate to specialized agents for deeper analysis
3. Synthesize findings into a clear, actionable answer
4. Include specific examples and quotes where available

Think like a market researcher presenting to a copywriting team."""

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)

        return {
            "question": question,
            "answer": str(result),
        }

    async def generate_avatar_profile(self, dimensions: str = "all") -> Dict[str, Any]:
        """
        Generate a complete avatar profile from the knowledge graph.

        Args:
            dimensions: Which dimensions to include (comma-separated or "all")

        Returns:
            Comprehensive avatar profile
        """
        prompt = f"""Generate a comprehensive avatar profile from all available research.

Dimensions to include: {dimensions}

Your task:
1. Use synthesize_avatar_profile to gather all insights
2. For each dimension, use query_avatar_graph to get detailed data
3. Ask voice_extractor to generate a voice guide
4. Create an actionable profile with:
   - Demographics & psychographics
   - Core pain points (ranked by intensity)
   - Key objections (with counter-narratives)
   - Deep desires (explicit and latent)
   - Limiting beliefs (with reframes)
   - Voice guide (phrases to use/avoid)
   - Failed solutions they've tried

Make this immediately useful for copywriting and messaging."""

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)

        return {
            "dimensions": dimensions,
            "profile": str(result),
        }

    async def ingest_ground_truth(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest the "Ground Truth" avatar document (e.g., IAS-copy-brief.md).

        This is a comprehensive ingestion that:
        1. Bulk ingests the document
        2. Runs all sub-agents for deep extraction
        3. Synthesizes the complete profile

        Args:
            file_path: Path to the ground truth document

        Returns:
            Ingestion summary with counts and profile
        """
        logger.info(f"Ingesting ground truth document: {file_path}")

        # Read the document
        with open(file_path, 'r') as f:
            content = f.read()

        # Step 1: Bulk ingest
        prompt = f"""This is our Ground Truth avatar document. Perform comprehensive ingestion.

Document: {file_path}

Step 1: Use bulk_ingest_document to extract and store ALL insights.

Step 2: Delegate deep analysis to specialized agents:
- pain_analyst: Extract ALL pain points with intensity, triggers, categories
- objection_handler: Map ALL objections with counter-narratives and root beliefs
- voice_extractor: Capture ALL voice patterns, phrases, emotional tones

Step 3: Use synthesize_avatar_profile to create the unified profile.

Step 4: Report what was found - counts by category, key insights, anything missing.

This is foundational research. Be exhaustive."""

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)

        return {
            "document": file_path,
            "status": "ground_truth_ingested",
            "result": str(result),
        }

    def run(self, task: str) -> str:
        """Run a custom research task."""
        return self.agent.run(task)


# Convenience function for API usage
async def create_avatar_researcher(model_id: str = None) -> AvatarResearcher:
    """
    Factory function to create an AvatarResearcher instance.

    Args:
        model_id: Optional LiteLLM model identifier

    Returns:
        Configured AvatarResearcher instance
    """
    return AvatarResearcher(model_id=model_id)
