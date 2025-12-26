"""
Shared Pytest Configuration and Fixtures
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator

# =============================================================================
# Async Support
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create session-wide event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# =============================================================================
# API Fixtures
# =============================================================================

@pytest.fixture
async def client():
    """Async client for integration testing."""
    from httpx import AsyncClient
    from api.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac