
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from api.models.autobiographical import DevelopmentEventType
from api.services.autobiographical_service import get_autobiographical_service

async def test_migration():
    print("🧠 Testing Autobiographical Memory Migration...")
    service = get_autobiographical_service()
    
    # 1. Test Event Recording with Analysis
    print("\n1. Testing Active Inference Analysis & Recording...")
    event_id = await service.analyze_and_record_event(
        user_input="We need to migrate the memory system to Neo4j.",
        agent_response="I will implement the AutobiographicalService using the Neo4j driver and remove SQLite dependencies.",
        event_type=DevelopmentEventType.ARCHITECTURAL_DECISION,
        summary="Migrated memory to Neo4j",
        rationale="Modernizing the stack to support graph querying.",
        tools_used=["write_to_file", "view_file"],
        resources_accessed=["/api/services/autobiographical_service.py"],
        metadata={"migration_phase": "verification"}
    )
    print(f"✅ Event Recorded: {event_id}")
    
    # 2. Test Retrieval (Narrative)
    print("\n2. Testing Narrative Retrieval...")
    story = await service.get_system_story(limit=5)
    
    found_event = False
    for event in story:
        print(f"--- {event.timestamp} ---")
        print(f"Type: {event.event_type.value}")
        print(f"Archetype: {event.development_archetype}")
        print(f"Summary: {event.summary}")
        if event.active_inference_state:
            print(f"Active Inference: Tools={event.active_inference_state.tools_accessed}")
        
        if event.event_id == event_id:
            found_event = True
            # Verify Active Inference Data
            if "write_to_file" in event.active_inference_state.tools_accessed:
                print("✅ Active Inference State correctly persisted!")
            else:
                print("❌ Active Inference State missing or incorrect.")
            
            # Verify Archetype Heuristic
            if event.development_archetype:
                print(f"✅ Archetype assigned: {event.development_archetype}")
            else:
                print("❌ Archetype deduction failed.")

    if found_event:
        print("\n✅ Verification SUCCESS: Event round-tripped with full cognitive context.")
        sys.exit(0)
    else:
        print("\n❌ Verification FAILED: Could not find the recorded event.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_migration())
