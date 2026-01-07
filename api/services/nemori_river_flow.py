import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict, Tuple
from uuid import uuid4

from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEpisode,
    AutobiographicalJourney,
    RiverStage,
    RiverStage,
    DevelopmentArchetype
)
from api.models.beautiful_loop import ResonanceSignal, ResonanceMode
from api.agents.consolidated_memory_stores import get_consolidated_memory_store
from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger("dionysus.nemori_river_flow")

class NemoriRiverFlow:
    """
    Service for managing the episodic 'River' flow.
    Implements Boundary Alignment and Predict-Calibrate principles.
    """
    def __init__(self):
        self.store = get_consolidated_memory_store()

    async def check_boundary(self, events: List[DevelopmentEvent], resonance_signal: Optional[ResonanceSignal] = None) -> bool:
        """
        Reflective boundary detection using Predict-Calibrate logic.
        Detects if current events represent a phase shift (Attractor transition).
        Incorporates Richmond/Zacks Event Segmentation Theory (EST).
        """
        logger.debug(f"Checking boundary for {len(events)} events...")
        if not events:
            return False

        # Prepare context with surprisal/uncertainty if available
        context_lines = []
        max_surprisal = 0.0
        for e in events:
            line = f"- {e.event_type.value}: {e.summary}"
            surprisal = 0.0
            if e.active_inference_state:
                surprisal = e.active_inference_state.surprisal
                line += f" [Surprisal: {surprisal:.2f}, Uncertainty: {e.active_inference_state.uncertainty:.2f}]"
            elif e.prediction_error:
                surprisal = e.prediction_error
                line += f" [PredErr: {surprisal:.2f}]"
            
            max_surprisal = max(max_surprisal, surprisal)
            context_lines.append(line)
        
        # Computational Trigger: High surprisal immediately triggers boundary
        if max_surprisal > 0.8: # Threshold could be dynamic
            logger.info(f"Computational EST Trigger: High surprisal detected ({max_surprisal:.2f})")
            return True

        # ULTRATHINK Trigger: Dissonance forces segmentation to protect Worldview
        if resonance_signal:
            if resonance_signal.mode == ResonanceMode.DISSONANT:
                logger.info(f"ULTRATHINK Trigger: Dissonance detected (Score: {resonance_signal.resonance_score:.2f}). Forcing boundary.")
                return True
            if resonance_signal.mode == ResonanceMode.TURBULENT and max_surprisal > 0.6:
                logger.info("ULTRATHINK Trigger: Turbulence + High Surprisal. Forcing boundary.")
                return True

        context = "\n".join(context_lines)
        
        prompt = f"""
        Analyze the following stream of development events (Nemori River SOURCE flow).
        Determine if the latest event represents an 'Episode Boundary' (a transition between attractor basins).
        
        Based on Richmond/Zacks EST (Event Segmentation Theory), a boundary occurs when:
        1. Prediction error (Surprisal) spikes significantly.
        2. The 'smooth dynamics' of the current activity are interrupted.
        3. A shift in thematic 'Strand' occurs (Character, Goal, Location).
        4. A goal has been achieved or abandoned.

        Events:
        {context}

        Respond ONLY with a JSON object:
        {{
            "boundary_detected": true/false,
            "confidence": 0.0-1.0,
            "surprisal_estimate": 0.0-1.0,
            "rationale": "Detailed explanation using EST principles"
        }}
        """
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Nemori Memory Architect, detecting phase shifts in cognitive flow using EST.",
                model=GPT5_NANO
            )
            result = json.loads(response.strip().strip("`").replace("json", "").strip())
            detected = result.get("boundary_detected", False)
            
            # Record the surprisal estimate back into the event if detected
            # (In a real flow, this would be computed by the agent during prediction)
            
            logger.info(f"Boundary check: {detected} (Confidence: {result.get('confidence')}) - {result.get('rationale')}")
            return detected
        except Exception as e:
            logger.error(f"Error in check_boundary: {e}")
            return False

    async def construct_episode(self, events: List[DevelopmentEvent], journey_id: str, parent_episode_id: Optional[str] = None) -> Optional[DevelopmentEpisode]:
        """
        Consolidates TRIBUTARY events into a coherent Episode (Stable Attractor).
        Supports Richmond/Zacks 'Strands' and Hierarchical structure.
        """
        logger.info(f"Constructing episode from {len(events)} events for journey {journey_id}")
        if not events:
            return None
            
        context = "\n".join([f"- {e.summary} (Impact: {e.impact})" for e in events])
        
        prompt = f"""
        Synthesize these development events into a coherent 'Development Episode'.
        Identify the 'Stabilizing Attractor' (the core theme/goal) and the thematic 'Strand'.
        
        Events:
        {context}

        Respond ONLY with a JSON object:
        {{
            "title": "Short descriptive title",
            "summary": "Brief summary",
            "narrative": "Coherent story of what happened",
            "archetype": "one of: creator, hero, sage, explorer, etc.",
            "stabilizing_attractor": "The core theme",
            "strand_id": "One-word thematic strand (e.g. 'coding', 'research', 'ops')"
        }}
        """
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Narrative Architect, distilling experience into hierarchical attractor basins.",
                model=GPT5_NANO
            )
            data = json.loads(response.strip().strip("`").replace("json", "").strip())
            
            # Aggregate Mosaic Metrics
            c_levels = [e.consciousness_level for e in events]
            peak_c = max(c_levels) if c_levels else 0.5
            avg_c = sum(c_levels) / len(c_levels) if c_levels else 0.5
            
            episode = DevelopmentEpisode(
                episode_id=str(uuid4()),
                journey_id=journey_id,
                title=data.get("title", "Untitled Episode"),
                summary=data.get("summary", ""),
                narrative=data.get("narrative", ""),
                start_time=events[0].timestamp,
                end_time=events[-1].timestamp,
                events=[e.event_id for e in events],
                dominant_archetype=DevelopmentArchetype(data.get("archetype", "sage")) if data.get("archetype") else None,
                river_stage=RiverStage.MAIN_RIVER,
                stabilizing_attractor=data.get("stabilizing_attractor", None),
                parent_episode_id=parent_episode_id,
                strand_id=data.get("strand_id", "general"),
                peak_consciousness_level=peak_c,
                avg_consciousness_level=avg_c
            )
            
            # Hippocampal Binding: Sharpen the narrative before storing
            episode.narrative = await self._sharpen_episode_narrative(episode, events)
            
            await self.store.create_episode(episode)
            return episode
        except Exception as e:
            logger.error(f"Error in episode construction: {e}")
            # Fallback
            return DevelopmentEpisode(
                episode_id=str(uuid4()),
                journey_id=journey_id,
                title="Consolidated Episode (Fallback)",
                summary="An error occurred during episode construction.",
                narrative="No detailed narrative due to error.",
                start_time=events[0].timestamp if events else datetime.now(timezone.utc),
                end_time=events[-1].timestamp if events else datetime.now(timezone.utc),
                events=[e.event_id for e in events],
                dominant_archetype=DevelopmentArchetype.SAGE,
                river_stage=RiverStage.MAIN_RIVER
            )

    async def predict_and_calibrate(self, episode: DevelopmentEpisode, original_events: List[DevelopmentEvent]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Implements the Predict-Calibrate Principle (Nemori 3.2 for DELTA).
        Returns distilled facts AND 'Symbolic Residue' for incremental continuity.
        """
        # 1. Prediction Stage
        prediction_prompt = (
            f"Based on the episode title '{episode.title}' and summary '{episode.summary}', "
            "predict what semantic facts or architectural lessons should be confirmed by this experience. "
            "Respond ONLY with a bulleted list of predictions."
        )
        
        # 2. Calibration Stage
        calibration_prompt = (
            "You are a knowledge distiller. Identify the 'Prediction Gap' and 'Symbolic Residue'.\n"
            "Prediction Gap: What new standalone semantic facts were learned?\n"
            "Symbolic Residue: What specific situational features (actors, goals, location) remain ACTIVE and should carry over to the next episode?\n"
            "Respond ONLY with a JSON object:\n"
            "{\n"
            "  \"new_facts\": [\"fact1\", \"fact2\"],\n"
            "  \"symbolic_residue\": {\"active_goals\": [], \"active_entities\": [], \"stable_context\": \"\"}\n"
            "}"
        )
        
        raw_logs = "\n".join([f"{e.summary}: {e.rationale}" for e in original_events])
        
        try:
            # Predict
            predictions = await chat_completion([{"role": "user", "content": "Generate predictions."}], prediction_prompt, model=GPT5_NANO)
            
            # Calibrate
            messages = [{"role": "user", "content": f"Predictions:\n{predictions}\n\nActual Logs:\n{raw_logs}"}]
            response = await chat_completion(messages, calibration_prompt, model=GPT5_NANO)
            data = json.loads(response.strip().strip("`").replace("json", "").strip())
            new_facts = data.get("new_facts", [])
            residue = data.get("symbolic_residue", {})
            
            # Record semantic distillation event
            distill_id = f"distill_{uuid4().hex[:6]}"
            distill_event = DevelopmentEvent(
                event_id=distill_id,
                timestamp=datetime.now(timezone.utc),
                event_type="semantic_distillation",
                summary=f"Distilled {len(new_facts)} facts from episode {episode.title}",
                rationale=f"Predict-Calibrate on {episode.episode_id}",
                impact="Semantic knowledge enrichment",
                metadata={"new_facts": new_facts, "residue": residue},
                river_stage=RiverStage.DELTA,
                parent_episode_id=episode.episode_id
            )
            await self.store.store_event(distill_event)
            
            return new_facts, residue
        except Exception as e:
            logger.error(f"Error in predict-calibrate cycle: {e}")
            return [], {}

    async def _sharpen_episode_narrative(self, episode: DevelopmentEpisode, events: List[DevelopmentEvent]) -> str:
        """
        Hippocampal Binding (Now Print) function.
        Sharps the narrative by reinforcing key situational features and goals.
        """
        logger.debug(f"Sharpening narrative for episode {episode.title}")
        
        prompt = f"""
        Refine and 'Sharpen' the following episode narrative. 
        Focus on the 'Hippocampal Binding' of situational features:
        - Key Entities (Objects, Actors)
        - Goal Trajectories (What was achieved)
        - Symbolic Residue (What remains for the next episode)
        
        Original Narrative: {episode.narrative}
        Events: {", ".join([e.summary for e in events])}
        
        Produce a more vivid, high-fidelity narrative that captures the essence of this cognitive scene.
        """
        try:
            sharpened = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Hippocampal Architect, sharpening situational bindings into long-term memory.",
                model=GPT5_NANO
            )
            return sharpened.strip()
        except Exception as e:
            logger.error(f"Error sharpening narrative: {e}")
            return episode.narrative

_instance: Optional[NemoriRiverFlow] = None

def get_nemori_river_flow() -> NemoriRiverFlow:
    global _instance
    if _instance is None:
        _instance = NemoriRiverFlow()
    return _instance
