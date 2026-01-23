"""
Integration test for Meta-Cognitive Learning loop.
Feature 043.
"""
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from api.agents.consciousness_manager import ConsciousnessManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_learning_loop():
    # Mock for the orchestrator (CodeAgent)
    mock_output = '{"reasoning": "I used tools and succeeded.", "confidence": 0.9, "actions": []}'
    
    with patch("api.agents.resource_gate.run_agent_with_timeout", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_output
        
        # Also need to mock the meta-learner's synthesizer to see it being called
        with patch("api.services.meta_cognitive_service.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "ADVICE: Follow the previous successful path."
            
            # Mock Neo4j driver to avoid connection errors
            with patch("api.services.meta_cognitive_service.get_neo4j_driver") as mock_driver:
                manager = ConsciousnessManager()
                
                # Mock the orchestrator instance to have steps (for tool extraction)
                manager.orchestrator = MagicMock()
                step = MagicMock()
                step.step_number = 1
                
                # Mock tool call object
                mock_tool_call = MagicMock()
                mock_tool_call.name = "understand_question"
                step.tool_calls = [mock_tool_call]
                manager.orchestrator.memory.steps = [step]
                
                # --- FIRST CYCLE ---
                logger.info("Starting First OODA Cycle...")
                ctx1 = {"task": "How to design a marketing page?", "meta_learning_enabled": True}
                
                result1 = await manager.run_ooda_cycle(ctx1)
                logger.info(f"First cycle finished. Confidence: {result1['confidence']}")
                
                # --- SECOND CYCLE (Similar Task) ---
                logger.info("Starting Second OODA Cycle (Similar Task)...")
                ctx2 = {"task": "Design another marketing page.", "meta_learning_enabled": True}
                
                # Mock retrieve_relevant_episodes to return the first episode
                from api.models.meta_cognition import CognitiveEpisode
                past_ep = CognitiveEpisode(
                    task_query=ctx1["task"],
                    success=True,
                    lessons_learned="Break it down."
                )
                
                with patch.object(manager.meta_learner, "retrieve_relevant_episodes", new_callable=AsyncMock) as mock_retrieve:
                    mock_retrieve.return_value = [past_ep]
                    
                    result2 = await manager.run_ooda_cycle(ctx2)
                    
                    # Verify that synthesize_lessons was called because First cycle was recorded
                    logger.info("Checking if lessons were synthesized for the second cycle...")
                    mock_chat.assert_called()
                    
                    logger.info("Integration simulation successful.")

if __name__ == "__main__":
    asyncio.run(simulate_learning_loop())
