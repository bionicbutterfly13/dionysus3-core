"""
Integration Tests: Neo4j Connectivity
Feature: 002-remote-persistence-safety
Task: T007

TDD Test - Write FIRST, verify FAILS before implementation.

Tests Neo4j driver connection and basic CRUD operations against VPS.
Requires SSH tunnel to VPS Neo4j instance.
"""

import os
import uuid
from datetime import datetime

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Skip all tests if Neo4j is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_PASSWORD"),
    reason="NEO4J_PASSWORD not configured - skipping integration tests",
)


@pytest.fixture
def neo4j_config():
    """Get Neo4j connection configuration."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", ""),
    }


@pytest.fixture
async def neo4j_client(neo4j_config):
    """Create Neo4j client for tests."""
    # This import will fail until T015 implements Neo4jClient
    from api.services.neo4j_client import Neo4jClient

    client = Neo4jClient(
        uri=neo4j_config["uri"],
        user=neo4j_config["user"],
        password=neo4j_config["password"],
    )
    await client.connect()
    yield client
    await client.close()


class TestNeo4jConnection:
    """Test Neo4j connection establishment."""

    @pytest.mark.asyncio
    async def test_can_connect_to_neo4j(self, neo4j_config):
        """Test that we can establish a connection to Neo4j."""
        from api.services.neo4j_client import Neo4jClient

        client = Neo4jClient(**neo4j_config)
        connected = await client.connect()
        assert connected is True
        await client.close()

    @pytest.mark.asyncio
    async def test_connection_returns_server_info(self, neo4j_client):
        """Test that connection provides server information."""
        info = await neo4j_client.get_server_info()
        assert info is not None
        assert "version" in info

    @pytest.mark.asyncio
    async def test_invalid_credentials_raise_error(self, neo4j_config):
        """Test that invalid credentials raise appropriate error."""
        from api.services.neo4j_client import Neo4jClient, Neo4jConnectionError

        bad_config = {**neo4j_config, "password": "wrong-password"}
        client = Neo4jClient(**bad_config)

        with pytest.raises(Neo4jConnectionError):
            await client.connect()


class TestNeo4jCRUD:
    """Test basic CRUD operations on Memory nodes."""

    @pytest.mark.asyncio
    async def test_create_memory_node(self, neo4j_client):
        """Test creating a Memory node in Neo4j."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Test memory content",
            "memory_type": "episodic",
            "importance": 0.5,
            "source_project": "test-project",
            "session_id": str(uuid.uuid4()),
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = await neo4j_client.create_memory(memory_data)
        assert result is not None
        assert result["id"] == memory_id

        # Cleanup
        await neo4j_client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_read_memory_node(self, neo4j_client):
        """Test reading a Memory node from Neo4j."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Test content for reading",
            "memory_type": "semantic",
            "importance": 0.7,
            "source_project": "test-project",
            "session_id": str(uuid.uuid4()),
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

        await neo4j_client.create_memory(memory_data)
        result = await neo4j_client.get_memory(memory_id)

        assert result is not None
        assert result["id"] == memory_id
        assert result["content"] == "Test content for reading"
        assert result["memory_type"] == "semantic"

        # Cleanup
        await neo4j_client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_update_memory_node(self, neo4j_client):
        """Test updating a Memory node in Neo4j."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Original content",
            "memory_type": "procedural",
            "importance": 0.5,
            "source_project": "test-project",
            "session_id": str(uuid.uuid4()),
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

        await neo4j_client.create_memory(memory_data)

        # Update with higher sync_version
        update_data = {
            "content": "Updated content",
            "sync_version": 2,
        }
        result = await neo4j_client.update_memory(memory_id, update_data)

        assert result is not None
        assert result["content"] == "Updated content"
        assert result["sync_version"] == 2

        # Cleanup
        await neo4j_client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_delete_memory_node(self, neo4j_client):
        """Test deleting a Memory node from Neo4j."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Content to be deleted",
            "memory_type": "episodic",
            "importance": 0.3,
            "source_project": "test-project",
            "session_id": str(uuid.uuid4()),
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

        await neo4j_client.create_memory(memory_data)
        deleted = await neo4j_client.delete_memory(memory_id)
        assert deleted is True

        # Verify deletion
        result = await neo4j_client.get_memory(memory_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_memory_returns_none(self, neo4j_client):
        """Test that getting a non-existent memory returns None."""
        fake_id = str(uuid.uuid4())
        result = await neo4j_client.get_memory(fake_id)
        assert result is None


class TestNeo4jSyncVersion:
    """Test sync version conflict resolution."""

    @pytest.mark.asyncio
    async def test_update_with_lower_version_ignored(self, neo4j_client):
        """Test that updates with lower sync_version are ignored."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Version 2 content",
            "memory_type": "episodic",
            "importance": 0.5,
            "source_project": "test-project",
            "session_id": str(uuid.uuid4()),
            "sync_version": 2,  # Start at version 2
            "created_at": datetime.utcnow().isoformat(),
        }

        await neo4j_client.create_memory(memory_data)

        # Try to update with lower version
        update_data = {
            "content": "Version 1 content (should be ignored)",
            "sync_version": 1,
        }
        result = await neo4j_client.update_memory(memory_id, update_data)

        # Content should remain unchanged
        assert result["content"] == "Version 2 content"
        assert result["sync_version"] == 2

        # Cleanup
        await neo4j_client.delete_memory(memory_id)

    @pytest.mark.asyncio
    async def test_update_with_higher_version_succeeds(self, neo4j_client):
        """Test that updates with higher sync_version succeed."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Version 1 content",
            "memory_type": "episodic",
            "importance": 0.5,
            "source_project": "test-project",
            "session_id": str(uuid.uuid4()),
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

        await neo4j_client.create_memory(memory_data)

        # Update with higher version
        update_data = {
            "content": "Version 3 content",
            "sync_version": 3,
        }
        result = await neo4j_client.update_memory(memory_id, update_data)

        assert result["content"] == "Version 3 content"
        assert result["sync_version"] == 3

        # Cleanup
        await neo4j_client.delete_memory(memory_id)
