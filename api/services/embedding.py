"""
Embedding Service
Feature: 003-semantic-search
Task: T002

Service to generate text embeddings via Ollama API for semantic search queries.
Uses nomic-embed-text model (768 dimensions) matching the memory embeddings.
"""

import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger("dionysus.embedding")


# =============================================================================
# Configuration
# =============================================================================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
EMBEDDING_DIMENSIONS = 768
DEFAULT_TIMEOUT = 30.0


# =============================================================================
# Embedding Service
# =============================================================================

class EmbeddingService:
    """
    Service for generating text embeddings via Ollama.

    Usage:
        service = EmbeddingService()
        embedding = await service.generate_embedding("rate limiting strategies")
        # Returns 768-dimensional vector
    """

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize embedding service.

        Args:
            ollama_url: Ollama API URL (default from env)
            model: Embedding model name (default from env)
            timeout: Request timeout in seconds
        """
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model = model or OLLAMA_EMBED_MODEL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")

        start_time = time.time()

        try:
            client = await self._get_client()

            response = await client.post(
                f"{self.ollama_url}/api/embed",
                json={
                    "model": self.model,
                    "input": text,
                }
            )

            response.raise_for_status()
            data = response.json()

            # Ollama returns embeddings in 'embeddings' array (for batch) or 'embedding' (single)
            if "embeddings" in data and len(data["embeddings"]) > 0:
                embedding = data["embeddings"][0]
            elif "embedding" in data:
                embedding = data["embedding"]
            else:
                raise EmbeddingError(f"Unexpected response format: {data.keys()}")

            duration_ms = (time.time() - start_time) * 1000

            # Validate dimensions
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise EmbeddingError(
                    f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)}"
                )

            logger.debug(
                f"Generated embedding in {duration_ms:.1f}ms",
                extra={
                    "text_length": len(text),
                    "dimensions": len(embedding),
                    "duration_ms": duration_ms,
                }
            )

            return embedding

        except httpx.HTTPStatusError as e:
            raise EmbeddingError(f"Ollama API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise EmbeddingError(f"Ollama connection error: {e}") from e
        except Exception as e:
            raise EmbeddingError(f"Embedding generation failed: {e}") from e

    async def generate_embeddings_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Ollama's /api/embed supports batch input
        if not texts:
            return []

        start_time = time.time()

        try:
            client = await self._get_client()

            response = await client.post(
                f"{self.ollama_url}/api/embed",
                json={
                    "model": self.model,
                    "input": texts,
                }
            )

            response.raise_for_status()
            data = response.json()

            embeddings = data.get("embeddings", [])

            if len(embeddings) != len(texts):
                raise EmbeddingError(
                    f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                )

            duration_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"Generated {len(embeddings)} embeddings in {duration_ms:.1f}ms",
                extra={
                    "batch_size": len(texts),
                    "duration_ms": duration_ms,
                }
            )

            return embeddings

        except httpx.HTTPStatusError as e:
            raise EmbeddingError(f"Ollama API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise EmbeddingError(f"Ollama connection error: {e}") from e

    async def check_model_available(self) -> bool:
        """
        Check if the embedding model is available in Ollama.

        Returns:
            True if model is available
        """
        try:
            client = await self._get_client()

            response = await client.get(f"{self.ollama_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            # Check for exact match or model family match
            model_available = any(
                self.model in m or m.startswith(self.model.split(":")[0])
                for m in models
            )

            return model_available

        except Exception as e:
            logger.warning(f"Failed to check model availability: {e}")
            return False

    async def health_check(self) -> dict:
        """
        Check embedding service health.

        Returns:
            Health status dict
        """
        try:
            client = await self._get_client()

            # Check Ollama is running
            response = await client.get(f"{self.ollama_url}/api/tags")
            ollama_up = response.status_code == 200

            # Check model available
            model_available = await self.check_model_available()

            return {
                "healthy": ollama_up and model_available,
                "ollama_url": self.ollama_url,
                "ollama_reachable": ollama_up,
                "model": self.model,
                "model_available": model_available,
                "dimensions": EMBEDDING_DIMENSIONS,
            }

        except Exception as e:
            return {
                "healthy": False,
                "ollama_url": self.ollama_url,
                "error": str(e),
            }


# =============================================================================
# Exceptions
# =============================================================================

class EmbeddingError(Exception):
    """Error during embedding generation."""
    pass


# =============================================================================
# Global Instance
# =============================================================================

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def generate_query_embedding(text: str) -> list[float]:
    """
    Convenience function to generate embedding for a query.

    Args:
        text: Query text

    Returns:
        Embedding vector
    """
    service = get_embedding_service()
    return await service.generate_embedding(text)
