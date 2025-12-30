"""
Rollback Safety Net Service
Feature: 021-rollback-safety-net

Handles checkpoint creation and fast rollback for agentic changes.
Ported and enhanced from Dionysus 2.0.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from api.models.rollback import (
    RollbackCheckpoint,
    CheckpointStatus,
    FileBackup,
    RollbackRecord,
    CheckpointCreateRequest
)

logger = logging.getLogger(__name__)


class RollbackService:
    def __init__(self, storage_path: str = ".checkpoints"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.checkpoints: Dict[str, RollbackCheckpoint] = {}
        self.history: List[RollbackRecord] = []
        self._load_local_state()

    def _load_local_state(self):
        """Load existing checkpoints from disk if any."""
        state_file = self.storage_path / "state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                for cid, cdata in data.get("checkpoints", {}).items():
                    self.checkpoints[cid] = RollbackCheckpoint(**cdata)
                for hdata in data.get("history", []):
                    self.history.append(RollbackRecord(**hdata))
            except Exception as e:
                logger.error(f"failed_to_load_rollback_state: {e}")

    def _save_local_state(self):
        """Persist checkpoints and history to disk."""
        state_file = self.storage_path / "state.json"
        try:
            data = {
                "checkpoints": {cid: c.model_dump(mode='json') for cid, c in self.checkpoints.items()},
                "history": [h.model_dump(mode='json') for h in self.history]
            }
            state_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"failed_to_save_rollback_state: {e}")
            raise

    async def create_checkpoint(self, request: CheckpointCreateRequest) -> str:
        """Create a rollback checkpoint for a component."""
        checkpoint_id = str(uuid4())
        checkpoint_dir = self.storage_path / checkpoint_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"creating_checkpoint: checkpoint_id={checkpoint_id} component_id={request.component_id}")

        try:
            # 1. Backup files
            file_backups = await self._backup_files(request, checkpoint_dir)

            # 2. Backup metadata
            metadata_path = checkpoint_dir / "metadata.json"
            metadata = {
                "component_id": request.component_id,
                "migration_state": request.migration_state,
                "created_at": datetime.utcnow().isoformat()
            }
            metadata_path.write_text(json.dumps(metadata, indent=2))

            # 3. Create record
            checkpoint = RollbackCheckpoint(
                checkpoint_id=checkpoint_id,
                component_id=request.component_id,
                retention_until=datetime.utcnow() + timedelta(days=request.retention_days),
                file_backups=file_backups,
                metadata_backup=str(metadata_path),
                migration_state=request.migration_state
            )

            self.checkpoints[checkpoint_id] = checkpoint
            self._save_local_state()
            return checkpoint_id

        except Exception as e:
            logger.error(f"checkpoint_failed: checkpoint_id={checkpoint_id} error={e}")
            if checkpoint_dir.exists():
                shutil.rmtree(checkpoint_dir)
            raise

    async def _backup_files(self, request: CheckpointCreateRequest, checkpoint_dir: Path) -> Dict[str, FileBackup]:
        backups = {}
        files_dir = checkpoint_dir / "files"
        files_dir.mkdir(exist_ok=True)

        all_files = [request.file_path] + request.related_files
        for fpath in all_files:
            source = Path(fpath)
            if not source.exists():
                logger.warning(f"file_not_found_for_backup: path={fpath}")
                continue

            dest = files_dir / source.name
            if dest.exists(): # avoid collisions for related files with same name
                dest = files_dir / f"{uuid4().hex[:8]}_{source.name}"
            
            shutil.copy2(source, dest)
            checksum = await self._calculate_checksum(source)
            
            backups[fpath] = FileBackup(
                backup_path=str(dest),
                original_path=fpath,
                size_bytes=dest.stat().st_size,
                backup_time=datetime.utcnow(),
                checksum=checksum
            )
        return backups

    async def _calculate_checksum(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def rollback(self, checkpoint_id: str, backup_current: bool = True) -> bool:
        """Rollback to a specific checkpoint."""
        if checkpoint_id not in self.checkpoints:
            return False

        checkpoint = self.checkpoints[checkpoint_id]
        start_time = time.time()
        success = False
        error = None

        try:
            # 1. Verify integrity
            for fpath, binfo in checkpoint.file_backups.items():
                if not Path(binfo.backup_path).exists():
                    raise ValueError(f"backup_file_missing: {binfo.backup_path}")
                # Optional: verify checksum here too

            # 2. Restore
            for fpath, binfo in checkpoint.file_backups.items():
                orig = Path(binfo.original_path)
                if orig.exists() and backup_current:
                    shutil.move(orig, orig.with_suffix(f"{orig.suffix}.pre_rollback_{checkpoint_id[:8]}"))
                
                orig.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(binfo.backup_path, orig)

            checkpoint.status = CheckpointStatus.RESTORED
            success = True
        except Exception as e:
            error = str(e)
            logger.error(f"rollback_failed: checkpoint_id={checkpoint_id} error={error}")
        finally:
            duration = time.time() - start_time
            record = RollbackRecord(
                rollback_id=str(uuid4()),
                checkpoint_id=checkpoint_id,
                component_id=checkpoint.component_id,
                duration_seconds=duration,
                success=success,
                error=error,
                options={"backup_current": backup_current}
            )
            self.history.append(record)
            self._save_local_state()

        return success

    async def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        to_delete = [cid for cid, c in self.checkpoints.items() if c.retention_until < now]
        count = 0
        for cid in to_delete:
            checkpoint_dir = self.storage_path / cid
            if checkpoint_dir.exists():
                shutil.rmtree(checkpoint_dir)
            del self.checkpoints[cid]
            count += 1
        if count > 0:
            self._save_local_state()
        return count

    def metrics(self) -> Dict:
        """Expose rollback metrics for monitoring."""
        failed = [r for r in self.history if not r.success]
        return {
            "total_checkpoints": len(self.checkpoints),
            "history_count": len(self.history),
            "failed_rollbacks": len(failed),
            "last_rollback_success": self.history[-1].success if self.history else None,
            "last_rollback_at": self.history[-1].rollback_id if self.history else None, # Using ID as proxy if no timestamp in record
        }


_rollback_service: Optional[RollbackService] = None


def get_rollback_service() -> RollbackService:
    global _rollback_service
    if _rollback_service is None:
        _rollback_service = RollbackService()
    return _rollback_service
