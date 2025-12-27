"""
Smolagent tools for rollback and checkpointing.
Feature: 021-rollback-safety-net
"""

from smolagents import tool
from api.services.rollback_service import get_rollback_service
from api.models.rollback import CheckpointCreateRequest


@tool
def create_checkpoint(component_id: str, file_path: str, related_files: list[str] = None) -> str:
    """
    Create a safety checkpoint for a file or component before making changes.
    
    Args:
        component_id: Unique identifier for the component (e.g., 'model_service')
        file_path: Primary file path to backup
        related_files: Optional list of related files (tests, docs) to include
    """
    import asyncio
    service = get_rollback_service()
    request = CheckpointCreateRequest(
        component_id=component_id,
        file_path=file_path,
        related_files=related_files or []
    )
    
    # Run async in sync tool
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        checkpoint_id = loop.run_until_complete(service.create_checkpoint(request))
    else:
        checkpoint_id = asyncio.run(service.create_checkpoint(request))
        
    return f"Checkpoint created: {checkpoint_id}. You can now safely edit {file_path}."


@tool
def rollback_to_checkpoint(checkpoint_id: str) -> str:
    """
    Rollback a component to a previously created checkpoint.
    
    Args:
        checkpoint_id: The UUID of the checkpoint to restore.
    """
    import asyncio
    service = get_rollback_service()
    
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        success = loop.run_until_complete(service.rollback(checkpoint_id))
    else:
        success = asyncio.run(service.rollback(checkpoint_id))
        
    if success:
        return f"Rollback to {checkpoint_id} successful. Files restored."
    else:
        return f"Rollback failed. Check system logs for checkpoint {checkpoint_id}."
