"""
MemEvolve Adapter Service

Service layer for MemEvolve integration.
Feature: 009-memevolve-integration
Phase: 2 - Retrieval

Handles communication between Dionysus and MemEvolve systems via n8n webhooks.
"""

import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from api.services.remote_sync import RemoteSyncService
from api.models.memevolve import MemoryRecallRequest, MemoryIngestRequest
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)


class MemEvolveAdapter:
    """
    Adapter service for MemEvolve integration.
    
    Handles communication between Dionysus and MemEvolve systems.
    """
    
    def __init__(self, sync_service: Optional[RemoteSyncService] = None):
        """
        Initialize the MemEvolve adapter.
        
        Args:
            sync_service: Optional RemoteSyncService for n8n webhook calls.
                         Creates default instance if not provided.
        """
        self._initialized_at = datetime.utcnow()
        self._sync_service = sync_service or RemoteSyncService()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for MemEvolve adapter.
        
        Returns:
            Health status dict with service info
        """
        return {
            "status": "ok",
            "service": "dionysus-memevolve-adapter",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def ingest_trajectory(self, request: MemoryIngestRequest) -> Dict[str, Any]:
        """
        Ingest trajectory data from MemEvolve.
        
        Args:
            request: MemoryIngestRequest containing trajectory data
            
        Returns:
            Ingestion result with success status
        """
        ingest_id = str(uuid4())
        try:
            graphiti = await get_graphiti_service()
            structured = await graphiti.extract_and_structure_from_trajectory(request.trajectory)
        except Exception as exc:
            logger.error(f"Graphiti extraction failed: {exc}")
            # Fallback to just using the summary
            structured = {
                "summary": request.trajectory.summary or "Trajectory summary unavailable.",
                "entities": [],
                "relationships": []
            }

        metadata = (
            request.trajectory.metadata.model_dump(exclude_none=True)
            if request.trajectory.metadata
            else {}
        )

        payload: Dict[str, Any] = {
            "operation": "memevolve_ingest",
            "ingest_id": ingest_id,
            "summary": structured.get("summary"),
            "entities": structured.get("entities", []),
            "relationships": structured.get("relationships", []),
            "metadata": metadata,
        }

        try:
            webhook_result = await self._sync_service._send_to_webhook(
                payload,
                webhook_url=self._sync_service.config.webhook_url,
            )

            if not webhook_result.get("success", True):
                raise RuntimeError(webhook_result.get("error", "Webhook returned failure"))

            entities_extracted = int(
                webhook_result.get("entities_extracted", len(payload["entities"]))
            )
            memories_created = int(
                webhook_result.get(
                    "memories_created",
                    1 if payload.get("summary") else 0,
                )
            )

            return {
                "ingest_id": ingest_id,
                "entities_extracted": entities_extracted,
                "memories_created": memories_created,
            }
        except Exception as exc:
            logger.error(f"MemEvolve ingest failed: {exc}")
            return {
                "ingest_id": ingest_id,
                "entities_extracted": 0,
                "memories_created": 0,
            }
    
    async def recall_memories(
        self, 
        request: MemoryRecallRequest
    ) -> Dict[str, Any]:
        """
        Recall memories for MemEvolve query via n8n webhook.
        
        Performs semantic vector search using RemoteSyncService which
        calls the N8N_RECALL_URL webhook with operation "vector_search".
        
        Args:
            request: MemoryRecallRequest with query and filter parameters
            
        Returns:
            Dict with memories list, query, result_count, and search_time_ms
        """
        start_time = time.time()
        
        # Build webhook payload for vector search
        payload: Dict[str, Any] = {
            "operation": "vector_search",
            "query": request.query,
            "k": request.limit,
            "threshold": 0.5,  # Default similarity threshold
        }
        
        # Add filters if provided
        filters: Dict[str, Any] = {}
        if request.memory_types:
            filters["memory_types"] = request.memory_types
        if request.project_id:
            filters["project_id"] = request.project_id
        if request.session_id:
            filters["session_id"] = request.session_id
        if request.include_temporal_metadata:
            filters["include_temporal"] = True
        if request.context:
            filters.update(request.context)
        
        if filters:
            payload["filters"] = filters
        
        # Call n8n webhook via RemoteSyncService
        try:
            result = await self._sync_service._send_to_webhook(
                payload,
                webhook_url=self._sync_service.config.recall_webhook_url
            )
            
            # Parse response - n8n may return "results" or "memories"
            items = result.get("results") or result.get("memories") or []
            
            # Transform to MemEvolve format
            memories: List[Dict[str, Any]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                memory = {
                    "id": str(item.get("id") or item.get("memory_id") or ""),
                    "content": str(item.get("content", "")),
                    "type": item.get("memory_type") or item.get("type") or "semantic",
                    "importance": float(item.get("importance", 0.5)),
                    "similarity": float(
                        item.get("similarity_score") 
                        or item.get("score") 
                        or item.get("similarity") 
                        or 0.0
                    ),
                    "session_id": item.get("session_id"),
                    "project_id": item.get("project_id"),
                    "tags": item.get("tags", []),
                }
                
                # Add temporal metadata if requested
                if request.include_temporal_metadata:
                    memory["valid_at"] = item.get("valid_at")
                    memory["invalid_at"] = item.get("invalid_at")
                
                memories.append(memory)
            
            search_time_ms = (time.time() - start_time) * 1000
            
            return {
                "memories": memories,
                "query": request.query,
                "result_count": len(memories),
                "search_time_ms": round(search_time_ms, 2),
            }
            
        except Exception as e:
            # Return empty results on error, log for debugging
            import logging
            logging.getLogger(__name__).error(f"MemEvolve recall failed: {e}")
            
            return {
                "memories": [],
                "query": request.query,
                "result_count": 0,
                "search_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }


# Singleton pattern
_adapter: Optional[MemEvolveAdapter] = None


def get_memevolve_adapter() -> MemEvolveAdapter:
    """
    Get or create the MemEvolve adapter singleton.
    
    Returns:
        MemEvolveAdapter instance
    """
    global _adapter
    if _adapter is None:
        _adapter = MemEvolveAdapter()
    return _adapter