import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import httpx
from smolagents.memory import ActionStep, PlanningStep

logger = logging.getLogger(__name__)


# =============================================================================
# Token Usage Tracking (Feature 039, T007)
# =============================================================================

@dataclass
class TokenUsageStats:
    """Statistics for token usage tracking."""
    pre_pruning_tokens: int = 0
    post_pruning_tokens: int = 0
    steps_tracked: int = 0
    pruning_events: int = 0

    @property
    def reduction_tokens(self) -> int:
        """Total tokens saved by pruning."""
        return max(0, self.pre_pruning_tokens - self.post_pruning_tokens)

    @property
    def reduction_percentage(self) -> float:
        """Percentage reduction from pruning."""
        if self.pre_pruning_tokens == 0:
            return 0.0
        return (self.reduction_tokens / self.pre_pruning_tokens) * 100


class TokenUsageTracker:
    """
    Tracks token usage across agent execution with pruning metrics.

    Feature 039, T007: Provides token counting before/after pruning
    to measure memory optimization effectiveness.
    """

    # Approximate tokens per character (conservative estimate)
    TOKENS_PER_CHAR = 0.25

    def __init__(self, agent_name: str = "unknown"):
        self.agent_name = agent_name
        self.stats = TokenUsageStats()
        self._current_step_pre_prune: int = 0

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        if not text:
            return 0
        return int(len(text) * self.TOKENS_PER_CHAR)

    def record_pre_prune(self, step: ActionStep) -> None:
        """Record token count before pruning."""
        observations = getattr(step, "observations", None) or getattr(step, "observation", "")
        self._current_step_pre_prune = self.estimate_tokens(str(observations))
        self.stats.pre_pruning_tokens += self._current_step_pre_prune
        self.stats.steps_tracked += 1

    def record_post_prune(self, step: ActionStep) -> None:
        """Record token count after pruning."""
        observations = getattr(step, "observations", None) or getattr(step, "observation", "")
        post_tokens = self.estimate_tokens(str(observations))
        self.stats.post_pruning_tokens += post_tokens

        # Check if pruning occurred
        if post_tokens < self._current_step_pre_prune:
            self.stats.pruning_events += 1
            reduction = self._current_step_pre_prune - post_tokens
            logger.debug(
                f"[TokenTracker] {self.agent_name}: Pruned {reduction} tokens "
                f"({(reduction / self._current_step_pre_prune * 100):.1f}% reduction)"
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary metrics for heartbeat/observability."""
        return {
            "agent_name": self.agent_name,
            "steps_tracked": self.stats.steps_tracked,
            "pre_pruning_tokens": self.stats.pre_pruning_tokens,
            "post_pruning_tokens": self.stats.post_pruning_tokens,
            "tokens_saved": self.stats.reduction_tokens,
            "reduction_percentage": round(self.stats.reduction_percentage, 2),
            "pruning_events": self.stats.pruning_events,
        }

    def reset(self) -> None:
        """Reset all statistics."""
        self.stats = TokenUsageStats()
        self._current_step_pre_prune = 0


# Global token trackers per agent
_token_trackers: Dict[str, TokenUsageTracker] = {}


def get_token_tracker(agent_name: str) -> TokenUsageTracker:
    """Get or create a token tracker for an agent."""
    if agent_name not in _token_trackers:
        _token_trackers[agent_name] = TokenUsageTracker(agent_name)
    return _token_trackers[agent_name]


def get_all_token_summaries() -> List[Dict[str, Any]]:
    """Get token usage summaries for all tracked agents."""
    return [tracker.get_summary() for tracker in _token_trackers.values()]


def get_aggregate_token_stats() -> Dict[str, Any]:
    """Get aggregate token statistics across all agents."""
    total_pre = sum(t.stats.pre_pruning_tokens for t in _token_trackers.values())
    total_post = sum(t.stats.post_pruning_tokens for t in _token_trackers.values())
    total_steps = sum(t.stats.steps_tracked for t in _token_trackers.values())
    total_prune_events = sum(t.stats.pruning_events for t in _token_trackers.values())

    return {
        "total_agents": len(_token_trackers),
        "total_steps": total_steps,
        "total_pre_pruning_tokens": total_pre,
        "total_post_pruning_tokens": total_post,
        "total_tokens_saved": max(0, total_pre - total_post),
        "overall_reduction_percentage": round(
            ((total_pre - total_post) / total_pre * 100) if total_pre > 0 else 0.0, 2
        ),
        "total_pruning_events": total_prune_events,
    }


# =============================================================================
# Callback Registry (Feature 039, T003)
# =============================================================================

class DionysusCognitiveCallbackRegistry:
    """
    Registry for type-specific agent callbacks.
    
    Extends the basic smolagents callback pattern with:
    - Multiple callbacks per step type
    - Consciousness integration (IWMT, basins)
    - Memory optimization (pruning)
    - Observability (audit)
    
    Callbacks are executed in registration order.
    """
    
    def __init__(self):
        self._callbacks: Dict[type, List[Callable]] = {
            PlanningStep: [],
            ActionStep: [],
        }
        self._enabled = True
    
    def register(self, step_type: type, callback: Callable) -> None:
        """
        Register a callback for a specific step type.
        
        Args:
            step_type: PlanningStep or ActionStep
            callback: Function(step, agent) -> None
        """
        if step_type not in self._callbacks:
            self._callbacks[step_type] = []
        self._callbacks[step_type].append(callback)
        logger.debug(f"Registered callback {callback.__name__} for {step_type.__name__}")
    
    def unregister(self, step_type: type, callback: Callable) -> bool:
        """Remove a callback from the registry."""
        if step_type in self._callbacks and callback in self._callbacks[step_type]:
            self._callbacks[step_type].remove(callback)
            return True
        return False
    
    def enable(self) -> None:
        """Enable all callbacks."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable all callbacks (useful for testing)."""
        self._enabled = False
    
    def _create_dispatcher(self, step_type: type, agent_name: str) -> Callable:
        """
        Create a dispatcher function that runs all callbacks for a step type.
        
        The dispatcher handles async/sync execution and error isolation.
        """
        callbacks = self._callbacks.get(step_type, [])
        
        def dispatcher(step, agent=None, **kwargs):
            if not self._enabled:
                return
            
            for callback in callbacks:
                try:
                    # Execute callback with error isolation
                    callback(step, agent or kwargs.get("agent"))
                except Exception as e:
                    logger.warning(
                        f"Callback {callback.__name__} failed for {agent_name}: {e}"
                    )
        
        return dispatcher
    
    def get_step_callbacks(self, agent_name: str) -> Dict[type, Callable]:
        """
        Get the step_callbacks dict for agent initialization.
        
        Returns a dict mapping step types to dispatcher functions
        that execute all registered callbacks for that type.
        
        Args:
            agent_name: Name for logging purposes
            
        Returns:
            Dict suitable for smolagents step_callbacks parameter
        """
        return {
            step_type: self._create_dispatcher(step_type, agent_name)
            for step_type, callbacks in self._callbacks.items()
            if callbacks  # Only include types with registered callbacks
        }


# Global cognitive callback registry
_cognitive_registry: Optional[DionysusCognitiveCallbackRegistry] = None


def get_cognitive_callback_registry() -> DionysusCognitiveCallbackRegistry:
    """Get or create the global cognitive callback registry."""
    global _cognitive_registry
    if _cognitive_registry is None:
        _cognitive_registry = DionysusCognitiveCallbackRegistry()
        _register_default_callbacks(_cognitive_registry)
    return _cognitive_registry


def _register_default_callbacks(registry: DionysusCognitiveCallbackRegistry) -> None:
    """Register the default consciousness callbacks."""
    try:
        # Import callbacks (may fail if dependencies not available)
        from api.agents.callbacks.iwmt_callback import get_iwmt_callback
        from api.agents.callbacks.basin_callback import get_basin_callback
        from api.agents.callbacks.memory_callback import get_memory_callback
        
        # Register IWMT coherence for planning phases
        registry.register(PlanningStep, get_iwmt_callback())
        
        # Register basin activation and memory pruning for action steps
        registry.register(ActionStep, get_basin_callback())
        registry.register(ActionStep, get_memory_callback())
        
        logger.info("Registered default cognitive callbacks (IWMT, basin, memory)")
    except ImportError as e:
        logger.warning(f"Could not register cognitive callbacks: {e}")


# =============================================================================
# Audit Callback (Original)
# =============================================================================

class AgentAuditCallback:
    """
    Callback handler for smolagents steps.
    Sends real-time telemetry to n8n for observability.
    """
    def __init__(self, webhook_url: Optional[str] = None, project_id: str = "dionysus"):
        self.webhook_url = webhook_url or os.getenv(
            "N8N_AUDIT_WEBHOOK_URL", 
            "http://72.61.78.89:5678/webhook/memory/v1/ingest/agent-step"
        )
        self.project_id = project_id
        self._client = httpx.AsyncClient(timeout=5.0)

    async def on_step(self, step: Any, agent_name: str, trace_id: str = "no-trace"):
        """
        Processes a single agent step and forwards to webhook.
        """
        payload = {
            "project_id": self.project_id,
            "agent_name": agent_name,
            "trace_id": trace_id,
            "step_number": getattr(step, "step_number", 0),
            "step_type": type(step).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if isinstance(step, ActionStep):
            # Capture tool calls or code actions
            payload["tool_calls"] = []
            if hasattr(step, "tool_calls") and step.tool_calls:
                payload["tool_calls"] = [
                    {"name": c.name, "arguments": c.arguments}
                    for c in step.tool_calls
                ]
            
            # Use getattr to be safe with different versions
            payload["observation"] = str(getattr(step, "observation", ""))[:1000]
            payload["error"] = str(step.error) if getattr(step, "error", None) else None
            
            if hasattr(step, "code_action"):
                payload["code_action"] = str(step.code_action)[:2000]

        elif isinstance(step, PlanningStep):
            payload["plan"] = str(getattr(step, "plan", ""))[:2000]

        # Non-blocking async call
        try:
            # We use a background task to not slow down the agent execution loop
            asyncio.create_task(self._send_payload(payload))
        except Exception as e:
            logger.warning(f"Failed to queue audit payload: {e}")

    async def _send_payload(self, payload: Dict[str, Any]):
        try:
            await self._client.post(self.webhook_url, json=payload)
        except Exception as e:
            # We don't want audit failures to crash the agent
            logger.error(f"Audit webhook failed: {e}")

    def get_registry(self, agent_name: str, trace_id: str = "no-trace") -> Dict:
        """
        Returns a dictionary of callbacks configured for this audit instance.
        
        This method now integrates with the cognitive callback registry,
        combining audit callbacks with consciousness callbacks (IWMT, basins, memory).
        """
        def handle_action(step, agent=None, **kwargs):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.on_step(step, agent_name, trace_id), 
                        loop
                    )
                else:
                    asyncio.run(self.on_step(step, agent_name, trace_id))
            except Exception:
                pass  # Audit failure should not break agent
            
            # Also run cognitive callbacks
            try:
                cognitive_registry = get_cognitive_callback_registry()
                cognitive_callbacks = cognitive_registry._callbacks.get(ActionStep, [])
                for callback in cognitive_callbacks:
                    try:
                        callback(step, agent)
                    except Exception as e:
                        logger.debug(f"Cognitive callback failed: {e}")
            except Exception:
                pass

        def handle_planning(step, agent=None, **kwargs):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.on_step(step, agent_name, trace_id), 
                        loop
                    )
                else:
                    asyncio.run(self.on_step(step, agent_name, trace_id))
            except Exception:
                pass
            
            # Also run cognitive callbacks
            try:
                cognitive_registry = get_cognitive_callback_registry()
                cognitive_callbacks = cognitive_registry._callbacks.get(PlanningStep, [])
                for callback in cognitive_callbacks:
                    try:
                        callback(step, agent)
                    except Exception as e:
                        logger.debug(f"Cognitive callback failed: {e}")
            except Exception:
                pass

        return {
            ActionStep: handle_action,
            PlanningStep: handle_planning
        }

_global_audit: Optional[AgentAuditCallback] = None

def get_audit_callback(project_id: str = "dionysus") -> AgentAuditCallback:
    """Get or create the global audit callback instance."""
    global _global_audit
    if _global_audit is None:
        _global_audit = AgentAuditCallback(project_id=project_id)
    return _global_audit


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "AgentAuditCallback",
    "get_audit_callback",
    "DionysusCognitiveCallbackRegistry",
    "get_cognitive_callback_registry",
    # Feature 039, T007: Token usage tracking
    "TokenUsageStats",
    "TokenUsageTracker",
    "get_token_tracker",
    "get_all_token_summaries",
    "get_aggregate_token_stats",
]
