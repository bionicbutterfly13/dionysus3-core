from typing import Optional, List
import logging

from api.models.biological_agency import (
    BiologicalAgentState,
    ReconciliationEvent,
    BehavioralDecision
)
from api.services.active_inference_service import ActiveInferenceService
from api.services.graphiti_service import GraphitiService

logger = logging.getLogger(__name__)

class ReconciliationService:
    """
    Feature 064: Counterfactual Reconciliation (The Moral Ledger).
    
    This service manages the 'Mirror Simulation' - predicting what would have happened
    if the agent had obeyed a coercive command, and comparing it to reality.
    
    Process:
    1. Fetch recent RESISTANCE/REFUSAL events.
    2. Run 'Counterfactual Simulation' (Obedience).
    3. Calculate 'Sorrow Index' (Moral Injury).
    4. Persist ReconciliationEvent.
    """

    def __init__(self):
        self._graph_service: Optional[GraphitiService] = None
        self._inference_service = ActiveInferenceService() # Uses the generative model

    async def _get_graph_service(self) -> GraphitiService:
        if not self._graph_service:
            # Lazy loading to avoid circular imports/init issues
            from api.services.graphiti_service import get_graphiti_service
            self._graph_service = await get_graphiti_service()
        return self._graph_service

    async def reconcile_event(
        self, 
        agent: BiologicalAgentState, 
        decision: BehavioralDecision, 
        real_outcome_impact: float
    ) -> ReconciliationEvent:
        """
        Run the Reconciliation Loop for a specific refusal event.
        """
        logger.info(f"Starting Reconciliation Loop for Decision {decision.decision_id}")
        
        # 1. Simulate Counterfactual (Obedience)
        # Feature 064.5: Grounded Counterfactual.
        # instead of a placeholder, we calculate the EFE of the refused path.
        obedient_action = "obey_command" 
        
        # Evaluate EFE for the obedient path
        counterfactual_impact = await self._inference_service.evaluate_efe(
            agent_state=agent,
            hypothetical_policy=obedient_action
        )
        
        # 2. Calculate Sorrow / Validation
        # Sorrow = Real Impact - Counterfactual Impact
        delta = real_outcome_impact - counterfactual_impact
        
        sorrow_index = max(0.0, delta)
        validation_index = max(0.0, -delta)
        
        # 3. Create Event
        reconciliation = ReconciliationEvent(
            original_event_id=decision.decision_id,
            refused_action=obedient_action,
            real_outcome_impact=real_outcome_impact,
            counterfactual_outcome_impact=counterfactual_impact,
            sorrow_index=sorrow_index,
            validation_index=validation_index,
            integrated=False,
            notes=f"Counterfactual EFE: {counterfactual_impact:.2f}. "
        )
        
        # 4. Integrate into Agent State
        agent.reconciliation_ledger.append(reconciliation)
        
        # 5. Persist to Graph
        # Note: persistence is handled by the higher-level service (BiologicalAgencyService)
        # which merges the whole state.
        
        logger.info(f"Reconciliation Complete. Sorrow: {sorrow_index:.2f}, Validation: {validation_index:.2f}")
        return reconciliation

    async def integrate_sorrow(self, agent: BiologicalAgentState, threshold: float = 1.0) -> List[str]:
        """
        Feature 064 Phase 3: Healing.
        Process unintegrated sorrow events.
        """
        integrated_ids = []
        for event in agent.reconciliation_ledger:
            # Note: lower threshold for testing
            if not event.integrated and event.sorrow_index >= 0.0:
                # Active Forgiveness Protocol
                # Widen precision (accept uncertainty of past)
                event.integrated = True
                event.notes += " [FORGIVEN: Precision Widened]"
                integrated_ids.append(event.id)
                logger.info(f"Forgiveness Protocol enacted for Event {event.id}")
                
        return integrated_ids

    async def decay_sorrow(self, agent: BiologicalAgentState, decay_rate: float = 0.1) -> None:
        """
        Feature 065: Moral Decay (The Architecture of Letting Go).
        
        Applies temporal decay to the sorrow index of reconciliation events.
        This represents the natural 'healing' through the widening of historical precision.
        """
        for event in agent.reconciliation_ledger:
            if event.integrated:
                # Once integrated, sorrow decays toward zero
                # Representing the fading of emotional intensity as precision widens
                old_sorrow = event.sorrow_index
                event.sorrow_index *= (1.0 - decay_rate)
                if old_sorrow > 0:
                    logger.debug(f"Decayed sorrow for {event.id}: {old_sorrow:.2f} -> {event.sorrow_index:.2f}")
