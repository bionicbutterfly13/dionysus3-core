
import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from api.services.context_packaging import TokenBudgetManager, fetch_schema_context
from api.services.consciousness.autoschemakg_integration import get_autoschemakg_service

# Configure simplified logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("schema_visualizer")

def print_header(title):
    print(f"\n{'='*60}")
    print(f" 🔭 {title}")
    print(f"{'='*60}")

def print_step(step, detail):
    print(f"\n➡️  STEP {step}: {detail}")

async def visualize_flow(query: str):
    print_header("Schema Retrieval Pipeline Visualization")
    print(f"Query: '{query}'")
    
    # Step 1: Initialize Budget
    print_step(1, "Initializing Token Budget Manager")
    budget = TokenBudgetManager(total_budget=4000)
    print(f"   Budget: {budget.total_budget} tokens")
    
    # Step 2: AutoSchema Retrieval
    print_step(2, "Calling AutoSchemaKG.retrieve_relevant_concepts()")
    svc = get_autoschemakg_service()
    
    # Inject a mock concept for visualization if DB is empty/unconnected (Simulation Mode)
    # For production usage, we would rely on actual DB. 
    # To ensure this visualizer works 'out of the box', we check connection first.
    try:
        concepts = await svc.retrieve_relevant_concepts(query)
    except Exception as e:
        print(f"   ⚠️  DB Connection Warning: {e}")
        concepts = []

    print(f"   Found {len(concepts)} relevant concepts via Hybrid Search.")
    for idx, c in enumerate(concepts):
        print(f"     {idx+1}. {c.name} ({c.concept_type.value}) - Conf: {c.confidence}")

    # Step 3: Context Packaging
    print_step(3, "Packaging into SchemaContextCell")
    cell = await fetch_schema_context(query, budget)
    
    if cell:
        print(f"   ✅ Cell Created: {cell.cell_id}")
        print(f"   Priority: {cell.priority}")
        print(f"   Token Cost: {cell.token_count}")
        print(f"   Utilization: {budget.utilization:.2%}")
        
        # Step 4: XML Rendering
        print_step(4, "Rendering System Prompt XML")
        print("   --- XML Output ---")
        print(cell.content)
        print("   ------------------")
    else:
        print("   ❌ No Schema Context created (No concepts found or budget full).")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        q = sys.argv[1]
    else:
        q = "How do I implement a memory optimization strategy?"
        
    asyncio.run(visualize_flow(q))
