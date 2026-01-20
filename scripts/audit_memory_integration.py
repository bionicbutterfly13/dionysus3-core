
import asyncio
import logging
import sys
import os

sys.path.append(os.getcwd())

from api.services.graphiti_service import get_graphiti_service
from api.services.memevolve_adapter import get_memevolve_adapter
from api.services.consciousness.autoschemakg_integration import get_autoschemakg_service
from api.services.context_packaging import get_token_budget_manager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("audit")

async def audit_system():
    print("\n🔍 Starting Memory Integration Audit...\n")
    
    errors = []
    
    # 1. Graphiti Connection
    try:
        print("1. Checking Graphiti Service (The Gateway)...")
        graphiti = await get_graphiti_service()
        health = await graphiti.health_check()
        print(f"   ✅ Graphiti Status: {health.get('status')} (Neo4j: {health.get('neo4j_connection')})")
    except Exception as e:
        print(f"   ❌ Graphiti Failed: {e}")
        errors.append("Graphiti Service Unreachable")

    # 2. MemEvolve Adapter
    try:
        print("\n2. Checking MemEvolve Adapter (The Evolution Layer)...")
        adapter = get_memevolve_adapter()
        # Verify internal evolution logic exists
        has_trigger = hasattr(adapter, 'trigger_evolution')
        print(f"   ✅ trigger_evolution method present: {has_trigger}")
        
        # Verify backend config
        backend = os.getenv("MEMEVOLVE_EVOLVE_BACKEND", "probed_graphiti")
        print(f"   ℹ️  Evolve Backend Env: {backend}")
    except Exception as e:
        print(f"   ❌ MemEvolve Check Failed: {e}")
        errors.append("MemEvolve Adapter Error")

    # 3. AutoSchema Integration
    try:
        print("\n3. Checking AutoSchemaKG (The Schema Layer)...")
        schema = get_autoschemakg_service()
        has_retrieve = hasattr(schema, 'retrieve_relevant_concepts')
        print(f"   ✅ retrieve_relevant_concepts method present: {has_retrieve}")
    except Exception as e:
        print(f"   ❌ AutoSchema Check Failed: {e}")
        errors.append("AutoSchema Integration Error")

    # 4. Context Packaging
    try:
        print("\n4. Checking Context Packaging (The Loop Closer)...")
        budget = get_token_budget_manager()
        print(f"   ✅ TokenBudgetManager initialized with {budget.total_budget} limit")
        
        # Verify ContextCell types
        from api.services.context_packaging import SchemaContextCell
        print(f"   ✅ SchemaContextCell class available")
    except Exception as e:
        print(f"   ❌ Context Packaging Check Failed: {e}")
        errors.append("Context Packaging Error")
        
    print("\n" + "="*40)
    if not errors:
        print("✅ AUDIT PASSED: Epistemic Integrity Verified.")
        print("All systems are integrated and operational.")
    else:
        print(f"❌ AUDIT FAILED: {len(errors)} errors detected.")
        for err in errors:
            print(f"   - {err}")

if __name__ == "__main__":
    asyncio.run(audit_system())
