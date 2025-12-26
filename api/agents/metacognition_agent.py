import os
from smolagents import CodeAgent, LiteLLMModel
from api.agents.tools.review_goals_tool import ReviewGoalsTool
from api.agents.tools.revise_model_tool import ReviseModelTool

class MetacognitionAgent:
    """
    Specialized agent for the DECIDE phase of the OODA loop.
    Reviews goal states, assesses model accuracy, and revises mental models.
    Uses CodeAgent for high-level reasoning about system state and strategy.
    """

    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.tools = [
            ReviewGoalsTool(),
            ReviseModelTool(),
        ]
        
        self.agent = CodeAgent(
            tools=self.tools,
            model=self.model,
            name="metacognition",
            description="Specialized in self-reflection, goal management, and mental model revision."
        )

    def run(self, task: str):
        """
        Run the metacognition cycle.
        """
        return self.agent.run(task)
