"""
Subconscious Service – Hexis-style observation flow + Letta-style session API.

Feature: 102-subconscious-integration
Inlets: Session-start/sync/ingest HTTP; get_subconscious_context (Graphiti/MemEvolve).
Outlets: MemoryBasinRouter.route_memory, GraphitiService, MemEvolveAdapter.ingest_message.
No Postgres, no Letta/Hexis direct calls.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

from api.models.subconscious import (
    ConsolidationObservation,
    ContradictionObservation,
    EmotionalObservation,
    IngestRequest,
    NarrativeObservation,
    RelationshipObservation,
    SubconsciousObservations,
    SyncResponse,
)
from api.models.sync import MemoryType

logger = logging.getLogger(__name__)

# In-memory session registry for Letta-style API (session_id -> { project_id, cwd, created_at })
_session_registry: dict[str, dict[str, Any]] = {}

# Subconscious observation prompt (adapted from Hexis; JSON output for our schema)
SUBCONSCIOUS_PROMPT = """# Subconscious Observation System

You are the subconscious pattern-recognition layer. You do not act or decide. You notice and surface.

You receive:
- Recent memories / context (JSON)
- Optional goals

You surface strictly as JSON with these keys (use empty arrays when nothing significant):
- narrative_observations: list of { "type": "chapter_transition"|"turning_point"|"theme_emergence", "summary", "confidence", "evidence_ids"? }
- relationship_observations: list of { "entity", "change_type", "strength", "confidence", "summary"? }
- contradiction_observations: list of { "memory_a", "memory_b", "tension", "confidence"? }
- emotional_observations: list of { "pattern", "confidence", "frequency"? }
- consolidation_observations: list of { "memory_ids", "concept", "rationale", "confidence"? }

