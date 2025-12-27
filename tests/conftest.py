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
    from httpx import AsyncClient, ASGITransport
    from api.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac