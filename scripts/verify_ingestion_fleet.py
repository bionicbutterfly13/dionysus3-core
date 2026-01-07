import asyncio
import os
import sys
import json
import logging
import threading
from typing import List, Any
from smolagents import CodeAgent, LiteLLMModel, Tool

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.services.graphiti_service import get_graphiti_service
from api.services.remote_sync import RemoteSyncService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa_fleet")

def run_async(coro):
    """Run an async coroutine from a synchronous context, even if an event loop is running."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If the loop is running, we run it in a separate thread
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)

class Neo4jVerifyTool(Tool):
    name = "verify_neo4j_skill"
    description = "Verify if a skill exists in Neo4j procedural memory."
    inputs = {
        "skill_id": {"type": "string", "description": "The ID of the skill to check"}
    }
    output_type = "string"

    def forward(self, skill_id: str) -> str:
        async def _run():
            sync = RemoteSyncService()
            q = "MATCH (s:Skill {skill_id: $skill_id}) RETURN s.name as name, s.proficiency as proficiency"
            res = await sync.run_cypher(q, {"skill_id": skill_id}, mode="read")
            # Result from n8n run_cypher is usually in res['results']
            if res.get("success") and res.get("results"):
                return f"Skill {skill_id} found: {res['results']}"
            return f"Skill {skill_id} NOT found in Neo4j."
        
        return run_async(_run())

class GraphitiVerifyTool(Tool):
    name = "search_graphiti_knowledge"
    description = "Search the Graphiti knowledge graph for specific facts."
    inputs = {
        "query": {"type": "string", "description": "Search query"}
    }
    output_type = "string"

    def forward(self, query: str) -> str:
        async def _run():
            gs = await get_graphiti_service()
            res = await gs.search(query, group_ids=["procedural_memory", "community_skills"], limit=3)
            return json.dumps(res, indent=2)
        
        return run_async(_run())

async def run_qa_fleet():
    print("🚀 Launching QA Agent Fleet (Fixed Loop Handling)...")
    
    model = LiteLLMModel(model_id="openai/gpt-5-nano")
    
    inspector = CodeAgent(
        tools=[Neo4jVerifyTool()],
        model=model,
        name="Inspector",
        description="Verifies the presence of Skill nodes in Neo4j."
    )
    
    researcher = CodeAgent(
        tools=[GraphitiVerifyTool()],
        model=model,
        name="Researcher",
        description="Verifies the richness of extracted knowledge in Graphiti."
    )
    
    coordinator = CodeAgent(
        tools=[],
        model=model,
        managed_agents=[inspector, researcher],
        name="Coordinator",
        description="Coordinates the QA fleet and provides a final report."
    )
    
    task = """
    Verify the ingestion of the Context Engineering skills.
    1. Check if 'context-compression' and 'multi-agent-patterns' exist as Skill nodes in Neo4j.
    2. Search Graphiti for 'anchored iterative summarization' to ensure it was extracted as a fact.
    3. search Graphiti for 'tokens-per-task' to ensure quality metrics were captured.
    Provide a final report on whether the ingestion was successful and high-fidelity.
    """
    
    report = coordinator.run(task)
    print("\n--- FINAL QA REPORT ---")
    print(report)

if __name__ == "__main__":
    asyncio.run(run_qa_fleet())