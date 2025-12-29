"""
Unit tests for Self-Healing Resilience module.

Feature: 035-self-healing-resilience
Tests T007: Search fallback (Empty results -> Suggested broaden)
"""

import pytest
from api.agents.resilience import (
    FailureType,
    RecoveryAction,
    RecoveryStrategy,
    StrategyHinter,
    get_strategy_hinter,
    get_strategies_for_failure,
    register_strategy,
    wrap_with_resilience,
    hint_for_timeout,
    hint_for_empty_results,
    hint_for_parse_error,
    RECOVERY_STRATEGIES,
)


class TestFailureTypeClassification:
    """Tests for error message classification."""

    def test_classify_timeout(self):
        """Test timeout error classification."""
        hinter = StrategyHinter()
        assert hinter.classify_error("Operation timed out") == FailureType.TIMEOUT
        assert hinter.classify_error("TIMEOUT after 30s") == FailureType.TIMEOUT

    def test_classify_empty_results(self):
        """Test empty results classification."""
        hinter = StrategyHinter()
        assert hinter.classify_error("No results found") == FailureType.EMPTY_RESULTS
        assert hinter.classify_error("Empty response") == FailureType.EMPTY_RESULTS
        assert hinter.classify_error("Entity not found") == FailureType.EMPTY_RESULTS

    def test_classify_parse_error(self):
        """Test parse error classification."""
        hinter = StrategyHinter()
        assert hinter.classify_error("JSON parsing failed") == FailureType.PARSE_ERROR
        assert hinter.classify_error("Invalid format") == FailureType.PARSE_ERROR

    def test_classify_rate_limit(self):
        """Test rate limit classification."""
        hinter = StrategyHinter()
        assert hinter.classify_error("Rate limit exceeded") == FailureType.RATE_LIMIT
        assert hinter.classify_error("HTTP 429") == FailureType.RATE_LIMIT

    def test_classify_connection_error(self):
        """Test connection error classification."""
        hinter = StrategyHinter()
        assert hinter.classify_error("Connection refused") == FailureType.CONNECTION_ERROR
        assert hinter.classify_error("Network error") == FailureType.CONNECTION_ERROR

    def test_classify_bridge_failure(self):
        """Test MCP bridge failure classification."""
        hinter = StrategyHinter()
        assert hinter.classify_error("MCP bridge error") == FailureType.BRIDGE_FAILURE
        assert hinter.classify_error("Bridge connection failed") == FailureType.BRIDGE_FAILURE

    def test_classify_unknown_defaults_to_tool_error(self):
        """Test unknown errors default to tool error."""
        hinter = StrategyHinter()
        assert hinter.classify_error("Some random error") == FailureType.TOOL_ERROR


class TestStrategyHinter:
    """Tests for StrategyHinter hint generation."""

    def test_get_hint_for_timeout(self):
        """Test hint generation for timeout."""
        hinter = StrategyHinter()
        hint = hinter.get_hint(FailureType.TIMEOUT, task_id="test-1")

        assert "RECOVERY_HINT:" in hint
        assert "timed out" in hint.lower() or "timeout" in hint.lower()

    def test_get_hint_for_empty_results_suggests_broaden(self):
        """T007: Verify Search fallback (Empty results -> Suggested broaden)."""
        hinter = StrategyHinter()
        hint = hinter.get_hint(FailureType.EMPTY_RESULTS, task_id="test-search")

        assert "RECOVERY_HINT:" in hint
        assert "BROADEN_QUERY" in hint or "broaden" in hint.lower()

    def test_get_hint_with_context_enrichment(self):
        """Test hint enrichment with query context."""
        hinter = StrategyHinter()
        context = {"query": "specific technical term"}
        hint = hinter.get_hint(
            FailureType.EMPTY_RESULTS,
            context=context,
            task_id="test-context"
        )

        assert "RECOVERY_HINT:" in hint
        # Context should enrich the hint
        assert "specific technical term" in hint or "related concepts" in hint.lower()

    def test_attempt_tracking_escalates_strategy(self):
        """Test that repeated failures escalate through strategies."""
        hinter = StrategyHinter()
        task_id = "test-escalation"

        # First attempt - should use high priority strategy
        hint1 = hinter.get_hint(FailureType.EMPTY_RESULTS, task_id=task_id)
        assert "BROADEN_QUERY" in hint1

        # Second attempt - should use next strategy (fallback tool)
        hint2 = hinter.get_hint(FailureType.EMPTY_RESULTS, task_id=task_id)
        assert "FALLBACK_TOOL" in hint2 or "query_wisdom_graph" in hint2

    def test_reset_attempts(self):
        """Test attempt counter reset."""
        hinter = StrategyHinter()
        task_id = "test-reset"

        # Make some attempts
        hinter.get_hint(FailureType.TIMEOUT, task_id=task_id)
        hinter.get_hint(FailureType.TIMEOUT, task_id=task_id)

        # Reset
        hinter.reset_attempts(task_id)

        # Should start fresh
        hint = hinter.get_hint(FailureType.TIMEOUT, task_id=task_id)
        assert "RETRY_PROMOTED" in hint  # First strategy again

    def test_get_hint_from_error_string(self):
        """Test hint generation from error message string."""
        hinter = StrategyHinter()
        hint = hinter.get_hint("Operation timed out after 30 seconds", task_id="test-str")

        assert "RECOVERY_HINT:" in hint
        assert "timeout" in hint.lower() or "RETRY" in hint

    def test_all_strategies_exhausted(self):
        """Test message when all strategies are exhausted."""
        hinter = StrategyHinter()
        task_id = "test-exhausted"

        # Exhaust all parse error strategies
        for _ in range(10):
            hint = hinter.get_hint(FailureType.PARSE_ERROR, task_id=task_id)

        assert "exhausted" in hint.lower() or "escalating" in hint.lower()


