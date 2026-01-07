"""
File Export Service
Feature: 013-marketing-assets, 018-ias-knowledge-base

Handles writing generated content to the filesystem with divert-to-review fallback.
"""

import os
import logging
from typing import Dict, Optional
from api.services.aspect_service import get_aspect_service

logger = logging.getLogger("dionysus.file_export")

class FileExportService:
    """
    Service for persisting agent-generated assets to disk.
    """

    async def export_content(self, file_path: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Write content to file. Diverts to human review on failure.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "w") as f:
                f.write(content)
                
            logger.info(f"Successfully exported asset to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export file to {file_path}: {e}")
            
            # FR-007: Divert to review on failure
            aspect_service = get_aspect_service()
            await aspect_service.add_to_human_review(
                reason=f"Export Failure: {os.path.basename(file_path)}",
                data={
                    "requested_path": file_path,
                    "content": content,
                    "error": str(e),
                    "metadata": metadata or {}
                },
                confidence=0.0
            )
            return False

# Factory
_instance = None
def get_file_export_service() -> FileExportService:
    global _instance
    if _instance is None:
        _instance = FileExportService()
    return _instance
