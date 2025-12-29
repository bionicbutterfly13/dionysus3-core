import pytest
import tempfile
import json
from pathlib import Path
from api.services.rollback_service import RollbackService
from api.models.rollback import CheckpointCreateRequest


@pytest.mark.asyncio
async def test_checkpoint_and_rollback_flow():
    with tempfile.TemporaryDirectory() as storage_dir:
        service = RollbackService(storage_path=storage_dir)
        
        # 1. Create a dummy file to backup
        with tempfile.TemporaryDirectory() as code_dir:
            file_path = Path(code_dir) / "logic.py"
            file_path.write_text("v1_content")
            
            # 2. Create checkpoint
            req = CheckpointCreateRequest(
                component_id="test_comp",
                file_path=str(file_path)
            )
            checkpoint_id = await service.create_checkpoint(req)
            assert checkpoint_id in service.checkpoints
            
            # 3. Mutate file
            file_path.write_text("v2_content")
            assert file_path.read_text() == "v2_content"
            
            # 4. Rollback
            success = await service.rollback(checkpoint_id)
            assert success is True
            assert file_path.read_text() == "v1_content"
            
            # Check history
            assert len(service.history) == 1
            assert service.history[0].success is True
            assert service.history[0].checkpoint_id == checkpoint_id


@pytest.mark.asyncio
async def test_cleanup_expired():
    with tempfile.TemporaryDirectory() as storage_dir:
        service = RollbackService(storage_path=storage_dir)
        
        # Manually inject an expired checkpoint
        from datetime import datetime, timedelta
        from api.models.rollback import RollbackCheckpoint, CheckpointStatus
        
        cid = "expired_one"
        checkpoint = RollbackCheckpoint(
            checkpoint_id=cid,
            component_id="comp",
            retention_until=datetime.utcnow() - timedelta(hours=1),
            status=CheckpointStatus.ACTIVE
        )
        service.checkpoints[cid] = checkpoint
        
        # Run cleanup
        count = await service.cleanup_expired()
        assert count == 1
        assert cid not in service.checkpoints
