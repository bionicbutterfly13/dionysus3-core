"""
Webhook Neo4j Driver (Authorized via Graphiti only)

REPAIRED: This driver no longer calls n8n or Neo4j directly.
It proxies all requests through GraphitiService, which is the sole
authorized component for Neo4j communication.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("dionysus.webhook_driver")

class WebhookNeo4jResult:
    def __init__(self, records: list[dict[str, Any]]):
        self._records = records

    async def data(self) -> list[dict[str, Any]]:
        return self._records

    async def single(self) -> Optional[dict[str, Any]]:
        return self._records[0] if self._records else None


class WebhookNeo4jSession:
    def __init__(self):
        pass

    async def __aenter__(self) -> WebhookNeo4jSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def run(self, statement: str, parameters: Optional[dict[str, Any]] = None, **kwargs):
        """
        Proxies query to GraphitiService.
        """
        from api.services.memevolve_adapter import get_memevolve_adapter
        adapter = get_memevolve_adapter()
        
        # Merge kwargs into parameters
        combined_params = (parameters or {}).copy()
        combined_params.update(kwargs)
        
        records = await adapter.execute_cypher(statement, combined_params)
        return WebhookNeo4jResult(records)


class WebhookNeo4jDriver:
    """
    Compatibility shim that enforces Graphiti-only access.
    """
    def session(self) -> WebhookNeo4jSession:
        return WebhookNeo4jSession()

    async def execute_query(self, statement: str, parameters: Optional[dict[str, Any]] = None, **kwargs):
        """
        Execute a Cypher query via Graphiti and return results.
        """
        from api.services.memevolve_adapter import get_memevolve_adapter
        adapter = get_memevolve_adapter()
        
        # Merge kwargs into parameters
        combined_params = (parameters or {}).copy()
        combined_params.update(kwargs)
        
        return await adapter.execute_cypher(statement, combined_params)

    async def close(self) -> None:
        return None


_driver: Optional[WebhookNeo4jDriver] = None


def get_neo4j_driver() -> WebhookNeo4jDriver:
    global _driver
    if _driver is None:
        _driver = WebhookNeo4jDriver()
    return _driver
