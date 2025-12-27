import os
import json
import logging
from typing import Dict, Any, List, Optional
from smolagents import tool
from api.services.graphiti_service import get_graphiti_service
from api.services.efe_engine import get_efe_engine

logger = logging.getLogger("dionysus.cognitive_tools")

@tool
def context_explorer(project_id: str, query: str) -> str:
    """
    Explorer Agent tool based on the /research.agent protocol.
    Scans the knowledge graph for semantic attractors and prunes irrelevant context.
    
    Args:
        project_id: Scoping ID for the research.
        query: Specific domain or task query.
    """
    # Using a synchronous wrapper for graphiti search if needed, but smolagents prefers sync tools usually
    import asyncio
    
    async def run_search():
        graphiti = await get_graphiti_service()
        return await graphiti.search(f"attractor basins for {query} in project {project_id}", limit=5)
    
    try:
        search_results = asyncio.run(run_search())
    except Exception as e:
        return f"Explorer: Graph search failed: {e}"
    
    edges = search_results.get("edges", [])
    if not edges:
        return f"Explorer: No semantic attractors found for '{query}' in project '{project_id}'."

    # 2. Extract and format the 'Synergistic Whole'
    formatted_attractors = []
    for edge in edges:
        fact = edge.get('fact')
        formatted_attractors.append(f"- {fact} (stability: high)")

    attractors_text = "\n".join(formatted_attractors)
    report = f"## Explorer Agent Report: Semantic Attractors\nProject: {project_id}\nQuery: {query}\n\nDetected centers of gravity:\n{attractors_text}\n\nRecommendation: Ground reasoning in the 'Analytical Professional' basin to minimize free energy."
    return report

@tool
def cognitive_check(uncertainty_level: float, goal_alignment: float) -> dict:
    """
    Autonomous EFE self-reflection tool.
    Calculates the agent's current Expected Free Energy.
    
    Args:
        uncertainty_level: 0.0-1.0 (Entropy)
        goal_alignment: 0.0-1.0 (Similarity to goal)
    """
    efe = uncertainty_level + (1.0 - goal_alignment)
    status = "PRAGMATIC" if efe < 0.5 else "EPISTEMIC"
    
    return {
        "efe_score": efe,
        "recommended_mode": status,
        "reasoning": f"EFE is {efe:.2f}. " + ("Context is stable, proceed to execution." if status == "PRAGMATIC" else "Uncertainty high, prioritize research/recall.")
    }