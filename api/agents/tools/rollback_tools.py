"""
Class-based tools for rollback and checkpointing.
Feature: 021-rollback-safety-net
Tasks: T4.1, T4.2
"""

from typing import Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.rollback_service import get_rollback_service
from api.models.rollback import CheckpointCreateRequest
from api.agents.resource_gate import async_tool_wrapper

class RollbackOutput(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Detailed result message")
    checkpoint_id: Optional[str] = Field(None, description="The UUID of the checkpoint involved")

class CreateCheckpointTool(Tool):
    name = "create_checkpoint"
    description = "Create a safety checkpoint for a file or component before making changes."
    
    inputs = {
        "component_id": {
            "type": "string",
            "description": "Unique identifier for the component (e.g., 'model_service')"
        },
        "file_path": {
            "type": "string",
            "description": "Primary file path to backup"
        },
        "related_files": {
            "type": "list",
            "description": "Optional list of related files (tests, docs) to include",
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, component_id: str, file_path: str, related_files: list[str] = None) -> dict:
        from api.agents.resilience import wrap_with_resilience
        service = get_rollback_service()
        request = CheckpointCreateRequest(
            component_id=component_id,
            file_path=file_path,
            related_files=related_files or []
        )
        
        try:
            checkpoint_id = async_tool_wrapper(service.create_checkpoint)(request)
            output = RollbackOutput(
                success=True,
                message=f"Checkpoint created successfully. You can now safely edit {file_path}.",
                checkpoint_id=checkpoint_id
            )
            return output.model_dump()
        except Exception as e:
            error_msg = wrap_with_resilience(f"Failed to create checkpoint: {e}")
            return RollbackOutput(
                success=False,
                message=error_msg
            ).model_dump()

class RollbackToCheckpointTool(Tool):
    name = "rollback_to_checkpoint"
    description = "Rollback a component to a previously created checkpoint."
    
    inputs = {
        "checkpoint_id": {
            "type": "string",
            "description": "The UUID of the checkpoint to restore."
        }
    }
    output_type = "any"

    def forward(self, checkpoint_id: str) -> dict:
        from api.agents.resilience import wrap_with_resilience
        service = get_rollback_service()
        
        try:
            success = async_tool_wrapper(service.rollback)(checkpoint_id)
            if success:
                return RollbackOutput(
                    success=True,
                    message=f"Rollback to {checkpoint_id} successful. Files restored.",
                    checkpoint_id=checkpoint_id
                ).model_dump()
            else:
                error_msg = wrap_with_resilience(f"Rollback failed for {checkpoint_id}. Check system logs.")
                return RollbackOutput(
                    success=False,
                    message=error_msg,
                    checkpoint_id=checkpoint_id
                ).model_dump()
        except Exception as e:
            error_msg = wrap_with_resilience(f"Rollback execution error: {e}")
            return RollbackOutput(
                success=False,
                message=error_msg,
                checkpoint_id=checkpoint_id
            ).model_dump()

# Export tool instances
create_checkpoint = CreateCheckpointTool()
rollback_to_checkpoint = RollbackToCheckpointTool()