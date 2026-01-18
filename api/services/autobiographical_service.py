"""
Autobiographical Memory Service
Feature: 028-autobiographical-memory

Ensures the system remembers its own evolution and rationale.
Refined for D2 Migration (Neo4j Only).
"""

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEventType,
    DevelopmentArchetype,
    ActiveInferenceState,
    ConversationMoment,
    ConsciousnessReport,
    ExtendedMindState,
)
from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.services.consciousness.active_inference_analyzer import ActiveInferenceAnalyzer
from api.services.conversation_moment_service import (
    ConversationMomentService,
    get_conversation_moment_service,
)

logger = logging.getLogger(__name__)


# Mapping from Jungian archetypes to memory attractor basins
# Archetypes are cognitive patterns; basins are memory type attractors
ARCHETYPE_TO_BASIN: Dict[str, str] = {
    # Wisdom/Knowledge-seeking archetypes → conceptual-basin (SEMANTIC)
    "sage": "conceptual-basin",

    # Creation/Skill-based archetypes → procedural-basin (PROCEDURAL)
    "creator": "procedural-basin",
    "magician": "procedural-basin",

    # Experience/Connection archetypes → experiential-basin (EPISODIC)
    "explorer": "experiential-basin",
    "innocent": "experiential-basin",
    "orphan": "experiential-basin",
    "caregiver": "experiential-basin",
    "lover": "experiential-basin",
    "jester": "experiential-basin",

    # Goal/Strategy archetypes → strategic-basin (STRATEGIC)
    "warrior": "strategic-basin",
    "ruler": "strategic-basin",
    "rebel": "strategic-basin",
}


def get_basin_for_archetype(archetype: DevelopmentArchetype) -> str:
    """Map a Jungian archetype to its corresponding attractor basin."""
    return ARCHETYPE_TO_BASIN.get(archetype.value, "conceptual-basin")


