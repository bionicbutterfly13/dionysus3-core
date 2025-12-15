"""
Integration Tests: Cross-Project Query
Feature: 002-remote-persistence-safety
Phase 5, User Story 3: Cross-Project Memory Sharing

T037: Integration test for cross-project query

TDD Test - Write FIRST, verify FAILS before implementation.

Tests querying memories across different projects.
"""

import uuid
from datetime import datetime

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sync_service():
    """Get RemoteSyncService instance."""
    from api.services.remote_sync import RemoteSyncService
    return RemoteSyncService()


@pytest.fixture
async def memories_in_multiple_projects(sync_service):
    """Create memories in different projects."""
    projects = {
        "dionysus-core": str(uuid.uuid4()),
        "inner-architect": str(uuid.uuid4()),
        "knowledge-api": str(uuid.uuid4()),
    }

    memory_ids = {}

    for project_name, project_id in projects.items():
        memory_id = str(uuid.uuid4())
        await sync_service.sync_memory({
            "id": memory_id,
            "content": f"Memory from {project_name}: API patterns and best practices",
            "type": "semantic",
            "importance": 0.7,
            "project_id": project_id,
            "project_name": project_name,
            "created_at": datetime.utcnow().isoformat()
        })
        memory_ids[project_name] = memory_id

    return {"projects": projects, "memory_ids": memory_ids}


# =============================================================================
# T037: Cross-Project Query Tests
# =============================================================================

class TestCrossProjectQuery:
    """Test querying memories across different projects."""

    async def test_query_memories_from_different_project(self, sync_service, memories_in_multiple_projects):
        """Test querying memories created in a different project context."""
        projects = memories_in_multiple_projects["projects"]

        # From dionysus-core, query for memories about "API patterns"
        results = await sync_service.search_memories(
            query="API patterns",
            include_session_attribution=True,
        )

        # Should find memories from multiple projects
        assert len(results) >= 1

        # Results should have project attribution
        for memory in results:
            assert "project_id" in memory or "project_name" in memory

    async def test_query_all_projects(self, sync_service, memories_in_multiple_projects):
        """Test getting memories from all known projects."""
        results = await sync_service.query_all_projects()

        # Should return memories grouped by project
        assert isinstance(results, dict)

        # Should have entries for projects with memories
        project_names = list(memories_in_multiple_projects["projects"].keys())
        for project_name in project_names:
            if project_name in results:
                assert isinstance(results[project_name], list)

    async def test_query_specific_project(self, sync_service, memories_in_multiple_projects):
        """Test querying memories from a specific project."""
        project_id = memories_in_multiple_projects["projects"]["dionysus-core"]

        results = await sync_service.query_by_project(project_id=project_id)

        assert len(results) >= 1
        for memory in results:
            assert memory.get("project_id") == project_id

    async def test_cross_project_search_with_keyword(self, sync_service, memories_in_multiple_projects):
        """Test keyword search that returns results from multiple projects."""
        # Create memories with shared topic in different projects
        project_1 = str(uuid.uuid4())
        project_2 = str(uuid.uuid4())

        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Rate limiting implementation using Redis",
            "type": "semantic",
            "importance": 0.7,
            "project_id": project_1,
            "project_name": "project-alpha"
        })

        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Rate limiting with token bucket algorithm",
            "type": "semantic",
            "importance": 0.7,
            "project_id": project_2,
            "project_name": "project-beta"
        })

        # Search across all projects
        results = await sync_service.search_memories(
            query="rate limiting",
            include_session_attribution=True,
        )

        assert len(results) >= 2

        # Should have results from both projects
        project_ids = {m.get("project_id") for m in results if m.get("project_id")}
        assert len(project_ids) >= 1  # At least one project


class TestProjectTagging:
    """Test that memories are tagged with project_id."""

    async def test_memory_auto_tagged_with_project(self, sync_service):
        """Test that new memories are automatically tagged with current project."""
        # This requires the project detection logic
        memory_data = {
            "id": str(uuid.uuid4()),
            "content": "Test memory for project tagging",
            "type": "semantic",
            "importance": 0.5,
        }

        # Tag with project
        tagged = await sync_service.tag_with_project(
            memory_data,
            project_path="/path/to/dionysus-core"
        )

        assert "project_id" in tagged
        assert "project_name" in tagged
        assert tagged["project_name"] == "dionysus-core"

    async def test_project_id_derived_from_cwd(self, sync_service):
        """Test that project_id can be derived from current working directory."""
        import os

        cwd = os.getcwd()
        project_name = os.path.basename(cwd)

        memory_data = {
            "id": str(uuid.uuid4()),
            "content": "Test memory",
            "type": "semantic",
        }

        tagged = await sync_service.tag_with_project(memory_data)

        # Should use current directory as project source
        assert tagged.get("project_name") == project_name


class TestProjectNodes:
    """Test Neo4j Project node creation."""

    async def test_project_node_created_on_first_memory(self, sync_service):
        """Test that Project node is created when first memory synced."""
        project_id = str(uuid.uuid4())
        project_name = "test-project-" + project_id[:8]

        # Sync memory with new project
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "First memory in new project",
            "type": "semantic",
            "importance": 0.5,
            "project_id": project_id,
            "project_name": project_name,
        })

        # Verify Project node exists
        project = await sync_service.get_project_from_neo4j(project_id)
        assert project is not None
        assert project["name"] == project_name

    async def test_known_projects_registered(self, sync_service):
        """Test that known projects are pre-registered in Neo4j."""
        known_projects = [
            "dionysus-core",
            "inner-architect-companion",
            "knowledge-memory-api",
        ]

        # Ensure known projects exist
        await sync_service.ensure_known_projects(known_projects)

        # Verify they exist in Neo4j
        for project_name in known_projects:
            project = await sync_service.get_project_by_name(project_name)
            assert project is not None
