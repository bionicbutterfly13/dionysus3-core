"""
Vector Search Service (MemEvolve-backed)
Feature: 003-semantic-search

The application routes through MemEvolve, which uses Graphiti as the sole Neo4j gateway.
This replaces the legacy n8n webhook implementation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from api.models.memevolve import MemoryRecallRequest
from api.services.memevolve_adapter import get_memevolve_adapter

logger = logging.getLogger("dionysus.vector_search")

DEFAULT_TOP_K = 10
DEFAULT_THRESHOLD = 0.7


@dataclass
@dataclass
class SearchFilters:
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    memory_types: Optional[list[str]] = None


@dataclass
class SearchResult:
    id: str
    content: str
    memory_type: str
    importance: float
    similarity_score: float
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    tags: Optional[list[str]] = None


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    count: int
    embedding_time_ms: float
    search_time_ms: float
    total_time_ms: float


class VectorSearchService:
    """
    MemEvolve-backed vector search service.
    
    Features:
    - MemEvolve routing through Graphiti gateway (no direct Neo4j access)
    - Hybrid search (semantic + graph)
    - Dynamic retrieval strategy
    """

    def __init__(self):
        pass

    async def close(self) -> None:
        return None

    async def health_check(self) -> dict[str, Any]:
        """Check connectivity via MemEvolve adapter."""
        try:
            adapter = get_memevolve_adapter()
            await adapter.execute_cypher("RETURN 1 AS status", {})
            return {"healthy": True, "backend": "memevolve"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _get_latest_strategy(self) -> dict[str, Any]:
        """Fetch the latest RetrievalStrategy node from Neo4j (T006)."""
        cypher = "MATCH (s:RetrievalStrategy) RETURN s ORDER BY s.created_at DESC LIMIT 1"
        try:
            adapter = get_memevolve_adapter()
            records = await adapter.execute_cypher(cypher)
            
            if records:
                # Graphiti returns records as dicts directly
                # Access 's' from the record dict
                strategy = records[0].get('s', {})
                return {
                    "top_k": int(strategy.get("top_k", DEFAULT_TOP_K)),
                    "threshold": float(strategy.get("threshold", DEFAULT_THRESHOLD)),
                    "id": strategy.get("id")
                }
        except Exception as e:
            logger.warning(f"Failed to fetch latest retrieval strategy: {e}")
        
        return {"top_k": DEFAULT_TOP_K, "threshold": DEFAULT_THRESHOLD}

    async def semantic_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResponse:
        total_start = time.time()

        # T006: Always use latest evolved strategy if specific overrides not provided
        if top_k is None or threshold is None:
            strategy = await self._get_latest_strategy()
            top_k = top_k or strategy["top_k"]
            threshold = threshold or strategy["threshold"]
            # logger.info(f"Using strategy: {strategy.get('id', 'default')} (k={top_k}, t={threshold})")

        # Start search timer
        search_start = time.time()
        
        try:
            adapter = get_memevolve_adapter()
            recall = await adapter.recall_memories(
                MemoryRecallRequest.model_construct(
                    query=query,
                    limit=top_k,
                    project_id=filters.project_id if filters else None,
                    session_id=filters.session_id if filters else None,
                    device_id=filters.device_id if filters else None,
                    memory_types=filters.memory_types if filters else None,
                    include_temporal_metadata=False,
                )
            )
            items = recall.get("memories", [])
            
        except Exception as e:
            logger.error(f"MemEvolve search failed: {e}")
            items = []

        search_ms = (time.time() - search_start) * 1000

        results: list[SearchResult] = []
        for item in items:
            content = str(item.get("content") or "")
            similarity = float(item.get("similarity", 0.0))
            
            results.append(
                SearchResult(
                    id=str(item.get("id", "")),
                    content=content,
                    memory_type=item.get("type") or "semantic",
                    importance=float(item.get("importance", 0.5)),
                    similarity_score=similarity,
                    session_id=item.get("session_id"),
                    project_id=item.get("project_id"),
                    created_at=None,
                    tags=item.get("tags", []),
                )
            )

        total_ms = (time.time() - total_start) * 1000
        
        return SearchResponse(
            query=query,
            results=results,
            count=len(results),
            embedding_time_ms=0.0, # Handled internally by Graphiti
            search_time_ms=search_ms,
            total_time_ms=total_ms,
        )


_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service
