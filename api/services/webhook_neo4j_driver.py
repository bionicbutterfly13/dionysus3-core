"""
Graphiti Neo4j Driver Adapter

Provides a minimal async session/run interface compatible with legacy
WebhookNeo4jDriver usage, now backed by Graphiti's Neo4j driver.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from api.services.graphiti_service import get_graphiti_service, GraphitiService

logger = logging.getLogger(__name__)


class GraphitiNeo4jResult:
    def __init__(self, records: list[dict[str, Any]]):
        self._records = records

    async def data(self) -> list[dict[str, Any]]:
        return self._records

    async def single(self) -> Optional[dict[str, Any]]:
        return self._records[0] if self._records else None


class GraphitiNeo4jSession:
    def __init__(self, graphiti_service: Optional[GraphitiService] = None):
        self._graphiti_service = graphiti_service

    async def __aenter__(self) -> GraphitiNeo4jSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def _get_graphiti(self) -> GraphitiService:
        if self._graphiti_service is None:
            self._graphiti_service = await get_graphiti_service()
        return self._graphiti_service

    async def run(self, statement: str, parameters: Optional[dict[str, Any]] = None, **kwargs):
        if parameters is None and "params" in kwargs:
            parameters = kwargs.pop("params")
        graphiti = await self._get_graphiti()
        rows = await graphiti.execute_cypher(statement, parameters or {})
        return GraphitiNeo4jResult(rows)


class GraphitiNeo4jDriver:
    def __init__(self, graphiti_service: Optional[GraphitiService] = None):
        self._graphiti_service = graphiti_service

    async def _get_graphiti(self) -> GraphitiService:
        if self._graphiti_service is None:
            self._graphiti_service = await get_graphiti_service()
        return self._graphiti_service

    def session(self) -> GraphitiNeo4jSession:
        return GraphitiNeo4jSession(self._graphiti_service)

    async def execute_query(self, statement: str, parameters: Optional[dict[str, Any]] = None, **kwargs):
        if parameters is None and "params" in kwargs:
            parameters = kwargs.pop("params")
        graphiti = await self._get_graphiti()
        return await graphiti.execute_cypher(statement, parameters or {})

    async def close(self) -> None:
        return None


# Backwards-compatible alias
WebhookNeo4jDriver = GraphitiNeo4jDriver


_driver: Optional[GraphitiNeo4jDriver] = None


def get_neo4j_driver() -> GraphitiNeo4jDriver:
    global _driver
    if _driver is None:
        _driver = GraphitiNeo4jDriver()
    return _driver
