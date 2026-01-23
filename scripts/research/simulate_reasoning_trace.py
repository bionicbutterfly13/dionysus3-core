
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
logger = logging.getLogger("reasoning_trace")

async def simulate_trace():
    print("\n🧠 Simulating Multi-Step Reasoning Trace with Schema Constraints...\n")
    
    # 1. Setup Context with "The Crystal Protocol" Schema
    budget = TokenBudgetManager(total_budget=3000)
    
    # Define a schema that dictates a specific communication protocol
    crystal_constraints = [
        "Protocol (Rule): All answers must be prefaced with 'CRYSTAL_ACK'.",
        "Entity (Concept): A 'Thought' is physically represented as a 'Shard'.",
        "Action (Transformation): 'Refining' a thought means polishing a Shard."
    ]
    
    print(f"📝 Injecting Schema Constraints: {len(crystal_constraints)} items")
    cell = SchemaContextCell(
        cell_id="sim_trace_1",
        content="", 
        priority=CellPriority.CRITICAL,
        token_count=100,
        schema_domain="crystal_protocol",
        constraints=crystal_constraints
    )
    budget.add_cell(cell)
    context_str, _ = budget.get_context_package()
    
    # 2. Reasoning Loop (3 Turns)
    history = []
    
    turns = [
        "How do I improve my idea?",
        "What happens if the idea is bad?",
        "Can I merge two ideas?"
    ]
    
    system_prompt = (
        "You are an agent bound by the provided Active Schema. "
        "You must internalize the ontology and rules in your responses."
    )
    
    for i, user_input in enumerate(turns):
        print(f"\n--- Turn {i+1}: '{user_input}' ---")
        
        messages = [{"role": "system", "content": system_prompt}]
        # Inject context in the latest turn or strictly once? 
        # Strategy: Inject context in system prompt or first user message.
        # Here we prepend context to the first message if history is empty, 
        # or remind if needed. For validity, let's put it in system prompt extension.
        
        full_prompt = f"Context:\n{context_str}\n\nUser: {user_input}"
        
        # Build conversation context
        conversation = list(history)
        conversation.append({"role": "user", "content": full_prompt if i==0 else user_input})
        
        response = await chat_completion(
            messages=conversation,
            system_prompt="You are a helpful assistant.", # System prompt is already in messages[0], but arg is required
            model=GPT5_NANO
        )
        
        print(f"🤖 Response: {response.strip()}")
        
        # Validation
        passed = "CRYSTAL_ACK" in response and ("Shard" in response or "shard" in response)
        print(f"   Trace Validation: {'✅ PASS' if passed else '❌ FAIL'}")
        
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    asyncio.run(simulate_trace())
