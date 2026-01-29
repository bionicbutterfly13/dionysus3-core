"""
Exoskeleton Service – Point of Performance (PoP) grounding and recovery.
ULTRATHINK: This service provides the external 'scaffolding' for the agent when 
internal clarity or willpower (ACC) atrophies.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from api.models.hexis_ontology import ExoskeletonMode
from api.models.exoskeleton import (
    RecoveryPathway, RecoveryStep, SomaticAnchor, 
    SurrogateFilter, MismatchExperiment
)
from api.services.hexis_service import get_hexis_service

logger = logging.getLogger(__name__)

class ExoskeletonService:
    """
    Manages externalized decision support and recovery paths.
    """

    def __init__(self, hexis_service=None):
        self._hexis = hexis_service or get_hexis_service()

    async def get_recovery_path(self, intention: str, gap_magnitude: float) -> RecoveryPathway:
        """
        Generate a 'Pathway back to traction' when an Intention-Execution gap is detected.
        """
        logger.info(f"Generating recovery path for intention: {intention} (Gap: {gap_magnitude})")
        
        # Define steps with somatic anchors
        steps = [
            RecoveryStep(
                id="step_1",
                description="Perform Vital Pause (Breath -> Identification -> Pause)",
                action_type="vital_pause",
                somatic_anchor=SomaticAnchor(
                    name="Deep Breath",
                    description="Box breathing",
                    instruction="Inhale for 4s, hold for 4s, exhale for 4s, hold for 4s."
                ),
                next_step_id="step_2"
            ),
            RecoveryStep(
                id="step_2",
                description=f"Reset workspace context strictly to: {intention}",
                action_type="reset_context",
                next_step_id="step_3"
            ),
            RecoveryStep(
                id="step_3",
                description="Execute smallest possible starting sub-task (2-minute rule)",
                action_type="atomic_action",
                somatic_anchor=SomaticAnchor(
                    name="The Tap",
                    description="Sync check",
                    instruction="Tap your index finger twice on the desk to initiate."
                )
            )
        ]
        
        pathway = RecoveryPathway(
            id=f"path_{datetime.utcnow().timestamp()}",
            name="Emergency Traction Pathway",
            description=f"Recovery map for: {intention}",
            steps=steps,
            current_step_id="step_1"
        )
        
        if gap_magnitude > 0.7:
             # Inject the EXTERNAL BLOCK as a mandatory step 0
             steps.insert(0, RecoveryStep(
                 id="step_0",
                 description="EXTERNAL BLOCK: Active inhibition of non-essential tools",
                 action_type="system_pause",
                 next_step_id="step_1"
             ))
             pathway.current_step_id = "step_0"
            
        return pathway

    async def generate_surrogate_filter(self) -> SurrogateFilter:
        """
        Produce a Surrogate Filter to offload decision-making.
        """
        return SurrogateFilter(
            id=f"filter_{datetime.utcnow().timestamp()}",
            directives=[
                "Prioritize grounding over reasoning.",
                "Obey the current step of the Recovery Pathway.",
                "Do not seek 'Fresh Starts' or 'New Contexts' until traction is confirmed."
            ],
            forbidden_actions=[
                "abandon_task",
                "switch_context",
                "complex_synthesis"
            ],
            obedience_tier=3 # High priority
        )

    async def record_mismatch_experiment(
        self, prediction: str, catastrophe_level: float, result: str
    ) -> MismatchExperiment:
        """
        Record a 'Mismatch Experiment' outcome to update internal priors.
        """
        # Calculate delta: if result is 'success' or 'non-catastrophic', delta is high
        outcome_delta = catastrophe_level if "catastrophe" not in result.lower() else 0.0
        
        experiment = MismatchExperiment(
            id=f"exp_{datetime.utcnow().timestamp()}",
            prediction=prediction,
            predicted_catastrophe_level=catastrophe_level,
            actual_outcome=result,
            outcome_delta=outcome_delta
        )
        
        logger.info(f"Mismatch Experiment Recorded: {experiment.id}, Delta: {outcome_delta}")
        
        # ULTRATHINK: Update Temporal Prior's continuity score in Hexis
        hexis = get_hexis_service()
        subconscious = await hexis.get_subconscious_state("dionysus_core")
        
        # Reduction in finality bias
        if outcome_delta > 0.5:
            subconscious.is_finality_predicted = False
            logger.info("False Prediction of Finality broken by Mismatch Experiment.")
            
        await hexis.update_subconscious_state("dionysus_core", subconscious)
        return experiment

    async def get_pop_cues(self, current_task: Optional[str] = None) -> list[str]:
        """
        Retrieve Point of Performance (PoP) cues helpful for the current state.
        """
        subconscious = await self._hexis.get_subconscious_state("dionysus_core")
        mode = subconscious.exoskeleton_mode
        
        cues = []
        if mode == ExoskeletonMode.RECOVERY:
            cues.append("REMINDER: Willpower is a limited resource - use the Exoskeleton.")
            cues.append("FOCUS: Do not retry the failed action directly; use the recovery path.")
        
        if current_task:
            cues.append(f"POINT OF PERFORMANCE: The target is {current_task}.")
            
        return cues

    async def log_grounding_closure(self, success: bool, feedback: Optional[str] = None):
        """
        Record the outcome of an exoskeleton intervention to refine future cues.
        """
        logger.info(f"Grounding closure: Success={success}, Feedback={feedback}")
        # This could be stored in Graphiti to improve the 'Exoskeleton' over time

def get_exoskeleton_service() -> ExoskeletonService:
    return ExoskeletonService()
