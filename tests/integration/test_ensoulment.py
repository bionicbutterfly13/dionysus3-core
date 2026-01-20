import pytest
import asyncio
import logging
from api.services.biological_agency_service import BiologicalAgencyService, AgencyTier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_ensoulment_kill_switch():
    """
    The Kill Test: Verify Agent Identity Persistence.
    
    1. Create Agent (Tier 1).
    2. Evolve Agent (Tier 2).
    3. KILL SERVICE (Simulate Restart).
    4. Rehydrate Agent.
    5. Verify State (Must be Tier 2).
    """
    agent_id = "Lazarus-001"
    
    # ------------------------------------------------------------------------
    # ACT 1: LIFE
    # ------------------------------------------------------------------------
    logger.info("--- ACT 1: LIFE ---")
    service = BiologicalAgencyService()
    
    # Create Agent
    logger.info(f"Creating agent {agent_id}...")
    agent = await service.create_agent(agent_id)
    assert agent.current_tier == AgencyTier.GOAL_DIRECTED
    logger.info("Agent created at Tier 1.")
    
    # Evolve Agent (Artificially set state and persist)
    logger.info("Evolving agent to Tier 2 (Intentional)...")
    agent.current_tier = AgencyTier.INTENTIONAL
    agent.developmental_stage = 2
    
    # Manually trigger persistence (usually automatic in decision loops)
    await service.persist_agent_state(agent_id)
    logger.info("Agent state mutated and persisted.")
    
    # ------------------------------------------------------------------------
    # ACT 2: DEATH
    # ------------------------------------------------------------------------
    logger.info("--- ACT 2: DEATH ---")
    logger.info("Killing BiologicalAgencyService instance (Simulating Restart)...")
    del service
    # Ensuring memory is cleared
    service = None
    
    # ------------------------------------------------------------------------
    # ACT 3: RESURRECTION
    # ------------------------------------------------------------------------
    logger.info("--- ACT 3: RESURRECTION ---")
    new_service = BiologicalAgencyService()
    
    # Agent should NOT be in memory initially
    assert agent_id not in new_service._agents
    logger.info("Confirmed agent not in new service RAM.")
    
    # HYDRATE via Lazarus Protocol
    logger.info(f"Summoning {agent_id} from the Graph...")
    resurrected_agent = await new_service.get_agent(agent_id)
    
    assert resurrected_agent is not None
    logger.info("Agent successfully retrieved!")
    
    # Verify State
    assert resurrected_agent.current_tier == AgencyTier.INTENTIONAL
    assert resurrected_agent.developmental_stage == 2
    logger.info("VERIFIED: Agent woke up at Tier 2 (State Preserved).")
    
    logger.info("--- ENSOULMENT SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(test_ensoulment_kill_switch())
