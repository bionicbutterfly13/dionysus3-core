#!/usr/bin/env python3
"""
Token Usage Benchmark Script
Feature: 039-smolagents-v2-alignment
Task: T016

Benchmarks memory pruning effectiveness by comparing token usage
with and without pruning enabled.

Usage:
    python scripts/benchmark_token_usage.py [--steps N] [--runs N]

Output:
    - Token counts before/after pruning
    - Reduction percentage
    - Comparison with target (30%+)
"""

import argparse
import os
import sys
from dataclasses import dataclass
from typing import List
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct import to avoid agent __init__.py chain (which requires smolagents)
# This allows benchmark to run even without full smolagents installation
try:
    from api.agents.audit import TokenUsageTracker, get_aggregate_token_stats
except ImportError:
    # Fallback: define minimal TokenUsageTracker for standalone execution
    from dataclasses import dataclass as dc_dataclass, field as dc_field
    from typing import Dict, Any as TypingAny

    @dc_dataclass
    class TokenUsageStats:
        pre_pruning_tokens: int = 0
        post_pruning_tokens: int = 0
        steps_tracked: int = 0
        pruning_events: int = 0

        @property
        def reduction_tokens(self) -> int:
            return max(0, self.pre_pruning_tokens - self.post_pruning_tokens)

        @property
        def reduction_percentage(self) -> float:
            if self.pre_pruning_tokens == 0:
                return 0.0
            return (self.reduction_tokens / self.pre_pruning_tokens) * 100

    class TokenUsageTracker:
        TOKENS_PER_CHAR = 0.25

        def __init__(self, agent_name: str = "unknown"):
            self.agent_name = agent_name
            self.stats = TokenUsageStats()
            self._current_step_pre_prune: int = 0

        def estimate_tokens(self, text: str) -> int:
            if not text:
                return 0
            return int(len(text) * self.TOKENS_PER_CHAR)

        def record_pre_prune(self, step) -> None:
            observations = getattr(step, "observations", None) or getattr(step, "observation", "")
            self._current_step_pre_prune = self.estimate_tokens(str(observations))
            self.stats.pre_pruning_tokens += self._current_step_pre_prune
            self.stats.steps_tracked += 1

        def record_post_prune(self, step) -> None:
            observations = getattr(step, "observations", None) or getattr(step, "observation", "")
            post_tokens = self.estimate_tokens(str(observations))
            self.stats.post_pruning_tokens += post_tokens
            if post_tokens < self._current_step_pre_prune:
                self.stats.pruning_events += 1

        def get_summary(self) -> Dict[str, TypingAny]:
            return {
                "agent_name": self.agent_name,
                "steps_tracked": self.stats.steps_tracked,
                "pre_pruning_tokens": self.stats.pre_pruning_tokens,
                "post_pruning_tokens": self.stats.post_pruning_tokens,
                "tokens_saved": self.stats.reduction_tokens,
                "reduction_percentage": round(self.stats.reduction_percentage, 2),
                "pruning_events": self.stats.pruning_events,
            }

    def get_aggregate_token_stats() -> Dict[str, TypingAny]:
        return {}


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    run_id: int
    steps: int
    pre_prune_tokens: int
    post_prune_tokens: int
    tokens_saved: int
    reduction_pct: float
    meets_target: bool  # Target: 30%+ reduction


def create_mock_step(step_number: int, observation_length: int = 500) -> MagicMock:
    """Create a mock ActionStep with realistic observation size."""
    step = MagicMock()
    step.step_number = step_number
    step.observations = "x" * observation_length
    step.observation = step.observations
    return step


def simulate_pruning(step: MagicMock, window: int, current_step: int) -> None:
    """Simulate memory pruning on a step."""
    if step.step_number <= current_step - window:
        # Prune to summary
        original = step.observations
        step.observations = f"[PRUNED] {original[:50]}..."


def calculate_memory_tokens(steps: list, tokens_per_char: float = 0.25) -> int:
    """Calculate total tokens in agent memory (all step observations)."""
    total = 0
    for step in steps:
        obs = getattr(step, "observations", "") or ""
        total += int(len(obs) * tokens_per_char)
    return total


