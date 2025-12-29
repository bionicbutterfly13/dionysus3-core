"""
Class-based tools for agentic KG learning loops.
Feature: 022-agentic-kg-learning
Tasks: T4.1, T4.2
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.kg_learning_service import get_kg_learning_service
from api.agents.resource_gate import async_tool_wrapper

class KGRelationship(BaseModel):
    source: str
    target: str
    relation_type: str
    confidence: float

class KGExtractionOutput(BaseModel):
    success: bool = Field(..., description="Whether the extraction was successful")
    entity_count: int = Field(..., description="Number of entities extracted")
    relationship_count: int = Field(..., description="Number of relationships extracted")
    top_relationships: List[KGRelationship] = Field(..., description="Details of the most confident relationships")
    summary: str = Field(..., description="Textual overview of the extraction result")
    error: Optional[str] = Field(None, description="Error message if extraction failed")

class AgenticKGExtractTool(Tool):
    name = "agentic_kg_extract"
    description = "Extract structured knowledge from content using the agentic learning loop."
    
    inputs = {
        "content": {
            "type": "string",
            "description": "The text content to analyze."
        },
        "source_id": {
            "type": "string",
            "description": "Unique identifier for the source (e.g., 'research_paper_01')."
        }
    }
    output_type = "any"

    def forward(self, content: str, source_id: str) -> dict:
        async def _extract():
            service = get_kg_learning_service()
            return await service.extract_and_learn(content, source_id)

        try:
            result = async_tool_wrapper(_extract)()
            
            top_rels = [
                KGRelationship(
                    source=rel.source,
                    target=rel.target,
                    relation_type=rel.relation_type,
                    confidence=rel.confidence
                ) for rel in result.relationships[:5]
            ]
            
            summary = f"Extracted {len(result.entities)} entities and {len(result.relationships)} relationships."
            
            output = KGExtractionOutput(
                success=True,
                entity_count=len(result.entities),
                relationship_count=len(result.relationships),
                top_relationships=top_rels,
                summary=summary
            )
            return output.model_dump()
            
        except Exception as e:
            return KGExtractionOutput(
                success=False,
                entity_count=0,
                relationship_count=0,
                top_relationships=[],
                summary="Extraction failed",
                error=str(e)
            ).model_dump()

@tool(structured_output=True)
def evaluate_kg_extraction(extraction_json: str, ground_truth: str) -> dict:
    """
    Evaluate the quality of a Knowledge Graph extraction against ground truth.
    Provides mathematical precision/recall proxies and learning signals.
    
    Args:
        extraction_json: The JSON string of the ExtractionResult to evaluate.
        ground_truth: The raw text or ground truth used for comparison.
    """
    from api.agents.resource_gate import async_tool_wrapper
    from api.models.kg_learning import ExtractionResult
    
    async def _eval():
        service = get_kg_learning_service()
        data = json.loads(extraction_json)
        extraction = ExtractionResult(**data)
        return await service.evaluate_extraction(extraction, ground_truth)

    return async_tool_wrapper(_eval)()


@tool
def agentic_kg_extract(content: str, source_id: str) -> str: