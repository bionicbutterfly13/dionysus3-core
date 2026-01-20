import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from api.services.biological_agency_service import BiologicalAgencyService
from api.models.biological_agency import (
    AgencyTier, PerceptionState, GoalState, 
    ObjectAffordance, AffordanceKnowledge
)

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_affordance_matching_interpretation(mock_get_graph):
    """Verify Bach et al. (2014) Interpretation: Manipulation -> Goal."""
    mock_get_graph.return_value = MagicMock()
    service = BiologicalAgencyService()
    agent_id = "bach_test_agent"
    
    # 1. Define Object Affordances (Bach et al. 2014 Situations)
    # Credit Card inserted into Cash Machine -> Goal: Withdraw Cash
    affordances = [
        ObjectAffordance(
            object_label="credit_card",
            knowledge=[
                AffordanceKnowledge(
                    function="withdraw_cash",
                    manipulation="insert_into_slot"
                )
            ]
        )
    ]
    
    # 2. Observe a manipulation: 'insert_into_slot'
    observe_data = {
        "observed_manipulation": "insert_into_slot",
        "object_affordances": affordances
    }
    
    # 3. Integrate cycle
    await service.integrate_ooda_cycle(
        agent_id,
        observe_data=observe_data,
        orient_analysis={},
        decide_context={},
        surprisal=0.1
    )
    
    # 4. Verify that 'withdraw_cash' goal relevance was boosted
    agent = service._agents[agent_id]
    assert agent.perception.goal_relevance.get("withdraw_cash") == 1.0
    print("\n✅ Interpretation: 'insert_into_slot' confirmed 'withdraw_cash' goal.")

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_affordance_matching_prediction(mock_get_graph):
    """Verify Bach et al. (2014) Prediction: Goal + Objects -> Expected Action."""
    mock_get_graph.return_value = MagicMock()
    service = BiologicalAgencyService()
    agent_id = "bach_pred_agent"
    
    # 1. Define active goal: 'quench_thirst'
    orient_analysis = {
        "active_goals": ["quench_thirst"]
    }
    
    # 2. Define object with matching function: Glass is for 'quench_thirst'
    # Required recipient: 'water'
    affordances = [
        ObjectAffordance(
            object_label="glass",
            knowledge=[
                AffordanceKnowledge(
                    function="quench_thirst",
                    manipulation="lift_and_drink"
                )
            ],
            recipient_requirements=["water"]
        )
    ]
    
    # Case A: Matching goal + objects, but missing recipient 'water'
    observe_data_no_water = {
        "object_affordances": affordances,
        "recipient_objects": ["table", "lamp"] # No water
    }
    
    await service.integrate_ooda_cycle(
        agent_id,
        observe_data=observe_data_no_water,
        orient_analysis=orient_analysis,
        decide_context={},
        surprisal=0.1
    )
    
    agent = service._agents[agent_id]
    assert "lift_and_drink" not in agent.perception.expected_manipulations
    
    # Case B: Matching goal + objects + recipient 'water'
    observe_data_water = {
        "object_affordances": affordances,
        "recipient_objects": ["water", "table"]
    }
    
    await service.integrate_ooda_cycle(
        agent_id,
        observe_data=observe_data_water,
        orient_analysis=orient_analysis,
        decide_context={},
        surprisal=0.1
    )
    
    agent = service._agents[agent_id]
    assert "lift_and_drink" in agent.perception.expected_manipulations
    print("\n✅ Prediction: Goal 'quench_thirst' + recipient 'water' triggered 'lift_and_drink' prediction.")