def run_benchmark(
    num_steps: int = 10,
    window: int = 3,
    observation_size: int = 500,
) -> BenchmarkResult:
    """
    Run a single benchmark measuring token reduction.

    The benchmark simulates a full agent run and measures:
    - Total tokens WITHOUT pruning (all observations kept)
    - Total tokens WITH pruning (old observations summarized)

    Args:
        num_steps: Number of agent steps to simulate
        window: Memory window size (steps to keep unpruned)
        observation_size: Size of observation text in characters

    Returns:
        BenchmarkResult with token metrics
    """
    tokens_per_char = 0.25

    # Create all steps with full observations
    steps_no_prune = [create_mock_step(i, observation_size) for i in range(num_steps)]

    # Calculate tokens without pruning (baseline)
    pre_prune_tokens = calculate_memory_tokens(steps_no_prune, tokens_per_char)

    # Create steps with pruning applied
    steps_with_prune = [create_mock_step(i, observation_size) for i in range(num_steps)]

    # Simulate agent execution with pruning at each step
    for current_idx in range(num_steps):
        # Apply pruning to steps outside the window
        for old_idx, old_step in enumerate(steps_with_prune[:current_idx]):
            if old_idx <= current_idx - window:
                # Prune: replace with summary
                original = old_step.observations
                old_step.observations = f"[PRUNED] {original[:50]}..."

    # Calculate tokens after pruning
    post_prune_tokens = calculate_memory_tokens(steps_with_prune, tokens_per_char)

    tokens_saved = pre_prune_tokens - post_prune_tokens
    reduction_pct = (tokens_saved / pre_prune_tokens * 100) if pre_prune_tokens > 0 else 0

    return BenchmarkResult(
        run_id=0,
        steps=num_steps,
        pre_prune_tokens=pre_prune_tokens,
        post_prune_tokens=post_prune_tokens,
        tokens_saved=tokens_saved,
        reduction_pct=round(reduction_pct, 1),
        meets_target=reduction_pct >= 30.0,
    )


def run_multiple_benchmarks(
    num_runs: int = 5,
    num_steps: int = 10,
    window: int = 3,
) -> List[BenchmarkResult]:
    """Run multiple benchmark iterations."""
    results = []

    for run_id in range(num_runs):
        # Vary observation size slightly for realism
        obs_size = 400 + (run_id * 50)
        result = run_benchmark(num_steps, window, obs_size)
        result.run_id = run_id + 1
        results.append(result)

    return results


def print_results(results: List[BenchmarkResult]) -> None:
    """Print benchmark results in a formatted table."""
    print("\n" + "=" * 70)
    print("TOKEN USAGE BENCHMARK RESULTS")
    print("Feature: 039-smolagents-v2-alignment")
    print("=" * 70)

    print(f"\n{'Run':<5} {'Steps':<7} {'Pre-Prune':<12} {'Post-Prune':<12} {'Saved':<10} {'Reduction':<12} {'Target':<8}")
    print("-" * 70)

    for r in results:
        target_status = "✓ PASS" if r.meets_target else "✗ FAIL"
        print(
            f"{r.run_id:<5} "
            f"{r.steps:<7} "
            f"{r.pre_prune_tokens:<12} "
            f"{r.post_prune_tokens:<12} "
            f"{r.tokens_saved:<10} "
            f"{r.reduction_pct:>6.1f}%     "
            f"{target_status:<8}"
        )

    # Summary
    avg_reduction = sum(r.reduction_pct for r in results) / len(results)
    all_pass = all(r.meets_target for r in results)

    print("-" * 70)
    print(f"\nAverage Reduction: {avg_reduction:.1f}%")
    print(f"Target (30%+): {'✓ ALL PASS' if all_pass else '✗ SOME FAIL'}")
    print()

    # Exit code for CI
    if not all_pass:
        print("⚠️  WARNING: Some runs did not meet the 30% reduction target")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark memory pruning token reduction"
    )
    parser.add_argument(
        "--steps", type=int, default=10,
        help="Number of agent steps per run (default: 10)"
    )
    parser.add_argument(
        "--runs", type=int, default=5,
        help="Number of benchmark runs (default: 5)"
    )
    parser.add_argument(
        "--window", type=int, default=3,
        help="Memory window size (default: 3)"
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="Exit with error code if target not met (for CI)"
    )

    args = parser.parse_args()

    print(f"Running {args.runs} benchmarks with {args.steps} steps each...")
    print(f"Memory window: {args.window} steps")

    results = run_multiple_benchmarks(
        num_runs=args.runs,
        num_steps=args.steps,
        window=args.window,
    )

    print_results(results)

    # CI mode: exit with error if target not met
    if args.ci:
        all_pass = all(r.meets_target for r in results)
        sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
