import pytest
import asyncio
import json
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_river")

@pytest.mark.asyncio
async def test_river_flow_full_chain():
    """
    Verifies the full chain: Core -> River -> Store with mocked LLM responses.
    This version mocks EVERYTHING to prevent hangs and supports EST fields.
    """
    logger.info("Starting test_river_flow_full_chain")

    llm_side_effects = [
        # check_boundary call 1 (No boundary)
        json.dumps({"boundary_detected": False, "confidence": 1.0, "surprisal_estimate": 0.1, "rationale": "Continue"}),
        # check_boundary call 2 (No boundary)
        json.dumps({"boundary_detected": False, "confidence": 1.0, "surprisal_estimate": 0.2, "rationale": "Continue"}),
        # check_boundary call 3 (Boundary detected!)
        json.dumps({"boundary_detected": True, "confidence": 1.0, "surprisal_estimate": 0.9, "rationale": "EST Shift detected"}),
        # construct_episode call (Synthesize)
        json.dumps({
            "title": "Nemori Integration",
            "summary": "Integrating memory flow",
            "narrative": "The system evolved.",
            "archetype": "creator",
            "stabilizing_attractor": "Memory Architecture",
            "strand_id": "research"
        }),
        # _sharpen_episode_narrative call (Hippocampal Binding)
        "Vivid sharpened narrative of the system evolution with situational features bound.",
        # predict_and_calibrate: predict stage
        "- Prediction 1\n- Prediction 2",
        # predict_and_calibrate: calibrate stage
        json.dumps({
            "new_facts": ["Fact A", "Fact B"],
            "symbolic_residue": {"active_goals": ["Integrate smolagents"]}
        })
    ]

    mock_driver = MagicMock()
    # Mocking execute_query to return a mock result object that can be iterated
    mock_result = MagicMock()
    mock_result.__iter__.return_value = []
    mock_driver.execute_query = AsyncMock(return_value=mock_result)
    
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_driver.session.return_value = mock_session

    # Mock GraphitiService to avoid the threaded event loop hang
    mock_graphiti = AsyncMock()
    mock_graphiti.ingest_message = AsyncMock()

    with patch("api.services.llm_service.chat_completion", AsyncMock(side_effect=llm_side_effects)), \
         patch("api.services.webhook_neo4j_driver.get_neo4j_driver", return_value=mock_driver), \
         patch("api.agents.consolidated_memory_stores.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.remote_sync.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.graphiti_service.get_graphiti_service", AsyncMock(return_value=mock_graphiti)):
        
        from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
        from api.agents.consciousness_memory_core import ConsciousnessMemoryCore
        
        core = ConsciousnessMemoryCore(journey_id="test_journey")
        
        # Interactions
        event1 = DevelopmentEvent(
            event_id="evt_1",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.RESEARCH_INTEGRATION,
            summary="Event 1",
            rationale="R1",
            impact="I1"
        )
        await core.record_interaction(event1)
        
        event2 = DevelopmentEvent(
            event_id="evt_2",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.IMPLEMENTATION_MILESTONE,
            summary="Event 2",
            rationale="R2",
            impact="I2"
        )
        await core.record_interaction(event2)
        
        event3 = DevelopmentEvent(
            event_id="evt_3",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.PROBLEM_RESOLUTION,
            summary="Event 3",
            rationale="R3",
            impact="I3"
        )
        await core.record_interaction(event3)
        
        assert len(core._event_buffer) == 0
        # Expecting at least 6 execute_query calls:
        # 3 for storing events + 1 for initial journey update + 1 for episode creation + 1 for journey link
        # Plus 1 for distillation event?
        assert mock_driver.execute_query.call_count >= 6
        logger.info("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_river_flow_full_chain())
