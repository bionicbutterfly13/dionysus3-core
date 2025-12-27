"""
Avatar Knowledge Graph Tools

smolagents tools that use Graphiti for avatar research.
Feature: 019-avatar-knowledge-graph
"""

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from smolagents import tool

from api.models.avatar import InsightType, AvatarInsight
from api.services.graphiti_service import get_graphiti_service
from api.services.claude import chat_completion, HAIKU

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
def ingest_avatar_insight(
    content: str,
    insight_type: str,
    source: str = "unknown"
) -> dict:
    """
    Extract and persist a structured avatar insight to the knowledge graph.

    Args:
        content: Raw text containing the insight (quote, description, observation)
        insight_type: Type of insight - one of: pain_point, objection, desire, belief, behavior, voice_pattern, failed_solution
        source: Source document or context for this insight

    Returns:
        Dict with extracted insight data and graph storage confirmation
    """
    # Validate insight type
    valid_types = [t.value for t in InsightType]
    if insight_type not in valid_types:
        return {"error": f"Invalid insight_type. Must be one of: {valid_types}"}

    async def _extract_and_store():
        # Build extraction prompt based on insight type
        schema_hints = {
            "pain_point": '{"description": "...", "category": "identity|achievement|relationship|health", "intensity": 0.0-1.0, "frequency": "daily|weekly|sometimes|rarely", "trigger": "...", "expressed_as": "..."}',
            "objection": '{"text": "...", "category": "price|time|trust|prior_solution|skepticism", "strength": 0.0-1.0, "counter_narrative": "...", "root_belief": "..."}',
            "desire": '{"description": "...", "priority": 1-10, "latent": true|false, "expressed_as": "...", "blocked_by": ["belief1", "belief2"]}',
            "belief": '{"content": "...", "certainty": 0.0-1.0, "origin": "...", "limiting": true|false, "blocks": ["desire1"]}',
            "behavior": '{"pattern": "...", "trigger": "...", "context": "...", "frequency": "daily|weekly|sometimes|rarely", "driven_by": "..."}',
            "voice_pattern": '{"phrase": "...", "emotional_tone": "frustrated|hopeful|resigned|defensive|neutral", "context": "...", "frequency": 0.0-1.0}',
            "failed_solution": '{"name": "...", "category": "therapy|coaching|self-help|biohacking|retreat|other", "why_failed": "...", "residual_belief": "...", "time_invested": "..."}',
        }

        system_prompt = f"""You are an avatar research analyst. Extract a structured {insight_type} from the content.

Respond with JSON only using this schema:
{schema_hints.get(insight_type, '{}')}

Be precise. Use exact quotes when available. Infer intensity/strength from language cues."""

        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": f"Extract {insight_type} from:\n\n{content}"}],
                system_prompt=system_prompt,
                model=HAIKU,
                max_tokens=512,
            )

            # Parse JSON response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]

            extracted = json.loads(cleaned)

            # Store in Graphiti
            graphiti = await get_graphiti_service()

            # Format for Graphiti ingestion
            episode_content = f"Avatar Insight ({insight_type}): {json.dumps(extracted)}\nSource: {source}"

            result = await graphiti.ingest_message(
                content=episode_content,
                source_description=f"avatar_research:{insight_type}",
                group_id="avatar_research",
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
            logger.error(f"Avatar insight extraction failed: {e}")
            return {"success": False, "error": str(e)}

    return run_sync(_extract_and_store())


@tool
def query_avatar_graph(query: str, insight_types: Optional[str] = None, limit: int = 10) -> dict:
    """
    Query the avatar knowledge graph using semantic search with graph traversal.

    Args:
        query: Natural language query about the avatar (e.g., "What pain points relate to identity?")
        insight_types: Optional comma-separated filter (e.g., "pain_point,objection")
        limit: Maximum results to return

    Returns:
        Dict with matching insights from the knowledge graph
    """
    async def _search():
        try:
            graphiti = await get_graphiti_service()

            # Search with avatar research group
            results = await graphiti.search(
                query=query,
                group_ids=["avatar_research"],
                limit=limit,
            )

            edges = results.get("edges", [])

            # Filter by insight types if specified
            if insight_types:
                type_list = [t.strip() for t in insight_types.split(",")]
                edges = [
                    e for e in edges
                    if any(t in str(e.get("fact", "")) for t in type_list)
                ]

            return {
                "query": query,
                "results": edges,
                "count": len(edges),
            }

        except Exception as e:
            logger.error(f"Avatar graph query failed: {e}")
            return {"query": query, "results": [], "count": 0, "error": str(e)}

    return run_sync(_search())


@tool
def synthesize_avatar_profile(dimensions: str = "all") -> dict:
    """
    Synthesize a comprehensive avatar profile from all graph data.

    Args:
        dimensions: Comma-separated dimensions to include, or "all" for everything.
                   Options: pain_point, objection, desire, belief, behavior, voice_pattern, failed_solution

    Returns:
        Dict with synthesized avatar profile organized by dimension
    """
    async def _synthesize():
        try:
            graphiti = await get_graphiti_service()

            # Determine which dimensions to query
            all_dims = ["pain_point", "objection", "desire", "belief", "behavior", "voice_pattern", "failed_solution"]
            if dimensions == "all":
                dims_to_query = all_dims
            else:
                dims_to_query = [d.strip() for d in dimensions.split(",") if d.strip() in all_dims]

            profile = {
                "archetype": "Analytical Empath",
                "synthesized_at": datetime.utcnow().isoformat(),
                "dimensions": {},
            }

            total_insights = 0

            for dim in dims_to_query:
                results = await graphiti.search(
                    query=f"avatar {dim}",
                    group_ids=["avatar_research"],
                    limit=20,
                )

                edges = results.get("edges", [])
                profile["dimensions"][dim] = {
                    "count": len(edges),
                    "items": [
                        {
                            "fact": e.get("fact"),
                            "valid_at": e.get("valid_at"),
                        }
                        for e in edges
                    ]
                }
                total_insights += len(edges)

            profile["total_insights"] = total_insights

            return profile

        except Exception as e:
            logger.error(f"Avatar profile synthesis failed: {e}")
            return {"error": str(e)}

    return run_sync(_synthesize())


@tool
def bulk_ingest_document(
    file_path: str,
    document_type: str = "copy_brief"
) -> dict:
    """
    Bulk ingest a document and extract all avatar insights.

    Args:
        file_path: Path to the document (markdown file)
        document_type: Type of document - copy_brief, email, interview, review

    Returns:
        Dict with extraction summary and counts by insight type
    """
    async def _bulk_ingest():
        try:
            # Read the document
            with open(file_path, 'r') as f:
                content = f.read()

            # Use LLM to identify and extract all insights
            system_prompt = """You are an avatar research analyst. Analyze this document and extract ALL avatar insights.

For each insight found, output a JSON object on its own line with this structure:
{"type": "pain_point|objection|desire|belief|behavior|voice_pattern|failed_solution", "content": "the relevant text", "extracted": {structured data}}

Extract as many insights as you can find. Be thorough."""

            response = await chat_completion(
                messages=[{"role": "user", "content": f"Document ({document_type}):\n\n{content}"}],
                system_prompt=system_prompt,
                model=HAIKU,
                max_tokens=4096,
            )

            # Parse multiple JSON objects from response
            insights = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        insight = json.loads(line)
                        insights.append(insight)
                    except json.JSONDecodeError:
                        continue

            # Store each insight in Graphiti
            graphiti = await get_graphiti_service()
            stored_count = 0
            by_type = {}

            for insight in insights:
                insight_type = insight.get("type", "unknown")
                by_type[insight_type] = by_type.get(insight_type, 0) + 1

                episode_content = f"Avatar Insight ({insight_type}): {json.dumps(insight.get('extracted', insight))}\nSource: {file_path}"

                try:
                    await graphiti.ingest_message(
                        content=episode_content,
                        source_description=f"bulk_ingest:{document_type}",
                        group_id="avatar_research",
                    )
                    stored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to store insight: {e}")

            return {
                "success": True,
                "document": file_path,
                "document_type": document_type,
                "insights_found": len(insights),
                "insights_stored": stored_count,
                "by_type": by_type,
            }

        except Exception as e:
            logger.error(f"Bulk ingest failed: {e}")
            return {"success": False, "error": str(e)}

    return run_sync(_bulk_ingest())
