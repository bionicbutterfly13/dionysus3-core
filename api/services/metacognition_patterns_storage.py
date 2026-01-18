"""
Procedural Metacognition Execution Patterns Storage (HOT Tier)

Feature: 040-metacognitive-particles + 047-multi-tier-memory

Implements persistent storage of metacognition execution patterns for fast agent
runtime access. Patterns include monitoring strategies, control thresholds,
thoughtseed competition algorithms, and loop prevention heuristics.

Tier: HOT (in-memory cache with configurable TTL)
Access: O(1) lookups during agent execution

AUTHOR: Mani Saint-Victor, MD
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from uuid import uuid4

logger = logging.getLogger("dionysus.metacognition_patterns")


class PatternType(str, Enum):
    """Types of metacognition execution patterns."""
    MONITORING = "monitoring"
    CONTROL = "control"
    THOUGHTSEED_COMPETITION = "thoughtseed_competition"
    LOOP_PREVENTION = "loop_prevention"


@dataclass
class MonitoringPattern:
    """Monitoring pattern: Check surprise, confidence, basin stability every N steps."""

    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    pattern_type: PatternType = PatternType.MONITORING
    check_interval: int = 3  # Every 3 steps
    ttl_hours: int = 1  # 1 hour cache

    # Metrics to monitor
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "surprise": 0.0,
        "confidence": 0.0,
        "basin_stability": 0.0,
    })

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0

    def is_expired(self) -> bool:
        """Check if pattern has expired based on TTL."""
        expiry = self.created_at + timedelta(hours=self.ttl_hours)
        return datetime.utcnow() > expiry

    def update_access(self):
        """Update last access time and increment counter."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "check_interval": self.check_interval,
            "ttl_hours": self.ttl_hours,
            "metrics": self.metrics,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }


@dataclass
class ControlPattern:
    """Control pattern: Actions based on high_surprise, low_confidence."""

    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    pattern_type: PatternType = PatternType.CONTROL

    # Thresholds
    surprise_threshold: float = 0.7
    confidence_threshold: float = 0.3
    free_energy_threshold: float = 3.0

    # Control actions (mappings to actions)
    actions: Dict[str, Any] = field(default_factory=lambda: {
        "high_surprise": "generate_thoughtseeds",
        "low_confidence": "replan",
        "high_free_energy": "reduce_model_complexity",
    })

    # Precision modulation settings
    precision_delta: float = 0.1
    precision_bounds: Dict[str, float] = field(default_factory=lambda: {
        "min": 0.1,
        "max": 0.9,
    })

    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0

    def update_access(self):
        """Update last access time and increment counter."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def get_action_for_state(self, surprise: float, confidence: float,
                            free_energy: float) -> Optional[str]:
        """Get control action based on current state."""
        if surprise > self.surprise_threshold:
            return self.actions.get("high_surprise")
        if confidence < self.confidence_threshold:
            return self.actions.get("low_confidence")
        if free_energy > self.free_energy_threshold:
            return self.actions.get("high_free_energy")
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "surprise_threshold": self.surprise_threshold,
            "confidence_threshold": self.confidence_threshold,
            "free_energy_threshold": self.free_energy_threshold,
            "actions": self.actions,
            "precision_delta": self.precision_delta,
            "precision_bounds": self.precision_bounds,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }


@dataclass
class ThoughtseedCompetitionPattern:
    """Thoughtseed competition algorithm using Active Inference Free Energy."""

    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    pattern_type: PatternType = PatternType.THOUGHTSEED_COMPETITION

    # Algorithm: Active Inference Competition
    algorithm: str = "active_inference_competition"
    max_iterations: int = 100

    # Winner selection criterion: min(free_energy)
    winner_criterion: str = "min_free_energy"

    # Active Inference parameters
    precision_weight: float = 2.0
    simulation_count: int = 32
    max_depth: int = 4

    # Thought generation parameters
    max_thoughtseeds_per_step: int = 5
    diversity_weight: float = 0.3

    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0

    def update_access(self):
        """Update last access time and increment counter."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "algorithm": self.algorithm,
            "max_iterations": self.max_iterations,
            "winner_criterion": self.winner_criterion,
            "precision_weight": self.precision_weight,
            "simulation_count": self.simulation_count,
            "max_depth": self.max_depth,
            "max_thoughtseeds_per_step": self.max_thoughtseeds_per_step,
            "diversity_weight": self.diversity_weight,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }


