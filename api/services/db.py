"""
Database pool management.

Provides a shared asyncpg pool for services that need direct SQL access.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


def _build_database_url() -> str:
    """Get DATABASE_URL from environment. Raises if not set."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable required. "
            "For VPS: start SSH tunnel then set DATABASE_URL=postgresql://dionysus:PASSWORD@localhost:5432/dionysus"
        )
    return url


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the shared database connection pool."""
    global _pool
    if _pool is None:
        database_url = _build_database_url()
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("Database pool created")
    return _pool


async def close_db_pool() -> None:
    """Close the shared database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")
