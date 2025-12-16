# Copyright 2025 Dionysus Project
# SPDX-License-Identifier: Apache-2.0

"""
Shared pytest fixtures for all tests.

Provides:
- db_pool: asyncpg connection pool for database tests
- cleanup utilities for test isolation
"""

import os

import pytest
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dionysus:dionysus2024@localhost:5432/dionysus"
)


@pytest.fixture(scope="session")
async def db_pool():
    """
    Create database connection pool for tests.

    Scope: session (one pool shared across all tests)
    """
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest.fixture
async def cleanup_mental_models(db_pool):
    """
    Cleanup mental model test data before and after each test.

    Uses test-prefixed UUIDs to avoid deleting production data.
    """
    test_uuid_prefix = "00000000-0000-0000-0000"

    async def cleanup():
        async with db_pool.acquire() as conn:
            # Clean up in dependency order
            await conn.execute(
                """
                DELETE FROM worldview_prediction_errors
                WHERE model_id IN (
                    SELECT id FROM mental_models
                    WHERE name LIKE 'Test%' OR name LIKE 'test%'
                )
                """
            )
            await conn.execute(
                """
                DELETE FROM model_worldview_links
                WHERE model_id IN (
                    SELECT id FROM mental_models
                    WHERE name LIKE 'Test%' OR name LIKE 'test%'
                )
                """
            )
            await conn.execute(
                """
                DELETE FROM model_identity_links
                WHERE model_id IN (
                    SELECT id FROM mental_models
                    WHERE name LIKE 'Test%' OR name LIKE 'test%'
                )
                """
            )
            await conn.execute(
                """
                DELETE FROM model_revisions
                WHERE model_id IN (
                    SELECT id FROM mental_models
                    WHERE name LIKE 'Test%' OR name LIKE 'test%'
                )
                """
            )
            await conn.execute(
                """
                DELETE FROM model_predictions
                WHERE model_id IN (
                    SELECT id FROM mental_models
                    WHERE name LIKE 'Test%' OR name LIKE 'test%'
                )
                """
            )
            await conn.execute(
                """
                DELETE FROM mental_models
                WHERE name LIKE 'Test%' OR name LIKE 'test%'
                """
            )
            await conn.execute(
                """
                DELETE FROM worldview_primitives
                WHERE category LIKE 'test%' OR category LIKE 'Test%'
                """
            )
            await conn.execute(
                """
                DELETE FROM identity_aspects
                WHERE content LIKE 'Test%' OR content LIKE 'test%'
                """
            )

    # Cleanup before test
    await cleanup()
    yield
    # Cleanup after test
    await cleanup()
