"""
Voice and Wisdom Research Tools

smolagents tools that use Graphiti for learning voice, processes, and evolution.
"""

import logging
from typing import Optional

from api.agents.tools.wisdom_tools import ingest_wisdom_insight, query_wisdom_graph

logger = logging.getLogger(__name__)

# The following functions are kept for direct API usage if needed
def run_sync(coro):
    """Helper to run async coroutines in a synchronous context."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)