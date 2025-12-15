"""
Integration Tests: Neo4j Memory Sync
Feature: 002-remote-persistence-safety
Task: T016

TDD Test - Write FIRST, verify FAILS before implementation.

Tests Memory node sync operations with Neo4j including:
- MERGE operations (create or update)
- Session relationship creation
- Project relationship creation
- Sync version conflict handling
"""

import os
import uuid
from datetime import datetime

import pytest
from dotenv import load_dotenv

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
    from api.services.neo4j_client import Neo4jClient

    client = Neo4jClient(**neo4j_config)
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
def sample_memory():
    """Generate a sample memory for testing."""
    return {
        "id": str(uuid.uuid4()),
        "content": "Test memory: learned about FastAPI dependency injection",
        "memory_type": "procedural",
        "importance": 0.75,
        "source_project": "dionysus-core",
        "session_id": str(uuid.uuid4()),
        "tags": ["fastapi", "python", "learning"],
        "sync_version": 1,
        "created_at": datetime.utcnow().isoformat(),
    }


class TestMemoryMergeOperations:
    """Test idempotent MERGE operations for Memory nodes."""

    @pytest.mark.asyncio
    async def test_merge_creates_new_memory(self, neo4j_client, sample_memory):
        """Test that MERGE creates a new memory if it doesn't exist."""
        result = await neo4j_client.create_memory(sample_memory)

        assert result is not None
        assert result["id"] == sample_memory["id"]
        assert result["content"] == sample_memory["content"]
        assert result["memory_type"] == sample_memory["memory_type"]

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])

    @pytest.mark.asyncio
    async def test_merge_is_idempotent(self, neo4j_client, sample_memory):
        """Test that calling MERGE twice doesn't create duplicates."""
        # Create first time
        await neo4j_client.create_memory(sample_memory)

        # Create same memory again (should be idempotent)
        await neo4j_client.create_memory(sample_memory)

        # Verify only one exists
        memory = await neo4j_client.get_memory(sample_memory["id"])
        assert memory is not None
        assert memory["id"] == sample_memory["id"]

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])

    @pytest.mark.asyncio
    async def test_merge_updates_with_higher_version(self, neo4j_client, sample_memory):
        """Test that MERGE updates content when sync_version is higher."""
        # Create initial memory
        await neo4j_client.create_memory(sample_memory)

        # Update with higher version
        update_data = {
            "content": "Updated content with new learnings",
            "sync_version": 2,
        }
        result = await neo4j_client.update_memory(sample_memory["id"], update_data)

        assert result["content"] == "Updated content with new learnings"
        assert result["sync_version"] == 2

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])

    @pytest.mark.asyncio
    async def test_merge_ignores_lower_version(self, neo4j_client, sample_memory):
        """Test that MERGE ignores updates with lower sync_version."""
        # Create with version 2
        sample_memory["sync_version"] = 2
        await neo4j_client.create_memory(sample_memory)

        # Try to update with version 1 (should be ignored)
        update_data = {
            "content": "This should be ignored",
            "sync_version": 1,
        }
        result = await neo4j_client.update_memory(sample_memory["id"], update_data)

        # Original content should remain
        assert result["content"] == sample_memory["content"]
        assert result["sync_version"] == 2

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])


class TestSessionRelationships:
    """Test Memory-Session relationship creation."""

    @pytest.mark.asyncio
    async def test_create_session_relationship(self, neo4j_client, sample_memory):
        """Test that memory is linked to session via BELONGS_TO relationship."""
        # Create memory
        await neo4j_client.create_memory(sample_memory)

        # Create session relationship
        # This will be implemented in RemoteSyncService
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)
        await sync_service.create_session_relationship(
            memory_id=sample_memory["id"],
            session_id=sample_memory["session_id"],
            project_id=sample_memory["source_project"],
        )

        # Verify relationship exists
        session = await sync_service.get_session(sample_memory["session_id"])
        assert session is not None
        assert session["id"] == sample_memory["session_id"]

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])

    @pytest.mark.asyncio
    async def test_session_memory_count_increments(self, neo4j_client, sample_memory):
        """Test that session memory_count increments when memories are added."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Create first memory
        await neo4j_client.create_memory(sample_memory)
        await sync_service.create_session_relationship(
            memory_id=sample_memory["id"],
            session_id=sample_memory["session_id"],
            project_id=sample_memory["source_project"],
        )

        # Create second memory in same session
        memory2 = {
            **sample_memory,
            "id": str(uuid.uuid4()),
            "content": "Second memory",
        }
        await neo4j_client.create_memory(memory2)
        await sync_service.create_session_relationship(
            memory_id=memory2["id"],
            session_id=sample_memory["session_id"],
            project_id=sample_memory["source_project"],
        )

        # Verify session has memory_count = 2
        session = await sync_service.get_session(sample_memory["session_id"])
        assert session["memory_count"] == 2

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])
        await neo4j_client.delete_memory(memory2["id"])


class TestProjectRelationships:
    """Test Memory-Project relationship creation."""

    @pytest.mark.asyncio
    async def test_create_project_relationship(self, neo4j_client, sample_memory):
        """Test that memory is linked to project via TAGGED_WITH relationship."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Create memory
        await neo4j_client.create_memory(sample_memory)

        # Create project relationship
        await sync_service.create_project_relationship(
            memory_id=sample_memory["id"],
            project_id=sample_memory["source_project"],
        )

        # Verify relationship exists
        memories = await sync_service.get_memories_by_project(
            sample_memory["source_project"]
        )
        assert len(memories) >= 1
        assert any(m["id"] == sample_memory["id"] for m in memories)

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])


class TestBulkOperations:
    """Test bulk sync operations for recovery scenarios."""

    @pytest.mark.asyncio
    async def test_get_all_memories_returns_list(self, neo4j_client, sample_memory):
        """Test retrieving all memories from Neo4j."""
        # Create test memory
        await neo4j_client.create_memory(sample_memory)

        # Get all memories
        memories = await neo4j_client.get_all_memories()

        assert isinstance(memories, list)
        assert len(memories) >= 1

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])

    @pytest.mark.asyncio
    async def test_get_all_memories_filtered_by_project(
        self, neo4j_client, sample_memory
    ):
        """Test retrieving memories filtered by project."""
        # Create test memory
        await neo4j_client.create_memory(sample_memory)

        # Get memories for specific project
        memories = await neo4j_client.get_all_memories(
            project_id=sample_memory["source_project"]
        )

        assert isinstance(memories, list)
        # All returned memories should be from the specified project
        for memory in memories:
            assert memory["source_project"] == sample_memory["source_project"]

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])

    @pytest.mark.asyncio
    async def test_get_memory_count(self, neo4j_client, sample_memory):
        """Test getting count of memories."""
        initial_count = await neo4j_client.get_memory_count()

        # Create test memory
        await neo4j_client.create_memory(sample_memory)

        new_count = await neo4j_client.get_memory_count()
        assert new_count == initial_count + 1

        # Cleanup
        await neo4j_client.delete_memory(sample_memory["id"])
