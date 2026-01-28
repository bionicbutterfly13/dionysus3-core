"""
Shadow Log Services

Track 002: Jungian Cognitive Archetypes - Archetype Shadow Log
Track 048: Cognitive Dissonance - Dissonance Shadow Log

The Shadow Log tracks:
1. Suppressed archetypes from EFE competition (ArchetypeShadowLog)
2. Cognitive dissonance events (ShadowLogService)
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import deque
from pydantic import BaseModel, Field

from api.models.biological_agency import DissonanceEvent
from api.services.graphiti_service import GraphitiService
from api.models.priors import (
    RESONANCE_THRESHOLD,
    RESONANCE_ACTIVATION_EFE,
    SHADOW_WINDOW_SIZE,
)

logger = logging.getLogger(__name__)

class ShadowLogService:
    """
    The Shadow Log: Persists Cognitive Dissonance (Epistemic Debt).
    
    Prevents Model Collapse (Canalization) by tracking the gap between
    Reality (Observation) and Identity (Prediction).
    """

    def __init__(self):
        self._graphiti: Optional[GraphitiService] = None

    async def _get_graph_service(self) -> GraphitiService:
        if self._graphiti is None:
            self._graphiti = await GraphitiService.get_instance()
        return self._graphiti

    async def log_dissonance(
        self,
        agent_id: str,
        surprisal: float,
        ignored_observation: str,
        maintained_belief: str,
        context: str
    ) -> None:
        """
        Log a dissonance event to the Shadow Graph.
        
        Schema:
        (:Agent {id: ...})-[:HAS_SHADOW]->(:ShadowLog)
        (:ShadowLog)-[:CONTAINS]->(:DissonanceEvent { ... })
        """
        
        event = DissonanceEvent(
            surprisal=surprisal,
            ignored_observation=ignored_observation,
            maintained_belief=maintained_belief,
            context=context
        )
        
        query = """
        MATCH (a:Agent {id: $agent_id})
        MERGE (a)-[:HAS_SHADOW]->(sl:ShadowLog)
        CREATE (e:DissonanceEvent {
            id: $event_id,
            timestamp: $timestamp,
            surprisal: $surprisal,
            ignored_observation: $ignored_observation,
            maintained_belief: $maintained_belief,
            context: $context,
            resolved: false
        })
        CREATE (sl)-[:CONTAINS]->(e)
        RETURN e
        """
        
        params = {
            "agent_id": agent_id,
            "event_id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "surprisal": event.surprisal,
            "ignored_observation": event.ignored_observation,
            "maintained_belief": event.maintained_belief,
            "context": event.context
        }
        
        try:
            graph = await self._get_graph_service()
            await graph.execute_cypher(query, params)
            logger.info(
                f"Shadow Logged: Agent {agent_id} ignored reality (VFE={surprisal:.2f}) "
                f"in context '{context}'"
            )
        except Exception as e:
            logger.error(f"Failed to log dissonance for {agent_id}: {e}")


# =============================================================================
# Track 002: Archetype Shadow Log
# =============================================================================

class ShadowEntry(BaseModel):
    """A single entry in the Archetype Shadow Log."""
    archetype: str = Field(description="Suppressed archetype name")
    efe_score: float = Field(description="EFE score at time of suppression")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: str = Field(default="", description="Context at time of suppression")
    basin: Optional[str] = Field(default=None, description="Active basin at suppression")
    dominant_archetype: str = Field(default="", description="Archetype that won")


class ArchetypeShadowLog:
    """
    In-memory log of suppressed archetypes.

    Track 002: Jungian Cognitive Archetypes

    The Shadow Log enables:
    1. Tracking of archetypes suppressed during competition
    2. Time-windowed retrieval for resonance candidates
    3. Resonance protocol activation under high allostatic load

    Integration (IO Map):
    - Inlets: Suppressed archetypes from EFEEngine.select_dominant_archetype()
    - Outlets: Resonance candidates to ConsciousnessManager
    """

    def __init__(self, max_size: int = 100, window_size: int = SHADOW_WINDOW_SIZE):
        """
        Initialize Shadow Log.

        Args:
            max_size: Maximum entries to keep (oldest evicted first)
            window_size: Number of recent entries to consider for resonance
        """
        self._entries: deque[ShadowEntry] = deque(maxlen=max_size)
        self._window_size = window_size
        self._resonance_active = False

    def log_suppression(
        self,
        archetype: str,
        efe_score: float,
        context: str = "",
        basin: Optional[str] = None,
        dominant_archetype: str = ""
    ) -> ShadowEntry:
        """
        Log a suppressed archetype.

        Called after EFE competition when an archetype loses.

        Args:
            archetype: Name of suppressed archetype
            efe_score: EFE score at suppression
            context: Context/content that triggered competition
            basin: Active attractor basin
            dominant_archetype: Archetype that won the competition

        Returns:
            Created ShadowEntry
        """
        entry = ShadowEntry(
            archetype=archetype,
            efe_score=efe_score,
            context=context[:200] if context else "",  # Truncate for memory
            basin=basin,
            dominant_archetype=dominant_archetype,
        )
        self._entries.append(entry)

        logger.debug(
            f"Archetype shadow: {archetype} suppressed by {dominant_archetype} "
            f"(EFE={efe_score:.4f}, basin={basin})"
        )

        return entry

    def log_suppressions_batch(
        self,
        suppressed_archetypes: List[Any],
        efe_scores: Dict[str, float],
        context: str = "",
        basin: Optional[str] = None,
        dominant_archetype: str = ""
    ) -> List[ShadowEntry]:
        """
        Log multiple suppressed archetypes from a competition.

        Args:
            suppressed_archetypes: List of ArchetypePrior instances
            efe_scores: Dict of archetype_name -> efe_score
            context: Competition context
            basin: Active attractor basin
            dominant_archetype: Winner name

        Returns:
            List of created ShadowEntry instances
        """
        entries = []
        for archetype in suppressed_archetypes:
            efe = efe_scores.get(archetype.archetype, 1.0)
            entry = self.log_suppression(
                archetype=archetype.archetype,
                efe_score=efe,
                context=context,
                basin=basin,
                dominant_archetype=dominant_archetype,
            )
            entries.append(entry)
        return entries

    def get_recent(self, window: Optional[int] = None) -> List[ShadowEntry]:
        """
        Get recent shadow entries within window.

        Args:
            window: Number of recent entries (default: SHADOW_WINDOW_SIZE)

        Returns:
            List of recent ShadowEntry instances
        """
        window = window or self._window_size
        entries = list(self._entries)
        return entries[-window:] if len(entries) > window else entries

    def get_recent_by_time(self, minutes: int = 5) -> List[ShadowEntry]:
        """
        Get shadow entries from the last N minutes.

        Args:
            minutes: Time window in minutes

        Returns:
            List of ShadowEntry instances within time window
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [e for e in self._entries if e.timestamp >= cutoff]

    def get_archetype_frequency(self, window: Optional[int] = None) -> Dict[str, int]:
        """
        Count how often each archetype has been suppressed recently.

        Args:
            window: Number of recent entries to consider

        Returns:
            Dict of archetype_name -> suppression count
        """
        recent = self.get_recent(window)
        counts: Dict[str, int] = {}
        for entry in recent:
            counts[entry.archetype] = counts.get(entry.archetype, 0) + 1
        return counts

    def check_resonance(
        self,
        allostatic_load: float,
        threshold: float = RESONANCE_THRESHOLD
    ) -> Optional[ShadowEntry]:
        """
        Check if resonance should be triggered.

        Track 002: Resonance Protocol

        When allostatic load exceeds threshold, find the best shadow candidate
        for reactivation (lowest EFE among recent suppressions).

        Args:
            allostatic_load: Current allostatic load (0-1)
            threshold: Activation threshold (default: RESONANCE_THRESHOLD)

        Returns:
            Best ShadowEntry for resonance, or None
        """
        if allostatic_load < threshold:
            return None

        recent = self.get_recent()
        if not recent:
            return None

        # Find candidate with lowest EFE (best suppressed potential)
        candidates = [e for e in recent if e.efe_score < RESONANCE_ACTIVATION_EFE]

        if not candidates:
            # No candidates below activation threshold
            return None

        # Select best candidate (lowest EFE)
        best = min(candidates, key=lambda e: e.efe_score)

        logger.info(
            f"Resonance triggered: load={allostatic_load:.3f}, "
            f"candidate={best.archetype} (EFE={best.efe_score:.4f})"
        )

        self._resonance_active = True
        return best

    def get_resonance_candidates(
        self,
        max_candidates: int = 3
    ) -> List[ShadowEntry]:
        """
        Get top resonance candidates sorted by EFE.

        Args:
            max_candidates: Maximum number to return

        Returns:
            List of ShadowEntry sorted by EFE (ascending)
        """
        recent = self.get_recent()
        candidates = [e for e in recent if e.efe_score < RESONANCE_ACTIVATION_EFE]
        sorted_candidates = sorted(candidates, key=lambda e: e.efe_score)
        return sorted_candidates[:max_candidates]

    def clear_old(self, max_age_minutes: int = 30) -> int:
        """
        Clear entries older than max_age.

        Args:
            max_age_minutes: Maximum age in minutes

        Returns:
            Number of entries removed
        """
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        old_count = len(self._entries)

        # Filter to keep only recent entries
        recent = [e for e in self._entries if e.timestamp >= cutoff]
        self._entries = deque(recent, maxlen=self._entries.maxlen)

        removed = old_count - len(self._entries)
        if removed > 0:
            logger.debug(f"Shadow log cleanup: removed {removed} old entries")

        return removed

    def clear_all(self) -> int:
        """Clear all entries. Returns count cleared."""
        count = len(self._entries)
        self._entries.clear()
        self._resonance_active = False
        return count

    @property
    def size(self) -> int:
        """Current number of entries."""
        return len(self._entries)

    @property
    def is_resonance_active(self) -> bool:
        """Whether resonance mode is currently active."""
        return self._resonance_active

    def deactivate_resonance(self) -> None:
        """Deactivate resonance mode."""
        self._resonance_active = False
        logger.debug("Resonance mode deactivated")


# Singleton instance for archetype shadow log
_archetype_shadow_log: Optional[ArchetypeShadowLog] = None


def get_archetype_shadow_log() -> ArchetypeShadowLog:
    """Get the global ArchetypeShadowLog instance."""
    global _archetype_shadow_log
    if _archetype_shadow_log is None:
        _archetype_shadow_log = ArchetypeShadowLog()
    return _archetype_shadow_log


def reset_archetype_shadow_log() -> None:
    """Reset the global ArchetypeShadowLog (for testing)."""
    global _archetype_shadow_log
    _archetype_shadow_log = None
