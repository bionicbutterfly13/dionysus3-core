"""
Reconstruction Service
Feature: 012-historical-reconstruction

Handles mirroring of local Archon task history into the Neo4j graph.
"""

import logging
import time
from typing import Any, Dict, List
from api.services.remote_sync import get_neo4j_driver
from api.services.archon_integration import get_archon_service

logger = logging.getLogger("dionysus.reconstruction")

class ReconstructionService:
    """
    Service for longitudinal task history reconstruction.
    """
    def __init__(self):
        self._driver = get_neo4j_driver()
        self.archon_svc = get_archon_service()

    async def reconstruct_task_history(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Fetch tasks from Archon and upsert them as nodes in Neo4j.
        """
        start_time = time.time()
        logger.info("Starting historical task reconstruction...")

        # 1. Fetch tasks from local Archon environment
        # Note: fetch_all_historical_tasks will be updated to use MCP
        tasks = await self.archon_svc.fetch_all_historical_tasks(limit=limit)
        if not tasks:
            return {"status": "completed", "fetched": 0, "mirrored": 0, "message": "No tasks found in Archon."}

        # 2. Idempotent batch upsert into Neo4j
        cypher = """
        UNWIND $tasks as task
        MERGE (t:ArchonTask {id: task.task_id})
        SET t.title = task.title,
            t.status = task.status,
            t.description = task.description,
            t.source = task.source,
            t.reconstructed_at = datetime()
        
        WITH t, task
        WHERE task.project_id IS NOT NULL
        MERGE (p:ArchonProject {id: task.project_id})
        ON CREATE SET p.name = task.project_name
        MERGE (t)-[:BELONGS_TO]->(p)
        RETURN count(t) as count
        """
        
        # Prepare parameters
        task_params = []
        for t in tasks:
            task_params.append({
                "task_id": t.get("task_id") or t.get("id"),
                "title": t.get("title") or t.get("description", "")[:50],
                "status": t.get("status"),
                "description": t.get("description"),
                "source": t.get("source", "archon"),
                "project_id": t.get("project_id") or t.get("project"),
                "project_name": t.get("project_name") or t.get("project")
            })

        try:
            result = await self._driver.execute_query(cypher, {"tasks": task_params})
            mirrored_count = result[0]["count"] if result else 0
            
            latency = (time.time() - start_time) * 1000
            logger.info(f"Reconstruction completed: {mirrored_count} tasks mirrored in {latency:.2f}ms")
            
            return {
                "status": "success",
                "fetched": len(tasks),
                "mirrored": mirrored_count,
                "latency_ms": latency
            }
        except Exception as e:
            logger.error(f"Reconstruction failed: {e}")
            return {"status": "error", "error": str(e)}

_reconstruction_service: Any = None

def get_reconstruction_service() -> ReconstructionService:
    global _reconstruction_service
    if _reconstruction_service is None:
        _reconstruction_service = ReconstructionService()
    return _reconstruction_service