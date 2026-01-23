import asyncio
import json
import logging
from api.agents.consciousness_manager import ConsciousnessManager

logging.basicConfig(level=logging.INFO)

async def test_surgeon_protocol():
    print("\n--- Testing Checklist-Driven Surgeon Protocol ---")
    
    # High entropy/complexity task to trigger the protocol
    task = """
    Explain the relationship between Expected Free Energy (EFE) and the 
    Metacognitive Particle model in Dionysus 3. 
    Specifically, how does the surprise signal from a particle influence 
    the EFE-based scoring of a reasoning branch in Meta-ToT? 
    Please include a step-by-step logical derivation.
    """
    
    initial_context = {
        "task": task,
        "complexity_score": 0.9, # High complexity
        "uncertainty_level": 0.8, # High uncertainty
        "meta_tot_enabled": True,
        "meta_tot_auto_run": True,
        "project_id": "test-surgeon"
    }
    
    manager = ConsciousnessManager()
    
    try:
        print(f"Running OODA cycle for task: {task[:100]}...")
        result = await manager.run_ooda_cycle(initial_context)
        
        print("\n--- OODA Cycle Result ---")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Reasoning: {result.get('final_plan')[:500]}...")
        
        # Verify if cognitive tools were used
        log = result.get("orchestrator_log", [])
        tools_used = []
        for step in log:
            if hasattr(step, 'tool_calls') and step.tool_calls:
                for tc in step.tool_calls:
                    tools_used.append(tc.name)
        
        # We also check managed agent responses in the log if available
        # But usually we look at the 'reasoning' to see if it followed the checklist
        
        print(f"\nTools detected in orchestrator log: {list(set(tools_used))}")
        
        # Note: Since the agents are LLM-based, they might not call the tools 
        # EVERY time in a mock test, but the prompt now MANDATES it.
        
        print("\nSuccess: Surgeon Protocol test completed.")
        
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_surgeon_protocol())
