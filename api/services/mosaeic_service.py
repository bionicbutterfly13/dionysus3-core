"""
MOSAEIC Protocol Service
Feature: 024-mosaeic-protocol

Mental Observation of Senses, Actions, Emotions, Impulses, Cognitions.
"""

import json
import logging
from typing import Optional

from api.models.mosaeic import MOSAEICCapture
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)


class MOSAEICService:
    def __init__(self):
        self.model = GPT5_NANO  # Use cheap model for extraction

    async def extract_capture(self, text: str, source_id: str = "user") -> MOSAEICCapture:
        """Extract five-window MOSAEIC state from raw text."""
        
        prompt = f"""
        Analyze the following narrative and extract the deep experiential state using the MOSAEIC protocol.
        
        MOSAEIC Windows:
        1. SENSES: Physical sensations (internal/external).
        2. ACTIONS: Physical movements or verbal behaviors.
        3. EMOTIONS: Visceral feeling states.
        4. IMPULSES: The 'urge' to do something before the action occurs.
        5. COGNITIONS: Thoughts, beliefs, or inner dialogue.
        
        NARRATIVE:
        "{text}"
        
        Respond ONLY with a JSON object:
        {{
            "senses": {{"content": "...", "intensity": 0.0, "tags": []}},
            "actions": {{"content": "...", "intensity": 0.0, "tags": []}},
            "emotions": {{"content": "...", "intensity": 0.0, "tags": []}},
            "impulses": {{"content": "...", "intensity": 0.0, "tags": []}},
            "cognitions": {{"content": "...", "intensity": 0.0, "tags": []}},
            "summary": "Synthesized meaning"
        }}
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert psychotherapist specializing in the MOSAEIC protocol.",
            model=self.model,
            max_tokens=1024
        )
        
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
            data = json.loads(cleaned)
            data["source_id"] = source_id
            return MOSAEICCapture(**data)
        except Exception as e:
            logger.error(f"failed_mosaeic_extraction: {e}")
            # Return empty/minimal capture on failure
            empty_win = {"content": "not detected", "intensity": 0.0, "tags": []}
            return MOSAEICCapture(
                senses=empty_win, actions=empty_win, emotions=empty_win,
                impulses=empty_win, cognitions=empty_win, summary="Extraction failed"
            )

    async def persist_capture(self, capture: MOSAEICCapture):
        """Save MOSAEIC capture to Graphiti/Neo4j."""
        graphiti = await get_graphiti_service()
        
        # 1. Ingest the summary as an episode
        episode_id = await graphiti.ingest_message(
            content=f"MOSAEIC Experience: {capture.summary}",
            source_description=f"mosaeic_capture:{capture.source_id}",
            valid_at=capture.timestamp
        )
        
        # 2. Ingest windows as factual edges linked to this context
        windows = {
            "Senses": capture.senses,
            "Actions": capture.actions,
            "Emotions": capture.emotions,
            "Impulses": capture.impulses,
            "Cognitions": capture.cognitions
        }
        
        for name, win in windows.items():
            if win.intensity > 0.1:
                fact = f"User experienced {name} during this episode: {win.content} (Intensity: {win.intensity:.1f})"
                await graphiti.ingest_message(
                    content=fact,
                    source_description=f"mosaeic_window:{name}",
                    valid_at=capture.timestamp
                )
        
        return episode_id


_mosaeic_service: Optional[MOSAEICService] = None


def get_mosaeic_service() -> MOSAEICService:
    global _mosaeic_service
    if _mosaeic_service is None:
        _mosaeic_service = MOSAEICService()
    return _mosaeic_service
