"""
Vector Search Service (Webhook-only)
Feature: 003-semantic-search

The application never connects to Neo4j directly. Vector search is executed via n8n
webhooks (which may embed the query and run the Neo4j vector index query).
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from api.services.remote_sync import RemoteSyncService, SyncConfig

logger = logging.getLogger("dionysus.vector_search")

DEFAULT_TOP_K = 10
DEFAULT_THRESHOLD = 0.7


@dataclass
class SearchFilters:
    project_id: Optional[str] = None
    session_id: Optional[str] = None
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
    Webhook-backed vector search.

    Expected n8n payload/response is intentionally flexible:
    - Request: {operation:'vector_search', query, k, threshold, filters}
    - Response: {success:true, results:[...]} or {memories:[...]}.
    """

    def __init__(
        self,
        *,
        sync_service: Optional[RemoteSyncService] = None,
        webhook_url: Optional[str] = None,
    ):
        self._sync = sync_service or RemoteSyncService(
            config=SyncConfig(
                recall_webhook_url=os.getenv(
                    "N8N_VECTOR_SEARCH_URL",
                    os.getenv("N8N_RECALL_URL", "http://localhost:5678/webhook/memory/v1/recall"),
                )
            )
        )
        self._webhook_url = webhook_url or self._sync.config.recall_webhook_url

    async def close(self) -> None:
        return None

    async def health_check(self) -> dict[str, Any]:
        """Check connectivity for the vector search webhook."""
        health = await self._sync.check_health()
        health["vector_search_webhook_url"] = self._webhook_url
        return health

    async def semantic_search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResponse:
        total_start = time.time()

        payload: dict[str, Any] = {
            "operation": "vector_search",
            "query": query,
            "k": top_k,
            "threshold": threshold,
        }

        if filters:
            payload["filters"] = {
                "project_id": filters.project_id,
                "session_id": filters.session_id,
                "from_date": filters.from_date.isoformat() if filters.from_date else None,
                "to_date": filters.to_date.isoformat() if filters.to_date else None,
                "memory_types": filters.memory_types,
            }

        # n8n may do embedding internally; keep metrics placeholders
        embed_ms = 0.0
        search_start = time.time()
        raw = await self._sync._send_to_webhook(payload, webhook_url=self._webhook_url)
        search_ms = (time.time() - search_start) * 1000

        items = raw.get("results") or raw.get("memories") or []
        results: list[SearchResult] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append(
                SearchResult(
                    id=str(item.get("id") or item.get("memory_id") or item.get("message_id") or ""),
                    content=str(item.get("content") or ""),
                    memory_type=str(item.get("memory_type") or item.get("type") or "unknown"),
                    importance=float(item.get("importance") or 0.5),
                    similarity_score=float(item.get("similarity_score") or item.get("score") or 0.0),
                    session_id=item.get("session_id"),
                    project_id=item.get("project_id"),
                    tags=item.get("tags"),
                )
            )

        total_ms = (time.time() - total_start) * 1000
        logger.info(
            "Vector search via n8n completed",
            extra={"query_length": len(query), "results_count": len(results), "total_ms": total_ms},
        )

        return SearchResponse(
            query=query,
            results=results,
            count=len(results),
            embedding_time_ms=embed_ms,
            search_time_ms=search_ms,
            total_time_ms=total_ms,
        )


_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service
