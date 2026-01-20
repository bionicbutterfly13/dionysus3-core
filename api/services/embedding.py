"""
Embedding Service
Feature: 003-semantic-search
Task: T002

Service to generate text embeddings via Ollama or OpenAI, depending on config.
Defaults to Ollama (nomic-embed-text, 768 dims) unless EMBEDDINGS_PROVIDER is set.
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

EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "ollama").lower()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
_DEFAULT_DIMENSIONS = 1536 if EMBEDDINGS_PROVIDER == "openai" else 768
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIM", str(_DEFAULT_DIMENSIONS)))
DEFAULT_TIMEOUT = 30.0


# =============================================================================
# Embedding Service
# =============================================================================

class EmbeddingService:
    """
    Service for generating text embeddings via the configured provider.

    Usage:
        service = EmbeddingService()
        embedding = await service.generate_embedding("rate limiting strategies")
        # Returns provider-specific embedding dimensions
    """

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        provider: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
    ):
        """
        Initialize embedding service.

        Args:
            ollama_url: Ollama API URL (default from env)
            model: Embedding model name (default from env)
            timeout: Request timeout in seconds
            provider: Embedding provider ("ollama" or "openai")
            openai_api_key: OpenAI API key (if provider is openai)
            openai_model: OpenAI embedding model (if provider is openai)
        """
        self.provider = (provider or EMBEDDINGS_PROVIDER).lower()
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model = model or OLLAMA_EMBED_MODEL
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_model = openai_model or OPENAI_EMBED_MODEL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._openai_client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for Ollama."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _get_openai_client(self):
        """Get or create OpenAI client."""
        if self._openai_client is None:
            from openai import AsyncOpenAI

            self._openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        return self._openai_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        if self._openai_client is not None:
            try:
                await self._openai_client.close()
            except Exception:
                pass
            self._openai_client = None

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")

        start_time = time.time()

        try:
            if self.provider == "openai":
                if not self.openai_api_key:
                    raise EmbeddingError("OPENAI_API_KEY is required for OpenAI embeddings")
                client = await self._get_openai_client()
                response = await client.embeddings.create(
                    model=self.openai_model,
                    input=text,
                )
                if not response.data:
                    raise EmbeddingError("OpenAI returned no embedding data")
                embedding = response.data[0].embedding
            else:
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
            if self.provider == "openai":
                if not self.openai_api_key:
                    raise EmbeddingError("OPENAI_API_KEY is required for OpenAI embeddings")
                client = await self._get_openai_client()
                response = await client.embeddings.create(
                    model=self.openai_model,
                    input=texts,
                )
                embeddings = [item.embedding for item in response.data]
            else:
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
        if self.provider == "openai":
            api_key_present = bool(self.openai_api_key)
            return {
                "healthy": api_key_present,
                "provider": "openai",
                "model": self.openai_model,
                "dimensions": EMBEDDING_DIMENSIONS,
                "openai_api_key_present": api_key_present,
            }

        try:
            client = await self._get_client()

            # Check Ollama is running
            response = await client.get(f"{self.ollama_url}/api/tags")
            ollama_up = response.status_code == 200

            # Check model available
            model_available = await self.check_model_available()

            return {
                "healthy": ollama_up and model_available,
                "provider": "ollama",
                "ollama_url": self.ollama_url,
                "ollama_reachable": ollama_up,
                "model": self.model,
                "model_available": model_available,
                "dimensions": EMBEDDING_DIMENSIONS,
            }

        except Exception as e:
            return {
                "healthy": False,
                "provider": self.provider,
                "ollama_url": self.ollama_url,
                "error": str(e),
            }


    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        """
        if text1 == text2:
            return 1.0
            
        embeddings = await self.generate_embeddings_batch([text1, text2])
        v1, v2 = embeddings[0], embeddings[1]

        # Cosine similarity for arbitrary vectors
        import numpy as np
        denom = float(np.linalg.norm(v1) * np.linalg.norm(v2))
        if denom == 0.0:
            return 0.0
        return float(np.dot(v1, v2) / denom)

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
