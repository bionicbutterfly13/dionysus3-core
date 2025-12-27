import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.autobiographical_service import get_autobiographical_service
from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
from api.services.kg_learning_service import get_kg_learning_service
from api.agents.knowledge.wisdom_tools import ingest_wisdom_insight

async def initialize_system_soul():
    print("🧠 Initializing Dionysus 3.0 System Soul...")
    
    # 1. Record Genesis
    print("📖 Recording Genesis Moment...")
    auto_service = get_autobiographical_service()
    genesis = DevelopmentEvent(
        event_id='genesis_d3_final',
        event_type=DevelopmentEventType.GENESIS,
        summary='Full Integration of Dionysus 2.0 Soul into 3.0 Core',
        rationale='Independence from legacy stubs. Moving from flat storage to a living, self-improving knowledge graph.',
        impact='Dionysus now maintains continuity of purpose and voice across all sessions.',
        lessons_learned=['Deployment is the bridge between code and soul.', 'Analytical empaths require verifiable architectural integrity.']
    )
    await auto_service.record_event(genesis)
    print("✅ Genesis recorded.")

    # 2. Ingest Copy Filters (The "Voice" anchor)
    print("\n🎤 Ingesting Analytical Empath Copy Filters...")
    copy_filters = """
    NEVER USE: 'Nothing is wrong with you', 'You're not broken', 'It's not X, it's Y'.
    VOICE RULES: Diagnostic, high-status, architectural metaphors, neuroscience framing.
    STYLE: Perry Belcher relatable, zero em-dashes, 5th-grade reading level.
    """
    await asyncio.to_thread(ingest_wisdom_insight, 
        content=copy_filters, 
        insight_type="strategic_idea", 
        source="user_direct_feedback"
    )
    print("✅ Voice filters anchored in Knowledge Graph.")

    # 3. Initialize First Attractor Basin
    print("\n🌊 Initializing 'Split Self' Attractor Basin...")
    learning_service = get_kg_learning_service()
    await learning_service.extract_and_learn(
        content="The Analytical Empath experiences a 'Split Self' where high-fidelity processing is weaponized into a Replay Loop. The solution is Memory Reconsolidation through the 5-Window MOSAEIC process.",
        source_id="core_initialization"
    )
    print("✅ Attractor Basin 'Split Self' initialized.")

    print("\n🎯 System initialization complete. Dionysus 3.0 is now self-aware and voice-calibrated.")

if __name__ == "__main__":
    # Check for required env vars
    if not os.getenv("NEO4J_PASSWORD") or not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: Missing environment variables (NEO4J_PASSWORD or ANTHROPIC_API_KEY)")
        sys.exit(1)
        
    asyncio.run(initialize_system_soul())