import pytest
from unittest.mock import MagicMock, patch
from smolagents.memory import ActionStep
from api.utils.callbacks import CallbackRegistry

def test_callback_registry_list_dispatch():
    """Verify that wrap_as_list() correctly dispatches calls."""
    registry = CallbackRegistry()
    
    mock_cb = MagicMock()
    registry.register(ActionStep, mock_cb)
    
    callbacks = registry.wrap_as_list()
    assert len(callbacks) == 1
    
    dispatcher = callbacks[0]
    
    # Trigger with ActionStep
    step = ActionStep(step_number=1, timing=MagicMock())
    dispatcher(step, agent_name="test")
    
    mock_cb.assert_called_once_with(step, agent_name="test")

def test_mosaeic_callback_integration():
    """Verify MOSAEIC callback extraction trigger."""
    from api.agents.mosaeic_callback import create_mosaeic_callback
    
    cb = create_mosaeic_callback("test_agent")
    
    step = ActionStep(step_number=1, timing=MagicMock())
    step.observation = "I feel a sense of progress."
    
    with patch("api.agents.mosaeic_callback.get_mosaeic_service") as mock_svc:
        mock_service = MagicMock()
        mock_svc.return_value = mock_service
        
        # We need to mock asyncio since we are in a unit test
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.is_running.return_value = False
            
            cb(step)
            
            # Should have triggered extraction
            assert mock_service.extract_capture.called
