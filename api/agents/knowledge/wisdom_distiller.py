"""
Wisdom Distiller Agent - Synthesis and Canonicalization.
"""

import os
import json
from typing import Any, Dict, List, Optional
from smolagents import CodeAgent, LiteLLMModel
from api.agents.tools.wisdom_tools import distill_wisdom_cluster, query_wisdom_graph
from api.services.llm_service import get_router_model, SONNET

class WisdomDistiller:
    """
    Agent responsible for synthesizing raw extracts into canonical wisdom.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        self.model = get_router_model(model_id=model_id)
        
        self.agent = CodeAgent(
            tools=[distill_wisdom_cluster, query_wisdom_graph],
            model=self.model,
            name="wisdom_distiller",
            description="Expert at synthesizing fragmented insights into canonical mental models.",
            executor_type="docker",
            executor_kwargs={
                "image": "dionysus/agent-sandbox:latest",
                "timeout": 60,
            },
            use_structured_outputs_internally=True,
            additional_authorized_imports=["json", "datetime"]
        )

    async def distill_cluster(self, fragments: List[Dict], wisdom_type: str) -> Dict[str, Any]:
        """Orchestrate the distillation of a specific cluster."""
        from api.agents.resource_gate import run_agent_with_timeout
        
        prompt = f"""
        Synthesize these {len(fragments)} fragmented insights into a single canonical {wisdom_type}.
        
        FRAGMENTS:
        {json.dumps(fragments, indent=2)}
        
        Use the 'distill_wisdom_cluster' tool to perform the core synthesis.
        Verify consistency with the existing wisdom graph if needed.
        """
        
        result = await run_agent_with_timeout(
            self.agent,
            prompt,
            timeout_seconds=120
        )
        
        return {
            "result": str(result),
            "fragments_count": len(fragments),
            "type": wisdom_type
        }