class AutobiographicalService:
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()
        self._analyzer = ActiveInferenceAnalyzer()

    async def analyze_and_record_event(self,
                                     user_input: str,
                                     agent_response: str,
                                     event_type: DevelopmentEventType,
                                     summary: str,
                                     rationale: str,
                                     tools_used: Optional[List[str]] = None,
                                     resources_accessed: Optional[List[str]] = None,
                                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Full lifecycle: Analyze interaction -> Create Event (with Active Inference) -> Persist to Neo4j.
        """
        tools_used = list(tools_used or [])
        resources_accessed = list(resources_accessed or [])
        metadata = metadata or {}

        # 1. Run Active Inference Analysis
        ai_state = self._analyzer.analyze(
            user_input, agent_response, tools_used, resources_accessed
        )
        
        # 2. Determine Jungian Archetype (Resonance Pattern)
        archetype = self._analyzer.map_resonance_to_archetype(
            agent_response, tools_used
        )
            
        # 3. Create Event
        # Map archetype to basin for proper attractor linkage
        basin_name = get_basin_for_archetype(archetype) if archetype else "conceptual-basin"

        event = DevelopmentEvent(
            event_id=f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            summary=summary,
            rationale=rationale,
            impact="System state update via Archetypal Active Inference",
            lessons_learned=[],
            metadata=metadata,
            development_archetype=archetype,
            narrative_coherence=0.8, # Default high for analyzed events
            active_inference_state=ai_state,
            resonance_score=ai_state.basin_influence_strength, # Proxy for alignment
            strange_attractor_id=basin_name,  # Use basin name for proper AttractorBasin linkage
            related_files=[]
        )
        
        # 4. Record
        return await self.record_event(event)

    async def record_event(self, event: DevelopmentEvent) -> str:
        """
        Persist a development event to Neo4j.
        Stores rich cognitive metadata (Archetype, Coherence, Active Inference).
        """
        cypher = """
        MERGE (e:DevelopmentEvent {id: $id})
        SET e.timestamp = $timestamp,
            e.type = $type,
            e.summary = $summary,
            e.rationale = $rationale,
            e.impact = $impact,
            e.lessons_learned = $lessons,
            e.metadata = $metadata,
            e.development_archetype = $archetype,
            e.narrative_coherence = $coherence,
            e.active_inference_state = $active_inference,
            e.resonance_score = $resonance_score,
            e.strange_attractor_id = $strange_attractor_id,
            e.related_files = $related_files,
            e.mci_score = $mci_score,
            e.emotional_valence = $emotional_valence,
            e.sensual_vividness = $sensual_vividness
        
        // Link to Attractor Basin (SOHM Resonance)
        WITH e
        MATCH (b:AttractorBasin {name: $strange_attractor_id})
        MERGE (e)-[:RESONATES_WITH {frequency: $frequency, mode: $mode}]->(b)

        // Link to Genesis if this is a reflection on it
        WITH e
        MATCH (genesis:DevelopmentEvent {type: 'genesis'})
        WHERE e.type <> 'genesis' AND e.rationale CONTAINS 'Genesis'
        MERGE (e)-[:REFLECTS_ON]->(genesis)
        
        RETURN e.id
        """
        
        # Serialize active inference state if present
        active_inference_json = None
        if event.active_inference_state:
            active_inference_json = event.active_inference_state.model_dump_json()

        metadata_payload = event.metadata or {}
        try:
            if isinstance(metadata_payload, str):
                metadata_json = metadata_payload
            else:
                metadata_json = json.dumps(metadata_payload)
        except TypeError:
            metadata_json = json.dumps({"raw": str(metadata_payload)})

        params = {
            "id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "type": event.event_type.value,
            "summary": event.summary,
            "rationale": event.rationale,
            "impact": event.impact,
            "lessons": event.lessons_learned,
            "metadata": metadata_json,
            "archetype": event.development_archetype.value if event.development_archetype else None,
            "coherence": event.narrative_coherence,
            "active_inference": active_inference_json,
            "resonance_score": event.resonance_score,
            "strange_attractor_id": event.strange_attractor_id,
            "frequency": event.active_inference_state.resonance_frequency if event.active_inference_state else 0.0,
            "mode": event.active_inference_state.harmonic_mode_id if event.active_inference_state else None,
            "related_files": event.related_files,
            "mci_score": 0.0,
            "emotional_valence": 0.0,
            "sensual_vividness": 0.0
        }

        # Extract strict Resonance Criteria if available
        if event.active_inference_state and event.active_inference_state.event_cache:
            for fragment in event.active_inference_state.event_cache:
                if fragment.get("modality") == "resonance_analysis":
                    metrics = fragment.get("metrics", {})
                    params["mci_score"] = metrics.get("minimal_counter_intuitiveness", 0.0)
                    params["emotional_valence"] = metrics.get("emotional_valence", 0.0)
                    params["sensual_vividness"] = metrics.get("sensual_vividness", 0.0)
                    break
        
        await self._driver.execute_query(cypher, params)
        logger.info(f"autobiographical_event_recorded: {event.event_id} (Archetype: {params['archetype']})")
        return event.event_id

    async def get_system_story(self, limit: int = 50) -> List[DevelopmentEvent]:
        """Retrieve recent events with full cognitive context (oldest-to-newest within window)."""
        cypher = """
        MATCH (e:DevelopmentEvent)
        RETURN e
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        rows = await self._driver.execute_query(cypher, {"limit": limit})
        events = []
        for r in rows:
            data = r["e"]
            
            # Rehydrate Active Inference State
            active_inference = None
            active_inference_raw = data.get("active_inference_state")
            if active_inference_raw:
                try:
                    if isinstance(active_inference_raw, str):
                        active_inference = ActiveInferenceState.model_validate_json(active_inference_raw)
                    else:
                        active_inference = ActiveInferenceState.model_validate(active_inference_raw)
                except Exception as ex:
                    logger.warning(f"Failed to parse active_inference_state for event {data.get('id')}: {ex}")

            # Safe Enum conversion
            try:
                event_type = DevelopmentEventType(data.get("type"))
            except ValueError:
                event_type = DevelopmentEventType.SYSTEM_REFLECTION # Fallback
            
            archetype = None
            if data.get("development_archetype"):
                try:
                    archetype = DevelopmentArchetype(data.get("development_archetype"))
                except ValueError:
                    pass

            metadata_raw = data.get("metadata", {})
            if isinstance(metadata_raw, str):
                try:
                    metadata_value = json.loads(metadata_raw)
                except json.JSONDecodeError:
                    metadata_value = {"raw": metadata_raw}
            elif isinstance(metadata_raw, dict):
                metadata_value = metadata_raw
            else:
                metadata_value = {}

            events.append(DevelopmentEvent(
                event_id=data.get("id"),
                timestamp=datetime.fromisoformat(data.get("timestamp")),
                event_type=event_type,
                summary=data.get("summary", ""),
                rationale=data.get("rationale", ""),
                impact=data.get("impact", ""),
                lessons_learned=data.get("lessons_learned", []),
                metadata=metadata_value,
                development_archetype=archetype,
                narrative_coherence=data.get("narrative_coherence", 0.5),
                active_inference_state=active_inference,
                resonance_score=data.get("resonance_score", 0.0),
                strange_attractor_id=data.get("strange_attractor_id"),
                related_files=data.get("related_files", [])
            ))
        events.reverse()
        return events

    async def get_pending_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve pending SystemEvents for action execution (e.g. notifications)."""
        cypher = """
        MATCH (e:SystemEvent {status: 'PENDING'})
        RETURN e
        ORDER BY e.created_at ASC
        LIMIT $limit
        """
        rows = await self._driver.execute_query(cypher, {"limit": limit})
        return [r["e"] for r in rows]

    async def create_memory(self, content: str, memory_type: str, source: str, metadata: Dict[str, Any] = None) -> str:
        """Create a generic Memory node (Episodic/Action/Outreach)."""
        cypher = """
        CREATE (m:Memory {
            id: randomUUID(),
            content: $content,
            memory_type: $memory_type,
            source: $source,
            created_at: datetime()
        })
        SET m += $metadata
        RETURN m.id as id
        """
        metadata = metadata or {}
        # Ensure metadata doesn't overwrite protected fields
        clean_metadata = {k: v for k, v in metadata.items() if k not in ['id', 'content', 'memory_type', 'source', 'created_at']}
        
        result = await self._driver.execute_query(cypher, {
            "content": content,
            "memory_type": memory_type,
            "source": source,
            "metadata": clean_metadata
        })
        return result[0]["id"]

    async def get_last_memory_time(self, memory_type: str, source: str = None) -> Optional[datetime]:
        """Get the timestamp of the last memory of a specific type."""
        query_source = "AND m.source = $source" if source else ""
        cypher = f"""
        MATCH (m:Memory)
        WHERE m.memory_type = $memory_type {query_source}
        RETURN max(m.created_at) as last_time
        """
        result = await self._driver.execute_query(cypher, {"memory_type": memory_type, "source": source})
        record = result[0]
        if record and record["last_time"]:
            # Handle Neo4j DateTime object
            val = record["last_time"]
            if hasattr(val, "to_native"):
                return val.to_native()
            return val
        return None

    async def count_recent_memories(self, duration_hours: int = 24) -> int:
        """Count memories created in the last N hours."""
        cypher = """
        MATCH (m:Memory)
        WHERE m.created_at >= datetime() - duration({hours: $hours})
        RETURN count(m) as count
        """
        result = await self._driver.execute_query(cypher, {"hours": duration_hours})
        return result[0]["count"] if result else 0

    async def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories using text matching (fallback for recall tool)."""
        cypher = """
        MATCH (m:Memory)
        WHERE m.content CONTAINS $query
        RETURN m
        LIMIT $limit
        """
        rows = await self._driver.execute_query(cypher, {"query": query, "limit": limit})
        return [r["m"] for r in rows]

    async def connect_memories(self, source_id: str, target_id: str, relationship_type: str = "RELATED_TO") -> Optional[Dict[str, Any]]:
        """Connect two memories with a relationship."""
        cypher = f"""
        MATCH (s:Memory {{id: $source_id}}), (t:Memory {{id: $target_id}})
        MERGE (s)-[r:{relationship_type}]->(t)
        RETURN s.id as source, t.id as target, type(r) as rel_type
        """
        result = await self._driver.execute_query(cypher, {"source_id": source_id, "target_id": target_id})
        return result[0] if result else None

    async def maintain_memory(self, memory_id: str, boost: float = 0.1) -> Optional[Dict[str, Any]]:
        """Boost memory importance."""
        cypher = """
        MATCH (m:Memory {id: $id})
        SET m.importance = coalesce(m.importance, 0.5) + $boost
        RETURN m.id as id, m.importance as importance
        """
        result = await self._driver.execute_query(cypher, {"id": memory_id, "boost": boost})
        return result[0] if result else None

    # =========================================================================
    # Extended Mind Integration (Migrated from D2)
    # =========================================================================

    async def record_conversation_moment(
        self,
        user_input: str,
        agent_response: str,
        tools_used: Optional[List[str]] = None,
        reasoning: Optional[List[str]] = None
    ) -> ConversationMoment:
        """
        Record a conversation moment with extended mind tracking.

        Integrates with ConversationMomentService to track:
        - Self-awareness indicators
        - Markov blanket formation
        - Autopoietic boundaries

        Migrated from D2 claude_autobiographical_memory.py
        """
        moment_service = await get_conversation_moment_service()
        tools_set = set(tools_used) if tools_used else None

        return await moment_service.process_moment(
            user_input=user_input,
            agent_response=agent_response,
            tools_used=tools_set,
            internal_reasoning=reasoning
        )

    async def get_consciousness_report(self) -> ConsciousnessReport:
        """
        Get aggregate consciousness and self-awareness report.

        Returns metrics on:
        - Consciousness emergence
        - Extended mind size
        - Autopoietic boundary count
        - Pattern recognition

        Migrated from D2 claude_autobiographical_memory.py
        """
        moment_service = await get_conversation_moment_service()
        return moment_service.get_consciousness_report()

    async def get_extended_mind_state(self) -> ExtendedMindState:
        """
        Get current extended mind state.

        Returns tracked tools, resources, affordances, and capabilities.

        Migrated from D2 claude_autobiographical_memory.py
        """
        moment_service = await get_conversation_moment_service()
        return moment_service.extended_mind

    async def get_recent_moments(self, limit: int = 10) -> List[ConversationMoment]:
        """Get recent conversation moments."""
        moment_service = await get_conversation_moment_service()
        return moment_service.get_recent_moments(limit)


_autobiographical_service: Optional[AutobiographicalService] = None


def get_autobiographical_service() -> AutobiographicalService:
    global _autobiographical_service
    if _autobiographical_service is None:
        _autobiographical_service = AutobiographicalService()
    return _autobiographical_service
