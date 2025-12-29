import asyncio
import logging
from typing import Any, Callable, Optional
from smolagents.memory import ActionStep

logger = logging.getLogger(__name__)

# Global semaphores to prevent "thundering herd" on resources
# Ollama is heavy on RAM/GPU, so we restrict it strictly
OLLAMA_SEMAPHORE = asyncio.Semaphore(1) 
# Cloud APIs can handle more, but we still gate to prevent cost/rate spikes
CLOUD_API_SEMAPHORE = asyncio.Semaphore(5)

async def run_agent_with_timeout(
    agent: Any, 
    prompt: str, 
    timeout_seconds: int = 30,
    use_ollama: bool = False,
    trace_id: str = "no-trace"
) -> Any:
    """
    Executes an agent run with a mandatory timeout and resource gating.
    Now automatically persists trajectories to Neo4j.
    
    Args:
        agent: The smolagent instance to run.
        prompt: The task/prompt for the agent.
        timeout_seconds: Max execution time.
        use_ollama: If True, uses the strict Ollama semaphore.
        trace_id: Correlation ID for logging and persistence.
    """
    from api.services.agent_memory_service import get_agent_memory_service
    
    semaphore = OLLAMA_SEMAPHORE if use_ollama else CLOUD_API_SEMAPHORE
    
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            # We always request full result for observability (T2.3)
            # return_full_result=True returns a RunResult object
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: agent.run(prompt, return_full_result=True)),
                timeout=timeout_seconds
            )
            
            # T017: Persist full agent run to Neo4j (T2.2)
            memory_service = get_agent_memory_service()
            # Note: We don't await this to avoid blocking the return, but here we are in an async def
            # so we can just fire and forget or await it.
            asyncio.create_task(memory_service.persist_run(
                agent_name=getattr(agent, "name", "unknown"),
                task=prompt,
                memory=agent.memory,
                result=result.output,
                trace_id=trace_id,
                timing={
                    "total_ms": result.timing.duration * 1000 if result.timing else 0
                },
                token_usage={
                    "input": result.token_usage.input_tokens if result.token_usage else 0,
                    "output": result.token_usage.output_tokens if result.token_usage else 0
                }
            ))
            
            # Return only the output to keep compatibility with existing code
            return result.output
            
        except asyncio.TimeoutError:
            logger.error(f"Agent {getattr(agent, 'name', 'unknown')} timed out after {timeout_seconds}s")
            return "Error: Agent execution timed out."
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise

def async_tool_wrapper(func: Callable) -> Callable:
    """
    Decorator/wrapper for async tools to run in a dedicated thread-per-tool 
    with an isolated event loop, eliminating nest_asyncio.
    """
    def wrapper(*args, **kwargs):
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(func(*args, **kwargs))
        finally:
            new_loop.close()
    return wrapper
