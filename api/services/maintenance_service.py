"""
Maintenance Service
Feature: 012-historical-reconstruction

Encapsulates system maintenance, data integrity, and reconstruction operations.
"""

import logging
from typing import Any, Dict, List
from api.services.reconstruction_service import get_reconstruction_service
from api.services.aspect_service import get_aspect_service

logger = logging.getLogger("dionysus.maintenance")

class MaintenanceService:
    """
    Unified service for system maintenance tasks.
    """
    def __init__(self):
        self.reconstruction_svc = get_reconstruction_service()
        self.aspect_svc = get_aspect_service()

    async def get_human_review_queue(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get items requiring human oversight.
        """
        return await self.aspect_svc.get_human_review_items(limit=limit)

    async def resolve_review_item(self, item_id: str) -> bool:
        """
        Mark a review item as resolved.
        """
        return await self.aspect_svc.delete_review_item(item_id)

_maintenance_service: Any = None

def get_maintenance_service() -> MaintenanceService:
    global _maintenance_service
    if _maintenance_service is None:
        _maintenance_service = MaintenanceService()
    return _maintenance_service
