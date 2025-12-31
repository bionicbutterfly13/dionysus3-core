"""
Procedural Metacognition Service - Monitor and Control Functions

Feature: 040-metacognitive-particles
Based on: Seragnoli et al. (2025) - Procedural Metacognition

Implements monitoring and control functions for cognitive self-regulation:
- Monitoring: Non-invasive assessment of cognitive state
- Control: Recommended mental actions based on issues detected

Issue Categories:
- HIGH_PREDICTION_ERROR: Error exceeds threshold
- LOW_CONFIDENCE: Precision below threshold
- STALLED_PROGRESS: No progress in N cycles
- ATTENTION_SCATTERED: Spotlight precision too low

AUTHOR: Mani Saint-Victor, MD
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.models.metacognitive_particle import MentalActionType

logger = logging.getLogger("dionysus.services.procedural_metacognition")


# Issue type constants
class IssueType:
    HIGH_PREDICTION_ERROR = "HIGH_PREDICTION_ERROR"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    STALLED_PROGRESS = "STALLED_PROGRESS"
    ATTENTION_SCATTERED = "ATTENTION_SCATTERED"


# Default thresholds
PREDICTION_ERROR_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.3
PROGRESS_STALL_CYCLES = 5
SPOTLIGHT_PRECISION_THRESHOLD = 0.2


@dataclass
class CognitiveAssessment:
    """
    Output of procedural metacognition monitoring function.

    Represents a non-invasive assessment of an agent's cognitive state.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    progress: float = 0.0  # Task progress (0.0 to 1.0)
    confidence: float = 0.0  # Overall confidence level
    prediction_error: float = 0.0  # Current prediction error magnitude
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "progress": self.progress,
            "confidence": self.confidence,
            "prediction_error": self.prediction_error,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "assessed_at": self.assessed_at.isoformat()
        }


@dataclass
class MentalActionRequest:
    """Request for a mental action (for control recommendations)."""
    source_agent: str
    target_agent: str
    action_type: MentalActionType
    modulation: Dict[str, Any] = field(default_factory=dict)


