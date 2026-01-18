import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import uuid4

from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEpisode,
    AutobiographicalJourney,
    RiverStage
)
from api.models.beautiful_loop import ResonanceSignal
from api.agents.consolidated_memory_stores import get_consolidated_memory_store
from api.services.nemori_river_flow import get_nemori_river_flow

logger = logging.getLogger("dionysus.memory.core")

class ConsciousnessMemoryCore:
    """
    The orchestrator for the high-level memory lifecycle.
    Bridges the 'River' from SOURCE events to DELTA wisdom.
    """
    def __init__(self, journey_id: str = "main_evolution"):
        self.store = get_consolidated_memory_store()
        self.river = get_nemori_river_flow()
        self.journey_id = journey_id
        self._event_buffer: List[DevelopmentEvent] = []
        self._buffer_lock = asyncio.Lock()
        self._max_buffer_size = 25
        self._last_symbolic_residue: Dict[str, Any] = {}
        
    async def record_interaction(self, event: DevelopmentEvent, resonance_signal: Optional[ResonanceSignal] = None):
        """Main entry point for agents to record an interaction."""
        # 1. Store raw event (SOURCE)
        await self.store.store_event(event)
        
        async with self._buffer_lock:
            # 2. Add to local buffer for boundary detection
            self._event_buffer.append(event)
            
            # 3. Check for boundary (TRIBUTARY)
            should_segment = await self.river.check_boundary(self._event_buffer, resonance_signal=resonance_signal)
            
            if should_segment or len(self._event_buffer) >= self._max_buffer_size:
                logger.info(f"Boundary detected or buffer full. Segmenting {len(self._event_buffer)} events.")
                await self._segment_episode()

    async def _segment_episode(self):
        """Segments the current buffer into a narrative episode and triggers distillation."""
        events_to_process = list(self._event_buffer)
        self._event_buffer = [] # Clear buffer immediately
        
        # 1. Identify or create journey
        journey = AutobiographicalJourney(
            journey_id=self.journey_id,
            title="Dionysus Autonomous Evolution",
            description="The continuous narrative of system development and cognitive emergence."
        )
        # Update journey (MERGE logic in store)
        await self.store.update_journey(journey)
        
        # 2. Construct narrative episode (MAIN_RIVER)
        episode = await self.river.construct_episode(events_to_process, self.journey_id)
        
        if episode:
            # 3. Trigger Predict-Calibrate distillation (DELTA)
            # predict_and_calibrate returns (new_facts, symbolic_residue) tuple
            new_facts, symbolic_residue = await self.river.predict_and_calibrate(episode, events_to_process)
            self._last_symbolic_residue = dict(symbolic_residue or {})
            logger.info(f"Episode '{episode.title}' created. Distilled {len(new_facts)} semantic facts, residue keys: {list(symbolic_residue.keys())}")
            
            # 4. Link EPISODE to JOURNEY
            journey.episodes.append(episode.episode_id)
            journey.total_episodes += 1
            journey.updated_at = datetime.utcnow()
            await self.store.update_journey(journey)

    async def get_current_narrative_context(self) -> str:
        """Retrieves a summary of the current journey for agent orientation."""
        # This could summarize the last few episodes
        return "System is currently in the 'Autonomous Evolution' journey, focused on Nemori integration."

    @property
    def last_symbolic_residue(self) -> Dict[str, Any]:
        """Expose the most recent symbolic residue from distillation."""
        return dict(self._last_symbolic_residue)

_instance: Optional[ConsciousnessMemoryCore] = None

def get_consciousness_memory_core() -> ConsciousnessMemoryCore:
    global _instance
    if _instance is None:
        _instance = ConsciousnessMemoryCore()
    return _instance
