"""
Smolagent tools for agentic KG learning loops.
Feature: 022-agentic-kg-learning
"""

from smolagents import tool
from api.services.kg_learning_service import get_kg_learning_service


@tool
def agentic_kg_extract(content: str, source_id: str) -> str:
    """
    Extract structured knowledge from content using the agentic learning loop.
    This tool uses attractor basins and cognition strategies to get better over time.
    
    Args:
        content: The text content to analyze.
        source_id: Unique identifier for the source (e.g., 'research_paper_01').
    """
    import asyncio
    service = get_kg_learning_service()
    
    # Run async in sync tool
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        result = loop.run_until_complete(service.extract_and_learn(content, source_id))
    else:
        result = asyncio.run(service.extract_and_learn(content, source_id))
        
    summary = f"Extracted {len(result.entities)} entities and {len(result.relationships)} relationships."
    if result.relationships:
        summary += "\nTop Relationships:"
        for rel in result.relationships[:3]:
            summary += f"\n- {rel.source} {rel.relation_type} {rel.target} ({rel.confidence:.2f})"
            
    return summary
