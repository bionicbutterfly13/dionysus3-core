import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from api.services.coordination_service import get_coordination_service, AgentStatus

def run_tests():
    print("=== Verifying Daedalus Phase 2: Context Isolation ===")
    
    svc = get_coordination_service()
    
    # 1. Test Initialization
    print("\n[Test 1] Testing Field Initialization...")
    svc.agents.clear()
    agent_id = svc.spawn_agent()
    agent = svc.agents[agent_id]
    
    if agent.tool_session_id and agent.memory_handle_id:
        print("PASS: tool_session_id and memory_handle_id are present.")
    else:
        print(f"FAIL: Missing fields. Session: {agent.tool_session_id}, Memory: {agent.memory_handle_id}")
        return

    # 2. Test Tool Session Collision
    print("\n[Test 2] Testing Tool Session Collision Detection...")
    svc.agents.clear()
    a1_id = svc.spawn_agent()
    a2_id = svc.spawn_agent()
    a1 = svc.agents[a1_id]
    a2 = svc.agents[a2_id]
    
    # Force collision
    print(f"DEBUG: Forcing collision. A1 Session: {a1.tool_session_id} -> Assigned to A2.")
    a2.tool_session_id = a1.tool_session_id
    
    svc._check_isolation(a2)
    
    if a2.isolation["shared_state_detected"]:
        print("PASS: Collision detected.")
    else:
        print("FAIL: Collision NOT detected.")
        return

    # 3. Test Report Generation
    print("\n[Test 3] Testing Isolation Report Generation...")
    report = svc.generate_isolation_report()
    print(f"Report Summary: {report['total_agents']} agents, {report['breaches_detected']} breaches.")
    
    if report["breaches_detected"] >= 1:
        print("PASS: Report correctly identified breach.")
    else:
        print("FAIL: Report failed to identify breach.")
        return

    print("\n=== ALL ISOLATION TESTS PASSED ===")

if __name__ == "__main__":
    run_tests()
