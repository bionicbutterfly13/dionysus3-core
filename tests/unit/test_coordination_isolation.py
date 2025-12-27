from api.services.coordination_service import get_coordination_service, AgentStatus

def test_isolation_fields_initialized():
    svc = get_coordination_service()
    svc.agents.clear()
    
    agent_id = svc.spawn_agent()
    agent = svc.agents[agent_id]
    
    assert agent.tool_session_id is not None
    assert agent.memory_handle_id is not None
    assert len(agent.tool_session_id) > 0
    assert len(agent.memory_handle_id) > 0

def test_tool_session_collision_detection():
    svc = get_coordination_service()
    svc.agents.clear()
    
    a1_id = svc.spawn_agent()
    a2_id = svc.spawn_agent()
    
    a1 = svc.agents[a1_id]
    a2 = svc.agents[a2_id]
    
    # Simulate collision
    a2.tool_session_id = a1.tool_session_id
    
    # Run check
    svc._check_isolation(a2)
    
    assert a2.isolation["shared_state_detected"] is True
    assert any("tool_session_id" in note for note in a2.isolation["notes"])

def test_memory_handle_collision_detection():
    svc = get_coordination_service()
    svc.agents.clear()
    
    a1_id = svc.spawn_agent()
    a2_id = svc.spawn_agent()
    
    a1 = svc.agents[a1_id]
    a2 = svc.agents[a2_id]
    
    # Simulate collision
    a2.memory_handle_id = a1.memory_handle_id
    
    # Run check
    svc._check_isolation(a2)
    
    assert a2.isolation["shared_state_detected"] is True
    assert any("memory_handle_id" in note for note in a2.isolation["notes"])

def test_generate_isolation_report():
    svc = get_coordination_service()
    svc.agents.clear()
    
    a1_id = svc.spawn_agent()
    a2_id = svc.spawn_agent()
    
    # Create collision
    svc.agents[a2_id].tool_session_id = svc.agents[a1_id].tool_session_id
    
    report = svc.generate_isolation_report()
    
    assert report["total_agents"] == 2
    assert report["breaches_detected"] >= 1  # a2 is breached, a1 might be depending on check order but usually current is checked against others
    
    details = report["details"]
    assert len(details) == 2
    
    # Find the breached agent in details
    breached = next(d for d in details if d["agent_id"] == a2_id)
    assert breached["isolated"] is False
    assert any("tool_session_id" in note for note in breached["issues"])
