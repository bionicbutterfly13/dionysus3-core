import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from api.services.biological_agency_service import BiologicalAgencyService
from api.models.biological_agency import AgencyTier, PerceptionState, GoalState, DecisionType, MentalAffordance

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_subcortical_arousal_set_switching(mock_get_graph):
    """Verify that high surprisal triggers set-switching (NE-driven)."""
    # Mock graph service to avoid Neo4j persistence errors
    mock_graph = MagicMock()
    mock_get_graph.return_value = mock_graph
    
    # Mock driver and session
    mock_driver = MagicMock()
    mock_graph.get_driver.return_value = mock_driver
    
    # Fix: session().__aenter__ should return the mock session
    mock_session = MagicMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    service = BiologicalAgencyService()
    agent_id = "test_set_switch_agent"
    
    # Create agent at Tier 3
    agent = await service.create_agent(agent_id, initial_tier=AgencyTier.METACOGNITIVE)
    
    # Mock data
    perception = PerceptionState(attended_situations=["status_quo"])
    goals = GoalState(active_goals=["pursue_goal"], goal_priorities={"pursue_goal": 0.5})
    decision_tree = [{"id": "path1", "action": "stay", "expected_outcome": 0.8}]
    
    # 1. Low surprisal - Should NOT trigger set-switch
    await service.integrate_ooda_cycle(
        agent_id=agent_id,
        observe_data={},
        orient_analysis={},
        decide_context={},
        surprisal=0.1
    )
    
    decision, metacog = await service.process_tier3_decision(
        agent_id=agent_id,
        perception=perception,
        goals=goals,
        decision_tree=decision_tree
    )
    
    assert "set_switching" not in metacog.active_strategies
    assert metacog.prior_weight == 0.5
    
    # 2. High repeated surprisal - Should trigger set-switch
    # Phasic NE accumulates
    for _ in range(5):
        await service.integrate_ooda_cycle(
            agent_id=agent_id,
            observe_data={},
            orient_analysis={},
            decide_context={},
            surprisal=0.9
        )
    
    decision, metacog = await service.process_tier3_decision(
        agent_id=agent_id,
        perception=perception,
        goals=goals,
        decision_tree=decision_tree
    )
    
    assert "set_switching" in metacog.active_strategies
    assert metacog.prior_weight == 0.1 # Heavily deweighted priors
    print(f"Set-switching triggered. NE phasic: {agent.subcortical.ne_phasic:.2f}")

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_dopamine_precision_gain(mock_get_graph):
    """Verify that goal proximity increases synaptic gain (DA-driven)."""
    mock_get_graph.return_value = MagicMock()
    
    service = BiologicalAgencyService()
    agent_id = "test_da_gain_agent"
    
    agent = await service.create_agent(agent_id, initial_tier=AgencyTier.METACOGNITIVE)
    initial_gain = agent.subcortical.synaptic_gain
    
    # High goal proximity (DA driven)
    await service.integrate_ooda_cycle(
        agent_id=agent_id,
        observe_data={},
        orient_analysis={},
        decide_context={},
        surprisal=0.0,
        goal_proximity=0.9
    )
    
    assert agent.subcortical.da_tonic > 0.5
    assert agent.subcortical.synaptic_gain > initial_gain
    
    # Verify it affects cognitive effort budget
    goals = GoalState(active_goals=["goal"])
    decision, metacog = await service.process_tier3_decision(
        agent_id=agent_id,
        perception=PerceptionState(),
        goals=goals,
        decision_tree=[{"action": "act"}]
    )
    
    # cognitive_effort_budget is multiplied by synaptic_gain
    assert metacog.cognitive_effort_budget > 0.3 # Base for 1 goal is roughly 0.3
    print(f"DA Gain: {agent.subcortical.synaptic_gain:.2f}, Budget: {metacog.cognitive_effort_budget:.2f}")

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_affective_atmosphere_modulation(mock_get_graph):
    """Verify that Affective Atmosphere (García 2024) modulates synaptic gain."""
    mock_get_graph.return_value = MagicMock()
    
    service = BiologicalAgencyService()
    agent_id = "test_atmosphere_agent"
    agent = await service.create_agent(agent_id)
    
    # 1. Neutral Atmosphere
    await service.integrate_ooda_cycle(agent_id, {}, {}, {}, affective_atmosphere=0.0)
    neutral_gain = agent.subcortical.synaptic_gain
    
    # 2. Positive Atmosphere
    await service.integrate_ooda_cycle(agent_id, {}, {}, {}, affective_atmosphere=0.8)
    positive_gain = agent.subcortical.synaptic_gain
    
    assert positive_gain > neutral_gain
    print(f"Atmospheric Modulation: {neutral_gain:.2f} -> {positive_gain:.2f}")

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_mental_affordance_potentiation(mock_get_graph):
    """Verify that 'doability' modulates mental affordance potentiation (Proust 2024)."""
    mock_get_graph.return_value = MagicMock()
    
    service = BiologicalAgencyService()
    agent_id = "test_potentiation_agent"
    
    # High surprisal to drive base potentiation
    surprisal = 0.8
    
    # Perceived mental opportunities
    opportunities = [
        MentalAffordance(label="calculate", doability_feeling=0.9), # Doable
        MentalAffordance(label="reflect", doability_feeling=0.1)     # Hopeless
    ]
    
    perception = PerceptionState(mental_opportunities=opportunities)
    
    await service.integrate_ooda_cycle(
        agent_id, 
        observe_data={"mental_opportunities": opportunities}, 
        orient_analysis={}, 
        decide_context={}, 
        surprisal=surprisal
    )
    
    # The integrate_ooda_cycle should have updated potentiation_level
    updated_opps = service._agents[agent_id].perception.mental_opportunities
    
    calculate = next(o for o in updated_opps if o.label == "calculate")
    reflect = next(o for o in updated_opps if o.label == "reflect")
    
    assert calculate.potentiation_level > reflect.potentiation_level
    print(f"Potentiation (Doable): {calculate.potentiation_level:.2f}")
    print(f"Potentiation (Hopeless): {reflect.potentiation_level:.2f}")

@pytest.mark.asyncio
@patch("api.services.biological_agency_service.BiologicalAgencyService._get_graph_service", new_callable=AsyncMock)
async def test_metacognitive_strategy_adjustment(mock_get_graph):
    """Verify that hopeless doability triggers strategy adjustment in Tier 3."""
    mock_get_graph.return_value = MagicMock()
    
    service = BiologicalAgencyService()
    agent_id = "test_strategy_agent"
    agent = await service.create_agent(agent_id, initial_tier=AgencyTier.METACOGNITIVE)
    
    # Perception with a hopeless mental affordance
    perception = PerceptionState(
        mental_opportunities=[MentalAffordance(label="complex_math", doability_feeling=0.05)]
    )
    
    decision, metacog = await service.process_tier3_decision(
        agent_id=agent_id,
        perception=perception,
        goals=GoalState(active_goals=["solve"]),
        decision_tree=[{"action": "try_math"}]
    )
    
    assert "seek_alternative_mental_path" in metacog.active_strategies
    # Should have reduced budget
    print(f"Hopeless Strategy: {metacog.active_strategies}, Budget: {metacog.cognitive_effort_budget:.2f}")

if __name__ == "__main__":
    asyncio.run(test_subcortical_arousal_set_switching())
    asyncio.run(test_dopamine_precision_gain())
