"""
Class-based tools for Voice and Wisdom Research.
Feature: 031-wisdom-distillation
Tasks: T4.1, T4.2
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.graphiti_service import get_graphiti_service
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger("dionysus.wisdom_tools")

class WisdomInsightOutput(BaseModel):
    success: bool = Field(..., description="Whether the extraction was successful")
    insight_type: str = Field(..., description="The type of insight extracted")
    extracted: Dict[str, Any] = Field(..., description="The structured data extracted")
    source: str = Field(..., description="The source of the wisdom")
    graph_nodes: int = Field(0, description="Number of nodes created in the graph")
    graph_edges: int = Field(0, description="Number of edges created in the graph")
    error: Optional[str] = Field(None, description="Error message if success is False")

class IngestWisdomInsightTool(Tool):
    name = "ingest_wisdom_insight"
    description = "Extract and persist a structured wisdom insight (voice, process, evolution) to the knowledge graph."
    
    inputs = {
        "content": {
            "type": "string", 
            "description": "Raw text containing the insight (quote, description, observation)"
        },
        "insight_type": {
            "type": "string", 
            "description": "Type of insight - one of: voice_pattern, process_insight, evolution_reasoning, strategic_idea"
        },
        "source": {
            "type": "string", 
            "description": "Source document or context for this insight",
            "default": "unknown",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, content: str, insight_type: str, source: str = "unknown") -> dict:
        from api.agents.resilience import wrap_with_resilience
        valid_types = ["voice_pattern", "process_insight", "evolution_reasoning", "strategic_idea"]
        if insight_type not in valid_types:
            error_msg = wrap_with_resilience(f"Invalid insight_type. Must be one of: {valid_types}")
            return WisdomInsightOutput(
                success=False,
                insight_type=insight_type,
                extracted={},
                source=source,
                error=error_msg
            ).model_dump()

        async def _run():
            from api.services.llm_service import chat_completion, GPT5_NANO
            
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

            graphiti = None
            try:
                response = await chat_completion(
                    messages=[{"role": "user", "content": f"Extract {insight_type} from:\n\n{content}"}],
                    system_prompt=system_prompt,
                    model=GPT5_NANO,
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
                episode_content = f"Wisdom Insight ({insight_type}): {json.dumps(extracted)}\nSource: {source}"

                result = await graphiti.ingest_message(
                    content=episode_content,
                    source_description=f"wisdom_research:{insight_type}",
                    group_id="ias_wisdom",
                )

                return WisdomInsightOutput(
                    success=True,
                    insight_type=insight_type,
                    extracted=extracted,
                    source=source,
                    graph_nodes=len(result.get("nodes", [])),
                    graph_edges=len(result.get("edges", [])),
                )

            except Exception as e:
                logger.error(f"Wisdom insight extraction failed: {e}")
                return WisdomInsightOutput(
                    success=False,
                    insight_type=insight_type,
                    extracted={},
                    source=source,
                    error=wrap_with_resilience(str(e))
                )
            finally:
                if graphiti:
                    await graphiti.close()

        # Run via isolated loop
        result_obj = async_tool_wrapper(_run)()
        return result_obj.model_dump()

class WisdomGraphQueryOutput(BaseModel):
    query: str = Field(..., description="The original search query")
    results: List[Dict[str, Any]] = Field(..., description="List of matching graph edges/facts")
    count: int = Field(..., description="Number of results found")
    error: Optional[str] = Field(None, description="Error message if query failed")

class QueryWisdomGraphTool(Tool):
    name = "query_wisdom_graph"
    description = "Query the wisdom knowledge graph for voice, processes, and evolution insights."
    
    inputs = {
        "query": {
            "type": "string",
            "description": "Search query (e.g., 'How has the tripwire evolved?')"
        },
        "insight_types": {
            "type": "string", 
            "description": "Optional comma-separated filter (voice_pattern, process_insight, etc.)",
            "nullable": True
        },
        "limit": {
            "type": "integer",
            "description": "Maximum results to return",
            "default": 10,
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, query: str, insight_types: Optional[str] = None, limit: int = 10) -> dict:
        from api.agents.resilience import wrap_with_resilience
        async def _run():
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
                return {"query": query, "results": [], "count": 0, "error": wrap_with_resilience(str(e))}
            finally:
                if 'graphiti' in locals() and graphiti:
                    await graphiti.close()

        return async_tool_wrapper(_run)()

class DistillWisdomClusterTool(Tool):
    name = "distill_wisdom_cluster"
    description = "Synthesize a group of fragmented insights into a single canonical Wisdom Unit."
    
    inputs = {
        "fragments_json": {
            "type": "string",
            "description": "JSON list of fragmented insights to merge."
        },
        "wisdom_type": {
            "type": "string",
            "description": "The target type: mental_model, strategic_principle, or case_study."
        }
    }
    output_type = "any"

    def forward(self, fragments_json: str, wisdom_type: str) -> dict:
        async def _run():
            from api.services.llm_service import chat_completion, GPT5_NANO
            from api.models.wisdom import WisdomType
            
            fragments = json.loads(fragments_json)
            
            system_prompt = f"You are a master of synthesis. Merge these {len(fragments)} fragments into ONE high-fidelity {wisdom_type}."
            user_content = f"Fragments to distill:\n{json.dumps(fragments, indent=2)}\n\nOutput a canonical JSON for a {wisdom_type}."
            
            response = await chat_completion(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=1024
            )
            
            try:
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`").replace("json", "").strip()
                data = json.loads(cleaned)
                return data
            except Exception as e:
                logger.error(f"distillation_synthesis_failed: {e}")
                return {"error": str(e)}

        return async_tool_wrapper(_run)()

# Export tool instances
ingest_wisdom_insight = IngestWisdomInsightTool()
query_wisdom_graph = QueryWisdomGraphTool()
distill_wisdom_cluster = DistillWisdomClusterTool()
