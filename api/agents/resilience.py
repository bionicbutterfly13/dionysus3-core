"""
Self-Healing Resilience - Recovery Strategy Registry

Feature: 035-self-healing-resilience
Implements T001-T002, T005: Recovery strategy registry, StrategyHinter, and observation hijacking.

Provides Plan B strategies for common agent failure modes.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("dionysus.resilience")


class FailureType(Enum):
    """Categories of recoverable failures."""
    TIMEOUT = "timeout"
    EMPTY_RESULTS = "empty_results"
    PARSE_ERROR = "parse_error"
    RATE_LIMIT = "rate_limit"
    CONNECTION_ERROR = "connection_error"
    TOOL_ERROR = "tool_error"
    MODEL_ERROR = "model_error"
    BRIDGE_FAILURE = "bridge_failure"


class RecoveryAction(Enum):
    """Available recovery actions."""
    RETRY_SAME = "retry_same"           # Retry with same parameters
    RETRY_PROMOTED = "retry_promoted"   # Retry with better model
    BROADEN_QUERY = "broaden_query"     # Broaden search parameters
    FALLBACK_TOOL = "fallback_tool"     # Use alternative tool
    INCREASE_BUDGET = "increase_budget" # More steps/tokens
    REDUCE_SCOPE = "reduce_scope"       # Simplify the task
    LOCAL_ONLY = "local_only"           # Use local tools only
    SKIP_AND_LOG = "skip_and_log"       # Log and continue
    ESCALATE = "escalate"               # Surface to orchestrator


@dataclass
class RecoveryStrategy:
    """A recovery strategy for a specific failure type."""
    failure_type: FailureType
    action: RecoveryAction
    hint_template: str
    priority: int = 0  # Higher = try first
    max_attempts: int = 2
    cooldown_seconds: float = 1.0
    metadata: dict = field(default_factory=dict)


# T001: Recovery Strategy Registry
RECOVERY_STRATEGIES: dict[FailureType, list[RecoveryStrategy]] = {
    FailureType.TIMEOUT: [
        RecoveryStrategy(
            failure_type=FailureType.TIMEOUT,
            action=RecoveryAction.RETRY_PROMOTED,
            hint_template="Previous attempt timed out. Retrying with enhanced model.",
            priority=10,
            max_attempts=2,
            cooldown_seconds=2.0
        ),
        RecoveryStrategy(
            failure_type=FailureType.TIMEOUT,
            action=RecoveryAction.REDUCE_SCOPE,
            hint_template="Timeout occurred. Try a more specific, smaller task or use a simpler tool.",
            priority=5,
        ),
    ],
    FailureType.EMPTY_RESULTS: [
        RecoveryStrategy(
            failure_type=FailureType.EMPTY_RESULTS,
            action=RecoveryAction.BROADEN_QUERY,
            hint_template="No results found. Broadening search to related concepts.",
            priority=10,
        ),
        RecoveryStrategy(
            failure_type=FailureType.EMPTY_RESULTS,
            action=RecoveryAction.FALLBACK_TOOL,
            hint_template="Semantic search empty. Try 'query_wisdom_graph' for conceptual context.",
            priority=5,
            metadata={"fallback_tool": "query_wisdom_graph"}
        ),
    ],
    FailureType.PARSE_ERROR: [
        RecoveryStrategy(
            failure_type=FailureType.PARSE_ERROR,
            action=RecoveryAction.RETRY_SAME,
            hint_template="Output format was invalid. Retrying with explicit JSON format request.",
            priority=10,
            max_attempts=2,
        ),
        RecoveryStrategy(
            failure_type=FailureType.PARSE_ERROR,
            action=RecoveryAction.RETRY_PROMOTED,
            hint_template="Parsing still failing. Switching to more capable model.",
            priority=5,
        ),
    ],
    FailureType.RATE_LIMIT: [
        RecoveryStrategy(
            failure_type=FailureType.RATE_LIMIT,
            action=RecoveryAction.RETRY_SAME,
            hint_template="Rate limited. Waiting before retry.",
            priority=10,
            cooldown_seconds=5.0,
            max_attempts=3,
        ),
    ],
    FailureType.CONNECTION_ERROR: [
        RecoveryStrategy(
            failure_type=FailureType.CONNECTION_ERROR,
            action=RecoveryAction.RETRY_SAME,
            hint_template="Connection failed. Retrying with exponential backoff.",
            priority=10,
            cooldown_seconds=2.0,
            max_attempts=3,
        ),
    ],
    FailureType.TOOL_ERROR: [
        RecoveryStrategy(
            failure_type=FailureType.TOOL_ERROR,
            action=RecoveryAction.FALLBACK_TOOL,
            hint_template="Tool execution failed. Suggesting alternative approach.",
            priority=10,
        ),
        RecoveryStrategy(
            failure_type=FailureType.TOOL_ERROR,
            action=RecoveryAction.SKIP_AND_LOG,
            hint_template="Tool unavailable. Proceeding without this data source.",
            priority=5,
        ),
    ],
    FailureType.MODEL_ERROR: [
        RecoveryStrategy(
            failure_type=FailureType.MODEL_ERROR,
            action=RecoveryAction.RETRY_PROMOTED,
            hint_template="Model error occurred. Switching to fallback model.",
            priority=10,
        ),
    ],
    FailureType.BRIDGE_FAILURE: [
        RecoveryStrategy(
            failure_type=FailureType.BRIDGE_FAILURE,
            action=RecoveryAction.LOCAL_ONLY,
            hint_template="MCP Tool Bridge is unstable. Fall back to internal reasoning or local reflection tools.",
            priority=10,
        ),
    ],
}


def get_strategies_for_failure(failure_type: FailureType) -> list[RecoveryStrategy]:
    """Get recovery strategies for a failure type, sorted by priority."""
    strategies = RECOVERY_STRATEGIES.get(failure_type, [])
    return sorted(strategies, key=lambda s: s.priority, reverse=True)


def register_strategy(strategy: RecoveryStrategy) -> None:
    """Register a custom recovery strategy."""
    if strategy.failure_type not in RECOVERY_STRATEGIES:
        RECOVERY_STRATEGIES[strategy.failure_type] = []
    RECOVERY_STRATEGIES[strategy.failure_type].append(strategy)
    logger.info(f"Registered recovery strategy: {strategy.action.value} for {strategy.failure_type.value}")


# T002: StrategyHinter - Generate Plan B suggestions
class StrategyHinter:
    """
    Generates Plan B hints based on error context.

    Analyzes failure details and returns appropriate recovery suggestions
    that can be injected into tool outputs or agent prompts.
    """

    def __init__(self):
        self._attempt_counts: dict[str, int] = {}

    def classify_error(self, error_msg: str) -> FailureType:
        """Classify an error message into a FailureType."""
        error_upper = error_msg.upper()

        if "TIMEOUT" in error_upper:
            return FailureType.TIMEOUT
        elif "EMPTY" in error_upper or "NO RESULTS" in error_upper or "NOT FOUND" in error_upper:
            return FailureType.EMPTY_RESULTS
        elif "JSON" in error_upper or "PARSE" in error_upper or "FORMAT" in error_upper:
            return FailureType.PARSE_ERROR
        elif "RATE" in error_upper or "429" in error_upper or "LIMIT" in error_upper:
            return FailureType.RATE_LIMIT
        elif "CONNECTION" in error_upper or "NETWORK" in error_upper or "SOCKET" in error_upper:
            return FailureType.CONNECTION_ERROR
        elif "BRIDGE" in error_upper or "MCP" in error_upper:
            return FailureType.BRIDGE_FAILURE
        elif "MODEL" in error_upper or "LLM" in error_upper:
            return FailureType.MODEL_ERROR
        else:
            return FailureType.TOOL_ERROR

    def get_hint(
        self,
        error_or_type: str | FailureType,
        context: Optional[dict] = None,
        task_id: str = "default"
    ) -> str:
        """
        Get a recovery hint for a failure.

        Args:
            error_or_type: Error message string or FailureType enum
            context: Optional context about the failure
            task_id: Identifier to track attempts per task

        Returns:
            Recovery hint string with RECOVERY_HINT marker
        """
        # Determine failure type
        if isinstance(error_or_type, str):
            failure_type = self.classify_error(error_or_type)
        else:
            failure_type = error_or_type

        # Track attempts per task
        attempt_key = f"{task_id}:{failure_type.value}"
        current_attempts = self._attempt_counts.get(attempt_key, 0)

        strategies = get_strategies_for_failure(failure_type)

        for strategy in strategies:
            if current_attempts < strategy.max_attempts:
                self._attempt_counts[attempt_key] = current_attempts + 1

                # Build hint with context
                hint = strategy.hint_template
                if context:
                    hint = self._enrich_hint(hint, context, strategy)

                logger.info(
                    f"StrategyHinter: {failure_type.value} -> {strategy.action.value} "
                    f"(attempt {current_attempts + 1}/{strategy.max_attempts})"
                )
                return f"RECOVERY_HINT: {hint} Strategy: {strategy.action.value.upper()}"

        # All strategies exhausted
        logger.warning(f"StrategyHinter: No more strategies for {failure_type.value}")
        return "RECOVERY_HINT: All recovery strategies exhausted. Escalating to orchestrator."

    def _enrich_hint(
        self,
        hint: str,
        context: dict,
        strategy: RecoveryStrategy
    ) -> str:
        """Enrich hint with contextual information."""
        enrichments = []

        # Add specific suggestions based on failure context
        if strategy.action == RecoveryAction.BROADEN_QUERY and "query" in context:
            original_query = context["query"]
            enrichments.append(f"Original query: '{original_query}'")
            enrichments.append("Try removing specific terms or using related concepts.")

        if strategy.action == RecoveryAction.FALLBACK_TOOL and "fallback_tool" in strategy.metadata:
            enrichments.append(f"Suggested tool: {strategy.metadata['fallback_tool']}")

        if enrichments:
            hint = f"{hint} {' '.join(enrichments)}"

        return hint

    def reset_attempts(self, task_id: str = "default") -> None:
        """Reset attempt counts for a task."""
        keys_to_remove = [k for k in self._attempt_counts if k.startswith(f"{task_id}:")]
        for key in keys_to_remove:
            del self._attempt_counts[key]

    def get_strategy_action(
        self,
        failure_type: FailureType,
        task_id: str = "default"
    ) -> RecoveryAction:
        """Get the recommended recovery action without generating a hint."""
        attempt_key = f"{task_id}:{failure_type.value}"
        current_attempts = self._attempt_counts.get(attempt_key, 0)

        strategies = get_strategies_for_failure(failure_type)

        for strategy in strategies:
            if current_attempts < strategy.max_attempts:
                return strategy.action

        return RecoveryAction.ESCALATE


# Singleton instance
_strategy_hinter: Optional[StrategyHinter] = None


def get_strategy_hinter() -> StrategyHinter:
    """Get or create the StrategyHinter singleton."""
    global _strategy_hinter
    if _strategy_hinter is None:
        _strategy_hinter = StrategyHinter()
    return _strategy_hinter


# T005: Observation Hijacking - inject Plan B hints into tool output on failure
def wrap_with_resilience(observation: Any, task_id: str = "default") -> Any:
    """
    Hijacks tool observations to inject recovery hints if an error is detected.

    This is the key integration point for self-healing: when a tool returns
    an error or empty result, this function appends a RECOVERY_HINT that
    the agent's prompt recognizes and prioritizes.

    Args:
        observation: The raw tool output
        task_id: Task identifier for attempt tracking

    Returns:
        Original observation with RECOVERY_HINT appended if error detected
    """
    obs_str = str(observation)

    # Detect failure patterns
    error_patterns = ["Error", "failed", "timeout", "exception", "not found", "empty"]
    is_error = any(pattern.lower() in obs_str.lower() for pattern in error_patterns)

    if is_error:
        hinter = get_strategy_hinter()
        hint = hinter.get_hint(obs_str, task_id=task_id)
        return f"{obs_str}\n\n{hint}"

    return observation


# Convenience functions for common failure handling
def hint_for_timeout(context: Optional[dict] = None, task_id: str = "default") -> str:
    """Get recovery hint for timeout failure."""
    return get_strategy_hinter().get_hint(FailureType.TIMEOUT, context, task_id)


def hint_for_empty_results(context: Optional[dict] = None, task_id: str = "default") -> str:
    """Get recovery hint for empty results."""
    return get_strategy_hinter().get_hint(FailureType.EMPTY_RESULTS, context, task_id)


def hint_for_parse_error(context: Optional[dict] = None, task_id: str = "default") -> str:
    """Get recovery hint for parse error."""
    return get_strategy_hinter().get_hint(FailureType.PARSE_ERROR, context, task_id)
