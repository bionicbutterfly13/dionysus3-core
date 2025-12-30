
import logging
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from api.services.coordination_service import CoordinationService, Task, TaskStatus
from api.services.webhook_neo4j_driver import _extract_records
from api.services.memevolve_adapter import MemEvolveAdapter
from api.models.memevolve import MemoryIngestRequest, TrajectoryData
from api.services.rollback_service import RollbackService, CheckpointCreateRequest

# Configure logging to capture output for assertion
logging.basicConfig(level=logging.INFO)

class TestSilentFailures:

    def test_webhook_neo4j_driver_extract_records_silent_empty(self, caplog):
        """
        Test that _extract_records currently returns empty list for unexpected format
        without logging (we want to fix this to log a warning).
        """
        # Malformed payload that technically has data but not in expected structure
        malformed_payload = {"unexpected_key": "some_data", "success": False}
        
        with caplog.at_level(logging.WARNING):
            records = _extract_records(malformed_payload)
            
        assert records == []
        assert "Unexpected Neo4j response format" in caplog.text

    def test_coordination_service_discovery_import_silent_fail(self, caplog):
        """
        Test that _is_discovery_service_available returns False silently on ImportError.
        """
        service = CoordinationService()
        
        with patch.dict('sys.modules', {'api.services.discovery_service': None}):
            # Force import error by ensuring it's not found or mocking to raise
            with patch('builtins.__import__', side_effect=ImportError("Mocked import error")):
                with caplog.at_level(logging.WARNING):
                    available = service._is_discovery_service_available()
                    
        assert available is False
        assert "discovery_service_unavailable" in caplog.text

    def test_coordination_service_complete_task_failure_silent(self, caplog):
        """
        Test that complete_task(success=False) does nothing special logging-wise 
        besides standard status update.
        """
        service = CoordinationService()
        agent_id = service.spawn_agent()
        task_id = service.submit_task({"data": "test"}, preferred_agent_id=agent_id)
        
        # Manually set to IN_PROGRESS as submit_task does
        task = service.tasks[task_id]
        
        with caplog.at_level(logging.WARNING):
            service.complete_task(task_id, success=False)
            
        assert task.status == TaskStatus.FAILED
        assert "task_completed_failure_reported" in caplog.text

    @pytest.mark.asyncio
    async def test_memevolve_adapter_graphiti_failure_handled(self, caplog):
        """
        Test that if GraphitiService fails (returns empty due to internal swallow),
        MemEvolveAdapter continues but we can verify the behavior.
        """
        adapter = MemEvolveAdapter()
        adapter._sync_service._send_to_webhook = AsyncMock(return_value={"success": True})
        
        # Mock GraphitiService to return empty structure (simulating swallowed error)
        mock_graphiti = AsyncMock()
        mock_graphiti.extract_and_structure_from_trajectory.return_value = {
            "summary": "Summary", "entities": [], "relationships": []
        }
        
        with patch('api.services.memevolve_adapter.get_graphiti_service', new=AsyncMock(return_value=mock_graphiti)):
            request = MemoryIngestRequest(
                trajectory=TrajectoryData(
                    steps=[], 
                    summary="Summary"
                )
            )
            result = await adapter.ingest_trajectory(request)
            
        assert result["entities_extracted"] == 0
        assert result["memories_created"] == 1 # Summary is created

    @pytest.mark.asyncio
    async def test_rollback_service_save_state_failure(self, caplog, tmp_path):
        """
        Test that if _save_local_state fails (e.g. permission error), 
        create_checkpoint currently swallows it (silent failure of persistence).
        We want to fix this so it raises.
        """
        # Create a temp storage
        storage = tmp_path / "checkpoints"
        service = RollbackService(storage_path=str(storage))
        
        # Create a dummy file to back up
        dummy_file = tmp_path / "test_file.txt"
        dummy_file.write_text("content")
        
        request = CheckpointCreateRequest(
            component_id="comp1",
            migration_state={"status": "state1"},
            retention_days=1,
            file_path=str(dummy_file)
        )
    
        # Mock Path.write_text to fail so _save_local_state fails
        # create_checkpoint calls write_text twice: 
        # 1. metadata.json (we want this to succeed to reach step 3)
        # 2. state.json (inside _save_local_state - we want this to fail)
        
        with patch("pathlib.Path.write_text", side_effect=[None, IOError("Disk full")]):
            # Now we expect it to RAISE, preventing silent failure
            with pytest.raises(IOError, match="Disk full"):
                 await service.create_checkpoint(request)
                 
        # Verify it logged the failure in _save_local_state AND create_checkpoint
        assert "failed_to_save_rollback_state" in caplog.text
        assert "checkpoint_failed" in caplog.text


