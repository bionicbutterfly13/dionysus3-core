"""
Webhook Neo4j Driver (Neo4j access via n8n only)

Implements a tiny subset of the neo4j-driver API used in this codebase:
- driver.session() as async context manager
- session.run(cypher, parameters) -> result with .data() and .single()

All Cypher is executed via an n8n webhook; the application never connects to Neo4j directly.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from api.services.remote_sync import RemoteSyncService, SyncConfig


_WRITE_KEYWORDS = re.compile(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP)\b", re.IGNORECASE)


def _extract_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "records" in payload and isinstance(payload["records"], list):
        return payload["records"]

    # Support raw Neo4j HTTP transactional response via n8n passthrough.
    if isinstance(payload.get("results"), list) and payload["results"]:
        records: list[dict[str, Any]] = []
        for res in payload["results"]:
            columns = res.get("columns") or []
            for row_entry in res.get("data") or []:
                row = row_entry.get("row") if isinstance(row_entry, dict) else None
                if isinstance(columns, list) and isinstance(row, list) and len(columns) == len(row):
                    records.append(dict(zip(columns, row)))
        return records

    return []


class WebhookNeo4jResult:
    def __init__(self, raw: dict[str, Any]):
        self._raw = raw
        self._records = _extract_records(raw)

    async def data(self) -> list[dict[str, Any]]:
        return self._records

    async def single(self) -> Optional[dict[str, Any]]:
        return self._records[0] if self._records else None


class WebhookNeo4jSession:
    def __init__(self, sync: RemoteSyncService):
        self._sync = sync

    async def __aenter__(self) -> WebhookNeo4jSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def run(self, statement: str, parameters: Optional[dict[str, Any]] = None, **kwargs):
        mode = kwargs.pop("mode", None)
        if mode is None:
            mode = "write" if _WRITE_KEYWORDS.search(statement or "") else "read"

        result = await self._sync.run_cypher(statement, parameters=parameters, mode=mode)
        # Normalize "success" signals so callers can debug failures
        if result.get("success", True) is False:
            raise RuntimeError(result.get("error", "Cypher execution failed"))
        return WebhookNeo4jResult(result)


class WebhookNeo4jDriver:
    def __init__(self, config: Optional[SyncConfig] = None):
        self._sync = RemoteSyncService(config=config)

    def session(self) -> WebhookNeo4jSession:
        return WebhookNeo4jSession(self._sync)

    async def execute_query(self, statement: str, parameters: Optional[dict[str, Any]] = None, **kwargs):
        """
        Execute a Cypher query and return the results directly.
        Matches the modern neo4j-driver API.
        """
        async with self.session() as session:
            result = await session.run(statement, parameters, **kwargs)
            return await result.data()

    async def close(self) -> None:
        return None

