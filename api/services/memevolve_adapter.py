"""
MemEvolve Adapter Service

Service layer for MemEvolve integration.
Feature: 009-memevolve-integration
Phase: 2 - Retrieval

Handles communication between Dionysus and MemEvolve systems via n8n webhooks.
"""

import time
import logging
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from api.services.remote_sync import RemoteSyncService
from api.models.memevolve import (
    MemoryRecallRequest,
    MemoryIngestRequest,
    TrajectoryType,
    TrajectoryData,
    TrajectoryStep,
    TrajectoryMetadata,
)

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

    async def _get_graphiti_service(self):
        from api.services.graphiti_service import get_graphiti_service
        return await get_graphiti_service()
    
    async def ingest_trajectory(self, request: MemoryIngestRequest) -> Dict[str, Any]:
        """
        Ingest trajectory data from MemEvolve.
        
        Args:
            request: MemoryIngestRequest containing trajectory data
            
        Returns:
            Ingestion result with success status
        """
        ingest_id = str(uuid4())
        graphiti_ingested = 0
        webhook_enabled = os.getenv("MEMEVOLVE_WEBHOOK_INGEST_ENABLED", "false").lower() == "true"
        provided_entities = request.entities or []
        provided_edges = request.edges or []
        graphiti = None
        try:
            graphiti = await self._get_graphiti_service()
            trajectory_text = graphiti._format_trajectory_text(request.trajectory, max_chars=8000)
            summary = request.trajectory.summary or await graphiti._summarize_trajectory(trajectory_text)
            if provided_entities or provided_edges:
                structured = {
                    "summary": summary,
                    "entities": provided_entities,
                    "relationships": provided_edges,
                }
            else:
                extraction = await graphiti.extract_with_context(
                    content=trajectory_text,
                    confidence_threshold=0.6,
                )
                structured = {
                    "summary": summary,
                    "entities": extraction.get("entities", []),
                    "relationships": extraction.get("relationships", []),
                }
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
        session_id = request.session_id or metadata.get("session_id")
        project_id = request.project_id or metadata.get("project_id")
        if session_id and "session_id" not in metadata:
            metadata["session_id"] = session_id
        if project_id and "project_id" not in metadata:
            metadata["project_id"] = project_id
        if request.memory_type and "memory_type" not in metadata:
            metadata["memory_type"] = request.memory_type
        
        trajectory_type = metadata.get("trajectory_type", TrajectoryType.EPISODIC)
        if isinstance(trajectory_type, TrajectoryType):
            trajectory_type = trajectory_type.value
        else:
            trajectory_type = str(trajectory_type)

        summary = structured.get("summary") or request.trajectory.summary or "Trajectory summary unavailable."
        step_payload = [
            step.model_dump(exclude_none=True)
            for step in request.trajectory.steps
        ]
        if not step_payload and request.trajectory.trajectory:
            step_payload = [
                item if isinstance(item, dict) else {"observation": str(item)}
                for item in request.trajectory.trajectory
            ]

        metadata_json = json.dumps(metadata, default=str) if metadata else None
        trajectory_json = json.dumps(step_payload, default=str) if step_payload else None
        trajectory_preview = ""
        try:
            if graphiti:
                trajectory_preview = graphiti._format_trajectory_text(request.trajectory, max_chars=2000)
            else:
                trajectory_preview = summary
        except Exception:
            trajectory_preview = summary

        valid_at = self._resolve_valid_at(metadata)

        payload: Dict[str, Any] = {
            "operation": "memevolve_ingest",
            "ingest_id": ingest_id,
            "summary": summary,
            "entities": structured.get("entities", []),
            "relationships": structured.get("relationships", []),
            "metadata": metadata,
            "trajectory_type": trajectory_type,
        }

        try:
            await graphiti.execute_cypher(
                """
                CREATE (t:Trajectory {
                    id: $id,
                    summary: $summary,
                    query: $query,
                    result: $result,
                    trajectory_type: $trajectory_type,
                    created_at: datetime(),
                    occurred_at: $occurred_at,
                    processed_at: null,
                    agent_id: $agent_id,
                    session_id: $session_id,
                    project_id: $project_id,
                    success: $success,
                    reward: $reward,
                    cost: $cost,
                    latency_ms: $latency_ms,
                    step_count: $step_count,
                    metadata: $metadata,
                    trajectory_json: $trajectory_json,
                    trajectory_preview: $trajectory_preview
                })
                """,
                {
                    "id": ingest_id,
                    "summary": summary,
                    "query": request.trajectory.query,
                    "result": request.trajectory.result,
                    "trajectory_type": trajectory_type,
                    "occurred_at": valid_at.isoformat() if valid_at else None,
                    "agent_id": metadata.get("agent_id"),
                    "session_id": session_id,
                    "project_id": project_id,
                    "success": metadata.get("success"),
                    "reward": metadata.get("reward"),
                    "cost": metadata.get("cost"),
                    "latency_ms": metadata.get("latency_ms"),
                    "step_count": len(step_payload),
                    "metadata": metadata_json,
                    "trajectory_json": trajectory_json,
                    "trajectory_preview": trajectory_preview,
                },
            )

            normalized_relationships = []
            for rel in structured.get("relationships", []):
                if not isinstance(rel, dict):
                    continue
                confidence = float(rel.get("confidence", 0.5))
                status = rel.get("status")
                if not status:
                    status = "approved" if confidence >= 0.6 else "pending_review"
                normalized_relationships.append(
                    {
                        "source": rel.get("source", ""),
                        "target": rel.get("target", ""),
                        "relation_type": rel.get("type", rel.get("relation", "RELATES_TO")),
                        "evidence": rel.get("evidence", ""),
                        "confidence": confidence,
                        "status": status,
                    }
                )
            pending_relationships = [
                rel for rel in normalized_relationships if rel.get("status") != "approved"
            ]
            if pending_relationships and graphiti:
                await self._record_pending_relationships(
                    graphiti=graphiti,
                    relationships=pending_relationships,
                    source_id=f"memevolve:{ingest_id}",
                    session_id=session_id,
                    project_id=project_id,
                )

            approved_relationships = [
                rel for rel in normalized_relationships if rel.get("status") == "approved"
            ]
            if approved_relationships:
                ingest_result = await graphiti.ingest_extracted_relationships(
                    relationships=approved_relationships,
                    source_id=f"memevolve:{ingest_id}",
                    valid_at=valid_at,
                )
                graphiti_ingested = int(ingest_result.get("ingested", 0))

            if webhook_enabled:
                webhook_result = await self._sync_service._send_to_webhook(
                    payload,
                    webhook_url=self._sync_service.config.webhook_url,
                )
                if not webhook_result.get("success", True):
                    raise RuntimeError(webhook_result.get("error", "Webhook returned failure"))

            entities_extracted = int(
                payload.get("entities") and len(payload["entities"]) or 0
            )
            memories_created = int(
                graphiti_ingested + (1 if payload.get("summary") else 0)
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

    async def ingest_message(
        self,
        content: str,
        source_id: str,
        *,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        valid_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a single content message through MemEvolve.
        """
        trajectory = TrajectoryData(
            query=source_id,
            steps=[TrajectoryStep(observation=content)],
            metadata=TrajectoryMetadata(
                session_id=session_id,
                project_id=project_id,
                timestamp=valid_at,
                tags=tags or [],
            ),
        )
        request = MemoryIngestRequest(
            trajectory=trajectory,
            session_id=session_id,
            project_id=project_id,
            memory_type=memory_type,
        )
        return await self.ingest_trajectory(request)
    
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
        backend = os.getenv("MEMEVOLVE_RECALL_BACKEND", "graphiti").lower()

        if backend == "graphiti":
            return await self._recall_from_graphiti(request, start_time)
        
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
            if isinstance(request.context, str):
                payload["context"] = request.context
            else:
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
            logging.getLogger(__name__).error(f"MemEvolve recall failed: {e}")
            if os.getenv("MEMEVOLVE_RECALL_FALLBACK", "true").lower() == "true":
                return await self._recall_from_graphiti(request, start_time, error=str(e))

            return {
                "memories": [],
                "query": request.query,
                "result_count": 0,
                "search_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    async def _recall_from_graphiti(
        self,
        request: MemoryRecallRequest,
        start_time: float,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        graphiti = await self._get_graphiti_service()
        group_ids = [request.project_id] if request.project_id else None
        results = await graphiti.search(
            query=request.query,
            group_ids=group_ids,
            limit=request.limit,
        )
        edges = results.get("edges", [])
        memories: List[Dict[str, Any]] = []
        for edge in edges:
            content = edge.get("fact") or edge.get("name") or ""
            memory = {
                "id": str(edge.get("uuid") or ""),
                "content": str(content),
                "type": "semantic",
                "importance": 0.5,
                "similarity": 0.0,
                "session_id": request.session_id,
                "project_id": request.project_id,
                "tags": [],
            }
            if request.include_temporal_metadata:
                memory["valid_at"] = edge.get("valid_at")
                memory["invalid_at"] = edge.get("invalid_at")
            memories.append(memory)

        search_time_ms = (time.time() - start_time) * 1000
        response = {
            "memories": memories,
            "query": request.query,
            "result_count": len(memories),
            "search_time_ms": round(search_time_ms, 2),
        }
        if error:
            response["error"] = error
        return response

    async def execute_cypher(
        self,
        statement: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        graphiti = await self._get_graphiti_service()
        combined_params = (parameters or {}).copy()
        combined_params.update(kwargs)
        return await graphiti.execute_cypher(statement, combined_params)

    async def extract_with_context(
        self,
        *,
        content: str,
        basin_context: Optional[str] = None,
        strategy_context: Optional[str] = None,
        confidence_threshold: float = 0.6,
    ) -> Dict[str, Any]:
        graphiti = await self._get_graphiti_service()
        return await graphiti.extract_with_context(
            content=content,
            basin_context=basin_context,
            strategy_context=strategy_context,
            confidence_threshold=confidence_threshold,
        )

    async def ingest_relationships(
        self,
        *,
        relationships: List[Dict[str, Any]],
        source_id: str,
        valid_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        graphiti = await self._get_graphiti_service()
        return await graphiti.ingest_extracted_relationships(
            relationships=relationships,
            source_id=source_id,
            valid_at=valid_at,
        )

    async def trigger_evolution(self) -> Dict[str, Any]:
        """
        Trigger the meta-evolution workflow to optimize retrieval strategies (T003).
        
        Returns:
            Dict with evolution result summary
        """
        backend = os.getenv("MEMEVOLVE_EVOLVE_BACKEND", "graphiti").lower()
        payload = {
            "operation": "trigger_evolution",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            if backend == "graphiti":
                graphiti = await self._get_graphiti_service()
                records = await graphiti.execute_cypher(
                    """
                    MATCH (t:Trajectory)
                    WHERE t.created_at > datetime() - duration('P1D')
                    RETURN t
                    ORDER BY t.created_at DESC
                    LIMIT 50
                    """
                )
                count = len(records)

                top_k = 5
                threshold = 0.7
                if count > 20:
                    top_k = 7
                    threshold = 0.75
                if count > 40:
                    top_k = 10
                    threshold = 0.8

                basis = f"Analyzed {count} recent trajectories"
                created = await graphiti.execute_cypher(
                    """
                    CREATE (s:RetrievalStrategy {
                        id: randomUUID(),
                        top_k: $top_k,
                        threshold: $threshold,
                        version: $version,
                        created_at: datetime(),
                        basis: $basis
                    })
                    RETURN s
                    """,
                    {
                        "top_k": top_k,
                        "threshold": threshold,
                        "version": int(time.time() * 1000),
                        "basis": basis,
                    },
                )
                return {"success": True, "records": created, "basis": basis}

            result = await self._sync_service._send_to_webhook(
                payload,
                webhook_url=self._sync_service.config.memevolve_evolve_webhook_url,
            )
            return result
        except Exception as e:
            logger.error(f"Meta-evolution trigger failed: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _resolve_valid_at(metadata: Dict[str, Any]) -> Optional[datetime]:
        raw = metadata.get("timestamp") or metadata.get("valid_at") or metadata.get("created_at")
        if not raw:
            return datetime.utcnow()
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, (int, float)):
            try:
                return datetime.fromtimestamp(raw)
            except (OSError, ValueError):
                return None
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                return None
        return None

    @staticmethod
    async def _record_pending_relationships(
        graphiti: Any,
        relationships: List[Dict[str, Any]],
        source_id: str,
        session_id: Optional[str],
        project_id: Optional[str],
    ) -> None:
        if not relationships:
            return
        await graphiti.execute_cypher(
            """
            UNWIND $rels AS rel
            CREATE (r:RelationshipProposal {
                id: randomUUID(),
                source: rel.source,
                target: rel.target,
                relation_type: rel.relation_type,
                evidence: rel.evidence,
                confidence: rel.confidence,
                status: rel.status,
                source_id: $source_id,
                session_id: $session_id,
                project_id: $project_id,
                created_at: datetime()
            })
            """,
            {
                "rels": relationships,
                "source_id": source_id,
                "session_id": session_id,
                "project_id": project_id,
            },
        )


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
