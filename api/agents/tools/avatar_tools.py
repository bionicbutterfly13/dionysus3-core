"""
Class-based tools for Avatar Research.
Feature: 019-avatar-knowledge-graph
Tasks: T4.1, T4.2
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.models.avatar import InsightType
from api.services.graphiti_service import get_graphiti_service
from api.agents.resource_gate import async_tool_wrapper

logger = logging.getLogger(__name__)

class AvatarInsightOutput(BaseModel):
    success: bool = Field(..., description="Whether the ingestion was successful")
    insight_type: str = Field(..., description="The type of insight extracted")
    extracted: Dict[str, Any] = Field(..., description="The structured data extracted")
    source: str = Field(..., description="The source of the insight")
    graph_nodes: int = Field(0, description="Number of nodes created in the graph")
    graph_edges: int = Field(0, description="Number of edges created in the graph")
    error: Optional[str] = Field(None, description="Error message if success is False")

class IngestAvatarInsightTool(Tool):
    name = "ingest_avatar_insight"
    description = "Extract and persist a structured avatar insight to the knowledge graph."
    
    inputs = {
        "content": {
            "type": "string", 
            "description": "Raw text containing the insight (quote, description, observation)"
        },
        "insight_type": {
            "type": "string", 
            "description": "Type of insight - one of: pain_point, objection, desire, belief, behavior, voice_pattern, failed_solution"
        },
        "source": {
            "type": "string", 
            "description": "Source document or context for this insight",
            "nullable": True
        }
    }
    output_type = "any" # We return a dict from model_dump()

    def setup(self):
        """Called once before first use."""
        # Note: We don't initialize graphiti here because it needs an event loop.
        # We use get_graphiti_service() inside the forward method.
        pass

    def forward(self, content: str, insight_type: str, source: Optional[str] = "unknown") -> dict:
        # 1. Validate insight type
        valid_types = [t.value for t in InsightType]
        if insight_type not in valid_types:
            return AvatarInsightOutput(
                success=False,
                insight_type=insight_type,
                extracted={},
                source=source,
                error=f"Invalid insight_type. Must be one of: {valid_types}"
            ).model_dump()

        async def _run():
            from api.agents.knowledge.tools import openai_chat_completion
            
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

            graphiti = None
            try:
                response = await openai_chat_completion(
                    messages=[{"role": "user", "content": f"Extract {insight_type} from:\n\n{content}"}],
                    system_prompt=system_prompt,
                    model="gpt-5-nano",
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

                return AvatarInsightOutput(
                    success=True,
                    insight_type=insight_type,
                    extracted=extracted,
                    source=source,
                    graph_nodes=len(result.get("nodes", [])),
                    graph_edges=len(result.get("edges", [])),
                )

            except Exception as e:
                logger.error(f"Avatar insight extraction failed: {e}")
                return AvatarInsightOutput(
                    success=False,
                    insight_type=insight_type,
                    extracted={},
                    source=source,
                    error=str(e)
                )
            finally:
                if graphiti:
                    await graphiti.close()

        # Run via isolated loop
        result_obj = async_tool_wrapper(_run)()
        return result_obj.model_dump()

class AvatarGraphQueryOutput(BaseModel):
    query: str = Field(..., description="The original search query")
    results: List[Dict[str, Any]] = Field(..., description="List of matching graph edges/facts")
    count: int = Field(..., description="Number of results found")
    error: Optional[str] = Field(None, description="Error message if query failed")

class QueryAvatarGraphTool(Tool):
    name = "query_avatar_graph"
    description = "Query the avatar knowledge graph using semantic search with graph traversal."
    
    inputs = {
        "query": {
            "type": "string",
            "description": "Natural language query about the avatar (e.g., 'What pain points relate to identity?')"
        },
        "insight_types": {
            "type": "string",
            "description": "Optional comma-separated filter (e.g., 'pain_point,objection')",
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
        async def _run():
            from api.agents.knowledge.tools import async_query_avatar_graph
            return await async_query_avatar_graph(query, insight_types, limit)

        result_dict = async_tool_wrapper(_run)()
        # Map to Pydantic for validation and consistency
        output = AvatarGraphQueryOutput(**result_dict)
        return output.model_dump()

class AvatarProfileOutput(BaseModel):
    archetype: str = Field(..., description="The synthesized avatar archetype")
    synthesized_at: str = Field(..., description="Timestamp of synthesis")
    dimensions: Dict[str, Any] = Field(..., description="Insights organized by dimension")
    total_insights: int = Field(..., description="Total number of insights found")
    error: Optional[str] = Field(None, description="Error message if synthesis failed")

class SynthesizeAvatarProfileTool(Tool):
    name = "synthesize_avatar_profile"
    description = "Synthesize a comprehensive avatar profile from all graph data."
    
    inputs = {
        "dimensions": {
            "type": "string",
            "description": "Comma-separated dimensions to include, or 'all' for everything.",
            "default": "all",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, dimensions: str = "all") -> dict:
        async def _run():
            from api.agents.knowledge.tools import run_sync
            # We wrap the existing logic
            graphiti = None
            try:
                graphiti = await get_graphiti_service()
                all_dims = ["pain_point", "objection", "desire", "belief", "behavior", "voice_pattern", "failed_solution"]
                dims_to_query = all_dims if dimensions == "all" else [d.strip() for d in dimensions.split(",") if d.strip() in all_dims]

                profile = {
                    "archetype": "Analytical Empath",
                    "synthesized_at": datetime.utcnow().isoformat(),
                    "dimensions": {},
                }
                total_insights = 0
                for dim in dims_to_query:
                    results = await graphiti.search(query=f"avatar {dim}", group_ids=["avatar_research"], limit=20)
                    edges = results.get("edges", [])
                    profile["dimensions"][dim] = {"count": len(edges), "items": [{"fact": e.get("fact"), "valid_at": e.get("valid_at")} for e in edges]}
                    total_insights += len(edges)
                profile["total_insights"] = total_insights
                return AvatarProfileOutput(**profile)
            except Exception as e:
                return AvatarProfileOutput(archetype="unknown", synthesized_at="", dimensions={}, total_insights=0, error=str(e))
            finally:
                if graphiti: await graphiti.close()

        result_obj = async_tool_wrapper(_run)()
        return result_obj.model_dump()

class BulkIngestOutput(BaseModel):
    success: bool = Field(..., description="Whether the bulk ingestion was successful")
    document: str = Field(..., description="Path to the ingested document")
    document_type: str = Field(..., description="Type of the document")
    insights_found: int = Field(..., description="Number of insights identified by LLM")
    insights_stored: int = Field(..., description="Number of insights successfully stored in graph")
    by_type: Dict[str, int] = Field(..., description="Counts of insights by type")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class BulkIngestDocumentTool(Tool):
    name = "bulk_ingest_document"
    description = "Bulk ingest a document and extract all avatar insights."
    
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to the document (markdown file)"
        },
        "document_type": {
            "type": "string",
            "description": "Type of document - copy_brief, email, interview, review",
            "default": "copy_brief",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, file_path: str, document_type: str = "copy_brief") -> dict:
        async def _run():
            from api.agents.knowledge.tools import openai_chat_completion
            graphiti = None
            try:
                with open(file_path, 'r') as f: content = f.read()
                system_prompt = """You are an avatar research analyst. Analyze this document and extract ALL avatar insights.
