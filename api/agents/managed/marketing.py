"""
Managed Agent wrapper for the Marketing Strategist.
"""

from api.agents.marketing_strategist import MarketingStrategistAgent

class ManagedMarketingStrategist:
    """
    Managed agent wrapper for the Marketing Strategist.
    Provides rich description for the Consciousness Manager orchestrator.
    """

    def __init__(self, model_id: str = "dionysus-marketing"):
        self.agent_instance = MarketingStrategistAgent(model_id)
        self.agent = self.agent_instance.get_agent()

    def get_managed(self):
        # Update description for the orchestrator
        self.agent.description = """Direct Response Architect. 
        MANDATORY for: Drafting emails, sales pages, Substack articles, or any audience-facing copy.
        EXPERTISE: Analytical Empath avatar, 21 Forbidden Frameworks, Mirror Tone.
        TOOLS: Can retrieve avatar intel and marketing templates."""
        return self.agent