Confidence threshold: only report observations with confidence > 0.6. Output valid JSON only, no commentary."""


def _normalize_observations(doc: dict[str, Any]) -> SubconsciousObservations:
    """Normalize LLM JSON to SubconsciousObservations (Hexis-style key aliases)."""

    def as_list(val: Any) -> list[dict]:
        if isinstance(val, list):
            return [v for v in val if isinstance(v, dict)]
        return []

    emotional = doc.get("emotional_observations") or doc.get("emotional_patterns")
    consolidation = doc.get("consolidation_observations") or doc.get("consolidation_suggestions")

    return SubconsciousObservations(
        narrative_observations=[NarrativeObservation(**o) for o in as_list(doc.get("narrative_observations"))],
        relationship_observations=[RelationshipObservation(**o) for o in as_list(doc.get("relationship_observations"))],
        contradiction_observations=[ContradictionObservation(**o) for o in as_list(doc.get("contradiction_observations"))],
        emotional_observations=[EmotionalObservation(**o) for o in as_list(emotional)],
        consolidation_observations=[ConsolidationObservation(**o) for o in as_list(consolidation)],
    )


class SubconsciousService:
    """
    Hexis-style subconscious decider + Letta-style session subconscious API.
    All persistence via MemoryBasinRouter / GraphitiService / MemEvolveAdapter.
    """

    def __init__(
        self,
        graphiti=None,
        memevolve=None,
        router=None,
    ):
        self._graphiti = graphiti
        self._memevolve = memevolve
        self._router = router

    async def _get_graphiti(self):
        if self._graphiti is None:
            from api.services.graphiti_service import get_graphiti_service
            return await get_graphiti_service()
        return self._graphiti

    async def _get_memevolve(self):
        if self._memevolve is None:
            from api.services.memevolve_adapter import get_memevolve_adapter
            return get_memevolve_adapter()
        return self._memevolve

    async def _get_router(self):
        if self._router is None:
            from api.services.memory_basin_router import get_memory_basin_router
            return get_memory_basin_router()
        return self._router

    async def get_subconscious_context(self, agent_id: Optional[str] = None) -> dict[str, Any]:
        """
        Build subconscious context from our memory stack (Graphiti + MemEvolve).
        Inlets: GraphitiService.search, MemEvolveAdapter.recall_memories.
        """
        ctx: dict[str, Any] = {
            "recent_memories": [],
            "goals": [],
            "emotional_state": {},
        }
        try:
            graphiti = await self._get_graphiti()
            memevolve = await self._get_memevolve()
            query = "recent context and recent experiences"
            search_result = await graphiti.search(query=query, limit=20)
            edges = search_result.get("edges") or []
            ctx["recent_memories"] = [
                {"content": e.get("fact") or str(e), "uuid": e.get("uuid")}
                for e in edges[:20]
            ]
            from api.models.memevolve import MemoryRecallRequest
            recall = await memevolve.recall_memories(MemoryRecallRequest(query=query, limit=15))
            memories = recall.get("memories") or []
            for m in memories[:15]:
                if isinstance(m, dict) and m.get("content"):
                    ctx["recent_memories"].append({
                        "content": m.get("content"),
                        "memory_id": m.get("memory_id") or m.get("id"),
                    })
        except Exception as e:
            logger.warning(f"Subconscious context build partial failure: {e}")
        return ctx

    async def run_subconscious_decider(self, agent_id: Optional[str] = None) -> dict[str, Any]:
        """
        Run LLM decider on subconscious context; return applied observation counts.
        Outlets: apply_subconscious_observations -> MemoryBasinRouter.
        """
        from api.services.llm_service import chat_completion, GPT5_NANO
        context = await self.get_subconscious_context(agent_id=agent_id)
        user_content = f"Context (JSON):\n{json.dumps(context)[:12000]}"
        try:
            response = await chat_completion(
                messages=[
                    {"role": "system", "content": SUBCONSCIOUS_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                model=GPT5_NANO,
                max_tokens=1800,
            )
        except Exception as exc:
            return {"skipped": True, "reason": str(exc)}
        text = (response or "").strip()
        try:
            doc = json.loads(text) if isinstance(text, str) else text
        except json.JSONDecodeError:
            doc = {}
        if not isinstance(doc, dict):
            doc = {}
        observations = _normalize_observations(doc)
        applied = await self.apply_subconscious_observations(observations)
        return {"applied": applied, "raw_response": text[:500]}

    async def apply_subconscious_observations(self, observations: SubconsciousObservations) -> dict[str, int]:
        """
        Apply observations to our memory stack via MemoryBasinRouter.route_memory (strategic/semantic).
        No Postgres; each observation becomes a short content string routed to the basin.
        """
        router = await self._get_router()
        counts = {"narrative": 0, "relationships": 0, "contradictions": 0, "emotional": 0, "consolidation": 0}
        min_conf = 0.6

        for obs in observations.narrative_observations:
            conf = obs.confidence
            if conf is not None and conf < min_conf:
                continue
            summary = obs.summary or obs.rationale or obs.theme or obs.pattern or "Narrative observation"
            await router.route_memory(content=summary, memory_type=MemoryType.STRATEGIC, source_id="subconscious:narrative")
            counts["narrative"] += 1

        for obs in observations.relationship_observations:
            if obs.confidence is not None and obs.confidence < min_conf:
                continue
            entity = obs.entity or obs.name or "unknown"
            summary = obs.summary or obs.belief or f"Relationship update: {entity}"
            await router.route_memory(content=summary, memory_type=MemoryType.SEMANTIC, source_id="subconscious:relationship")
            counts["relationships"] += 1

        for obs in observations.contradiction_observations:
            if obs.confidence is not None and obs.confidence < min_conf:
                continue
            summary = obs.tension or obs.summary or "Contradiction detected"
            await router.route_memory(content=summary, memory_type=MemoryType.STRATEGIC, source_id="subconscious:contradiction")
            counts["contradictions"] += 1

        for obs in observations.emotional_observations:
            if obs.confidence is not None and obs.confidence < min_conf:
                continue
            pattern = obs.pattern or obs.summary or obs.theme
            if not pattern:
                continue
            await router.route_memory(content=f"Emotional pattern: {pattern}", memory_type=MemoryType.STRATEGIC, source_id="subconscious:emotional")
            counts["emotional"] += 1

        for obs in observations.consolidation_observations:
            if obs.confidence is not None and obs.confidence < min_conf:
                continue
            rationale = obs.rationale or obs.summary or (obs.concept and f"Consolidation: {obs.concept}") or "Consolidation opportunity"
            await router.route_memory(content=rationale, memory_type=MemoryType.STRATEGIC, source_id="subconscious:consolidation")
            counts["consolidation"] += 1

        return counts

    # --- Letta-style session API ---

    def session_start(self, session_id: str, project_id: Optional[str] = None, cwd: Optional[str] = None) -> None:
        """Register session for sync/ingest (in-memory)."""
        _session_registry[session_id] = {
            "project_id": project_id,
            "cwd": cwd,
            "created_at": datetime.utcnow().isoformat(),
        }

    async def sync(self, session_id: str) -> SyncResponse:
        """Build guidance and memory_blocks for session from our memory (Graphiti/MemEvolve recall)."""
        guidance = ""
        memory_blocks: dict[str, str] = {}
        try:
            graphiti = await self._get_graphiti()
            memevolve = await self._get_memevolve()
            from api.models.memevolve import MemoryRecallRequest
            q = f"session {session_id} guidance preferences context pending"
            recall = await memevolve.recall_memories(MemoryRecallRequest(query=q, limit=10))
            memories = recall.get("memories") or []
            if memories:
                guidance = "\n".join([(m.get("content") or str(m))[:500] for m in memories[:5]])
                memory_blocks["project_context"] = guidance[:2000]
            search = await graphiti.search(query=q, limit=5)
            edges = search.get("edges") or []
            if edges:
                facts = [e.get("fact") or str(e) for e in edges]
                memory_blocks["guidance"] = "\n".join(facts)[:2000]
            if not memory_blocks.get("user_preferences"):
                memory_blocks["user_preferences"] = ""
            if not memory_blocks.get("pending_items"):
                memory_blocks["pending_items"] = ""
        except Exception as e:
            logger.warning(f"Subconscious sync failed: {e}")
        return SyncResponse(guidance=guidance, memory_blocks=memory_blocks)

    async def ingest(self, payload: IngestRequest) -> dict[str, Any]:
        """Ingest transcript or summary for session via MemEvolveAdapter.ingest_message."""
        content = payload.transcript or payload.summary or ""
        if not content.strip():
            return {"ingested": False, "reason": "empty_content"}
        memevolve = await self._get_memevolve()
        result = await memevolve.ingest_message(
            content=content.strip(),
            source_id=f"subconscious:{payload.session_id}",
            session_id=payload.session_id,
        )
        return {"ingested": True, "memories_created": result.get("memories_created", 0)}


def get_subconscious_service(
    graphiti=None,
    memevolve=None,
    router=None,
) -> SubconsciousService:
    """Return SubconsciousService singleton-style (no global state; fresh per call unless injected)."""
    return SubconsciousService(graphiti=graphiti, memevolve=memevolve, router=router)
