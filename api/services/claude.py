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
HAIKU = "claude-3-5-haiku-20241022"
SONNET = "claude-3-5-sonnet-20241022"


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


async def analyze_for_diagnosis(
    conversation: list[dict],
    framework: list[dict]
) -> dict:
    """Use Sonnet to analyze conversation and produce diagnosis."""
    system_prompt = f"""You are an expert coach trained in the Inner Architect System (IAS).
Analyze the conversation and determine which specific step, action, and obstacle the user is facing.

THE IAS FRAMEWORK:
{framework}

Your task:
1. Review the conversation history
2. Identify the specific IAS position (step_id 1-9, action_id 1-3, obstacle_id 0-2)
3. Provide an explanation of why this is their block
4. Provide a contrarian insight that reframes their situation

Respond with JSON:
{{
    "step_id": <1-9>,
    "action_id": <1-3>,
    "obstacle_id": <0-2>,
    "explanation": "<why this specific block applies>",
    "contrarian_insight": "<reframing insight>"
}}"""

    response = await client.messages.create(
        model=SONNET,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Conversation to analyze:\n{conversation}"}]
    )

    import json
    return json.loads(response.content[0].text)


async def generate_woop_plans(
    wish: str,
    outcome: str,
    obstacle: str,
    diagnosis_context: str
) -> list[str]:
    """Generate If-Then implementation plans."""
    system_prompt = """You are a WOOP methodology expert. Generate exactly 3 specific If-Then implementation plans.

Format each plan as: "If [specific obstacle situation], then I will [specific action grounded in mindfulness/awareness]."

Return as JSON array of 3 strings."""

    prompt = f"""Create WOOP plans for:
- Wish: {wish}
- Desired Outcome: {outcome}
- Inner Obstacle: {obstacle}
- Diagnosis Context: {diagnosis_context}"""

    response = await client.messages.create(
        model=HAIKU,
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    return json.loads(response.content[0].text)
