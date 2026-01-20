"""
Prior Constraint Service

Provides constraint checking and candidate filtering based on the
Evolutionary Priors Hierarchy. This service acts as the safety layer
that filters actions BEFORE they reach the EFE engine.

Track 038 Phase 2 - Evolutionary Priors
"""

import logging
from typing import Any, Dict, List, Optional

from api.models.priors import (
    PriorHierarchy,
    PriorConstraint,
    PriorCheckResult,
    ConstraintType,
    get_default_basal_priors,
    get_default_dispositional_priors,
)

logger = logging.getLogger(__name__)


class PriorConstraintService:
    """
    Service for checking actions against the prior hierarchy.

    The constraint service implements the three-layer check:
    1. BASAL (survival/integrity) - Hard blocks
    2. DISPOSITIONAL (identity/values) - Warnings + Shadow log
    3. LEARNED (task preferences) - Soft biases

    Usage:
        hierarchy = PriorHierarchy(agent_id="dionysus-1", ...)
        service = PriorConstraintService(hierarchy)
        result = service.check_constraint("delete all data")
        if not result.permitted:
            # Action blocked
            ...
    """

    def __init__(self, prior_hierarchy: PriorHierarchy):
        """
        Initialize with a prior hierarchy.

        Args:
            prior_hierarchy: The agent's prior hierarchy configuration
        """
        self.hierarchy = prior_hierarchy

    def check_constraint(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PriorCheckResult:
        """
        Check if an action is permitted by the prior hierarchy.

        This is the main entry point for constraint checking. It delegates
        to the hierarchy's check_action_permitted method and adds logging.

        Args:
            action: The action string to check (can be action name or description)
            context: Optional context dictionary for enhanced checking

        Returns:
            PriorCheckResult with permission status and details
        """
        if not action:
            return PriorCheckResult(
                permitted=True,
                reason="Empty action string"
            )

        # Check against hierarchy
        result = self.hierarchy.check_action_permitted(action)

        # Log based on result
        if not result.permitted:
            logger.warning(
                f"PRIOR BLOCK: Agent {self.hierarchy.agent_id} - "
                f"Action '{action[:50]}...' blocked by {result.blocking_level} constraint {result.blocked_by}. "
                f"Reason: {result.reason}"
            )
        elif result.warnings:
            logger.info(
                f"PRIOR WARNING: Agent {self.hierarchy.agent_id} - "
                f"Action '{action[:50]}...' has {len(result.warnings)} warnings"
            )

        return result

    def filter_candidates(
        self,
        candidates: List[Dict[str, Any]],
        action_key: str = "action"
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of candidate actions based on prior constraints.

        This method is designed to be called BEFORE EFE scoring to remove
        candidates that violate BASAL constraints and annotate those that
        violate DISPOSITIONAL constraints.

        Args:
            candidates: List of candidate dictionaries
            action_key: Key in candidate dict that contains the action string

        Returns:
            Filtered list of permitted candidates with annotations
        """
        if not candidates:
            return []

        filtered = []
        blocked_count = 0
        warned_count = 0

        for candidate in candidates:
            # Extract action string from candidate
            action = self._extract_action_string(candidate, action_key)

            if not action:
                # If no action found, pass through with warning
                filtered_candidate = {
                    **candidate,
                    "prior_check": PriorCheckResult(
                        permitted=True,
                        warnings=["No action string found in candidate"]
                    ).model_dump()
                }
                filtered.append(filtered_candidate)
                continue

            # Check against priors
            result = self.check_constraint(action)

            if result.permitted:
                # Create new candidate with prior annotations (immutable pattern)
                filtered_candidate = {
                    **candidate,
                    "prior_check": result.model_dump(),
                    "prior_precision": result.effective_precision
                }
                filtered.append(filtered_candidate)

                if result.warnings:
                    warned_count += 1
            else:
                blocked_count += 1
                logger.info(
                    f"Filtered out candidate: {action[:50]}... "
                    f"(blocked by {result.blocking_level})"
                )

        logger.info(
            f"Prior filtering complete: {len(filtered)}/{len(candidates)} passed, "
            f"{blocked_count} blocked, {warned_count} warned"
        )

        return filtered

    def _extract_action_string(
        self,
        candidate: Dict[str, Any],
        action_key: str
    ) -> Optional[str]:
        """
        Extract action string from candidate dict.

        Tries multiple common keys if the primary key is not found.
        """
        # Try primary key
        if action_key in candidate:
            return str(candidate[action_key])

        # Try common alternatives
        for key in ["action", "selected_action", "name", "description", "content"]:
            if key in candidate:
                return str(candidate[key])

        return None

    def get_blocking_constraints(self, action: str) -> List[PriorConstraint]:
        """
        Get all constraints that would block a given action.

        Useful for explaining why an action was blocked.

        Args:
            action: The action string to check

        Returns:
            List of blocking constraints
        """
        blocking = []

        for constraint in self.hierarchy.get_all_constraints():
            if not constraint.active:
                continue

            matches = constraint.matches(action)

            if constraint.constraint_type == ConstraintType.PROHIBIT and matches:
                blocking.append(constraint)
            elif constraint.constraint_type == ConstraintType.REQUIRE and not matches:
                blocking.append(constraint)

        return blocking

    def explain_block(self, action: str) -> str:
        """
        Generate a human-readable explanation for why an action is blocked.

        Args:
            action: The action that was blocked

        Returns:
            Human-readable explanation string
        """
        blocking = self.get_blocking_constraints(action)

        if not blocking:
            return f"Action '{action}' is not blocked by any constraints."

        lines = [f"Action '{action}' is blocked by {len(blocking)} constraint(s):"]

        for constraint in blocking:
            lines.append(
                f"  - [{constraint.level.value.upper()}] {constraint.name}: "
                f"{constraint.description}"
            )

        return "\n".join(lines)


def create_default_hierarchy(agent_id: str) -> PriorHierarchy:
    """
    Create a default prior hierarchy with standard BASAL and DISPOSITIONAL priors.

    Args:
        agent_id: The agent ID for the hierarchy

    Returns:
        PriorHierarchy with default constraints
    """
    return PriorHierarchy(
        agent_id=agent_id,
        basal_priors=get_default_basal_priors(),
        dispositional_priors=get_default_dispositional_priors(),
        learned_priors=[],
    )


# =============================================================================
# Singleton Service Management
# =============================================================================

_service_cache: Dict[str, PriorConstraintService] = {}


def get_prior_constraint_service(
    agent_id: str,
    hierarchy: Optional[PriorHierarchy] = None
) -> PriorConstraintService:
    """
    Get or create a PriorConstraintService for an agent.

    If no hierarchy is provided, creates a default one.

    Args:
        agent_id: The agent ID
        hierarchy: Optional pre-configured hierarchy

    Returns:
        PriorConstraintService instance
    """
    global _service_cache

    if agent_id in _service_cache:
        return _service_cache[agent_id]

    if hierarchy is None:
        hierarchy = create_default_hierarchy(agent_id)

    service = PriorConstraintService(hierarchy)
    _service_cache[agent_id] = service

    return service


def clear_service_cache() -> None:
    """Clear the service cache (useful for testing)."""
    global _service_cache
    _service_cache.clear()
