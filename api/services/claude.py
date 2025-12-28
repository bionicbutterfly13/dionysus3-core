"""
Claude API Service for IAS

Supports multiple LLM providers via LLM_PROVIDER env var:
- "anthropic" (default): Uses Claude API
- "ollama": Uses local Ollama with qwen2.5:7b
"""

import os
import json
from typing import AsyncGenerator, Optional
import anthropic
from litellm import acompletion

# Initialize Anthropic client (used when LLM_PROVIDER=anthropic)
client = anthropic.AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Provider config
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama/qwen2.5:7b")

# Anthropic Models
# Remapped to gpt-5-nano for bill protection
HAIKU = "openai/gpt-5-nano"
SONNET = "openai/gpt-5-nano"

# OpenAI / Unified Models
GPT5_NANO = "openai/gpt-5-nano"


async def chat_completion(
    messages: list[dict],
    system_prompt: str,
    model: str = GPT5_NANO,
    max_tokens: int = 1024
) -> str:
    """
    Non-streaming chat completion.

    Uses LLM_PROVIDER env var to select backend:
    - "anthropic": Claude API
    - "ollama": Local Ollama with qwen2.5:7b
    - "openai": OpenAI API or LiteLLM compatible
    """
    if LLM_PROVIDER == "ollama":
        # Use LiteLLM with Ollama
        ollama_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await acompletion(
            model=OLLAMA_MODEL,
            messages=ollama_messages,
            max_tokens=max_tokens,
            api_base=OLLAMA_BASE_URL,
        )
        return response.choices[0].message.content
    elif LLM_PROVIDER == "openai" or model.startswith("openai/"):
        # Use LiteLLM for OpenAI models
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Ensure model has openai/ prefix for LiteLLM if not present
        llm_model = model if model.startswith("openai/") else f"openai/{model}"
        
        print(f"DEBUG: LiteLLM Calling {llm_model} with {len(openai_messages)} messages")
        
        try:
            response = await acompletion(
                model=llm_model,
                messages=openai_messages,
                max_tokens=max_tokens,
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=60,
            )
            print(f"DEBUG: LiteLLM Response Object: {response}")
            content = response.choices[0].message.content
            if not content:
                print("DEBUG: LiteLLM returned empty content!")
            return content or ""
        except Exception as e:
            print(f"DEBUG: LiteLLM EXCEPTION: {e}")
            return ""
    else:
        # Default: Anthropic
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
    def __init__(self, model_id: Optional[str] = None):
        if model_id is None:
            model_id = GPT5_NANO # Use the cheap gpt-5-nano
            
        self.model = LiteLLMModel(
            model_id=model_id,
            api_key=os.getenv("OPENAI_API_KEY")
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
