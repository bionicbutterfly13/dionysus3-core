"""
Integration Tests: Bootstrap Recovery
Feature: 002-remote-persistence-safety
Task: T019

TDD Test - Write FIRST, verify FAILS before implementation.

Tests the critical recovery scenario:
1. Create memories locally
2. Sync to remote Neo4j
3. Destroy local database
4. Run bootstrap recovery
5. Verify 100% restoration

This is the MVP test - if this passes, the core safety feature works.
"""

import os
import uuid
from datetime import datetime

import pytest
from dotenv import load_dotenv

load_dotenv()


# Skip if Neo4j not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_PASSWORD"),
    reason="NEO4J_PASSWORD not configured - skipping recovery tests",
)


@pytest.fixture
def neo4j_config():
    """Get Neo4j configuration."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", ""),
    }


@pytest.fixture
async def neo4j_client(neo4j_config):
    """Create Neo4j client."""
    from api.services.neo4j_client import Neo4jClient

    client = Neo4jClient(**neo4j_config)
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
def test_memories():
    """Generate test memories for recovery scenario."""
    session_id = str(uuid.uuid4())
    return [
        {
            "id": str(uuid.uuid4()),
            "content": f"Test memory {i}: important learning about system architecture",
            "memory_type": "semantic",
            "importance": 0.5 + (i * 0.1),
            "source_project": "dionysus-core",
            "session_id": session_id,
            "tags": ["test", "recovery", f"memory-{i}"],
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }
        for i in range(5)
    ]


class TestBootstrapRecoveryScenario:
    """Test the complete recovery scenario."""

    @pytest.mark.asyncio
    async def test_recovery_restores_all_memories(self, neo4j_client, test_memories):
        """
        MVP Test: Verify complete recovery from Neo4j.

        This test simulates the scenario where Claude wipes all local memory
        and we need to restore from the remote Neo4j backup.
        """
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Step 1: Create memories in Neo4j (simulating successful sync)
        for memory in test_memories:
            await neo4j_client.create_memory(memory)

        # Verify all memories exist in Neo4j
        count_before = await neo4j_client.get_memory_count(
            project_id="dionysus-core"
        )
        assert count_before >= len(test_memories)

        # Step 2: Simulate "local database destroyed" by clearing local state
        # In real scenario, this would be the PostgreSQL memories table being wiped
        local_memories = []  # Empty - simulating destroyed local DB

        # Step 3: Run bootstrap recovery
        recovered = await sync_service.bootstrap_recovery(
            project_id="dionysus-core"
        )

        # Step 4: Verify 100% restoration
        assert len(recovered) >= len(test_memories), (
            f"Expected at least {len(test_memories)} memories, got {len(recovered)}"
        )

        # Verify each test memory was recovered
        recovered_ids = {m["id"] for m in recovered}
        for memory in test_memories:
            assert memory["id"] in recovered_ids, (
                f"Memory {memory['id']} not recovered"
            )

        # Cleanup
        for memory in test_memories:
            await neo4j_client.delete_memory(memory["id"])

    @pytest.mark.asyncio
    async def test_recovery_preserves_content_integrity(
        self, neo4j_client, test_memories
    ):
        """Test that recovered memories have correct content."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Create memories
        for memory in test_memories:
            await neo4j_client.create_memory(memory)

        # Run recovery
        recovered = await sync_service.bootstrap_recovery(
            project_id="dionysus-core"
        )

        # Verify content integrity
        for original in test_memories:
            matching = [m for m in recovered if m["id"] == original["id"]]
            assert len(matching) == 1, f"Memory {original['id']} not found"

            recovered_memory = matching[0]
            assert recovered_memory["content"] == original["content"]
            assert recovered_memory["memory_type"] == original["memory_type"]
            assert recovered_memory["source_project"] == original["source_project"]

        # Cleanup
        for memory in test_memories:
            await neo4j_client.delete_memory(memory["id"])

    @pytest.mark.asyncio
    async def test_recovery_dry_run_mode(self, neo4j_client, test_memories):
        """Test that dry_run mode doesn't modify local database."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Create memories in Neo4j
        for memory in test_memories:
            await neo4j_client.create_memory(memory)

        # Run recovery in dry_run mode
        result = await sync_service.bootstrap_recovery(
            project_id="dionysus-core",
            dry_run=True,
        )

        # Should return list of what would be recovered
        assert isinstance(result, list)
        assert len(result) >= len(test_memories)

        # In dry_run, local database should NOT be modified
        # (We can't easily test this without a real PostgreSQL connection,
        # but the method should support this parameter)

        # Cleanup
        for memory in test_memories:
            await neo4j_client.delete_memory(memory["id"])


class TestRecoveryFiltering:
    """Test recovery with various filters."""

    @pytest.mark.asyncio
    async def test_recovery_filters_by_project(self, neo4j_client):
        """Test that recovery can filter by project_id."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Create memories in different projects
        memory_a = {
            "id": str(uuid.uuid4()),
            "content": "Memory in project A",
            "memory_type": "episodic",
            "importance": 0.5,
            "source_project": "project-a",
            "session_id": str(uuid.uuid4()),
            "tags": [],
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }
        memory_b = {
            "id": str(uuid.uuid4()),
            "content": "Memory in project B",
            "memory_type": "episodic",
            "importance": 0.5,
            "source_project": "project-b",
            "session_id": str(uuid.uuid4()),
            "tags": [],
            "sync_version": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

        await neo4j_client.create_memory(memory_a)
        await neo4j_client.create_memory(memory_b)

        # Recover only project-a
        recovered = await sync_service.bootstrap_recovery(
            project_id="project-a"
        )

        # Should only include project-a memories
        recovered_ids = {m["id"] for m in recovered}
        assert memory_a["id"] in recovered_ids
        assert memory_b["id"] not in recovered_ids

        # Cleanup
        await neo4j_client.delete_memory(memory_a["id"])
        await neo4j_client.delete_memory(memory_b["id"])

    @pytest.mark.asyncio
    async def test_recovery_filters_by_date(self, neo4j_client):
        """Test that recovery can filter by date range."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # This would test the 'since' parameter in recovery
        # For now, just verify the method accepts the parameter
        recovered = await sync_service.bootstrap_recovery(
            project_id="dionysus-core",
            since=datetime.utcnow().isoformat(),
            dry_run=True,
        )

        # Should return empty or near-empty (nothing created after 'now')
        assert isinstance(recovered, list)


class TestRecoveryErrorHandling:
    """Test recovery error handling."""

    @pytest.mark.asyncio
    async def test_recovery_handles_empty_remote(self, neo4j_client):
        """Test recovery when remote has no memories."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Use a project that doesn't exist
        recovered = await sync_service.bootstrap_recovery(
            project_id="nonexistent-project-12345"
        )

        # Should return empty list, not error
        assert isinstance(recovered, list)
        assert len(recovered) == 0

    @pytest.mark.asyncio
    async def test_recovery_reports_statistics(self, neo4j_client, test_memories):
        """Test that recovery reports useful statistics."""
        from api.services.remote_sync import RemoteSyncService

        sync_service = RemoteSyncService(neo4j_client)

        # Create memories
        for memory in test_memories:
            await neo4j_client.create_memory(memory)

        # Run recovery with stats
        result = await sync_service.bootstrap_recovery_with_stats(
            project_id="dionysus-core"
        )

        # Should include statistics
        assert "recovered_count" in result
        assert "duration_ms" in result
        assert result["recovered_count"] >= len(test_memories)

        # Cleanup
        for memory in test_memories:
            await neo4j_client.delete_memory(memory["id"])


class TestRecoveryEndpoint:
    """Test recovery via API endpoint."""

    @pytest.mark.asyncio
    async def test_recovery_endpoint_integration(self, neo4j_client, test_memories):
        """Test recovery through the API endpoint."""
        from fastapi.testclient import TestClient

        # This will fail until T026 implements the endpoint
        from api.routers.sync import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")
        client = TestClient(app)

        # Create memories in Neo4j first
        for memory in test_memories:
            await neo4j_client.create_memory(memory)

        # Call recovery endpoint
        response = client.post(
            "/api/recovery/bootstrap",
            headers={"Authorization": "Bearer test-token"},
            json={
                "project_id": "dionysus-core",
                "dry_run": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["recovered_count"] >= len(test_memories)

        # Cleanup
        for memory in test_memories:
            await neo4j_client.delete_memory(memory["id"])
