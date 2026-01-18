"""
Marketing Strategist Agent (Feature 050)

Specialized CodeAgent for generating audience-aligned marketing content.
Grounded in '[LEGACY_AVATAR_HOLDER]' research and the '21 Forbidden Email Frameworks'.
"""

import logging
from typing import Optional, List
from smolagents import CodeAgent, LiteLLMModel
from api.services.llm_service import GPT5_NANO, get_router_model
from api.agents.tools.cognitive_tools import understand_question, recall_related, examine_answer
from api.agents.tools.marketing_tools import get_marketing_framework, get_avatar_intel

logger = logging.getLogger("dionysus.marketing_agent")

class MarketingStrategistAgent:
    """
    World-class Direct Response Architect specializing in the [LEGACY_AVATAR_HOLDER].
    Uses 'Mirror Tone' and 'Contrarian Truth' frameworks.
    """

    def __init__(self, model_id: str = "dionysus-marketing"):
        self.model = get_router_model(model_id=model_id)
        
        # Tools specific to marketing generation
        self.tools = [
            understand_question,
            recall_related,
            examine_answer,
            get_marketing_framework,
            get_avatar_intel
        ]
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            name="marketing_strategist",
            description="""Direct Response Architect. 
            Generates emails, Substack articles, and sales copy.
            Grounded in [LEGACY_AVATAR_HOLDER] research. 
            Uses 21 Forbidden Email Frameworks.""",
            use_structured_outputs_internally=True
        )

    def get_agent(self) -> CodeAgent:
        return self.agent
