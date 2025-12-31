"""
Unified Consciousness Integration Pipeline (Feature 045)

The central orchestrator for integrating reasoning results across semantic, 
episodic, and meta-cognitive memory systems.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
from api.models.meta_cognition import CognitiveEpisode
from api.services.autobiographical_service import get_autobiographical_service
from api.services.graphiti_service import get_graphiti_service
from api.services.meta_cognitive_service import get_meta_learner
from api.services.multi_tier_service import get_multi_tier_service

logger = logging.getLogger("dionysus.consciousness_pipeline")

class ConsciousnessIntegrationPipeline:
    """
    Ensures that every 'Cognitive Event' (reasoning session) updates the 
    Knowledge Graph, self-story, and strategic learning systems in a single pass.
    """

    async def process_cognitive_event(
        self,
        problem: str,
        reasoning_trace: str,
        outcome: Optional[str] = None,
        active_inference_state: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Main entry point for unified integration.
        
        Triggers:
        1. Autobiographical recording (Self-story)
        2. Graphiti ingestion (Entity extraction)
        3. Meta-Cognitive recording (Strategy learning)
        4. Tiered Memory storage (HOT cache)
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        context = context or {}
        
        logger.info(f"Initiating Unified Consciousness Integration for event {event_id}")
        
        # --- 1. TIERED MEMORY BRANCH (HOT Cache) ---
        try:
            tiered_svc = get_multi_tier_service()
            await tiered_svc.store_memory(
                content=reasoning_trace,
                importance=context.get("importance", 0.5),
                id=event_id,
                project_id=context.get("project_id", "default"),
                metadata={"problem": problem, "outcome": outcome}
            )
            logger.info(f"Event {event_id}: Stored in HOT tiered memory.")
        except Exception as e:
            logger.error(f"Event {event_id}: Tiered memory storage failed: {e}")

        # --- 2. AUTOBIOGRAPHICAL BRANCH ---
        try:
            auto_svc = get_autobiographical_service()
            dev_event = DevelopmentEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=DevelopmentEventType.SYSTEM_REFLECTION,
                summary=f"Cognitive Event: {problem[:100]}...",
                rationale=f"System engaged in reasoning about: {problem}",
                impact="Updating internal model and strategic alignment."
            )
            await auto_svc.record_event(dev_event)
            logger.info(f"Event {event_id}: Autobiographical update successful.")
        except Exception as e:
            logger.error(f"Event {event_id}: Autobiographical update failed: {e}")

        # --- 2. GRAPHITI BRANCH (Semantic Extraction) ---
        try:
            # We ingest the reasoning trace into Graphiti to extract new entities/facts
            graphiti = await get_graphiti_service()
            content_to_ingest = f"Problem: {problem}\nReasoning: {reasoning_trace}\nOutcome: {outcome or 'Unknown'}"
            await graphiti.ingest_message(
                content=content_to_ingest,
                source_description="cognitive_integration_pipeline",
                group_id=context.get("project_id", "dionysus_consciousness")
            )
            logger.info(f"Event {event_id}: Graphiti ingestion successful.")
        except Exception as e:
            logger.error(f"Event {event_id}: Graphiti ingestion failed: {e}")

        # --- 3. META-COGNITIVE BRANCH (Strategy Learning) ---
        try:
            learner = get_meta_learner()
            
            # Reconstruct tools used if possible from context or trace
            tools_used = context.get("tools_used", [])
            
            episode = CognitiveEpisode(
                id=event_id,
                timestamp=timestamp,
                task_query=problem,
                task_context={k: v for k, v in context.items() if isinstance(v, (str, int, float, bool))},
                tools_used=tools_used,
                reasoning_trace=reasoning_trace,
                success=context.get("confidence", 0.0) > 0.6,
                outcome_summary=outcome or reasoning_trace[:200],
                surprise_score=active_inference_state.get("surprise", 0.0) if active_inference_state else 0.0,
                lessons_learned=f"Cognitive event integrated with ID {event_id}."
            )
            await learner.record_episode(episode)
            logger.info(f"Event {event_id}: Meta-learning update successful.")
        except Exception as e:
            logger.error(f"Event {event_id}: Meta-learning update failed: {e}")

        logger.info(f"Unified Consciousness Integration completed for event {event_id}.")
        return event_id

# Singleton
_pipeline_instance: Optional[ConsciousnessIntegrationPipeline] = None

def get_consciousness_pipeline() -> ConsciousnessIntegrationPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ConsciousnessIntegrationPipeline()
    return _pipeline_instance