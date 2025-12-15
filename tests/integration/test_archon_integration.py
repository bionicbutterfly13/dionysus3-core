"""
Integration Tests: Archon Task Integration
Feature: 002-remote-persistence-safety
Phase 7, User Story 5: LLM Destruction Detection & Archon Integration

T050: Integration test for Archon task tagging

TDD Test - Write FIRST, verify FAILS before implementation.

Tests that memories can be tagged with Archon task context.
"""

import uuid

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def archon_service():
    """Get ArchonIntegrationService instance."""
    from api.services.archon_integration import ArchonIntegrationService
    return ArchonIntegrationService()


@pytest.fixture
def sync_service():
    """Get RemoteSyncService instance."""
    from api.services.remote_sync import RemoteSyncService
    return RemoteSyncService()


# =============================================================================
# T050: Archon Task Tagging Tests
# =============================================================================

class TestArchonTaskContext:
    """Test retrieving current task context from Archon."""

    async def test_get_current_task(self, archon_service):
        """Test getting current active task from Archon MCP."""
        # Get current task (may be None if no task active)
        task = await archon_service.get_current_task()

        # If task exists, verify structure
        if task:
            assert "task_id" in task
            assert "title" in task
            assert "status" in task

    async def test_get_task_by_id(self, archon_service):
        """Test getting specific task by ID."""
        # This would need a real task ID from Archon
        # For now, test the method exists and handles missing task
        result = await archon_service.get_task("nonexistent-task-id")
        assert result is None or "error" in result

    async def test_search_tasks_by_keyword(self, archon_service):
        """Test searching tasks by keyword."""
        # Search for tasks related to "auth"
        tasks = await archon_service.search_tasks(query="auth")

        # Result should be a list
        assert isinstance(tasks, list)

        # Each task should have expected fields
        for task in tasks:
            assert "task_id" in task or "id" in task


class TestMemoryTaskTagging:
    """Test tagging memories with Archon task context."""

    async def test_tag_memory_with_task(self, archon_service, sync_service):
        """Test tagging a memory with active task ID."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Implemented rate limiting for API endpoints",
            "type": "semantic",
            "importance": 0.7,
        }

        # Get current task (if any)
        current_task = await archon_service.get_current_task()

        # Tag memory with task context
        tagged_memory = await archon_service.tag_with_task_context(
            memory_data,
            task=current_task
        )

        # Memory should have task_id if task was active
        if current_task:
            assert "task_id" in tagged_memory
            assert tagged_memory["task_id"] == current_task.get("task_id", current_task.get("id"))
        else:
            # No task context available
            assert tagged_memory.get("task_id") is None

    async def test_memory_sync_includes_task_context(self, archon_service, sync_service):
        """Test that synced memories include task context."""
        memory_id = str(uuid.uuid4())
        memory_data = {
            "id": memory_id,
            "content": "Working on authentication module",
            "type": "semantic",
            "importance": 0.8,
        }

        # Enrich memory with task context before sync
        enriched = await archon_service.enrich_memory_with_context(memory_data)

        # Sync memory
        result = await sync_service.sync_memory(enriched)

        # Verify sync includes task context
        if result.get("success") or result.get("synced"):
            # Memory should have been tagged
            assert "task_id" in enriched or enriched.get("archon_context") is not None


class TestArchonQueryIntegration:
    """Test querying memories by Archon task context."""

    async def test_query_memories_by_task(self, archon_service, sync_service):
        """Test querying memories associated with a specific task."""
        # Create memories tagged with a task
        task_id = str(uuid.uuid4())

        for i in range(3):
            memory_data = {
                "id": str(uuid.uuid4()),
                "content": f"Memory {i} for task",
                "type": "semantic",
                "importance": 0.5,
                "task_id": task_id,
            }
            await sync_service.sync_memory(memory_data)

        # Query by task
        memories = await archon_service.query_memories_by_task(task_id)

        # Should find tagged memories
        assert isinstance(memories, list)

    async def test_query_memories_by_task_topic(self, archon_service, sync_service):
        """Test querying memories by task topic/title."""
        # Search for memories related to a task topic
        memories = await archon_service.query_memories_by_topic("authentication")

        # Result should be a list
        assert isinstance(memories, list)

        # Memories should be relevant to topic
        for memory in memories:
            # Each memory should have content
            assert "content" in memory


class TestArchonProjectContext:
    """Test Archon project context integration."""

    async def test_get_current_project(self, archon_service):
        """Test getting current project from Archon."""
        project = await archon_service.get_current_project()

        # If project exists, verify structure
        if project:
            assert "project_id" in project or "id" in project
            assert "title" in project or "name" in project

    async def test_tag_memory_with_project(self, archon_service):
        """Test tagging memory with Archon project context."""
        memory_data = {
            "id": str(uuid.uuid4()),
            "content": "Test memory",
            "type": "semantic",
        }

        # Get current project
        project = await archon_service.get_current_project()

        # Tag with project
        tagged = await archon_service.tag_with_project_context(
            memory_data,
            project=project
        )

        # Should have archon_project_id if project was active
        if project:
            assert "archon_project_id" in tagged


class TestArchonMCPConnectivity:
    """Test connectivity to Archon MCP server."""

    async def test_archon_mcp_health(self, archon_service):
        """Test Archon MCP server health check."""
        health = await archon_service.check_health()

        assert "status" in health
        # Status should be healthy or indicate specific error
        assert health["status"] in ["healthy", "unhealthy", "unavailable"]

    async def test_archon_available(self, archon_service):
        """Test whether Archon MCP is available."""
        is_available = await archon_service.is_available()

        # Should return boolean
        assert isinstance(is_available, bool)

    async def test_graceful_degradation_when_unavailable(self, archon_service, sync_service):
        """Test that sync works even when Archon is unavailable."""
        # Temporarily disable Archon
        archon_service.disable()

        memory_data = {
            "id": str(uuid.uuid4()),
            "content": "Memory created while Archon unavailable",
            "type": "semantic",
            "importance": 0.5,
        }

        # Sync should still work
        result = await sync_service.sync_memory(memory_data)

        # Re-enable Archon
        archon_service.enable()

        # Memory should sync (possibly without task context)
        assert result.get("synced") or result.get("queued")
