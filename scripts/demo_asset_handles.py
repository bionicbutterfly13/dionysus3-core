
import os
import json
from smolagents import CodeAgent, LiteLLMModel, tool

# 1. Define tools that leverage the new library-level Assets

@tool
def save_manuscript_chapter(chapter_num: int, content: str) -> str:
    """
    Saves a chapter to the system's native Asset store.
    Returns a handle that can be used by other agents.
    
    Args:
        chapter_num: The index of the chapter.
        content: The actual text content of the chapter.
    """
    # Access the agent's memory directly via library enhancement
    # 'agent' is passed to tool calls in smolagents
    from smolagents.agents import MultiStepAgent
    import inspect
    
    # Locate the agent in the stack to access its memory
    frame = inspect.currentframe()
    agent = None
    while frame:
        if 'self' in frame.f_locals and isinstance(frame.f_locals['self'], MultiStepAgent):
            agent = frame.f_locals['self']
            break
        frame = frame.f_back
    
    if agent:
        handle = agent.memory.save_asset(f"chapter_{chapter_num}", content)
        return handle
    return "Error: Could not find agent memory store."

@tool
def audit_asset(asset_handle: str) -> str:
    """
    Retrieves an asset by its handle and performs a tone audit.
    
    Args:
        asset_handle: The handle returned by save_manuscript_chapter (e.g. '{{asset:chapter_1}}')
    """
    from smolagents.agents import MultiStepAgent
    import inspect
    
    frame = inspect.currentframe()
    agent = None
    while frame:
        if 'self' in frame.f_locals and isinstance(frame.f_locals['self'], MultiStepAgent):
            agent = frame.f_locals['self']
            break
        frame = frame.f_back
        
    if agent:
        content = agent.memory.get_asset(asset_handle)
        if content:
            # Perform mock audit
            return f"AUDIT for {asset_handle}: Word count is {len(content.split())}. Tone is authoritative. Synergy: High."
        return f"Error: Asset for handle {asset_handle} not found."
    return "Error: Could not find agent memory store."

# 2. Setup the agent with gpt-5-nano
model = LiteLLMModel(model_id="openai/gpt-5-nano")

agent = CodeAgent(
    tools=[save_manuscript_chapter, audit_asset],
    model=model,
    name="ManuscriptManager",
    description="Uses native asset handles to manage large-scale writing tasks."
)

# 3. Task that demonstrates Pass-by-Handle
task = """
Let's start the expansion of Chapter 1 of our audiobook.
1. Create a 500-word draft for 'Chapter 1: The First Principle of Cognitive Flow'.
2. Save this draft as an asset using 'save_manuscript_chapter'.
3. Take the handle returned and run an 'audit_asset' on it to verify quality.
"""

if __name__ == "__main__":
    print("🚀 Running Native Asset Handle Demo...")
    # Since we are using the local smolagents repo via PYTHONPATH in Docker, 
    # this script will use the ENHANCED library.
    result = agent.run(task)
    print("\n--- EXECUTION SUMMARY ---")
    print(result)
