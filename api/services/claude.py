"""
LLM service abstraction with OpenAI default (5-mini family) and Anthropic fallback.
"""

import os
from typing import AsyncGenerator

import anthropic
from openai import AsyncOpenAI

# Model defaults (can be overridden via env)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
ANTHROPIC_MODEL_HAIKU = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
ANTHROPIC_MODEL_SONNET = os.getenv("ANTHROPIC_DIAG_MODEL", "claude-3-5-sonnet-20241022")

# Backwards-compatible aliases
HAIKU = OPENAI_MODEL
SONNET = OPENAI_MODEL

_anthropic_client = None
_openai_client = None


def _get_provider() -> str:
    """Choose provider based on env and available keys."""
    preferred = os.getenv("LLM_PROVIDER", "openai").lower()

    if preferred == "openai" and not os.getenv("OPENAI_API_KEY"):
        preferred = "anthropic"
    if preferred == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        preferred = ""
    return preferred


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
    return _anthropic_client


async def _chat_openai(messages: list[dict], system_prompt: str, model: str, max_tokens: int) -> str:
    client = _get_openai_client()
    resp = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return resp.choices[0].message.content or ""


async def _chat_stream_openai(
    messages: list[dict], system_prompt: str, model: str, max_tokens: int
) -> AsyncGenerator[str, None]:
    client = _get_openai_client()
    stream = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        stream=True,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if isinstance(delta, list):
            delta = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in delta
            )
        if delta:
            yield delta


async def _chat_anthropic(messages: list[dict], system_prompt: str, model: str, max_tokens: int) -> str:
    client = _get_anthropic_client()
    resp = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return resp.content[0].text


async def _chat_stream_anthropic(
    messages: list[dict], system_prompt: str, model: str, max_tokens: int
) -> AsyncGenerator[str, None]:
    client = _get_anthropic_client()
    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def chat_completion(
    messages: list[dict],
    system_prompt: str,
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    """Non-streaming chat completion with OpenAI default and Anthropic fallback."""
    provider = _get_provider()
    if provider == "openai":
        return await _chat_openai(messages, system_prompt, model or OPENAI_MODEL, max_tokens)
    if provider == "anthropic":
        return await _chat_anthropic(messages, system_prompt, model or ANTHROPIC_MODEL_HAIKU, max_tokens)
    raise RuntimeError("No LLM provider configured")


async def chat_stream(
    messages: list[dict],
    system_prompt: str,
    model: str | None = None,
    max_tokens: int = 1024,
) -> AsyncGenerator[str, None]:
    """Streaming chat completion with OpenAI default and Anthropic fallback."""
    provider = _get_provider()
    if provider == "openai":
        async for chunk in _chat_stream_openai(
            messages, system_prompt, model or OPENAI_MODEL, max_tokens
        ):
            yield chunk
        return
    if provider == "anthropic":
        async for chunk in _chat_stream_anthropic(
            messages, system_prompt, model or ANTHROPIC_MODEL_HAIKU, max_tokens
        ):
            yield chunk
        return
    raise RuntimeError("No LLM provider configured")


async def analyze_for_diagnosis(
    conversation: list[dict],
    framework: list[dict],
    model: str | None = None,
) -> dict:
    """Analyze conversation and produce diagnosis JSON."""
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

    provider = _get_provider()
    if provider == "openai":
        client = _get_openai_client()
        resp = await client.chat.completions.create(
            model=model or OPENAI_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation to analyze:\n{conversation}"},
            ],
        )
        import json

        return json.loads(resp.choices[0].message.content)

    if provider == "anthropic":
        client = _get_anthropic_client()
        resp = await client.messages.create(
            model=model or ANTHROPIC_MODEL_SONNET,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Conversation to analyze:\n{conversation}"}],
        )
        import json

        return json.loads(resp.content[0].text)

    raise RuntimeError("No LLM provider configured")


async def generate_woop_plans(
    wish: str,
    outcome: str,
    obstacle: str,
    diagnosis_context: str,
    model: str | None = None,
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

    provider = _get_provider()
    if provider == "openai":
        client = _get_openai_client()
        resp = await client.chat.completions.create(
            model=model or OPENAI_MODEL,
            max_tokens=512,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        import json

        return json.loads(resp.choices[0].message.content)

    if provider == "anthropic":
        client = _get_anthropic_client()
        resp = await client.messages.create(
            model=model or ANTHROPIC_MODEL_HAIKU,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        import json

        return json.loads(resp.content[0].text)

    raise RuntimeError("No LLM provider configured")