@dataclass
class LoopPreventionPattern:
    """Loop prevention: Depth limit, termination on diminishing returns."""

    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    pattern_type: PatternType = PatternType.LOOP_PREVENTION

    # Depth limit
    max_recursion_depth: int = 3

    # Termination conditions
    diminishing_returns_threshold: float = 0.05  # If improvement < 5%, terminate
    improvement_window: int = 3  # Check over last 3 iterations

    # Force execution after N meta-steps
    force_execution_after_steps: int = 5

    # Tracking state
    step_counter: int = 0
    last_improvements: List[float] = field(default_factory=list)
    recursion_depth: int = 0

    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0

    def update_access(self):
        """Update last access time and increment counter."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def should_continue_recursion(self) -> bool:
        """Determine if recursion should continue."""
        # Hard limit on depth
        if self.recursion_depth >= self.max_recursion_depth:
            logger.debug(f"Recursion limit reached: {self.recursion_depth}")
            return False

        # Check for diminishing returns
        if len(self.last_improvements) >= self.improvement_window:
            recent = self.last_improvements[-self.improvement_window:]
            avg_improvement = sum(recent) / len(recent)
            if avg_improvement < self.diminishing_returns_threshold:
                logger.debug(f"Diminishing returns detected: avg={avg_improvement:.4f}")
                return False

        # Force execution check
        if self.step_counter >= self.force_execution_after_steps:
            logger.debug(f"Force execution triggered after {self.step_counter} steps")
            return False

        return True

    def record_improvement(self, improvement: float):
        """Record improvement in current iteration."""
        self.last_improvements.append(improvement)
        # Keep only recent improvements
        if len(self.last_improvements) > self.improvement_window * 2:
            self.last_improvements = self.last_improvements[-(self.improvement_window * 2):]

    def increment_step(self):
        """Increment step counter."""
        self.step_counter += 1

    def reset_for_new_context(self):
        """Reset state for new recursion context."""
        self.step_counter = 0
        self.last_improvements = []
        self.recursion_depth = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "max_recursion_depth": self.max_recursion_depth,
            "diminishing_returns_threshold": self.diminishing_returns_threshold,
            "improvement_window": self.improvement_window,
            "force_execution_after_steps": self.force_execution_after_steps,
            "step_counter": self.step_counter,
            "last_improvements": self.last_improvements,
            "recursion_depth": self.recursion_depth,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }


class ProceduralMetacognitionPatternsStorage:
    """
    HOT-tier in-memory storage for metacognition execution patterns.

    Provides O(1) access to patterns for agent runtime.
    Patterns are cached with TTL and accessed frequently during execution.
    """

    def __init__(self):
        """Initialize pattern storage."""
        # Pattern stores by type
        self._monitoring_patterns: Dict[str, MonitoringPattern] = {}
        self._control_patterns: Dict[str, ControlPattern] = {}
        self._thoughtseed_patterns: Dict[str, ThoughtseedCompetitionPattern] = {}
        self._loop_prevention_patterns: Dict[str, LoopPreventionPattern] = {}

        # Global pattern indices for quick lookup
        self._pattern_index: Dict[str, tuple] = {}  # pattern_id -> (type, pattern)

        # Statistics
        self._stats = {
            "patterns_stored": 0,
            "patterns_accessed": 0,
            "patterns_expired": 0,
            "total_access_count": 0,
        }

        # Initialize default patterns
        self._initialize_defaults()

        logger.info("ProceduralMetacognitionPatternsStorage initialized (HOT tier)")

    def _initialize_defaults(self):
        """Initialize default patterns."""
        # Default monitoring pattern
        monitor = MonitoringPattern(
            check_interval=3,
            ttl_hours=1,
            config={
                "description": "Standard monitoring with 3-step interval",
                "enabled": True,
            }
        )
        self.store_monitoring_pattern(monitor)

        # Default control pattern
        control = ControlPattern(
            surprise_threshold=0.7,
            confidence_threshold=0.3,
            free_energy_threshold=3.0,
            config={
                "description": "Standard control with precision modulation",
                "enabled": True,
            }
        )
        self.store_control_pattern(control)

        # Default thoughtseed pattern
        thoughtseed = ThoughtseedCompetitionPattern(
            algorithm="active_inference_competition",
            max_iterations=100,
            winner_criterion="min_free_energy",
            config={
                "description": "Active Inference-based thoughtseed competition",
                "enabled": True,
            }
        )
        self.store_thoughtseed_pattern(thoughtseed)

        # Default loop prevention pattern
        loop_prev = LoopPreventionPattern(
            max_recursion_depth=3,
            diminishing_returns_threshold=0.05,
            improvement_window=3,
            force_execution_after_steps=5,
            config={
                "description": "Loop prevention with depth and improvement checks",
                "enabled": True,
            }
        )
        self.store_loop_prevention_pattern(loop_prev)

        logger.info("Initialized 4 default metacognition patterns")

    # --- Monitoring Pattern Methods ---

    def store_monitoring_pattern(self, pattern: MonitoringPattern) -> str:
        """Store a monitoring pattern."""
        self._monitoring_patterns[pattern.pattern_id] = pattern
        self._pattern_index[pattern.pattern_id] = (PatternType.MONITORING, pattern)
        self._stats["patterns_stored"] += 1
        logger.debug(f"Stored monitoring pattern: {pattern.pattern_id}")
        return pattern.pattern_id

    def get_monitoring_pattern(self, pattern_id: str) -> Optional[MonitoringPattern]:
        """Retrieve a monitoring pattern with access tracking."""
        pattern = self._monitoring_patterns.get(pattern_id)
        if pattern:
            pattern.update_access()
            self._stats["patterns_accessed"] += 1
            self._stats["total_access_count"] += 1
        return pattern

    def get_default_monitoring_pattern(self) -> Optional[MonitoringPattern]:
        """Get the first (default) monitoring pattern."""
        for pattern in self._monitoring_patterns.values():
            return pattern
        return None

    # --- Control Pattern Methods ---

    def store_control_pattern(self, pattern: ControlPattern) -> str:
        """Store a control pattern."""
        self._control_patterns[pattern.pattern_id] = pattern
        self._pattern_index[pattern.pattern_id] = (PatternType.CONTROL, pattern)
        self._stats["patterns_stored"] += 1
        logger.debug(f"Stored control pattern: {pattern.pattern_id}")
        return pattern.pattern_id

    def get_control_pattern(self, pattern_id: str) -> Optional[ControlPattern]:
        """Retrieve a control pattern with access tracking."""
        pattern = self._control_patterns.get(pattern_id)
        if pattern:
            pattern.update_access()
            self._stats["patterns_accessed"] += 1
            self._stats["total_access_count"] += 1
        return pattern

    def get_default_control_pattern(self) -> Optional[ControlPattern]:
        """Get the first (default) control pattern."""
        for pattern in self._control_patterns.values():
            return pattern
        return None

    # --- Thoughtseed Competition Pattern Methods ---

    def store_thoughtseed_pattern(self, pattern: ThoughtseedCompetitionPattern) -> str:
        """Store a thoughtseed competition pattern."""
        self._thoughtseed_patterns[pattern.pattern_id] = pattern
        self._pattern_index[pattern.pattern_id] = (PatternType.THOUGHTSEED_COMPETITION, pattern)
        self._stats["patterns_stored"] += 1
        logger.debug(f"Stored thoughtseed pattern: {pattern.pattern_id}")
        return pattern.pattern_id

    def get_thoughtseed_pattern(self, pattern_id: str) -> Optional[ThoughtseedCompetitionPattern]:
        """Retrieve a thoughtseed pattern with access tracking."""
        pattern = self._thoughtseed_patterns.get(pattern_id)
        if pattern:
            pattern.update_access()
            self._stats["patterns_accessed"] += 1
            self._stats["total_access_count"] += 1
        return pattern

    def get_default_thoughtseed_pattern(self) -> Optional[ThoughtseedCompetitionPattern]:
        """Get the first (default) thoughtseed pattern."""
        for pattern in self._thoughtseed_patterns.values():
            return pattern
        return None

    # --- Loop Prevention Pattern Methods ---

    def store_loop_prevention_pattern(self, pattern: LoopPreventionPattern) -> str:
        """Store a loop prevention pattern."""
        self._loop_prevention_patterns[pattern.pattern_id] = pattern
        self._pattern_index[pattern.pattern_id] = (PatternType.LOOP_PREVENTION, pattern)
        self._stats["patterns_stored"] += 1
        logger.debug(f"Stored loop prevention pattern: {pattern.pattern_id}")
        return pattern.pattern_id

    def get_loop_prevention_pattern(self, pattern_id: str) -> Optional[LoopPreventionPattern]:
        """Retrieve a loop prevention pattern with access tracking."""
        pattern = self._loop_prevention_patterns.get(pattern_id)
        if pattern:
            pattern.update_access()
            self._stats["patterns_accessed"] += 1
            self._stats["total_access_count"] += 1
        return pattern

    def get_default_loop_prevention_pattern(self) -> Optional[LoopPreventionPattern]:
        """Get the first (default) loop prevention pattern."""
        for pattern in self._loop_prevention_patterns.values():
            return pattern
        return None

    # --- Cleanup Methods ---

    def cleanup_expired_patterns(self) -> Dict[str, int]:
        """Remove expired patterns from storage."""
        expired_counts = {
            "monitoring": 0,
            "control": 0,
            "thoughtseed": 0,
            "loop_prevention": 0,
        }

        # Clean monitoring patterns
        expired_ids = [
            pid for pid, p in self._monitoring_patterns.items()
            if p.is_expired()
        ]
        for pid in expired_ids:
            del self._monitoring_patterns[pid]
            del self._pattern_index[pid]
            expired_counts["monitoring"] += 1

        # Note: Control patterns don't have TTL, so skip them

        # Total expiry count
        self._stats["patterns_expired"] += sum(expired_counts.values())

        if sum(expired_counts.values()) > 0:
            logger.info(f"Cleaned expired patterns: {expired_counts}")

        return expired_counts

    def clear_all_patterns(self):
        """Clear all patterns from storage."""
        self._monitoring_patterns.clear()
        self._control_patterns.clear()
        self._thoughtseed_patterns.clear()
        self._loop_prevention_patterns.clear()
        self._pattern_index.clear()
        logger.info("Cleared all patterns from storage")

    # --- Statistics and Inspection ---

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            **self._stats,
            "monitoring_patterns_count": len(self._monitoring_patterns),
            "control_patterns_count": len(self._control_patterns),
            "thoughtseed_patterns_count": len(self._thoughtseed_patterns),
            "loop_prevention_patterns_count": len(self._loop_prevention_patterns),
            "total_patterns": len(self._pattern_index),
        }

    def list_all_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all patterns as serialized dicts."""
        return {
            "monitoring": [p.to_dict() for p in self._monitoring_patterns.values()],
            "control": [p.to_dict() for p in self._control_patterns.values()],
            "thoughtseed": [p.to_dict() for p in self._thoughtseed_patterns.values()],
            "loop_prevention": [p.to_dict() for p in self._loop_prevention_patterns.values()],
        }

    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve any pattern by ID."""
        pattern_tuple = self._pattern_index.get(pattern_id)
        if not pattern_tuple:
            return None

        pattern_type, pattern = pattern_tuple

        # Update access count
        if hasattr(pattern, "update_access"):
            pattern.update_access()
            self._stats["patterns_accessed"] += 1
            self._stats["total_access_count"] += 1

        if hasattr(pattern, "to_dict"):
            return pattern.to_dict()
        return None


# Singleton instance
_patterns_storage_instance: Optional[ProceduralMetacognitionPatternsStorage] = None


def get_metacognition_patterns_storage() -> ProceduralMetacognitionPatternsStorage:
    """Get or create the singleton patterns storage instance."""
    global _patterns_storage_instance
    if _patterns_storage_instance is None:
        _patterns_storage_instance = ProceduralMetacognitionPatternsStorage()
    return _patterns_storage_instance


async def initialize_metacognition_patterns_storage() -> ProceduralMetacognitionPatternsStorage:
    """Initialize patterns storage on startup."""
    storage = get_metacognition_patterns_storage()
    logger.info("Metacognition patterns storage initialized")
    return storage
