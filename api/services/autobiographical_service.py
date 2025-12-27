"""
Autobiographical Memory Service
Feature: 028-autobiographical-memory

Ensures the system remembers its own evolution and rationale.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from api.models.autobiographical import DevelopmentEvent, DevelopmentEventType
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger(__name__)


class AutobiographicalService:
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def record_event(self, event: DevelopmentEvent) -> str:
        """Persist a development event to Neo4j."""
        cypher = """
        MERGE (e:DevelopmentEvent {id: $id})
        SET e.timestamp = $timestamp,
            e.type = $type,
            e.summary = $summary,
            e.rationale = $rationale,
            e.impact = $impact,
            e.lessons_learned = $lessons,
            e.metadata = $metadata
        RETURN e.id
        """
        params = {
            "id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "type": event.event_type.value,
            "summary": event.summary,
            "rationale": event.rationale,
            "impact": event.impact,
            "lessons": event.lessons_learned,
            "metadata": event.metadata
        }
        
        await self._driver.execute_query(cypher, params)
        logger.info(f"autobiographical_event_recorded: {event.event_id}")
        return event.event_id

    async def get_system_story(self, limit: int = 20) -> List[DevelopmentEvent]:
        """Retrieve the system's chronological story."""
        cypher = """
        MATCH (e:DevelopmentEvent)
        RETURN e
        ORDER BY e.timestamp ASC
        LIMIT $limit
        """
        rows = await self._driver.execute_query(cypher, {"limit": limit})
        events = []
        for r in rows:
            data = r["e"]
            # Adapt from Neo4j props to model
            events.append(DevelopmentEvent(
                event_id=data["id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                event_type=DevelopmentEventType(data["type"]),
                summary=data["summary"],
                rationale=data["rationale"],
                impact=data["impact"],
                lessons_learned=data.get("lessons_learned", []),
                metadata=data.get("metadata", {})
            ))
        return events


_autobiographical_service: Optional[AutobiographicalService] = None


def get_autobiographical_service() -> AutobiographicalService:
    global _autobiographical_service
    if _autobiographical_service is None:
        _autobiographical_service = AutobiographicalService()
    return _autobiographical_service
