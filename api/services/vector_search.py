"""
Vector Search Service
Feature: 003-semantic-search
Task: T003

Service to execute Neo4j vector similarity queries for semantic memory search.
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from neo4j import AsyncGraphDatabase

from api.services.embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger("dionysus.vector_search")


# =============================================================================
# Configuration
# =============================================================================

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

DEFAULT_TOP_K = 10
DEFAULT_THRESHOLD = 0.7


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SearchFilters:
    """Filters for semantic search."""
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    memory_types: Optional[list[str]] = None


@dataclass
class SearchResult:
    """Single search result."""
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
    """Full search response."""
    query: str
    results: list[SearchResult]
    count: int
    embedding_time_ms: float
    search_time_ms: float
    total_time_ms: float


# =============================================================================
# Vector Search Service
# =============================================================================

class VectorSearchService:
    """
    Service for executing semantic similarity searches against Neo4j.

    Usage:
        service = VectorSearchService()
        results = await service.semantic_search(
            query="rate limiting strategies",
            top_k=10,
            threshold=0.7,
            filters=SearchFilters(project_id="dionysus-core")
        )
    """

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize vector search service.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            embedding_service: Service for generating query embeddings
        """
        self.neo4j_uri = neo4j_uri or NEO4J_URI
        self.neo4j_user = neo4j_user or NEO4J_USER
        self.neo4j_password = neo4j_password or NEO4J_PASSWORD
        self.embedding_service = embedding_service or get_embedding_service()
        self._driver = None

    async def _get_driver(self):
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
        return self._driver

    async def close(self) -> None:
        """Close connections."""
        if self._driver:
            await self._driver.close()
            self._driver = None
        await self.embedding_service.close()

    async def semantic_search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResponse:
        """
        Execute semantic similarity search.

        Args:
            query: Natural language query text
            top_k: Maximum number of results
            threshold: Minimum similarity score (0.0-1.0)
            filters: Optional filters for project, session, date range

        Returns:
            SearchResponse with ranked results
        """
        total_start = time.time()

        # Generate query embedding
        embed_start = time.time()
        query_embedding = await self.embedding_service.generate_embedding(query)
        embedding_time_ms = (time.time() - embed_start) * 1000

        # Execute vector search
        search_start = time.time()
        results = await self._execute_vector_search(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold,
            filters=filters,
        )
        search_time_ms = (time.time() - search_start) * 1000

        total_time_ms = (time.time() - total_start) * 1000

        logger.info(
            f"Semantic search completed in {total_time_ms:.1f}ms",
            extra={
                "query_length": len(query),
                "results_count": len(results),
                "embedding_time_ms": embedding_time_ms,
                "search_time_ms": search_time_ms,
            }
        )

        return SearchResponse(
            query=query,
            results=results,
            count=len(results),
            embedding_time_ms=embedding_time_ms,
            search_time_ms=search_time_ms,
            total_time_ms=total_time_ms,
        )

    async def _execute_vector_search(
        self,
        query_embedding: list[float],
        top_k: int,
        threshold: float,
        filters: Optional[SearchFilters],
    ) -> list[SearchResult]:
        """Execute the Neo4j vector similarity query."""

        # Build dynamic WHERE clause based on filters
        where_clauses = []
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "threshold": threshold,
            "top_k": top_k,
        }

        if filters:
            if filters.project_id:
                where_clauses.append("m.project_id = $project_id")
                params["project_id"] = filters.project_id

            if filters.session_id:
                where_clauses.append("m.session_id = $session_id")
                params["session_id"] = filters.session_id

            if filters.from_date:
                where_clauses.append("m.created_at >= $from_date")
                params["from_date"] = filters.from_date.isoformat()

            if filters.to_date:
                where_clauses.append("m.created_at <= $to_date")
                params["to_date"] = filters.to_date.isoformat()

            if filters.memory_types:
                where_clauses.append("m.memory_type IN $memory_types")
                params["memory_types"] = filters.memory_types

        # Build WHERE clause
        where_filter = " AND ".join(where_clauses) if where_clauses else "true"

        # Neo4j vector similarity query
        cypher_query = f"""
        MATCH (m:Memory)
        WHERE m.embedding IS NOT NULL AND {where_filter}
        WITH m, vector.similarity.cosine(m.embedding, $query_embedding) AS score
        WHERE score >= $threshold
        RETURN
            m.id AS id,
            m.content AS content,
            m.memory_type AS memory_type,
            m.importance AS importance,
            m.session_id AS session_id,
            m.project_id AS project_id,
            m.created_at AS created_at,
            m.tags AS tags,
            score
        ORDER BY score DESC
        LIMIT $top_k
        """

        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(cypher_query, params)
            records = await result.data()

        # Convert to SearchResult objects
        results = []
        for record in records:
            results.append(SearchResult(
                id=record["id"],
                content=record["content"],
                memory_type=record["memory_type"] or "unknown",
                importance=record["importance"] or 0.5,
                similarity_score=record["score"],
                session_id=record.get("session_id"),
                project_id=record.get("project_id"),
                created_at=self._parse_datetime(record.get("created_at")),
                tags=record.get("tags"),
            ))

        return results

    async def search_by_embedding(
        self,
        embedding: list[float],
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD,
        filters: Optional[SearchFilters] = None,
    ) -> list[SearchResult]:
        """
        Search using a pre-computed embedding vector.

        Args:
            embedding: 768-dimensional embedding vector
            top_k: Maximum results
            threshold: Minimum similarity
            filters: Optional filters

        Returns:
            List of search results
        """
        return await self._execute_vector_search(
            query_embedding=embedding,
            top_k=top_k,
            threshold=threshold,
            filters=filters,
        )

    async def find_similar_memories(
        self,
        memory_id: str,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD,
        exclude_self: bool = True,
    ) -> list[SearchResult]:
        """
        Find memories similar to an existing memory.

        Args:
            memory_id: ID of memory to find similar to
            top_k: Maximum results
            threshold: Minimum similarity
            exclude_self: Exclude the source memory from results

        Returns:
            List of similar memories
        """
        driver = await self._get_driver()

        # First get the source memory's embedding
        async with driver.session() as session:
            result = await session.run(
                "MATCH (m:Memory {id: $id}) RETURN m.embedding AS embedding",
                {"id": memory_id}
            )
            record = await result.single()

            if not record or not record["embedding"]:
                return []

            source_embedding = record["embedding"]

        # Now search for similar, optionally excluding source
        cypher_query = """
        MATCH (m:Memory)
        WHERE m.embedding IS NOT NULL
        """ + ("AND m.id <> $exclude_id" if exclude_self else "") + """
        WITH m, vector.similarity.cosine(m.embedding, $embedding) AS score
        WHERE score >= $threshold
        RETURN
            m.id AS id,
            m.content AS content,
            m.memory_type AS memory_type,
            m.importance AS importance,
            m.session_id AS session_id,
            m.project_id AS project_id,
            m.created_at AS created_at,
            m.tags AS tags,
            score
        ORDER BY score DESC
        LIMIT $top_k
        """

        params = {
            "embedding": source_embedding,
            "threshold": threshold,
            "top_k": top_k,
        }
        if exclude_self:
            params["exclude_id"] = memory_id

        async with driver.session() as session:
            result = await session.run(cypher_query, params)
            records = await result.data()

        return [
            SearchResult(
                id=r["id"],
                content=r["content"],
                memory_type=r["memory_type"] or "unknown",
                importance=r["importance"] or 0.5,
                similarity_score=r["score"],
                session_id=r.get("session_id"),
                project_id=r.get("project_id"),
                created_at=self._parse_datetime(r.get("created_at")),
                tags=r.get("tags"),
            )
            for r in records
        ]

    async def hybrid_search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD,
        keyword_weight: float = 0.3,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResponse:
        """
        Execute hybrid search combining keyword and semantic similarity.

        Keyword matches are boosted by keyword_weight, semantic results fill gaps.
        Results are deduplicated and ranked by combined score.

        Args:
            query: Natural language query text
            top_k: Maximum number of results
            threshold: Minimum similarity score (0.0-1.0)
            keyword_weight: Weight for keyword matches (0.0-1.0)
                           0.0 = pure semantic, 1.0 = pure keyword
            filters: Optional filters for project, session, date range

        Returns:
            SearchResponse with ranked, deduplicated results
        """
        total_start = time.time()

        # Generate query embedding
        embed_start = time.time()
        query_embedding = await self.embedding_service.generate_embedding(query)
        embedding_time_ms = (time.time() - embed_start) * 1000

        # Execute hybrid search
        search_start = time.time()
        results = await self._execute_hybrid_search(
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold,
            keyword_weight=keyword_weight,
            filters=filters,
        )
        search_time_ms = (time.time() - search_start) * 1000

        total_time_ms = (time.time() - total_start) * 1000

        logger.info(
            f"Hybrid search completed in {total_time_ms:.1f}ms",
            extra={
                "query_length": len(query),
                "results_count": len(results),
                "keyword_weight": keyword_weight,
            }
        )

        return SearchResponse(
            query=query,
            results=results,
            count=len(results),
            embedding_time_ms=embedding_time_ms,
            search_time_ms=search_time_ms,
            total_time_ms=total_time_ms,
        )

    async def _execute_hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int,
        threshold: float,
        keyword_weight: float,
        filters: Optional[SearchFilters],
    ) -> list[SearchResult]:
        """Execute hybrid keyword + semantic search."""

        # Build WHERE clauses
        where_clauses = []
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "threshold": threshold,
            "top_k": top_k * 2,  # Fetch more, deduplicate later
            "keyword_pattern": f"(?i).*{query.replace(' ', '.*')}.*",
            "query_words": query.lower().split(),
        }

        if filters:
            if filters.project_id:
                where_clauses.append("m.project_id = $project_id")
                params["project_id"] = filters.project_id
            if filters.session_id:
                where_clauses.append("m.session_id = $session_id")
                params["session_id"] = filters.session_id
            if filters.from_date:
                where_clauses.append("m.created_at >= $from_date")
                params["from_date"] = filters.from_date.isoformat()
            if filters.to_date:
                where_clauses.append("m.created_at <= $to_date")
                params["to_date"] = filters.to_date.isoformat()
            if filters.memory_types:
                where_clauses.append("m.memory_type IN $memory_types")
                params["memory_types"] = filters.memory_types

        where_filter = " AND ".join(where_clauses) if where_clauses else "true"

        # Hybrid query: combines vector similarity with keyword matching
        # Uses APOC functions if available, otherwise fallback to basic matching
        cypher_query = f"""
        MATCH (m:Memory)
        WHERE m.embedding IS NOT NULL AND {where_filter}
        WITH m,
             vector.similarity.cosine(m.embedding, $query_embedding) AS semantic_score,
             CASE
                 WHEN ANY(word IN $query_words WHERE toLower(m.content) CONTAINS word)
                 THEN 1.0
                 ELSE 0.0
             END AS keyword_match
        WITH m,
             semantic_score,
             keyword_match,
             // Combined score: weighted average of semantic and keyword
             (semantic_score * (1.0 - $keyword_weight) + keyword_match * $keyword_weight) AS combined_score
        WHERE semantic_score >= $threshold OR keyword_match > 0
        RETURN
            m.id AS id,
            m.content AS content,
            m.memory_type AS memory_type,
            m.importance AS importance,
            m.session_id AS session_id,
            m.project_id AS project_id,
            m.created_at AS created_at,
            m.tags AS tags,
            semantic_score,
            keyword_match,
            combined_score AS score
        ORDER BY combined_score DESC
        LIMIT $top_k
        """
        params["keyword_weight"] = keyword_weight

        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(cypher_query, params)
            records = await result.data()

        # Deduplicate by ID and convert to SearchResult
        seen_ids = set()
        results = []
        for record in records:
            if record["id"] in seen_ids:
                continue
            seen_ids.add(record["id"])

            results.append(SearchResult(
                id=record["id"],
                content=record["content"],
                memory_type=record["memory_type"] or "unknown",
                importance=record["importance"] or 0.5,
                similarity_score=record["score"],
                session_id=record.get("session_id"),
                project_id=record.get("project_id"),
                created_at=self._parse_datetime(record.get("created_at")),
                tags=record.get("tags"),
            ))

            if len(results) >= top_k:
                break

        return results

    async def check_vector_index_exists(self) -> bool:
        """Check if the vector index exists in Neo4j."""
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                "SHOW INDEXES WHERE name = 'memory_embedding_index'"
            )
            records = await result.data()
            return len(records) > 0

    async def health_check(self) -> dict:
        """Check vector search service health."""
        try:
            driver = await self._get_driver()

            # Check Neo4j connection
            async with driver.session() as session:
                result = await session.run("RETURN 1 AS n")
                await result.single()
                neo4j_up = True

            # Check vector index
            index_exists = await self.check_vector_index_exists()

            # Check embedding service
            embedding_health = await self.embedding_service.health_check()

            return {
                "healthy": neo4j_up and index_exists and embedding_health["healthy"],
                "neo4j_url": self.neo4j_uri,
                "neo4j_connected": neo4j_up,
                "vector_index_exists": index_exists,
                "embedding_service": embedding_health,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse datetime from Neo4j value."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None


# =============================================================================
# Global Instance
# =============================================================================

_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    """Get or create global vector search service."""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service
