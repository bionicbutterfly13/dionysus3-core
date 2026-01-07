import asyncio
import json
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_core")

async def main():
    logger.info("Starting standalone core test")

    llm_side_effects = [
        json.dumps({"boundary_detected": False, "confidence": 1.0, "rationale": "Continue"}),
        json.dumps({"boundary_detected": False, "confidence": 1.0, "rationale": "Continue"}),
        json.dumps({"boundary_detected": True, "confidence": 1.0, "rationale": "Shift"}),
        json.dumps({
            "title": "Nemori Integration",
            "summary": "Integrating memory flow",
            "narrative": "The system evolved.",
            "archetype": "creator",
            "stabilizing_attractor": "Memory Architecture"
        }),
        "- Prediction 1\n- Prediction 2",
        json.dumps(["Fact A", "Fact B"])
    ]

    mock_driver = MagicMock()
    mock_driver.execute_query = AsyncMock(return_value=[])
    
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_driver.session.return_value = mock_session

    mock_graphiti = AsyncMock()
    mock_graphiti.ingest_message = AsyncMock()

    # Deep patching
    with patch("api.services.llm_service.chat_completion", AsyncMock(side_effect=llm_side_effects)), \
         patch("api.services.webhook_neo4j_driver.get_neo4j_driver", return_value=mock_driver), \
         patch("api.agents.consolidated_memory_stores.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.remote_sync.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.graphiti_service.get_graphiti_service", AsyncMock(return_value=mock_graphiti)):
        
        print("Importing core...")
        from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
        from api.agents.consciousness_memory_core import ConsciousnessMemoryCore
        
        print("Instantiating core...")
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
        print("Recording interaction 1...")
        await core.record_interaction(event1)
        
        event2 = DevelopmentEvent(
            event_id="evt_2",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.IMPLEMENTATION_MILESTONE,
            summary="Event 2",
            rationale="R2",
            impact="I2"
        )
        print("Recording interaction 2...")
        await core.record_interaction(event2)
        
        event3 = DevelopmentEvent(
            event_id="evt_3",
            timestamp=datetime.now(timezone.utc),
            event_type=DevelopmentEventType.PROBLEM_RESOLUTION,
            summary="Event 3",
            rationale="R3",
            impact="I3"
        )
        print("Recording interaction 3...")
        await core.record_interaction(event3)
        
        print(f"Buffer size: {len(core._event_buffer)}")
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