class ProceduralMetacognition:
    """
    Procedural metacognition service for monitoring and control.

    Implements FR-018-FR-020:
    - monitor(): Non-invasive assessment of cognitive state
    - control(): Recommended mental actions based on assessment
    - Observable events for logging
    """

    def __init__(
        self,
        prediction_error_threshold: float = PREDICTION_ERROR_THRESHOLD,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        stall_cycles: int = PROGRESS_STALL_CYCLES,
        spotlight_threshold: float = SPOTLIGHT_PRECISION_THRESHOLD
    ):
        self.prediction_error_threshold = prediction_error_threshold
        self.confidence_threshold = confidence_threshold
        self.stall_cycles = stall_cycles
        self.spotlight_threshold = spotlight_threshold

        # Track progress history for stall detection
        self.progress_history: Dict[str, List[float]] = {}

    async def monitor(self, agent_id: str) -> CognitiveAssessment:
        """
        Non-invasive assessment of cognitive state.

        FR-018: Monitoring function that observes without modifying.

        Args:
            agent_id: Agent to assess

        Returns:
            CognitiveAssessment with progress, confidence, issues
        """
        # Get agent state (placeholder - integrate with agent registry)
        state = await self._get_agent_state(agent_id)

        # Extract metrics
        progress = state.get("progress", 0.0)
        confidence = state.get("confidence", 0.5)
        prediction_error = state.get("prediction_error", 0.0)
        spotlight_precision = state.get("spotlight_precision", 0.5)

        # Detect issues
        issues = []
        recommendations = []

        # Check prediction error
        if prediction_error > self.prediction_error_threshold:
            issues.append(IssueType.HIGH_PREDICTION_ERROR)
            recommendations.append("Reduce prediction error through belief update")

        # Check confidence
        if confidence < self.confidence_threshold:
            issues.append(IssueType.LOW_CONFIDENCE)
            recommendations.append("Increase precision on key beliefs")

        # Check for stalled progress
        if self._is_stalled(agent_id, progress):
            issues.append(IssueType.STALLED_PROGRESS)
            recommendations.append("Consider alternative cognitive strategies")

        # Check spotlight precision
        if spotlight_precision < self.spotlight_threshold:
            issues.append(IssueType.ATTENTION_SCATTERED)
            recommendations.append("Focus attentional spotlight on primary goal")

        # Update progress history
        self._update_progress_history(agent_id, progress)

        assessment = CognitiveAssessment(
            agent_id=agent_id,
            progress=progress,
            confidence=confidence,
            prediction_error=prediction_error,
            issues=issues,
            recommendations=recommendations
        )

        # Log observable event (FR-020)
        self._log_assessment_event(assessment)

        return assessment

    async def control(
        self,
        assessment: CognitiveAssessment
    ) -> List[MentalActionRequest]:
        """
        Generate recommended control actions based on assessment.

        FR-019: Control function that returns mental actions to regulate cognition.

        Args:
            assessment: Cognitive assessment with detected issues

        Returns:
            List of recommended mental actions
        """
        actions = []

        for issue in assessment.issues:
            action = self._generate_control_action(assessment.agent_id, issue)
            if action:
                actions.append(action)

        # Log control actions (FR-020)
        logger.info(
            f"Generated {len(actions)} control actions for {assessment.agent_id}"
        )

        return actions

    def _generate_control_action(
        self,
        agent_id: str,
        issue: str
    ) -> Optional[MentalActionRequest]:
        """Generate a control action for a specific issue."""

        if issue == IssueType.HIGH_PREDICTION_ERROR:
            return MentalActionRequest(
                source_agent="procedural_metacognition",
                target_agent=agent_id,
                action_type=MentalActionType.PRECISION_DELTA,
                modulation={"precision_delta": -0.1}  # Reduce precision to be more open
            )

        elif issue == IssueType.LOW_CONFIDENCE:
            return MentalActionRequest(
                source_agent="procedural_metacognition",
                target_agent=agent_id,
                action_type=MentalActionType.SET_PRECISION,
                modulation={"precision": 0.5}  # Set moderate precision
            )

        elif issue == IssueType.STALLED_PROGRESS:
            return MentalActionRequest(
                source_agent="procedural_metacognition",
                target_agent=agent_id,
                action_type=MentalActionType.FOCUS_TARGET,
                modulation={
                    "focus_target": "alternative_strategy",
                    "spotlight_precision": 0.7
                }
            )

        elif issue == IssueType.ATTENTION_SCATTERED:
            return MentalActionRequest(
                source_agent="procedural_metacognition",
                target_agent=agent_id,
                action_type=MentalActionType.SPOTLIGHT_PRECISION,
                modulation={"spotlight_precision": 0.8}  # Focus attention
            )

        return None

    async def _get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Get current state of an agent.

        Placeholder - integrate with agent registry.
        """
        # TODO: Integrate with actual agent state retrieval
        # For now, return default values
        return {
            "progress": 0.5,
            "confidence": 0.6,
            "prediction_error": 0.2,
            "spotlight_precision": 0.5
        }

    def _is_stalled(self, agent_id: str, current_progress: float) -> bool:
        """Check if agent progress has stalled."""
        history = self.progress_history.get(agent_id, [])

        if len(history) < self.stall_cycles:
            return False

        # Check if progress has changed in last N cycles
        recent = history[-self.stall_cycles:]
        variance = max(recent) - min(recent)

        # Consider stalled if variance is very small
        return variance < 0.01

    def _update_progress_history(self, agent_id: str, progress: float):
        """Update progress history for an agent."""
        if agent_id not in self.progress_history:
            self.progress_history[agent_id] = []

        self.progress_history[agent_id].append(progress)

        # Keep only last 2x stall_cycles entries
        max_history = self.stall_cycles * 2
        if len(self.progress_history[agent_id]) > max_history:
            self.progress_history[agent_id] = self.progress_history[agent_id][-max_history:]

    def _log_assessment_event(self, assessment: CognitiveAssessment):
        """Log observable event for assessment (FR-020)."""
        logger.info(
            f"Cognitive assessment for {assessment.agent_id}: "
            f"progress={assessment.progress:.2f}, "
            f"confidence={assessment.confidence:.2f}, "
            f"issues={len(assessment.issues)}"
        )

    def clear_history(self, agent_id: Optional[str] = None):
        """Clear progress history for agent(s)."""
        if agent_id:
            self.progress_history.pop(agent_id, None)
        else:
            self.progress_history.clear()
