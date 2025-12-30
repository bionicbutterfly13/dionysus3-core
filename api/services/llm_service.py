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
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = "ollama/llama3.2" # Using locally available model
OLLAMA_FLEET_MODEL = "ollama/qwen2.5:14b"

# Model constants - GPT-5 Nano with fallback chain
GPT5_NANO = "openai/gpt-5-nano-2025-08-07"
GPT5_MINI = "openai/gpt-5-mini"
GPT4O_MINI = "openai/gpt-4o-mini"
HAIKU = "anthropic/claude-3-haiku-20240307"
SONNET = "anthropic/claude-3-5-sonnet-20240620"


def get_router_model(model_id: str = "dionysus-agents") -> LiteLLMRouterModel:
    """
    Returns a LiteLLMRouterModel with GPT-5 Nano -> Ollama fallback.
    """
    from smolagents import LiteLLMRouterModel
    
    # Use consistent model_name across deployments for the router group
    # Fallback order: GPT5_NANO -> GPT5_MINI -> GPT4O_MINI -> OLLAMA
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
                "model": GPT4O_MINI,
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
            "fallbacks": [{model_id: [model_id]}], # Fallback is handled by the model list order
        },
        drop_params=True
    )


async def chat_completion(
    messages: list[dict],
    system_prompt: str,
    model: str = GPT5_NANO,
    max_tokens: int = 1024
) -> str:
    """
    Non-streaming chat completion via LiteLLM.
    """
    # If model is an ollama model, force provider
    if model.startswith("ollama/"):
        llm_model = model
    else:
        llm_model = model if model.startswith("openai/") else f"openai/{model}"

    try:
        kwargs = {
            "model": llm_model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "timeout": 60,
            "drop_params": True
        }
        
        # Ollama support
        if "ollama" in llm_model:
            kwargs["api_base"] = OLLAMA_BASE_URL
            
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
    llm_model = model if model.startswith("openai/") else f"openai/{model}"

    response = await acompletion(
        model=llm_model,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        max_tokens=max_tokens,
        api_key=os.getenv("OPENAI_API_KEY"),
        stream=True,
        drop_params=True
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
        from api.agents.resource_gate import run_agent_with_timeout
        result = await run_agent_with_timeout(self.agent, prompt)
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
        from api.agents.resource_gate import run_agent_with_timeout
        result = await run_agent_with_timeout(self.agent, prompt)
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