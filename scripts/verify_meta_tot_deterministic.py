
import asyncio
import logging
import sys
import os

# Ensure we can import from api
sys.path.append(os.getcwd())

from api.services.meta_tot_engine import get_meta_tot_engine, MetaToTConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dionysus.verify")

async def verify_deterministic():
    print("--- Starting Meta-ToT Deterministic Verification ---")
    
    engine = get_meta_tot_engine()
    
    # Configuration: No LLM (use fallback) for speed and determinism check
    # Branching factor 3, Depth 2 -> Small tree
    config = MetaToTConfig(
        use_llm=False, 
        branching_factor=3, 
        max_depth=2,
        persist_trace=False
    )
    
    problem = "How to maximize system stability?"
    context = {"constraints": ["low latency", "high throughput"]}
    
    print(f"Problem: {problem}")
    print("Running 3 separate passes...")
    
    results = []
    traces = []
    
    for i in range(3):
        print(f"  Run {i+1}...")
        result, trace = await engine.run(problem, context, config_overrides=config.__dict__)
        results.append(result)
        traces.append(trace)
        
        # Verify Score Logic (1 / 1+FE)
        # We look at the best path leaf node from the trace
        leaf_id = result.best_path[-1]
        leaf_node = next(n for n in trace.nodes if n.node_id == leaf_id)
        
        print(f"    Selected Path: {result.best_path}")
        print(f"    Best Action: {leaf_node.thought[:50]}...")
        print(f"    Leaf Score: {leaf_node.score:.4f}")
        print(f"    Leaf Free Energy: {leaf_node.free_energy:.4f}")
        
    # Check Determinism of CONTENT (not UUIDs)
    final_thoughts = []
    for r, t in zip(results, traces):
        leaf_id = r.best_path[-1]
        leaf = next(n for n in t.nodes if n.node_id == leaf_id)
        final_thoughts.append(leaf.thought)
        
    if all(t == final_thoughts[0] for t in final_thoughts):
        print("\n✅ DETERMINISM CONFIRMED: All 3 runs produced identical thought content.")
    else:
        print("\n❌ DETERMINISM FAILED: Thoughts differed.")
        print(final_thoughts)
        
    # Check Active Inference Logic
    # The score should be 1.0 / (1.0 + free_energy)
    first_leaf = next(n for n in trace.nodes if n.node_id == results[0].best_path[-1])
    expected_score = 1.0 / (1.0 + first_leaf.free_energy)
    if abs(first_leaf.score - expected_score) < 0.0001:
        print("✅ SCORING LOGIC CONFIRMED: Score matches Free Energy formula.")
    else:
        print(f"❌ SCORING LOGIC FAILED: {first_leaf.score} != {expected_score}")
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_deterministic())
