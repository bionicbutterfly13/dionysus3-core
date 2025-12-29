"""
Avatar Knowledge Graph Tools

smolagents tools that use Graphiti for avatar research.
Feature: 019-avatar-knowledge-graph
"""

import os
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from smolagents import tool
from openai import AsyncOpenAI

from api.models.avatar import InsightType, AvatarInsight
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)

# OpenAI client for extraction (Anthropic credits exhausted)
_openai_client = None

def get_openai_client() -> AsyncOpenAI:
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


async def openai_chat_completion(
    messages: list[dict],
    system_prompt: str,
    model: str = "gpt-5-nano",
    max_tokens: int = 1024
) -> str:
    """OpenAI-based completion for extraction."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=model,
        max_completion_tokens=max_tokens,  # gpt-5 uses max_completion_tokens
        messages=[{"role": "system", "content": system_prompt}] + messages,
    )
    return response.choices[0].message.content

def run_sync(coro):
    """Helper to run async coroutines in a synchronous context."""
    # Always create a new event loop to avoid cross-loop issues
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

from api.agents.tools.avatar_tools import (
    ingest_avatar_insight, 
    query_avatar_graph, 
    synthesize_avatar_profile, 
    bulk_ingest_document
)

# The following functions are kept for direct API usage if needed
async def async_query_avatar_graph(query: str, insight_types: Optional[str] = None, limit: int = 10) -> dict:
    """
    Async version for use in async contexts (e.g., FastAPI endpoints).
    """
    graphiti = None
    try:
        graphiti = await get_graphiti_service()

        # Search with avatar research group
        results = await graphiti.search(
            query=query,
            group_ids=["avatar_research"],
            limit=limit,
        )

        edges = results.get("edges", [])

        # Filter by insight types if specified
        if insight_types:
            type_list = [t.strip() for t in insight_types.split(",")]
            edges = [
                e for e in edges
                if any(t in str(e.get("fact", "")) for t in type_list)
            ]

        return {
            "query": query,
            "results": edges,
            "count": len(edges),
        }

    except Exception as e:
        logger.error(f"Avatar graph query failed: {e}")
        return {"query": query, "results": [], "count": 0, "error": str(e)}
    finally:
        if graphiti:
            await graphiti.close()
