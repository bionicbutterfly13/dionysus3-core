"""
Rollback and Checkpoint Models
Feature: 021-rollback-safety-net
"""

import enum
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CheckpointStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RESTORED = "restored"
    DELETED = "deleted"


class FileBackup(BaseModel):
    backup_path: str
    original_path: str
    size_bytes: int
    backup_time: datetime
    checksum: str


class RollbackCheckpoint(BaseModel):
    checkpoint_id: str
    component_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retention_until: datetime
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    file_backups: Dict[str, FileBackup] = Field(default_factory=dict)
    metadata_backup: Optional[str] = None
    database_backup: Dict[str, str] = Field(default_factory=dict)
    migration_state: Dict = Field(default_factory=dict)


class RollbackRecord(BaseModel):
    rollback_id: str
    checkpoint_id: str
    component_id: str
    rollback_time: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float
    success: bool
    error: Optional[str] = None
    options: Dict = Field(default_factory=dict)


class CheckpointCreateRequest(BaseModel):
    component_id: str
    file_path: str
    related_files: List[str] = Field(default_factory=list)
    migration_state: Dict = Field(default_factory=dict)
    retention_days: int = 7


class RollbackRequest(BaseModel):
    checkpoint_id: str
    backup_current: bool = True
