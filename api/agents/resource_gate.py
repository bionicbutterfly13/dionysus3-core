import asyncio
import logging
from typing import Any, Callable, Optional

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
    trace_id: str = "no-trace",
    max_retries: int = 1,
    fallback_model_id: Optional[str] = "dionysus-agents-mini" # T004
) -> Any:
    """
    Executes an agent run with a mandatory timeout, resource gating, and self-healing retries.
    Now supports model promotion on first retry.
    """
    from api.services.agent_memory_service import get_agent_memory_service
    
    semaphore = OLLAMA_SEMAPHORE if use_ollama else CLOUD_API_SEMAPHORE
    
    current_attempt = 0
    
    while current_attempt <= max_retries:
        if current_attempt > 0 and fallback_model_id:
            if hasattr(agent.model, 'model_id'):
                agent.model.model_id = fallback_model_id
                logger.info(f"Retrying with promoted model: {fallback_model_id}")

        async with semaphore:
            def _run():
                # T033: Crucial fix for smolagents threads - must have local event loop
                # for any async calls (like Neo4j driver) inside tool execution.
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return agent.run(prompt, return_full_result=True)
                finally:
                    loop.close()

            try:
                loop = asyncio.get_event_loop()
                # return_full_result=True returns a RunResult object
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, _run),
                    timeout=timeout_seconds
                )
                
                # Success!
                # T017: Persist trajectory...
                memory_service = get_agent_memory_service()
                asyncio.create_task(memory_service.persist_run(
                    agent_name=getattr(agent, "name", "unknown"),
                    task=prompt,
                    memory=agent.memory,
                    result=result.output,
                    trace_id=trace_id,
                    timing={"total_ms": result.timing.duration * 1000 if result.timing else 0},
                    token_usage={
                        "input": result.token_usage.input_tokens if result.token_usage else 0,
                        "output": result.token_usage.output_tokens if result.token_usage else 0
                    }
                ))
                return result.output
                
            except asyncio.TimeoutError:
                current_attempt += 1
                if current_attempt > max_retries:
                    logger.error(f"Agent {getattr(agent, 'name', 'unknown')} timed out after {current_attempt} attempts.")
                    return "Error: Agent execution timed out after multiple attempts."
                # Small cool-down
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                raise
    
    return "Error: Unknown failure in execution loop."

def async_tool_wrapper(func: Callable) -> Callable:
    """
    Decorator/wrapper for async tools to run in a dedicated thread-per-tool 
    with a stable, dedicated event loop. 
    """
    def wrapper(*args, **kwargs):
        from api.services.graphiti_service import get_graphiti_loop
        loop = get_graphiti_loop()
        
        # Use run_coroutine_threadsafe to execute on the dedicated loop
        future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)
        return future.result()
            
    return wrapper
