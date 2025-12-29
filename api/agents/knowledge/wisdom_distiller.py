"""
Wisdom Distiller Agent
Feature: 031-wisdom-distillation

Specialized agent for synthesizing canonical wisdom from fragmented session data.
"""

import os
from typing import List, Dict, Any
from smolagents import ToolCallingAgent, LiteLLMModel
from api.services.llm_service import get_router_model, SONNET

class WisdomDistiller:
    """
    The 'Librarian' of Dionysus. Iterates through raw data to create an Effective Worldview.
    Uses ToolCallingAgent for stable conceptual synthesis.
    """

    def __init__(self, model_id: str = "openai/gpt-4o-mini"):
        # Use ToolCallingAgent for direct reasoning without the risks of CodeAgent for this task
        from smolagents import LiteLLMModel
        self.model = LiteLLMModel(model_id=model_id)
        self.name = "wisdom_distiller"
        self.description = """
            Expert at knowledge synthesis and conceptual deduplication. 
            Takes fragmented insights and merges them into canonical Strategic Principles and Mental Models.
            """
        self.agent = None

    def __enter__(self):
        from api.agents.tools.wisdom_tools import distill_wisdom_cluster
        from api.agents.audit import get_audit_callback
        audit = get_audit_callback()

        self.agent = ToolCallingAgent(
            tools=[distill_wisdom_cluster],
            model=self.model,
            name=self.name,
            description=self.description,
            max_steps=5,
            step_callbacks=audit.get_registry("wisdom_distiller")
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass # No specific cleanup for this wrapper yet

    def run(self, task: str):
        """Run the distillation cycle."""
        if not self.agent:
            with self:
                return self.agent.run(task)
        return self.agent.run(task)
