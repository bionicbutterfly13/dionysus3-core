"""
Claude API Service for IAS
"""

import os
from typing import AsyncGenerator
import anthropic

# Initialize client
client = anthropic.AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Models
HAIKU = "openai/gpt-5-nano-2025-08-07"
SONNET = "openai/gpt-5-nano-2025-08-07"


async def chat_completion(
    messages: list[dict],
    system_prompt: str,
    model: str = HAIKU,
    max_tokens: int = 1024
) -> str:
    """Non-streaming chat completion."""
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text


async def chat_stream(
    messages: list[dict],
    system_prompt: str,
    model: str = HAIKU,
    max_tokens: int = 1024
) -> AsyncGenerator[str, None]:
    """Streaming chat completion."""
    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    ) as stream:
        async for text in stream.text_stream:
            yield text


from smolagents import CodeAgent, LiteLLMModel

class CoachingAgent:
    """
    Agentic wrapper for IAS coaching logic.
    """
    def __init__(self, model_id: str = "openai/gpt-5-nano-2025-08-07"):
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.agent = CodeAgent(
            tools=[],
            model=self.model,
            name="coaching_agent"
        )

    async def diagnose(self, conversation: list[dict], framework: list[dict]) -> dict:
        prompt = f"""Review the conversation and identify the specific IAS framework position.
        Framework: {json.dumps(framework, indent=2)}
        Conversation: {json.dumps(conversation, indent=2)}
        Respond ONLY with a JSON object:
        {{
            "step_id": <1-9>,
            "action_id": <1-3>,
            "obstacle_id": <0-2>,
            "explanation": "...",
            "contrarian_insight": "..."
        }}
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
            return json.loads(cleaned)
        except:
            return {"error": "Failed to parse diagnosis", "raw": result}

    async def generate_woop(self, wish: str, outcome: str, obstacle: str, context: str) -> list[str]:
        prompt = f"""Generate 3 specific WOOP If-Then plans.
        Wish: {wish} | Outcome: {outcome} | Obstacle: {obstacle} | Context: {context}
        Respond ONLY with a JSON list of 3 strings.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, prompt)
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
            return json.loads(cleaned)
        except:
            return [result]

async def analyze_for_diagnosis(
    conversation: list[dict],
    framework: list[dict]
) -> dict:
    agent = CoachingAgent()
    return await agent.diagnose(conversation, framework)


async def generate_woop_plans(
    wish: str,
    outcome: str,
    obstacle: str,
    diagnosis_context: str
) -> list[str]:
    agent = CoachingAgent()
    return await agent.generate_woop(wish, outcome, obstacle, diagnosis_context)
