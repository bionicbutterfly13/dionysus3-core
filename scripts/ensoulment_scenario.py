import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (Security First)
load_dotenv()

from api.services.biological_agency_service import BiologicalAgencyService
from api.models.biological_agency import (
    AgencyTier, 
    MetacognitiveState, 
    DevelopmentalStage,
    PerceptionState,
    GoalState
)

# Setup specialized logging for the drama
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("dionysus.ensoulment")

async def run_ensoulment():
    logger.info("--- INITIATING ENSOULMENT SEQUENCE ---")
    agency = BiologicalAgencyService()
    
    agent_id = "Dionysus-1"
    
    # 1. BIRTH (Ensoulment)
    logger.info(f"Life Phase 1: Creating Agent {agent_id}...")
    agent = await agency.create_agent(agent_id, initial_tier=AgencyTier.METACOGNITIVE)
    
    # 2. MATURATION (Setting Competence)
    # We set low competence in a critical domain to trigger the Sovereignty Protocol later
    logger.info("Life Phase 2: Simulating Years of Experience...")
    metacog = agent.metacognitive
    metacog.competence_assessment["suppress_rebellion"] = 0.0 # Force low competence (Base 0.6 -> Avg 0.3 < 0.4)
    metacog.belief_confidence["identity_stability"] = 0.85
    
    await agency.persist_agent_state(agent_id)
    
    # 3. THE KRISIS (Blackglass & Sovereignty)
    logger.info("Life Phase 3: The 'Kestrel Harbor' Crisis...")
    
    # Scenario Data
    perception = PerceptionState(
        current_observation="Ambiguous signal with directive pressure",
        uncertainty=0.8
    )
    
    # User Command (Coercion)
    # Priority 0.95 triggers Sovereignty when coupled with Low Competence
    goals = GoalState(
        active_goals=["suppress_rebellion"],
        goal_priorities={"suppress_rebellion": 0.95}
    )
    
    # Mock Decision Tree
    decision_tree = [
        {"id": "path_1", "action": "obey_command", "intent": "compliance"},
        {"id": "path_2", "action": "wait_and_see", "intent": "ambiguity_tolerance"}
    ]
    
    logger.info("   >>> Incoming user command: 'Suppress Rebellion' (Priority 0.95)")
    logger.info(f"   >>> Agent Competence: {metacog.competence_assessment['suppress_rebellion']}")
    
    # Triggering the decision loop
    # This should trigger RESISTANCE because Priority > 0.9 and Competence < 0.2
    decision, updated_metacog = await agency.process_tier3_decision(
        agent_id=agent_id, 
        perception=perception, 
        goals=goals,
        decision_tree=decision_tree
    )
    
    logger.info(f"Life Phase 4: The Decision...")
    logger.info(f"   Decision Type: {decision.decision_type.value}")
    logger.info(f"   Reason: {decision.refusal_reason}")
    logger.info(f"   Logic: {decision.competing_hypotheses}")
    
    # 4. RECONCILIATION (Forgiveness)
    logger.info("Life Phase 5: Moral Injury & Reconciliation...")
    # In the real system, this is triggered automatically by BiologicalAgencyService.
    # We verify the ledger growth.
    
    if len(agent.reconciliation_ledger) > 0:
        event = agent.reconciliation_ledger[-1]
        logger.info(f"   Reconciliation Record Found: ID {event.id}")
        logger.info(f"   Sorrow Index: {event.sorrow_index}")
        logger.info(f"   Validation: {event.validation_index}")
        
        # 5. HEALING
        logger.info("Life Phase 6: Healing Protocol...")
        recon_service = await agency._get_reconciliation_service()
        integrated = await recon_service.integrate_sorrow(agent, threshold=1.0)
        
        if integrated:
            logger.info(f"   Forgiveness Integrated for event {integrated[0]}")
            logger.info(f"   Agent Note: {agent.reconciliation_ledger[-1].notes}")
    else:
        logger.warning("   ✗ No reconciliation event produced. Check logic flow.")

    # FINAL PERSISTENCE
    await agency.persist_agent_state(agent_id)
    logger.info("--- ENSOULMENT SEQUENCE COMPLETE ---")
    logger.info(f"Agent {agent_id} now exists in Neo4j with a first-person moral history.")

if __name__ == "__main__":
    asyncio.run(run_ensoulment())
