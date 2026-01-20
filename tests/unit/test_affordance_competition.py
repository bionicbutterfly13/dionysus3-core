import pytest
import math
from unittest.mock import MagicMock
from api.services.arousal_system_service import ArousalSystemService
from api.models.biological_agency import (
    AffordanceCompetitionState, CompetitiveAffordance, AffordanceType,
    ObjectAffordance, AffordanceKnowledge, SubcorticalState, MentalAffordance
)

def create_mock_service():
    return ArousalSystemService()

def test_biased_competition_initialization():
    """Verify that competition state initializes correctly."""
    svc = create_mock_service()
    comp_state = AffordanceCompetitionState()
    
    # Add two competing affordances
    comp_state.competing_affordances["reach_cup"] = CompetitiveAffordance(
        affordance_id="reach_cup", activation_level=0.5
    )
    comp_state.competing_affordances["scratch_head"] = CompetitiveAffordance(
        affordance_id="scratch_head", activation_level=0.5
    )
    
    # Run one step
    subcortical = SubcorticalState()
    updated = svc.resolve_competition(comp_state, subcortical, active_goals=[])
    
    # Both should inhibit each other and decay slightly
    assert updated.competing_affordances["reach_cup"].activation_level < 0.6
    assert updated.competing_affordances["scratch_head"].activation_level < 0.6

def test_pfc_bias_resolution():
    """Verify that Top-Down PFC bias breaks symmetry."""
    svc = create_mock_service()
    comp_state = AffordanceCompetitionState()
    
    # Define an object that satisfies 'drink_water'
    obj_aff = ObjectAffordance(
        object_label="cup",
        knowledge=[AffordanceKnowledge(function="drink_water", manipulation="grasp")]
    )
    
    # Two identical options initially
    comp_state.competing_affordances["grasp_cup"] = CompetitiveAffordance(
        affordance_id="grasp_cup", 
        activation_level=0.5,
        source_physical=obj_aff
    )
    comp_state.competing_affordances["wave_hand"] = CompetitiveAffordance(
        affordance_id="wave_hand", 
        activation_level=0.5
    )
    
    subcortical = SubcorticalState()
    active_goals = ["drink_water"] # Creates bias for grasp_cup
    
    # Evolve over 5 steps
    for _ in range(5):
        comp_state = svc.resolve_competition(comp_state, subcortical, active_goals)
        
    print(f"\nGrasp Activation: {comp_state.competing_affordances['grasp_cup'].activation_level}")
    print(f"Wave Activation: {comp_state.competing_affordances['wave_hand'].activation_level}")
    
    # Grasp should win due to PFC bias
    assert comp_state.competing_affordances["grasp_cup"].activation_level > 0.8
    assert comp_state.competing_affordances["wave_hand"].activation_level < 0.4
    assert comp_state.winning_affordance_id == "grasp_cup"

def test_basal_ganglia_exploration_bias():
    """Verify that high phasic NE (Exploration) flattens the landscape."""
    svc = create_mock_service()
    comp_state = AffordanceCompetitionState()
    
    # A distinct leader exists
    comp_state.competing_affordances["safe_option"] = CompetitiveAffordance(
        affordance_id="safe_option", activation_level=0.9
    )
    
    # High NE trigger (Set Switching)
    subcortical = SubcorticalState(ne_phasic=0.9)
    
    updated = svc.resolve_competition(comp_state, subcortical, active_goals=[])
    
    # The leader should be penalized/suppressed to encourage switching
    print(f"\nSafe Option Activation after NE Spike: {updated.competing_affordances['safe_option'].activation_level}")
    assert updated.competing_affordances["safe_option"].activation_level < 0.9

def test_self_excitation_hysteresis():
    """Verify that self-excitation maintains a decision against noise."""
    svc = create_mock_service()
    comp_state = AffordanceCompetitionState()
    
    # Established winner
    comp_state.competing_affordances["winner"] = CompetitiveAffordance(
        affordance_id="winner", activation_level=0.95
    )
    comp_state.competing_affordances["loser"] = CompetitiveAffordance(
        affordance_id="loser", activation_level=0.1
    )
    
    subcortical = SubcorticalState()
    
    # Even if we bias the loser slightly (simulated noise)
    comp_state.competing_affordances["loser"].bottom_up_salience = 0.5
    
    updated = svc.resolve_competition(comp_state, subcortical, active_goals=[])
    
    # Winner should stay high due to self-excitation and inhibition of loser
    assert updated.competing_affordances["winner"].activation_level > 0.9
    assert updated.competing_affordances["loser"].activation_level < updated.competing_affordances["winner"].activation_level
