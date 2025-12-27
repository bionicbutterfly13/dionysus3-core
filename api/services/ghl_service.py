"""
GoHighLevel Integration Service
Feature: 013-marketing-assets, 017-ias-marketing-suite

Handles communication with GoHighLevel API v2.
"""

import os
import logging
import httpx
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dionysus.ghl_service")

class GHLService:
    """
    Service for interacting with GoHighLevel API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GHL_API_KEY")
        self.base_url = "https://services.leadconnectorhq.com"
        
        if not self.api_key:
            logger.warning("GHL_API_KEY not found in environment.")

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Version": "2021-07-28",
            "Accept": "application/json"
        }

    async def get_workflows(self, location_id: str) -> List[Dict[str, Any]]:
        """Retrieve all workflows for a specific location."""
        url = f"{self.base_url}/workflows/"
        params = {"locationId": location_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers, params=params)
            if response.status_code == 200:
                return response.json().get("workflows", [])
            else:
                logger.error(f"GHL get_workflows failed: {response.status_code} - {response.text}")
                return []

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve details for a specific workflow, including its actions."""
        # Note: GHL API v2 might have specific endpoints for workflow steps
        # or it might be included in the detail response.
        url = f"{self.base_url}/workflows/{workflow_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 200:
                return response.json().get("workflow")
            else:
                logger.error(f"GHL get_workflow failed: {response.status_code} - {response.text}")
                return None

# Factory
_instance = None
def get_ghl_service() -> GHLService:
    global _instance
    if _instance is None:
        _instance = GHLService()
    return _instance
