"""
Rollback API Router
Feature: 021-rollback-safety-net
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from api.models.rollback import (
    CheckpointCreateRequest,
    RollbackRequest,
    RollbackCheckpoint,
    RollbackRecord
)
from api.services.rollback_service import get_rollback_service

router = APIRouter(prefix="/api/rollback", tags=["rollback"])


@router.post("/checkpoints", response_model=Dict[str, str])
async def create_checkpoint(request: CheckpointCreateRequest):
    service = get_rollback_service()
    try:
        checkpoint_id = await service.create_checkpoint(request)
        return {"checkpoint_id": checkpoint_id, "status": "active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkpoints", response_model=List[RollbackCheckpoint])
async def list_checkpoints():
    service = get_rollback_service()
    return list(service.checkpoints.values())


@router.post("/run", response_model=Dict[str, bool])
async def run_rollback(request: RollbackRequest):
    service = get_rollback_service()
    success = await service.rollback(request.checkpoint_id, request.backup_current)
    if not success:
        raise HTTPException(status_code=400, detail="rollback_failed_check_logs")
    return {"success": success}


@router.get("/history", response_model=List[RollbackRecord])
async def get_history():
    service = get_rollback_service()
    return service.history


@router.post("/cleanup", response_model=Dict[str, int])
async def cleanup_expired():
    service = get_rollback_service()
    count = await service.cleanup_expired()
    return {"cleaned_count": count}
