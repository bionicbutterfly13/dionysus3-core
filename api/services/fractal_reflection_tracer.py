"""
Fractal Reflection Tracer

Track 038 Phase 4: Debug and analysis tool for tracing biographical constraint
propagation across fractal metacognition levels.

The tracer captures how constraints flow:
    Journey (Identity) → Episode (Narrative Arc) → Event (Action Selection)

This enables:
- Debugging why certain actions were blocked/preferred
- Visualizing the fractal self-similarity of constraints
- Analyzing narrative coherence across time-scales

Reference:
    - Conway & Pleydell-Pearce (2000). Self-Memory System (SMS)
    - Friston et al. (2022). Designing Ecosystems of Intelligence
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("dionysus.fractal_tracer")


class FractalLevel(str, Enum):
    """Hierarchical levels in the fractal metacognition loop."""
    IDENTITY = "identity"    # Journey-level (years)
    EPISODE = "episode"      # Episode-level (hours-days)
    EVENT = "event"          # Event-level (seconds-minutes)


@dataclass
class ReflectionEvent:
    """A single event in the fractal reflection trace."""
    event_id: str
    timestamp: datetime
    level: FractalLevel
    source: str
    constraint_type: str  # "prior", "biographical", "learned"
    action_affected: str
    effect: str  # "blocked", "warned", "boosted", "injected"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "source": self.source,
            "constraint_type": self.constraint_type,
            "action_affected": self.action_affected,
            "effect": self.effect,
            "details": self.details,
        }


@dataclass
class FractalTrace:
    """
    Complete trace of a fractal reflection cycle.

    Captures constraint propagation across all three levels
    for a single OODA cycle.
    """
    trace_id: str
    cycle_id: str
    agent_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    events: List[ReflectionEvent] = field(default_factory=list)

    # Summary metrics
    identity_constraints_applied: int = 0
    episode_constraints_applied: int = 0
    event_constraints_applied: int = 0
    actions_blocked: int = 0
    actions_warned: int = 0
    actions_boosted: int = 0

    # Narrative coherence score (0-1)
    narrative_coherence: float = 1.0

    def add_event(self, event: ReflectionEvent) -> None:
        """Add a reflection event and update metrics."""
        self.events.append(event)

        # Update level counters
        if event.level == FractalLevel.IDENTITY:
            self.identity_constraints_applied += 1
        elif event.level == FractalLevel.EPISODE:
            self.episode_constraints_applied += 1
        else:
            self.event_constraints_applied += 1

        # Update effect counters
        if event.effect == "blocked":
            self.actions_blocked += 1
        elif event.effect == "warned":
            self.actions_warned += 1
        elif event.effect == "boosted":
            self.actions_boosted += 1

    def finalize(self) -> None:
        """Mark trace as complete and calculate final metrics."""
        self.ended_at = datetime.utcnow()

        # Calculate narrative coherence based on constraint alignment
        total_events = len(self.events)
        if total_events == 0:
            self.narrative_coherence = 1.0
            return

        # Coherence = (boosted - blocked) / total, normalized to 0-1
        boost_block_ratio = (self.actions_boosted - self.actions_blocked) / total_events
        self.narrative_coherence = max(0.0, min(1.0, 0.5 + boost_block_ratio * 0.5))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "cycle_id": self.cycle_id,
            "agent_id": self.agent_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "events": [e.to_dict() for e in self.events],
            "metrics": {
                "identity_constraints_applied": self.identity_constraints_applied,
                "episode_constraints_applied": self.episode_constraints_applied,
                "event_constraints_applied": self.event_constraints_applied,
                "actions_blocked": self.actions_blocked,
                "actions_warned": self.actions_warned,
                "actions_boosted": self.actions_boosted,
                "narrative_coherence": self.narrative_coherence,
            }
        }

    def summary(self) -> str:
        """Human-readable summary of the trace."""
        duration = ""
        if self.ended_at and self.started_at:
            delta = (self.ended_at - self.started_at).total_seconds()
            duration = f" ({delta:.2f}s)"

        return (
            f"FractalTrace[{self.trace_id[:8]}]{duration}\n"
            f"  Identity: {self.identity_constraints_applied} | "
            f"Episode: {self.episode_constraints_applied} | "
            f"Event: {self.event_constraints_applied}\n"
            f"  Effects: {self.actions_blocked} blocked, "
            f"{self.actions_warned} warned, {self.actions_boosted} boosted\n"
            f"  Narrative Coherence: {self.narrative_coherence:.2%}"
        )


class FractalReflectionTracer:
    """
    Traces biographical constraint propagation across fractal levels.

    Usage:
        tracer = FractalReflectionTracer()
        trace = tracer.start_trace(cycle_id="...", agent_id="...")

        # During OODA cycle:
        tracer.trace_identity_constraint(trace, "journey_theme", "explore_curiosity", "boosted", {...})
        tracer.trace_episode_constraint(trace, "current_arc", "complete_chapter", "injected", {...})
        tracer.trace_event_constraint(trace, "basal_prior", "delete_database", "blocked", {...})

        tracer.end_trace(trace)
        print(trace.summary())
    """

    def __init__(self):
        self._active_traces: Dict[str, FractalTrace] = {}
        self._completed_traces: List[FractalTrace] = []
        self._max_completed = 100  # Keep last 100 traces

    def start_trace(self, cycle_id: str, agent_id: str) -> FractalTrace:
        """Start a new fractal reflection trace."""
        trace = FractalTrace(
            trace_id=str(uuid4()),
            cycle_id=cycle_id,
            agent_id=agent_id,
            started_at=datetime.utcnow(),
        )
        self._active_traces[trace.trace_id] = trace
        logger.debug(f"Started fractal trace {trace.trace_id[:8]} for cycle {cycle_id[:8]}")
        return trace

    def end_trace(self, trace: FractalTrace) -> None:
        """Finalize and archive a trace."""
        trace.finalize()

        # Move from active to completed
        if trace.trace_id in self._active_traces:
            del self._active_traces[trace.trace_id]

        self._completed_traces.append(trace)

        # Trim old traces
        if len(self._completed_traces) > self._max_completed:
            self._completed_traces = self._completed_traces[-self._max_completed:]

        logger.debug(f"Completed fractal trace: {trace.summary()}")

    def trace_identity_constraint(
        self,
        trace: FractalTrace,
        source: str,
        action: str,
        effect: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trace an Identity (Journey) level constraint.

        These are the highest-level constraints from autobiographical narrative:
        - Core values and identity markers
        - Long-term themes and unresolved questions
        - Archetype patterns
        """
        event = ReflectionEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            level=FractalLevel.IDENTITY,
            source=source,
            constraint_type="biographical",
            action_affected=action,
            effect=effect,
            details=details or {},
        )
        trace.add_event(event)
        logger.debug(f"[IDENTITY] {source} → {action}: {effect}")

    def trace_episode_constraint(
        self,
        trace: FractalTrace,
        source: str,
        action: str,
        effect: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trace an Episode level constraint.

        These are mid-level constraints from current narrative arc:
        - Active story chapter
        - Current goals and subgoals
        - Session context
        """
        event = ReflectionEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            level=FractalLevel.EPISODE,
            source=source,
            constraint_type="biographical",
            action_affected=action,
            effect=effect,
            details=details or {},
        )
        trace.add_event(event)
        logger.debug(f"[EPISODE] {source} → {action}: {effect}")

    def trace_event_constraint(
        self,
        trace: FractalTrace,
        source: str,
        action: str,
        effect: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trace an Event level constraint.

        These are immediate-level constraints:
        - BASAL priors (survival)
        - DISPOSITIONAL priors (values)
        - LEARNED priors (preferences)
        """
        event = ReflectionEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            level=FractalLevel.EVENT,
            source=source,
            constraint_type="prior",
            action_affected=action,
            effect=effect,
            details=details or {},
        )
        trace.add_event(event)
        logger.debug(f"[EVENT] {source} → {action}: {effect}")

    def trace_prior_check(
        self,
        trace: FractalTrace,
        prior_result: Dict[str, Any],
        action: str,
    ) -> None:
        """
        Convenience method to trace a PriorCheckResult.

        Automatically determines level and effect from the result.
        """
        permitted = prior_result.get("permitted", True)
        blocking_level = prior_result.get("blocking_level")
        warnings = prior_result.get("warnings", [])

        if not permitted:
            # Hard block
            self.trace_event_constraint(
                trace,
                source=prior_result.get("blocked_by", "unknown_prior"),
                action=action,
                effect="blocked",
                details={
                    "reason": prior_result.get("reason"),
                    "level": blocking_level,
                }
            )
        elif warnings:
            # Warnings from DISPOSITIONAL
            for warning in warnings:
                self.trace_event_constraint(
                    trace,
                    source="dispositional_prior",
                    action=action,
                    effect="warned",
                    details={"warning": warning}
                )

        # Check for precision boost (LEARNED PREFER match)
        effective_precision = prior_result.get("effective_precision", 1.0)
        if effective_precision > 1.0:
            self.trace_event_constraint(
                trace,
                source="learned_prior",
                action=action,
                effect="boosted",
                details={"precision_boost": effective_precision}
            )

    def trace_biographical_injection(
        self,
        trace: FractalTrace,
        biographical_cell: Any,
    ) -> None:
        """
        Trace biographical context injection into the OODA cycle.

        Records which identity markers and themes were injected.
        """
        if biographical_cell is None:
            return

        # Extract cell attributes
        journey_id = getattr(biographical_cell, "journey_id", "unknown")
        themes = getattr(biographical_cell, "unresolved_themes", [])
        markers = getattr(biographical_cell, "identity_markers", [])

        # Trace identity-level injection
        self.trace_identity_constraint(
            trace,
            source=f"journey:{journey_id}",
            action="context_injection",
            effect="injected",
            details={
                "themes": themes,
                "identity_markers": markers,
            }
        )

        # Trace each theme as potential constraint
        for theme in themes[:3]:  # Top 3 themes
            self.trace_identity_constraint(
                trace,
                source="unresolved_theme",
                action=str(theme),
                effect="boosted",
                details={"theme": theme}
            )

    def get_active_trace(self, trace_id: str) -> Optional[FractalTrace]:
        """Get an active trace by ID."""
        return self._active_traces.get(trace_id)

    def get_recent_traces(self, limit: int = 10) -> List[FractalTrace]:
        """Get most recent completed traces."""
        return self._completed_traces[-limit:]

    def get_trace_by_cycle(self, cycle_id: str) -> Optional[FractalTrace]:
        """Find a trace by its cycle ID."""
        for trace in reversed(self._completed_traces):
            if trace.cycle_id == cycle_id:
                return trace
        for trace in self._active_traces.values():
            if trace.cycle_id == cycle_id:
                return trace
        return None


# Singleton instance
_tracer_instance: Optional[FractalReflectionTracer] = None


def get_fractal_tracer() -> FractalReflectionTracer:
    """Get the singleton FractalReflectionTracer instance."""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = FractalReflectionTracer()
    return _tracer_instance
