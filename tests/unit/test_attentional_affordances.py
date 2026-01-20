import pytest
from unittest.mock import MagicMock
from api.models.biological_agency import (
    SubcorticalState, MentalAffordance, ObjectAffordance, 
    AffordanceKnowledge, AttentionalAffordance
)
from api.services.arousal_system_service import ArousalSystemService

@pytest.fixture
def arousal_service():
    return ArousalSystemService(shadow_log_service=MagicMock())

@pytest.fixture
def subcortical_baseline():
    return SubcorticalState(
        ne_phasic=0.2, ne_tonic=0.2,
        da_phasic=0.2, da_tonic=0.2,
        synaptic_gain=1.0
    )

def test_generate_attendabilia_objects(arousal_service):
    """Test that physical objects are converted to attentional affordances."""
    obj_affs = [
        ObjectAffordance(
            object_id="obj_1", object_label="cup",
            knowledge=[AffordanceKnowledge(function="drink", manipulation="grasp")]
        )
    ]
    mental_affs = []
    
    attendabilia = arousal_service.generate_attendabilia(obj_affs, mental_affs)
    
    assert len(attendabilia) == 1
    assert attendabilia[0].affordance_id == "attn_cup"
    assert attendabilia[0].target_object_id == "cup"
    assert attendabilia[0].bottom_up_salience == 0.5 # Default

def test_generate_attendabilia_mental(arousal_service):
    """Test that mental opportunities are converted to attentional affordances."""
    obj_affs = []
    mental_affs = [
        MentalAffordance(label="calculate_pi", potentiation_level=0.8)
    ]
    
    attendabilia = arousal_service.generate_attendabilia(obj_affs, mental_affs)
    
    assert len(attendabilia) == 1
    assert attendabilia[0].affordance_id == "attn_mental_calculate_pi"
    assert attendabilia[0].bottom_up_salience == 0.8 # Inherited

def test_competition_bottom_up_capture(arousal_service, subcortical_baseline):
    """
    Test that a highly salient object captures attention despite no goal relevance.
    Simulates 'The Bee' (McClelland 2024).
    """
    # High Bottom-Up Salience
    distractor = AttentionalAffordance(
        affordance_id="bee",
        bottom_up_salience=0.9,
        top_down_relevance=0.0
    )
    # Low Salience, No relevance
    boring = AttentionalAffordance(
        affordance_id="wall",
        bottom_up_salience=0.1,
        top_down_relevance=0.0
    )
    
    attendabilia = [distractor, boring]
    active_goals = []
    
    # NE Phasic boost (Startle) to enhance bottom-up capture
    subcortical_baseline.ne_phasic = 0.8 
    
    updated, winner_id = arousal_service.resolve_attention_competition(
        attendabilia, active_goals, subcortical_baseline
    )
    
    assert winner_id == "bee"
    # Verify 'bee' potentiation is high
    bee = next(a for a in updated if a.affordance_id == "bee")
    assert bee.is_focally_attended is True

def test_competition_top_down_search(arousal_service, subcortical_baseline):
    """
    Test that goal relevance boosts a low-salience object to win.
    Simulates 'Searching for keys'.
    """
    # Low Salience but High Relevance
    keys = AttentionalAffordance(
        affordance_id="keys",
        bottom_up_salience=0.2,
        top_down_relevance=0.8 # Strong relevance
    )
    # Medium Salience but irrelevant
    tv = AttentionalAffordance(
        affordance_id="tv",
        bottom_up_salience=0.5,
        top_down_relevance=0.0
    )
    
    attendabilia = [keys, tv]
    active_goals = ["find_keys"]
    
    # DA Tonic boost (Persistence) to enhance top-down gain
    subcortical_baseline.da_tonic = 0.8
    
    updated, winner_id = arousal_service.resolve_attention_competition(
        attendabilia, active_goals, subcortical_baseline
    )
    
    assert winner_id == "keys"
    keys_res = next(a for a in updated if a.affordance_id == "keys")
    assert keys_res.is_focally_attended is True

def test_competition_inhibition(arousal_service, subcortical_baseline):
    """
    Test that multiple high-salience items inhibit each other, potentially causing no winner
    if the threshold is high. (Distributed Control / Consensus).
    """
    # Two identical high salience items
    item1 = AttentionalAffordance(affordance_id="A", bottom_up_salience=0.8)
    item2 = AttentionalAffordance(affordance_id="B", bottom_up_salience=0.8)
    
    attendabilia = [item1, item2]
    active_goals = []
    
    # With mutual inhibition, neither might win if they cancel out or struggle
    # In our simplified logic, they might both have high excitation but only one wins due to order
    # OR if we implemented strict inhibition, they both drop.
    # Our current logic finds the MAX.
    
    updated, winner_id = arousal_service.resolve_attention_competition(
        attendabilia, active_goals, subcortical_baseline
    )
    
    # Ideally, one wins (arbitrary) or both fail.
    # Given the logic: "if total_excitation > highest... winner = ID"
    # It selects the first one encountered if equal? No, strict > checks.
    # total_excitation will be same. 
    # Logic: if total > highest (starts 0).
    # 1. A: exc=X. highest=X. winner=A.
    # 2. B: exc=X. X > X is False. 
    # Winner remains A.
    
    assert winner_id == "A" 
