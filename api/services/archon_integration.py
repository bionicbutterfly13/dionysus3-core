"""
Archon Integration Service
Feature: 002-remote-persistence-safety
Phase 7, User Story 5: LLM Destruction Detection & Archon Integration

T053: Tag memories with active Archon task_id when available.
T054: Query Archon MCP for current task context on memory creation.

Provides integration with Archon MCP server for:
- Getting current active task context
- Tagging memories with task/project associations
- Querying memories by Archon task

IMPORTANT: This service gracefully degrades when Archon is unavailable.
Memory sync continues to work without Archon context enrichment.
"""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Archon MCP server configuration
ARCHON_MCP_URL = os.getenv("ARCHON_MCP_URL", "http://archon-mcp:8051")
ARCHON_TIMEOUT = float(os.getenv("ARCHON_TIMEOUT", "10.0"))


# =============================================================================
# Archon Integration Service
# =============================================================================

class ArchonIntegrationService:
    """
    Integration service for Archon MCP task management.

    Provides methods to:
    - Get current active task from Archon
    - Tag memories with task context
    - Query memories by Archon task/project

    Gracefully degrades when Archon is unavailable - memory operations
    continue without task context enrichment.

    Usage:
        archon = ArchonIntegrationService()
        task = await archon.get_current_task()
        enriched = await archon.enrich_memory_with_context(memory_data)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = ARCHON_TIMEOUT,
    ):
        """
        Initialize Archon integration service.

        Args:
            base_url: Archon MCP server URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or ARCHON_MCP_URL
        self.timeout = timeout
        self._enabled = True
        self._cached_task: Optional[dict[str, Any]] = None
        self._cached_project: Optional[dict[str, Any]] = None
        self._cache_ttl = 30.0  # seconds
        self._last_cache_time = 0.0

    # =========================================================================
    # Enable/Disable
    # =========================================================================

    def enable(self) -> None:
        """Enable Archon integration."""
        self._enabled = True
        logger.info("Archon integration enabled")

    def disable(self) -> None:
        """Disable Archon integration."""
        self._enabled = False
        logger.info("Archon integration disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if integration is enabled."""
        return self._enabled

    # =========================================================================
    # Health Check
    # =========================================================================

    async def check_health(self) -> dict[str, Any]:
        """
        Check Archon MCP server health.

        Returns:
            Health status dictionary
        """
        if not self._enabled:
            return {"status": "disabled"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")

                if response.status_code == 200:
                    return {"status": "healthy", "response": response.json()}
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Status {response.status_code}",
                    }

        except httpx.TimeoutException:
            return {"status": "unhealthy", "error": "Timeout"}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    async def is_available(self) -> bool:
        """
        Check if Archon MCP is available.

        Returns:
            True if available, False otherwise
        """
        if not self._enabled:
            return False

        health = await self.check_health()
        return health.get("status") == "healthy"

    # =========================================================================
    # Task Context (T054)
    # =========================================================================

    async def get_current_task(self) -> Optional[dict[str, Any]]:
        """
        Get current active task from Archon.

        Checks for task with status "doing" assigned to current agent.

        Returns:
            Task data or None if no active task
        """
        if not self._enabled:
            return None

        # Check cache
        import time
        if self._cached_task and (time.time() - self._last_cache_time) < self._cache_ttl:
            return self._cached_task

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call Archon's find_tasks endpoint
                response = await client.post(
                    f"{self.base_url}/tools/find_tasks",
                    json={
                        "filter_by": "status",
                        "filter_value": "doing",
                        "per_page": 1,
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    tasks = result.get("tasks", result if isinstance(result, list) else [])

                    if tasks:
                        task = tasks[0]
                        self._cached_task = {
                            "task_id": task.get("id") or task.get("task_id"),
                            "title": task.get("title"),
                            "status": task.get("status"),
                            "project_id": task.get("project_id"),
                            "description": task.get("description"),
                        }
                        self._last_cache_time = time.time()
                        return self._cached_task

                return None

        except Exception as e:
            logger.debug(f"Failed to get current task from Archon: {e}")
            return None

    async def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """
        Get specific task by ID.

        Args:
            task_id: Task UUID

        Returns:
            Task data or None
        """
        if not self._enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tools/find_tasks",
                    json={"task_id": task_id}
                )

                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict) and "task" in result:
                        return result["task"]
                    elif isinstance(result, dict):
                        return result

                return None

        except Exception as e:
            logger.debug(f"Failed to get task {task_id}: {e}")
            return None

    async def search_tasks(self, query: str) -> list[dict[str, Any]]:
        """
        Search tasks by keyword.

        Args:
            query: Search query

        Returns:
            List of matching tasks
        """
        if not self._enabled:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tools/find_tasks",
                    json={"query": query}
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("tasks", result if isinstance(result, list) else [])

                return []

        except Exception as e:
            logger.debug(f"Failed to search tasks: {e}")
            return []

    async def fetch_all_historical_tasks(self, limit: int = 1000) -> list[dict[str, Any]]:
        """
        Fetch all historical tasks from Archon for reconstruction.
        
        Args:
            limit: Maximum tasks to fetch
            
        Returns:
            List of all tasks from Archon
        """
        if not self._enabled:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Call Archon's find_tasks without filters to get all
                response = await client.post(
                    f"{self.base_url}/tools/find_tasks",
                    json={
                        "per_page": limit,
                        "include_closed": True
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    # Archon response might be {"tasks": [...]} or [...]
                    if isinstance(result, dict):
                        return result.get("tasks", [])
                    return result if isinstance(result, list) else []

                return []

        except Exception as e:
            logger.error(f"Failed to fetch historical tasks from Archon: {e}")
            return []

    # =========================================================================
    # Project Context
    # =========================================================================

    async def get_current_project(self) -> Optional[dict[str, Any]]:
        """
        Get current project from Archon.

        Returns:
            Project data or None
        """
        if not self._enabled:
            return None

        # If we have a cached task with project_id, get that project
        if self._cached_task and self._cached_task.get("project_id"):
            return await self.get_project(self._cached_task["project_id"])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tools/find_projects",
                    json={"per_page": 1}
                )

                if response.status_code == 200:
                    result = response.json()
                    projects = result.get("projects", result if isinstance(result, list) else [])

                    if projects:
                        project = projects[0]
                        self._cached_project = {
                            "project_id": project.get("id") or project.get("project_id"),
                            "title": project.get("title"),
                            "description": project.get("description"),
                        }
                        return self._cached_project

                return None

        except Exception as e:
            logger.debug(f"Failed to get current project: {e}")
            return None

    async def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """
        Get specific project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project data or None
        """
        if not self._enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tools/find_projects",
                    json={"project_id": project_id}
                )

                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict) and "project" in result:
                        return result["project"]
                    elif isinstance(result, dict):
                        return result

                return None

        except Exception as e:
            logger.debug(f"Failed to get project {project_id}: {e}")
            return None

    # =========================================================================
    # Memory Tagging (T053)
    # =========================================================================

    async def tag_with_task_context(
        self,
        memory_data: dict[str, Any],
        task: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Tag memory with task context.

        Args:
            memory_data: Memory data dictionary
            task: Task to tag with (if None, gets current task)

        Returns:
            Memory data with task_id added
        """
        tagged = memory_data.copy()

        if task is None and self._enabled:
            task = await self.get_current_task()

        if task:
            tagged["task_id"] = task.get("task_id") or task.get("id")
            tagged["task_title"] = task.get("title")
            if task.get("project_id"):
                tagged["archon_project_id"] = task["project_id"]

        return tagged

    async def tag_with_project_context(
        self,
        memory_data: dict[str, Any],
        project: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Tag memory with project context.

        Args:
            memory_data: Memory data dictionary
            project: Project to tag with (if None, gets current project)

        Returns:
            Memory data with archon_project_id added
        """
        tagged = memory_data.copy()

        if project is None and self._enabled:
            project = await self.get_current_project()

        if project:
            tagged["archon_project_id"] = project.get("project_id") or project.get("id")
            tagged["archon_project_title"] = project.get("title")

        return tagged

    async def enrich_memory_with_context(
        self,
        memory_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Enrich memory with all available Archon context.

        Adds task_id, project_id, and related metadata.

        Args:
            memory_data: Memory data dictionary

        Returns:
            Enriched memory data
        """
        if not self._enabled:
            return memory_data

        enriched = memory_data.copy()

        # Get current task
        task = await self.get_current_task()
        if task:
            enriched["task_id"] = task.get("task_id") or task.get("id")
            enriched["task_title"] = task.get("title")

            # Get project from task
            if task.get("project_id"):
                enriched["archon_project_id"] = task["project_id"]
        else:
            # Try to get current project directly
            project = await self.get_current_project()
            if project:
                enriched["archon_project_id"] = project.get("project_id") or project.get("id")

        # Add context timestamp
        from datetime import datetime
        enriched["archon_context"] = {
            "enriched_at": datetime.utcnow().isoformat(),
            "task_id": enriched.get("task_id"),
            "project_id": enriched.get("archon_project_id"),
        }

        return enriched

    # =========================================================================
    # Memory Query by Task
    # =========================================================================

    async def query_memories_by_task(self, task_id: str) -> list[dict[str, Any]]:
        """
        Query memories associated with a specific task.

        Args:
            task_id: Task UUID

        Returns:
            List of memories tagged with this task
        """
        # This would query via RemoteSyncService
        # For now, return empty list (implementation depends on Neo4j query)
        from api.services.remote_sync import RemoteSyncService
        sync_service = RemoteSyncService()

        try:
            # Query memories with task_id filter
            payload = {
                "operation": "query",
                "filters": {"task_id": task_id},
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    sync_service.config.recall_webhook_url,
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("memories", [])

                return []

        except Exception as e:
            logger.debug(f"Failed to query memories by task: {e}")
            return []

    async def query_memories_by_topic(self, topic: str) -> list[dict[str, Any]]:
        """
        Query memories by topic/keyword.

        Args:
            topic: Topic to search for

        Returns:
            List of relevant memories
        """
        from api.services.remote_sync import RemoteSyncService
        sync_service = RemoteSyncService()

        return await sync_service.search_memories(
            query=topic,
            include_session_attribution=True,
            limit=20,
        )


# =============================================================================
# Global Instance
# =============================================================================

_global_archon: Optional[ArchonIntegrationService] = None


def get_archon_service() -> ArchonIntegrationService:
    """Get or create global Archon integration service."""
    global _global_archon
    if _global_archon is None:
        _global_archon = ArchonIntegrationService()
    return _global_archon
