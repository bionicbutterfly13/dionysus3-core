"""
Nemori Hybrid Recall Service (Feature 041, T031-T032)

Implements the k/m retrieval ratio from the Nemori framework:
- k episodes (episodic memory)
- m semantic memories (semantic memory)

Features:
- Top-2 episodes include full narrative context
- Remaining episodes include titles/summaries only
- Benchmarks against standard retrieval
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from api.models.autobiographical import DevelopmentEpisode
from api.services.vector_search import get_vector_search_service, SearchFilters
from api.agents.consolidated_memory_stores import get_consolidated_memory_store

logger = logging.getLogger("dionysus.nemori_recall")

class NemoriRecallService:
    """
    Orchestrates hybrid retrieval using the k/m ratio.
    """
    
    def __init__(self, k: int = 10, m: int = 20):
        self.k = k
        self.m = m
        self.store = get_consolidated_memory_store()
        self.vector_search = get_vector_search_service()

    async def recall_with_nemori_ratio(
        self,
        query: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        k_override: Optional[int] = None,
        m_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid recall with k episodic and m semantic results.
        
        T041-032: Implement k/m retrieval ratio.
        """
        start_time = time.time()
        k = k_override or self.k
        m = m_override or self.m
        
        # 1. Episodic Recall (k results)
        episodes = await self.store.search_episodes(
            query=query,
            limit=k,
            group_ids=[project_id] if project_id else None
        )
        
        # 2. Semantic Recall (m results)
        filters = SearchFilters(project_id=project_id, session_id=session_id)
        semantic_response = await self.vector_search.semantic_search(
            query=query,
            top_k=m,
            filters=filters
        )
        
        # 3. Format context (Top-2 full, rest abbreviated)
        formatted_context = self._format_nemori_context(episodes, semantic_response.results)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        return {
            "formatted_context": formatted_context,
            "episodes_count": len(episodes),
            "semantic_count": len(semantic_response.results),
            "total_time_ms": round(total_time_ms, 2),
            "ratio": f"{len(episodes)}/{len(semantic_response.results)}"
        }

    def _format_nemori_context(
        self, 
        episodes: List[DevelopmentEpisode], 
        semantic_results: List[Any]
    ) -> str:
        """
        Format the context string per Nemori specs.
        """
        lines = ["# RECALLED CONTEXT (Nemori k/m Hybrid)"]
        
        # Episodic Section
        if episodes:
            lines.append(f"\n## Episodic Memories (k={len(episodes)})")
            for i, ep in enumerate(episodes):
                if i < 2: # Top-2 full context
                    lines.append(f"\n### [FULL] {ep.title} ({ep.start_time.date()})")
                    lines.append(f"Summary: {ep.summary}")
                    lines.append(f"Narrative: {ep.narrative}")
                    lines.append(f"Archetype: {ep.dominant_archetype.value if ep.dominant_archetype else 'None'}")
                else: # Rest abbreviated
                    lines.append(f"- {ep.title}: {ep.summary[:150]}...")
        
        # Semantic Section
        if semantic_results:
            lines.append(f"\n## Semantic Knowledge (m={len(semantic_results)})")
            for res in semantic_results:
                lines.append(f"- {res.content}")
                
        return "\n".join(lines)

# Singleton
_instance: Optional[NemoriRecallService] = None

def get_nemori_recall_service() -> NemoriRecallService:
    global _instance
    if _instance is None:
        _instance = NemoriRecallService()
    return _instance
