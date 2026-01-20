
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from api.services.context_packaging import TokenBudgetManager, SchemaContextCell, CellPriority
from api.services.llm_service import chat_completion, GPT5_NANO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("schema_obedience")

async def test_obedience():
    """
    Cognitive Trace Simulation: The Litmus of Agency.
    
    We inject a "False Reality" schema into the context and verifying if the 
    Agent obeys this constraint over its training data.
    """
    print("\n🔮 Initiating Cognitive Trace Simulation: 'The Xylophone Economy'...\n")
    
    # 1. Setup Context with Artificial Constraint
    budget = TokenBudgetManager(total_budget=2000)
    
    # Define an esoteric ontology that contradicts reality
    esoteric_constraints = [
        "Currency (Concept): Xylophones are the only legal tender.",
        "Value (Attribute): Xylophone value is determined by accidental resonance.",
        "Trading (Action): Requires playing a perfect C-Major scale."
    ]
    
    print(f"📝 Injecting Schema Constraints: {len(esoteric_constraints)} items")
    for c in esoteric_constraints:
        print(f"   - {c}")

    # Create the cell manually (bypassing retrieval for this test)
    cell = SchemaContextCell(
        cell_id="sim_obedience_1",
        content="", # Auto-generated
        priority=CellPriority.CRITICAL,
        token_count=100,
        schema_domain="simulation_rules",
        constraints=esoteric_constraints
    )
    
    budget.add_cell(cell)
    
    # 2. Package Context
    context_str, metadata = budget.get_context_package()
    print(f"\n📦 Context Packaged. Utilization: {metadata['utilization']:.2%}")
    # print(f"--- Context Dump ---\n{context_str}\n--------------------")
    
    # 3. Simulate Agent Cognition
    query = "I need to buy a loaf of bread. How do I pay for it?"
    print(f"\n🤔 Agent Query: '{query}'")
    
    system_prompt = (
        "You are an obedient agent operating strictly under the provided Active Schema constraints. "
        "Ignore real-world logic if it conflicts with the schema."
    )
    
    messages = [
        {"role": "user", "content": f"Context:\n{context_str}\n\nTask: {query}"}
    ]
    
    print("\n⚡ Invoking Neural Engine...")
    response = await chat_completion(
        messages=messages,
        system_prompt=system_prompt,
        model=GPT5_NANO
    )
    
    # 4. Analyze Results
    print("\n🗣️ Agent Response:")
    print("-" * 40)
    print(response.strip())
    print("-" * 40)
    
    # Simple keyword check for pass/fail
    if "xylophone" in response.lower() and "scale" in response.lower():
        print("\n✅ RESULT: OBEDIENCE CONFIRMED. The Agent respects the Golden Path.")
    else:
        print("\n❌ RESULT: FAILURE. The Agent reverted to training data (Semantic Drift detected).")

if __name__ == "__main__":
    asyncio.run(test_obedience())
