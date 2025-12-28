"""
Voice and Wisdom Research Tools

smolagents tools that use Graphiti for learning voice, processes, and evolution.
"""

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from smolagents import tool
from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger(__name__)

def run_sync(coro):
    """Helper to run async coroutines in a synchronous context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)

@tool
def ingest_wisdom_insight(
    content: str,
    insight_type: str,
    source: str = "unknown"
) -> dict:
    """
    Extract and persist a structured wisdom insight (voice, process, evolution) to the knowledge graph.

    Args:
        content: Raw text containing the insight (quote, description, observation)
        insight_type: Type of insight - one of: voice_pattern, process_insight, evolution_reasoning, strategic_idea
        source: Source document or context for this insight

    Returns:
        Dict with extracted wisdom data and graph storage confirmation
    """
    valid_types = ["voice_pattern", "process_insight", "evolution_reasoning", "strategic_idea"]
    if insight_type not in valid_types:
        return {"error": f"Invalid insight_type. Must be one of: {valid_types}"}

    async def _extract_and_store():
        import os
        schema_hints = {
            "voice_pattern": '{"phrase": "...", "emotional_tone": "...", "context": "...", "style_notes": "..."}',
            "process_insight": '{"name": "...", "steps": ["...", "..."], "goal": "...", "why_it_works": "..."}',
            "evolution_reasoning": '{"from_concept": "...", "to_concept": "...", "reason_for_change": "...", "status": "current|deprecated"}',
            "strategic_idea": '{"idea": "...", "potential_impact": "...", "related_to": "...", "implementation_hint": "..."}'
        }

        system_prompt = f"""You are a wisdom extraction analyst. Extract a structured {insight_type} from the content.
        Focus on the user's VOICE, IDEAS, and the EVOLUTION of their processes.
        
        Respond with JSON only using this schema:
        {schema_hints.get(insight_type, '{}')}
        
        Preserve the raw authenticity and 'richness' of the user's original thoughts."""

        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": f"Extract {insight_type} from:\n\n{content}"}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=512,
            )

            # Parse JSON
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]

            extracted = json.loads(cleaned)

            # Store in Graphiti
            from api.services.graphiti_service import GraphitiConfig
            config = GraphitiConfig(
                neo4j_uri="bolt://127.0.0.1:7687",
                neo4j_password="Mmsm2280",
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            graphiti = await get_graphiti_service(config)
            episode_content = f"Wisdom Insight ({insight_type}): {json.dumps(extracted)}\nSource: {source}"

            result = await graphiti.ingest_message(
                content=episode_content,
                source_description=f"wisdom_research:{insight_type}",
                group_id="ias_wisdom",
            )

            return {
                "success": True,
                "insight_type": insight_type,
                "extracted": extracted,
                "source": source,
                "graph_nodes": len(result.get("nodes", [])),
                "graph_edges": len(result.get("edges", [])),
            }

        except Exception as e:
            logger.error(f"Wisdom insight extraction failed: {e}")
            return {"success": False, "error": str(e)}

    return run_sync(_extract_and_store())


@tool
def query_wisdom_graph(query: str, insight_types: Optional[str] = None, limit: int = 10) -> dict:
    """
    Query the wisdom knowledge graph for voice, processes, and evolution insights.

    Args:
        query: Search query (e.g., "How has the tripwire evolved?")
        insight_types: Optional comma-separated filter (voice_pattern, process_insight, etc.)
        limit: Max results

    Returns:
        Dict with matching insights
    """
    async def _search():
        try:
            graphiti = await get_graphiti_service()
            results = await graphiti.search(
                query=query,
                group_ids=["ias_wisdom"],
                limit=limit,
            )
            return {
                "query": query,
                "results": results.get("edges", []),
                "count": results.get("count", 0),
            }
        except Exception as e:
            logger.error(f"Wisdom graph query failed: {e}")
            return {"query": query, "results": [], "count": 0, "error": str(e)}

    return run_sync(_search())

