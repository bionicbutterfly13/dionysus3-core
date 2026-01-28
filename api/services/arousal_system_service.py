"""
Arousal System Service (Subcortical Controller)

Implements the dual subcortical control systems (Luu, Tucker, & Friston, 2024):
1. Dorsal / Lemnothalamic (NE): Mediates phasic triggers and set-switching (Epistemic).
2. Ventral / Collothalamic (DA): Mediates tonic activation and persistence (Instrumental).

Provides the "Synaptic Gain" modulation for vertical integration of cognition.
"""

from typing import Dict, Optional, Tuple, List
from api.models.biological_agency import (
    SubcorticalState, AgencyTier, MentalAffordance, ObjectAffordance, AffordanceCompetitionState, AttentionalAffordance
)
from api.services.shadow_log_service import ShadowLogService

class ArousalSystemService:
    """
    Manages the neurocomputational dynamics of subcortical arousal.
    
    This service acts as the 'subcortical controller' that modulates 
    cortical precision-weighting (synaptic gain).
    """
    
    def __init__(self, shadow_log_service: Optional[ShadowLogService] = None):
        self.shadow_log_service = shadow_log_service
        # Constants for dynamics
        self.NE_DECAY = 0.1  # Phasic NE decays quickly but not too fast
        self.DA_DECAY = 0.1  # Phasic DA decays more slowly
        self.SWITCH_THRESHOLD = 0.7  # Threshold for NE-driven set-switching
        self.BASE_GAIN = 1.0

    async def update_subcortical_state(
        self,
        current_state: SubcorticalState,
        surprisal: float,
        goal_proximity: float,
        affective_atmosphere: float,
        agency_tier: AgencyTier
    ) -> SubcorticalState:
        """
        Update the subcortical state based on new observations and goals.
        
        Args:
            current_state: Previous subcortical levels
            surprisal: Magnitude of prediction error (VFE)
            goal_proximity: Normalized distance to active goal (0-1)
            affective_atmosphere: Global balance of environment (-1.0 to 1.0)
            agency_tier: The agent's current operating tier
            
        Returns:
            Updated SubcorticalState
        """
        # 1. Update Norepinephrine (Dorsal System)
        # NE phasic is driven by surprisal/innovation
        new_ne_phasic = current_state.ne_phasic + (surprisal * (1.0 - current_state.ne_phasic))
        new_ne_phasic *= (1.0 - self.NE_DECAY)
        
        # NE tonic is influenced by the sustained level of surprise (uncertainty)
        new_ne_tonic = current_state.ne_tonic + 0.05 * (surprisal - current_state.ne_tonic)
        new_ne_tonic = max(0.0, min(1.0, new_ne_tonic))

        # 2. Update Dopamine (Ventral System)
        # DA phasic is driven by goal progress or 'Instrumental Affordance'
        # We use goal_proximity as a proxy for progress
        new_da_phasic = current_state.da_phasic + (goal_proximity * (1.0 - current_state.da_phasic))
        new_da_phasic *= (1.0 - self.DA_DECAY)
        
        # DA tonic is driven by the density of available affordances (persistence)
        new_da_tonic = current_state.da_tonic + 0.05 * (goal_proximity - current_state.da_tonic)
        new_da_tonic = max(0.1, min(1.0, new_da_tonic)) # Minimum tonic DA to prevent paralysis

        # 3. Calculate Synaptic Gain (Precision Modulation)
        # Gain = Weight * (DA_tonic) / (NE_tonic + small_epsilon)
        # Jorba & López-Silva (2024): Affective Atmosphere modulates the solicitation
        # We model this by shifting the gain: Positive atmosphere increases precision/focus.
        gain = (new_da_tonic * 2.0) / (0.5 + new_ne_tonic)
        gain += (affective_atmosphere * 0.5) 
        
        # Clip gain to avoid extreme values
        gain = max(0.1, min(5.0, gain))

        return SubcorticalState(
            ne_phasic=new_ne_phasic,
            ne_tonic=new_ne_tonic,
            da_phasic=new_da_phasic,
            da_tonic=new_da_tonic,
            synaptic_gain=gain
        )

    def potentiate_mental_affordances(
        self,
        subcortical: SubcorticalState,
        affordances: List[MentalAffordance]
    ) -> List[MentalAffordance]:
        """
        Calculate potentiation levels for mental opportunities.
        
        Informed by Proust (2024): Metacognitive feelings (doability)
        influence the reactive potentiation of cognitive actions.
        """
        updated = []
        for aff in affordances:
            # Base potentiation driven by phasic subcortical state (NE for exploration, DA for exploitation)
            # If it's a 'mental' action, we weight it by doability
            base_p = (subcortical.ne_phasic + subcortical.da_phasic) / 2.0
            
            # Feature 070: Potentiation = base * doability * fittingness_mod
            fitting_mod = 1.0 + (aff.fittingness * 0.2)
            potentiation = base_p * aff.doability_feeling * fitting_mod
            
            # Update the affordance instance
            aff.potentiation_level = max(0.0, min(1.0, potentiation))
            updated.append(aff)
            
        return updated

    def predict_manipulations(
        self,
        goals: List[str],
        object_affordances: List[ObjectAffordance],
        recipient_objects: List[str]
    ) -> List[str]:
        """
        Bach et al. (2014) Prediction Pathway: Goal -> Function -> Manipulation.
        """
        predictions = []
        for obj in object_affordances:
            for knowledge in obj.knowledge:
                # If the object function matches one of our goals
                if knowledge.function in goals:
                    # Check if any perceived recipient objects match requirements
                    if not obj.recipient_requirements or any(r in recipient_objects for r in obj.recipient_requirements):
                        predictions.append(knowledge.manipulation)
        return predictions

    def interpret_action_goal(
        self,
        observed_manipulation: str,
        object_affordances: List[ObjectAffordance]
    ) -> Dict[str, float]:
        """
        Bach et al. (2014) Interpretation Pathway: Manipulation -> Function -> Goal.
        """
        relevance_updates = {}
        for obj in object_affordances:
            for knowledge in obj.knowledge:
                # If observed movement matches object manipulation knowledge
                if knowledge.manipulation == observed_manipulation:
                    # Confirm the associated goal/function
                    relevance_updates[knowledge.function] = 1.0
        return relevance_updates

    def generate_attendabilia(
        self,
        object_affordances: List[ObjectAffordance],
        mental_opportunities: List[MentalAffordance]
    ) -> List[AttentionalAffordance]:
        """
        McClelland (2024): Populate the Priority Map (Attendabilia).
        Objects and mental actions are converted into opportunities for focal attention.
        """
        attendabilia = []
        
        # 1. Physical Objects -> Attentional Affordances
        for obj in object_affordances:
            aff_id = f"attn_{obj.object_label}"
            # Salience Heuristic: Novelty or visual movement (simulated here as random variation or passed data)
            # For now, we assume a baseline salience
            salience = 0.5 
            
            attendabilia.append(AttentionalAffordance(
                affordance_id=aff_id,
                target_object_id=obj.object_label,
                bottom_up_salience=salience
            ))
            
        # 2. Mental Opportunities -> Attentional Affordances (e.g., attending to a thought)
        for mental in mental_opportunities:
            aff_id = f"attn_mental_{mental.label}"
            attendabilia.append(AttentionalAffordance(
                affordance_id=aff_id,
                bottom_up_salience=mental.potentiation_level # Mental potentiation acts as 'internal salience'
            ))
            
        return attendabilia

    def resolve_attention_competition(
        self,
        attendabilia: List[AttentionalAffordance],
        active_goals: List[str],
        subcortical: SubcorticalState
    ) -> Tuple[List[AttentionalAffordance], Optional[str]]:
        """
        McClelland (2024) / Cisek (2007): Resolve competition for Focal Attention.
        
        Returns:
            - Updated list of attendabilia (with calculated Potentiation)
            - Winner ID (if any crosses threshold)
        """
        updated_list = []
        highest_potentiation = 0.0
        winner_id = None
        selection_threshold = 0.7
        
        # Distributed Control: Competition occurs via mutual inhibition simulation
        # In a snapshot simulation, we approximate the equilibrium state
        
        for aff in attendabilia:
            new_aff = aff.model_copy()
            
            # A. Top-Down Relevance (The 'Search')
            # If the attendabile links to an object that satisfies a goal
            relevance = 0.0
            # Note: We need the object map to verify this deep link, but for now we rely on 
            # the fact that perception passed valid objects.
            # Simplified: Assume if it exists it has some relevance unless filtered.
            if hasattr(new_aff, 'top_down_relevance'):
                 relevance = new_aff.top_down_relevance

            # B. Potentiation (Activation)
            # Potentiation = Salience + Relevance - Inhibition
            # We simulate inhibition as a function of the *total* salience of others (normalization)
            
            # Subcortical Modulation:
            # NE Phasic boosts 'Bottom-Up' (Startle/Capture)
            # DA Tonic boosts 'Top-Down' (Focus/Persistence)
            
            ne_factor = 1.0 + (subcortical.ne_phasic * 0.5)
            da_factor = 1.0 + (subcortical.da_tonic * 0.5)
            
            weighted_salience = new_aff.bottom_up_salience * ne_factor
            weighted_relevance = relevance * da_factor
            
            total_excitation = weighted_salience + weighted_relevance
            
            # Normalize to simulate lateral inhibition (Simplification of Cisek's ODE)
            # For a rigorous ODE we need the previous state, but here we calculate the *tendency* 
            # for the Priority Map snapshot.
            
            # Risk of Trivialization Note (Segundo-Ortin): 
            # We must ensure this isn't just a utility function. It represents 'Force of Pull'.
            
            if total_excitation > highest_potentiation:
                highest_potentiation = total_excitation
                if total_excitation > selection_threshold:
                    winner_id = new_aff.affordance_id
                    new_aff.is_focally_attended = True
            
            updated_list.append(new_aff)
            
        return updated_list, winner_id

    def resolve_competition(
        self,
        competition_state: AffordanceCompetitionState,
        subcortical: SubcorticalState,
        active_goals: List[str]
    ) -> AffordanceCompetitionState:
        """
        Cisek (2007) Affordance Competition using Biased Competition.
        """
        updated_affordances = {}
        highest_activation = 0.0
        winner_id = None
        
        # 1. Update each affordance
        for aff_id, aff in competition_state.competing_affordances.items():
            # Copy to avoid mutation
            new_aff = aff.model_copy()
            
            # A. Calculate Biasing Inputs
            # PFC Bias: If affordance aligns with active goals (Function Knowledge)
            pfc_bias = 0.0
            if new_aff.source_physical:
                for knowledge in new_aff.source_physical.knowledge:
                    if knowledge.function in active_goals:
                        pfc_bias += 0.3 # Strong Goal Support
            
            # Basal Ganglia Bias (Instrumental vs Exploration)
            bg_bias = 0.0
            if subcortical.da_tonic > 0.6: # High exploitation drive
                bg_bias += new_aff.instrumental_value * 0.2
            if subcortical.ne_phasic > 0.7: # High exploration drive (flattening)
                # Exploration reduces the advantage of currently active items
                if new_aff.activation_level > 0.5:
                    bg_bias -= 0.1
            
            # Update internal biases
            new_aff.top_down_utility = pfc_bias
            
            # B. Mutual Inhibition (Lateral Inhibition)
            # Sum of activation of ALL OTHER affordances
            inhibition = 0.0
            for other_id, other_aff in competition_state.competing_affordances.items():
                if other_id != aff_id:
                    inhibition += other_aff.activation_level * 0.4 # Inhibitory Weight
            
            # C. Self-Excitation (Hysteresis)
            self_excitation = new_aff.activation_level * 0.1
            
            # D. Net Activation Update
            # d(Act)/dt = -Decay + Excitation - Inhibition + Bias
            decay = 0.1 * new_aff.activation_level
            net_change = self_excitation - inhibition + pfc_bias + bg_bias - decay + (aff.bottom_up_salience * 0.2)
            
            new_act = new_aff.activation_level + net_change
            new_aff.activation_level = max(0.0, min(1.0, new_act))
            
            # Track winner candidate
            if new_aff.activation_level > highest_activation:
                highest_activation = new_aff.activation_level
                if highest_activation > competition_state.selection_threshold:
                    winner_id = aff_id
            
            updated_affordances[aff_id] = new_aff
            
        return AffordanceCompetitionState(
            competing_affordances=updated_affordances,
            winning_affordance_id=winner_id,
            selection_threshold=competition_state.selection_threshold
        )

    def should_set_switch(self, state: SubcorticalState) -> bool:
        """
        Determine if the agent should abandon current decision tree and explore.
        
        Driven by the Dorsal/Lemnothalamic system (NE phasic).
        """
        return state.ne_phasic > self.SWITCH_THRESHOLD

    def get_instrumental_weight(self, state: SubcorticalState) -> float:
        """
        Calculate the weight for instrumental affordances vs epistemic affordances.

        Driven by the Ventral/Collothalamic system (DA).
        """
        # High DA shifts weight towards exploitation (Instrumental)
        return max(0.1, min(0.9, state.da_tonic))

    def get_allostatic_load(self, state: SubcorticalState) -> float:
        """
        Calculate allostatic load for archetype resonance protocol.

        Track 002: Jungian Cognitive Archetypes

        Allostatic load represents the cumulative burden of adaptation and
        prediction errors. High load triggers resonance protocol to resurface
        suppressed archetypes (IFS-style "parts" rebalancing).

        Integration (IO Map):
        - Inlets: SubcorticalState from update_subcortical_state()
        - Outlets: float → ShadowLog.check_resonance()

        Components:
        1. High NE tonic (sustained uncertainty/surprisal)
        2. Low DA tonic (lack of goal progress/reward)
        3. High NE phasic (recent startle/prediction errors)
        4. Low synaptic gain (impaired precision weighting)

        Returns:
            Normalized allostatic load (0-1), where >0.75 triggers resonance
        """
        # NE tonic: sustained uncertainty contributes to load
        uncertainty_component = state.ne_tonic * 0.35

        # DA tonic: low goal progress contributes to load (inverted)
        # Low DA = high load, High DA = low load
        goal_deficit_component = (1.0 - state.da_tonic) * 0.25

        # NE phasic: recent prediction errors contribute
        prediction_error_component = state.ne_phasic * 0.25

        # Synaptic gain: low gain (impaired integration) contributes
        # Normalize gain from [0.1, 5.0] to [0, 1] then invert
        normalized_gain = (state.synaptic_gain - 0.1) / 4.9
        gain_deficit_component = (1.0 - normalized_gain) * 0.15

        # Combine components
        allostatic_load = (
            uncertainty_component +
            goal_deficit_component +
            prediction_error_component +
            gain_deficit_component
        )

        return max(0.0, min(1.0, allostatic_load))
