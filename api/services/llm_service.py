"""
LLM Service for IAS

Uses GPT-5 Nano via LiteLLM. Ollama available as fallback.
"""

from __future__ import annotations

import os
import json
import logging
from typing import AsyncGenerator, Optional, TYPE_CHECKING
from litellm import acompletion

if TYPE_CHECKING:
    from smolagents import LiteLLMRouterModel

logger = logging.getLogger(__name__)

# Provider config
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama/phi3:mini")
OLLAMA_FLEET_MODEL = os.getenv("OLLAMA_FLEET_MODEL", "deepseek-v3")

# Model constants - mapping to gpt-4o-mini for stability until gpt-5 is fully GA
GPT5_NANO = "openai/gpt-4o-mini"
GPT5_MINI = "openai/gpt-4o-mini"
HAIKU = "anthropic/claude-3-haiku-20240307"
SONNET = "anthropic/claude-3-5-sonnet-20240620"
OLLAMA_MODEL = "ollama/llama3.2" # Using locally available model


def get_router_model(model_id: str = "dionysus-agents") -> LiteLLMRouterModel:
    """
    Returns a LiteLLMRouterModel with GPT-5 Nano -> GPT-5 Mini -> Ollama fallback.
    T3.1: Ensures high availability and cost optimization.
    """
    from smolagents import LiteLLMRouterModel
    
    model_list = [
        {
            "model_name": model_id,
            "litellm_params": {
                "model": GPT5_NANO,
                "api_key": os.getenv("OPENAI_API_KEY"),
            }
        },
        {
            "model_name": model_id,
            "litellm_params": {
                "model": GPT5_MINI,
                "api_key": os.getenv("OPENAI_API_KEY"),
            }
        },
        {
            "model_name": model_id,
            "litellm_params": {
                "model": OLLAMA_MODEL,
                "api_base": OLLAMA_BASE_URL,
            }
        }
    ]
    
    return LiteLLMRouterModel(
        model_id=model_id,
        model_list=model_list,
        client_kwargs={
            "routing_strategy": "simple-shuffle",
            "num_retries": 2,
            "fallbacks": [{GPT5_NANO: [GPT5_MINI, OLLAMA_MODEL]}],
        },
        drop_params=True # T033: Prevent UnsupportedParamsError
    )


async def chat_completion(
    messages: list[dict],
    system_prompt: str,
    model: str = GPT5_NANO,
    max_tokens: int = 1024
) -> str:
    """
    Non-streaming chat completion via LiteLLM.

    Uses LLM_PROVIDER env var:
    - "openai": GPT-5 Nano (default)
    - "ollama": Local Ollama
    """
    # If model is an ollama model, force provider
    current_provider = LLM_PROVIDER
    if model.startswith("ollama/"):
        current_provider = "ollama"
        model = model.replace("ollama/", "")

    if current_provider == "ollama":
        # Use LiteLLM with Ollama
        ollama_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await acompletion(
            model=f"ollama/{model}",
            messages=ollama_messages,
            max_tokens=max_tokens,
            api_base=OLLAMA_BASE_URL,
            drop_params=True # Ollama doesn't like some OpenAI params
        )
        return response.choices[0].message.content or ""
    else:
        # OpenAI / GPT-5 Nano
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        llm_model = model if model.startswith("openai/") else f"openai/{model}"

        try:
            # T004: Explicitly omit max_tokens for gpt-5-nano if needed
            kwargs = {
                "model": llm_model,
                "messages": openai_messages,
                "api_key": os.getenv("OPENAI_API_KEY"),
                "timeout": 60,
                "drop_params": True # T033: Ensure stability
            }
            if "gpt-5" not in llm_model:
                kwargs["max_tokens"] = max_tokens
                
            response = await acompletion(**kwargs)
            content = response.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            logger.error(f"LiteLLM error ({llm_model}): {e}")
            return ""


async def chat_stream(
    messages: list[dict],
    system_prompt: str,
    model: str = GPT5_NANO,
    max_tokens: int = 1024
) -> AsyncGenerator[str, None]:
    """Streaming chat completion via LiteLLM."""
    openai_messages = [{"role": "system", "content": system_prompt}] + messages
    llm_model = model if model.startswith("openai/") else f"openai/{model}"

    response = await acompletion(
        model=llm_model,
        messages=openai_messages,
        max_tokens=max_tokens,
        api_key=os.getenv("OPENAI_API_KEY"),
        stream=True,
    )
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


from smolagents import CodeAgent, LiteLLMModel

class CoachingAgent:
    """Agentic wrapper for IAS coaching logic."""

    def __init__(self, model_id: Optional[str] = None):
        model_id = model_id or GPT5_NANO
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
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
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
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
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
