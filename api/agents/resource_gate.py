import asyncio
import logging
import threading
from typing import Any, Callable, Optional
from smolagents.memory import ActionStep

logger = logging.getLogger(__name__)

# Global semaphores to prevent "thundering herd" on resources
OLLAMA_SEMAPHORE = threading.Semaphore(1) 
CLOUD_API_SEMAPHORE = threading.Semaphore(5)

async def run_agent_with_timeout(
    agent: Any, 
    prompt: str, 
    timeout_seconds: int = 30,
    use_ollama: bool = False,
    trace_id: str = "no-trace",
    max_retries: int = 1
) -> Any:
    """
    Executes an agent run with a mandatory timeout and resource gating.
    Uses threading.Semaphore for robust cross-thread management.
    """
    from api.services.agent_memory_service import get_agent_memory_service
    
    semaphore = OLLAMA_SEMAPHORE if use_ollama else CLOUD_API_SEMAPHORE
    current_attempt = 0
    
    while current_attempt <= max_retries:
        with semaphore:
            try:
                # We use asyncio.to_thread to run the sync agent.run in a thread
                # but we also need to handle the timeout and the nested asyncio calls from litellm.
                
                def _execute():
                    # If the agent is CodeAgent, it's sync. If it's ToolCallingAgent, it's sync.
                    # They might call async tools via wrappers.
                    return agent.run(prompt, return_full_result=True)

                # Use a loop to run the sync executor with a timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(_execute),
                    timeout=timeout_seconds
                )
                
                # Success! Persist trajectory
                memory_service = get_agent_memory_service()
                # Run persistence in background
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
                
                return result.output
                
            except asyncio.TimeoutError:
                current_attempt += 1
                if current_attempt > max_retries:
                    return "Error: Agent execution timed out."
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                raise
    
    return "Error: Unknown failure in execution loop."

def async_tool_wrapper(func: Callable) -> Callable:
    """
    Decorator/wrapper for async tools to run in a dedicated loop.
    Ensures each tool call has its own isolated event loop if none exists.
    """
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in a thread with a running loop (like the main thread)
                # This shouldn't happen for tools in smolagents threadpool
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(func(*args, **kwargs))
            else:
                return loop.run_until_complete(func(*args, **kwargs))
        except RuntimeError:
            # No loop in this thread, create one
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(func(*args, **kwargs))
            finally:
                new_loop.close()
    return wrapper