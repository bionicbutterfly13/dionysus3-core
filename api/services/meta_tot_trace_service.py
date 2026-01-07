"""
Meta-ToT Trace Persistence Service (Graphiti-backed)
Feature: 041-meta-tot-engine
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from api.models.meta_tot import MetaToTTracePayload
from api.services.graphiti_service import get_graphiti_service, GraphitiService

logger = logging.getLogger("dionysus.meta_tot_trace")


class MetaToTTraceService:
    def __init__(self, graphiti_service: Optional[GraphitiService] = None):
        self._graphiti_service = graphiti_service

    async def _get_graphiti(self) -> GraphitiService:
        if self._graphiti_service is None:
            self._graphiti_service = await get_graphiti_service()
        return self._graphiti_service

    async def store_trace(self, payload: MetaToTTracePayload) -> str:
        trace_id = payload.trace_id
        cypher = """
        MERGE (t:MetaToTTrace {id: $id})
        SET t.session_id = $session_id,
            t.created_at = $created_at,
            t.payload = $payload
        RETURN t.id as id
        """
        params = {
            "id": trace_id,
            "session_id": payload.session_id,
            "created_at": payload.created_at,
            "payload": json.dumps(payload.model_dump()),
        }
        graphiti = await self._get_graphiti()
        await graphiti.execute_cypher(cypher, params)
        logger.info(f"meta_tot_trace_stored: {trace_id}")
        return trace_id

    async def get_trace(self, trace_id: str) -> Optional[MetaToTTracePayload]:
        cypher = """
        MATCH (t:MetaToTTrace {id: $id})
        RETURN t.payload as payload
        """
        graphiti = await self._get_graphiti()
        rows = await graphiti.execute_cypher(cypher, {"id": trace_id})
        if not rows:
            return None
        payload_raw = rows[0].get("payload")
        if not payload_raw:
            return None
        payload = json.loads(payload_raw)
        return MetaToTTracePayload(**payload)


_meta_tot_trace_service: Optional[MetaToTTraceService] = None


def get_meta_tot_trace_service() -> MetaToTTraceService:
    global _meta_tot_trace_service
    if _meta_tot_trace_service is None:
        _meta_tot_trace_service = MetaToTTraceService()
    return _meta_tot_trace_service