class TestGetStrategyAction:
    """Tests for get_strategy_action method."""

    def test_get_action_without_hint(self):
        """Test getting action without generating full hint."""
        hinter = StrategyHinter()
        action = hinter.get_strategy_action(FailureType.TIMEOUT, task_id="test-action")

        assert action == RecoveryAction.RETRY_PROMOTED

    def test_action_escalates_to_escalate(self):
        """Test action becomes ESCALATE when strategies exhausted."""
        hinter = StrategyHinter()
        task_id = "test-action-exhaust"

        # Exhaust strategies by calling get_hint multiple times
        for _ in range(10):
            hinter.get_hint(FailureType.MODEL_ERROR, task_id=task_id)

        action = hinter.get_strategy_action(FailureType.MODEL_ERROR, task_id=task_id)
        assert action == RecoveryAction.ESCALATE


class TestWrapWithResilience:
    """Tests for observation hijacking."""

    def test_wrap_error_observation(self):
        """Test that error observations get RECOVERY_HINT appended."""
        # Reset singleton for clean test
        from api.agents import resilience
        resilience._strategy_hinter = None

        observation = "Error: Connection failed to database"
        wrapped = wrap_with_resilience(observation, task_id="test-wrap")

        assert "Error: Connection failed" in wrapped
        assert "RECOVERY_HINT:" in wrapped

    def test_wrap_success_observation_unchanged(self):
        """Test that successful observations pass through unchanged."""
        observation = "Successfully retrieved 5 results"
        wrapped = wrap_with_resilience(observation, task_id="test-success")

        assert wrapped == observation
        assert "RECOVERY_HINT" not in wrapped

    def test_wrap_empty_result_gets_hint(self):
        """Test that empty result observations get hints."""
        from api.agents import resilience
        resilience._strategy_hinter = None

        observation = "Search returned empty results"
        wrapped = wrap_with_resilience(observation, task_id="test-empty")

        assert "RECOVERY_HINT:" in wrapped

    def test_wrap_timeout_gets_hint(self):
        """Test that timeout observations get hints."""
        from api.agents import resilience
        resilience._strategy_hinter = None

        observation = "Request timeout after 30 seconds"
        wrapped = wrap_with_resilience(observation, task_id="test-timeout")

        assert "RECOVERY_HINT:" in wrapped


class TestConvenienceFunctions:
    """Tests for convenience hint functions."""

    def test_hint_for_timeout(self):
        """Test timeout convenience function."""
        from api.agents import resilience
        resilience._strategy_hinter = None

        hint = hint_for_timeout(task_id="test-conv-timeout")
        assert "RECOVERY_HINT:" in hint

    def test_hint_for_empty_results(self):
        """Test empty results convenience function."""
        from api.agents import resilience
        resilience._strategy_hinter = None

        hint = hint_for_empty_results(task_id="test-conv-empty")
        assert "RECOVERY_HINT:" in hint

    def test_hint_for_parse_error(self):
        """Test parse error convenience function."""
        from api.agents import resilience
        resilience._strategy_hinter = None

        hint = hint_for_parse_error(task_id="test-conv-parse")
        assert "RECOVERY_HINT:" in hint


class TestRecoveryStrategyRegistry:
    """Tests for strategy registry operations."""

    def test_get_strategies_sorted_by_priority(self):
        """Test strategies are returned sorted by priority."""
        strategies = get_strategies_for_failure(FailureType.TIMEOUT)

        assert len(strategies) >= 2
        # Should be sorted descending by priority
        for i in range(len(strategies) - 1):
            assert strategies[i].priority >= strategies[i + 1].priority

    def test_register_custom_strategy(self):
        """Test registering a custom strategy."""
        custom = RecoveryStrategy(
            failure_type=FailureType.TOOL_ERROR,
            action=RecoveryAction.SKIP_AND_LOG,
            hint_template="Custom: Skip this tool and continue.",
            priority=100,  # Very high priority
        )

        original_count = len(get_strategies_for_failure(FailureType.TOOL_ERROR))
        register_strategy(custom)
        new_count = len(get_strategies_for_failure(FailureType.TOOL_ERROR))

        assert new_count == original_count + 1

        # High priority should be first
        strategies = get_strategies_for_failure(FailureType.TOOL_ERROR)
        assert strategies[0].priority == 100

    def test_all_failure_types_have_strategies(self):
        """Test all failure types have at least one strategy."""
        for failure_type in FailureType:
            strategies = get_strategies_for_failure(failure_type)
            assert len(strategies) > 0, f"No strategies for {failure_type.value}"


class TestSingletonBehavior:
    """Tests for singleton pattern."""

    def test_get_strategy_hinter_returns_singleton(self):
        """Test that get_strategy_hinter returns same instance."""
        from api.agents import resilience
        resilience._strategy_hinter = None

        hinter1 = get_strategy_hinter()
        hinter2 = get_strategy_hinter()

        assert hinter1 is hinter2
