import asyncio
import logging
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("nemori_demo")

async def run_demo():
    logger.info("🌊 Starting Real-time Nemori River Demo...")
    
    # 1. Setup Mocks for demo (simulating LLMs and Neo4j)
    llm_responses = [
        # check_boundary 1 (Stable)
        json.dumps({"boundary_detected": False, "confidence": 0.9, "surprisal_estimate": 0.1, "rationale": "Smooth progress"}),
        # check_boundary 2 (Spike!)
        json.dumps({"boundary_detected": True, "confidence": 1.0, "surprisal_estimate": 0.95, "rationale": "Sudden shift in cognitive strand"}),
        # construct_episode
        json.dumps({
            "title": "Architecture Alignment",
            "summary": "Bridging D2 and D3 memory models",
            "narrative": "The agent meticulously ported enums and logic.",
            "archetype": "creator",
            "stabilizing_attractor": "Model Integrity",
            "strand_id": "migration"
        }),
        # sharpen_episode_narrative
        "The creator agent successfully bridged the legacy Mosaic schema into the modern Nemori River flow, stabilizing the cognitive architecture for real-time emergence.",
        # predict_and_calibrate (predict)
        "- Memory enums ported\n- EST logic active",
        # predict_and_calibrate (calibrate)
        json.dumps({
            "new_facts": ["D3 now supports Mosaic states", "Hippocampal binding improves narrative fidelity"],
            "symbolic_residue": {"active_goals": ["Integrate smolagents loop"], "active_entities": ["NemoriRiverFlow"]}
        })
    ]
    
    mock_driver = MagicMock()
    mock_result = MagicMock()
    mock_result.__iter__.return_value = []
    mock_driver.execute_query = AsyncMock(return_value=mock_result)
    
    mock_graphiti = AsyncMock()

    with patch("api.services.llm_service.chat_completion", AsyncMock(side_effect=llm_responses)), \
         patch("api.services.webhook_neo4j_driver.get_neo4j_driver", return_value=mock_driver), \
         patch("api.agents.consolidated_memory_stores.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.remote_sync.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.graphiti_service.get_graphiti_service", AsyncMock(return_value=mock_graphiti)):
        
        from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType, ObservationType, MosaicState
        from api.agents.consciousness_memory_core import ConsciousnessMemoryCore
        
        core = ConsciousnessMemoryCore(journey_id="demo_journey")
        
        # --- PHASE 1: Raw Observation (SOURCE) ---
        logger.info("STEP 1: Recording raw observations (SOURCE)...")
        event1 = DevelopmentEvent(
            event_id="evt_101",
            event_type=DevelopmentEventType.RESEARCH_INTEGRATION,
            summary="Analyzing D2 memory gaps",
            rationale="User requested migration plan",
            impact="Strategic alignment",
            observation_type=ObservationType.COGNITIVE,
            mosaic_state=MosaicState.ACTIVE,
            consciousness_level=0.6
        )
        await core.record_interaction(event1)
        logger.info("Event 1 recorded. Buffer size: 1")

        # --- PHASE 2: Prediciton Error Spike (TRIBUTARY) ---
        logger.info("STEP 2: Unexpected discovery triggers EST Boundary...")
        event2 = DevelopmentEvent(
            event_id="evt_102",
            event_type=DevelopmentEventType.PROBLEM_RESOLUTION,
            summary="Ported Mosaic enums to D3",
            rationale="Schema mapping complete",
            impact="Model convergence",
            prediction_error=0.92, # This will trigger a computational boundary spike
            observation_type=ObservationType.BEHAVIORAL,
            mosaic_state=MosaicState.REFLECTIVE,
            consciousness_level=0.85
        )
        await core.record_interaction(event2)
        
        # --- PHASE 3: Segmentation & Sharpening (MAIN_RIVER) ---
        logger.info("STEP 3: Segmentation complete. Narrative sharpened via Hippocampal Binding.")
        
        # --- PHASE 4: Distillation & Residue (DELTA) ---
        logger.info("STEP 4: Wisdom distilled into DELTA. Symbolic Residue extracted for continuity.")

    logger.info("🎉 Demo completed! Check logs for flow details.")

if __name__ == "__main__":
    asyncio.run(run_demo())