For each insight found, output a JSON object on its own line with this structure:
{"type": "pain_point|objection|desire|belief|behavior|voice_pattern|failed_solution", "content": "the relevant text", "extracted": {structured data}}
Extract as many insights as you can find. Be thorough."""
                response = await openai_chat_completion(messages=[{"role": "user", "content": f"Document ({document_type}):\n\n{content}"}], system_prompt=system_prompt, model="gpt-5-nano", max_tokens=4096)
                insights = []
                for line in response.strip().split("\n"):
                    line = line.strip()
                    if line.startswith("{") and line.endswith("}"):
                        try: insights.append(json.loads(line))
                        except: continue
                graphiti = await get_graphiti_service()
                stored_count, by_type = 0, {}
                for insight in insights:
                    it = insight.get("type", "unknown")
                    by_type[it] = by_type.get(it, 0) + 1
                    episode_content = f"Avatar Insight ({it}): {json.dumps(insight.get('extracted', insight))}\nSource: {file_path}"
                    try:
                        await graphiti.ingest_message(content=episode_content, source_description=f"bulk_ingest:{document_type}", group_id="avatar_research")
                        stored_count += 1
                    except: continue
                return BulkIngestOutput(success=True, document=file_path, document_type=document_type, insights_found=len(insights), insights_stored=stored_count, by_type=by_type)
            except Exception as e:
                return BulkIngestOutput(success=False, document=file_path, document_type=document_type, insights_found=0, insights_stored=0, by_type={}, error=str(e))
            finally:
                if graphiti: await graphiti.close()

        result_obj = async_tool_wrapper(_run)()
        return result_obj.model_dump()

# Export tool instances
ingest_avatar_insight = IngestAvatarInsightTool()
query_avatar_graph = QueryAvatarGraphTool()
synthesize_avatar_profile = SynthesizeAvatarProfileTool()
bulk_ingest_document = BulkIngestDocumentTool()
