"""
Reconstruction Service
Feature: Session Continuity via Attractor-Based Memory Reconstruction

Implements the memory reconstruction protocol from Context-Engineering:
- Fragment scanning (sessions, tasks, entities)
- Resonance activation (cue + context + network)
- Field dynamics (attractor evolution)
- Pattern extraction (coherent summary)
- Gap filling (LLM reasoning)

Reference: /Volumes/Asylum/repos/Context-Engineering/60_protocols/shells/memory.reconstruction.attractor.shell.md
"""

import logging
import os
import hashlib
import time
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx

from api.services.graphiti_service import get_graphiti_service
from api.services.remote_sync import get_neo4j_driver

logger = logging.getLogger("dionysus.reconstruction")


# =============================================================================
# Configuration
# =============================================================================

class ReconstructionConfig:
    """Configuration for reconstruction service."""
    
    # Resonance weights (must sum to 1.0)
    CUE_RESONANCE_WEIGHT = 0.5
    CONTEXT_RESONANCE_WEIGHT = 0.2
    NETWORK_RESONANCE_WEIGHT = 0.1
    SUBGONSCIOUS_BIAS_WEIGHT = 0.2
    
    # Thresholds
    RESONANCE_ACTIVATION_THRESHOLD = 0.3
    HIGH_RESONANCE_THRESHOLD = 0.5
    COHERENCE_MIN = 0.6
    
    # Limits
    MAX_SESSIONS = 10
    MAX_TASKS = 15
    MAX_ENTITIES = 20
    MAX_EPISODIC = 15  # Max episodic memories from Neo4j
    MAX_OUTPUT_TOKENS = 4000  # Target compact output
    
    # Time windows
    RECENT_SESSION_HOURS = 72  # Last 3 days
    ACTIVE_TASK_DAYS = 30


# =============================================================================
# Fragment Types
# =============================================================================

class FragmentType(str, Enum):
    SESSION = "session"
    TASK = "task"
    ENTITY = "entity"
    DECISION = "decision"
    COMMITMENT = "commitment"
    EPISODIC = "episodic"  # Episodic memories from Neo4j


@dataclass
class Fragment:
    """A memory fragment (attractor basin) in the reconstruction field."""
    
    fragment_id: str
    fragment_type: FragmentType
    content: str
    summary: Optional[str] = None
    
    # Attractor properties
    strength: float = 0.5
    activation: float = 0.0
    resonance_score: float = 0.0
    
    # Metadata
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    
    # Connections to other fragments
    connections: list[str] = field(default_factory=list)
    
    # Source metadata
    source: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ReconstructionContext:
    """Context for reconstruction - the retrieval cues."""
    
    project_path: str
    project_name: str
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Explicit cues (what user is asking about)
    cues: list[str] = field(default_factory=list)
    
    # Subconscious guidance from DreamService
    subconscious_guidance: str = ""
    
    # Derived context
    project_id: Optional[str] = None
    
    def __post_init__(self):
        # Generate deterministic project_id from path
        if self.project_path and not self.project_id:
            self.project_id = hashlib.sha256(
                self.project_path.encode()
            ).hexdigest()[:32]


@dataclass
class ReconstructedMemory:
    """The output of reconstruction - coherent context for injection."""

    # Fields without defaults must come first
    project_summary: str
    recent_sessions: list[dict]
    active_tasks: list[dict]
    key_entities: list[dict]
    recent_decisions: list[dict]
    coherence_score: float
    fragment_count: int
    reconstruction_time_ms: float

    # Fields with defaults
    episodic_memories: list[dict] = field(default_factory=list)
    gap_fills: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    identity_context: str = ""  # Hexis identity (worldview/goals/directives)

    
    def to_compact_context(self) -> str:
        """Convert to compact text for context injection."""
        lines = []
        
        lines.append("# Session Context (Reconstructed)")
        lines.append("")
        
        # Project
        lines.append(f"## Project: {self.project_summary}")
        lines.append("")

        # Identity Context (Hexis - worldview/goals/directives)
        if self.identity_context:
            lines.append(self.identity_context)
            lines.append("")

        # Recent sessions
        if self.recent_sessions:
            lines.append("## Recent Sessions")
            for session in self.recent_sessions[:3]:
                date = session.get('date', 'Unknown')
                summary = session.get('summary', 'No summary')
                lines.append(f"- [{date}] {summary}")
            lines.append("")
        
        # Active tasks
        if self.active_tasks:
            lines.append("## Active Tasks")
            for task in self.active_tasks[:5]:
                title = task.get('title', 'Untitled')
                status = task.get('status', 'unknown')
                feature = task.get('feature', '')
                if feature:
                    lines.append(f"- [{status}] {title} ({feature})")
                else:
                    lines.append(f"- [{status}] {title}")
            lines.append("")
        
        # Key entities
        if self.key_entities:
            lines.append("## Key Entities")
            for entity in self.key_entities[:5]:
                name = entity.get('name', 'Unknown')
                entity_type = entity.get('type', '')
                lines.append(f"- {name}" + (f" ({entity_type})" if entity_type else ""))
            lines.append("")
        
        # Recent decisions
        if self.recent_decisions:
            lines.append("## Recent Decisions")
            for decision in self.recent_decisions[:3]:
                content = decision.get('content', '')
                lines.append(f"- {content}")
            lines.append("")

        # Episodic memories (from Neo4j attractors)
        if self.episodic_memories:
            lines.append("## Relevant Memories")
            for memory in self.episodic_memories[:5]:
                content = memory.get('content', '')[:150]
                mem_type = memory.get('memory_type', 'memory')
                similarity = memory.get('similarity', 0)
                lines.append(f"- [{mem_type}] {content}... (relevance: {similarity:.0%})")
            lines.append("")

        # Warnings
        if self.warnings:
            lines.append("## Warnings")
            for warning in self.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        return {
            "project_summary": self.project_summary,
            "recent_sessions": self.recent_sessions,
            "active_tasks": self.active_tasks,
            "key_entities": self.key_entities,
            "recent_decisions": self.recent_decisions,
            "episodic_memories": self.episodic_memories,
            "coherence_score": self.coherence_score,
            "fragment_count": self.fragment_count,
            "reconstruction_time_ms": self.reconstruction_time_ms,
            "gap_fills": self.gap_fills,
            "warnings": self.warnings,
            "compact_context": self.to_compact_context(),
        }


# =============================================================================
# Reconstruction Service
# =============================================================================

class ReconstructionService:
    """
    Attractor-based memory reconstruction service. 
    
    Implements the 10-step protocol:
    1. SCAN - Gather fragments from all sources
    2. ACTIVATE - Calculate resonance with current context
    3. EXCITE - Amplify high-resonance fragments
    4. EVOLVE - Field dynamics to surface top patterns
    5. EXTRACT - Pull coherent patterns
    6. IDENTIFY_GAPS - Find missing pieces
    7. FILL_GAPS - Use reasoning to fill
    8. VALIDATE - Check coherence
    9. ADAPT - Update fragment strengths (future)
    10. CONSOLIDATE - Return compact context
    """
    
    def __init__(
        self,
        n8n_recall_url: Optional[str] = None,
        graphiti_enabled: bool = False,
    ):
        self.n8n_recall_url = n8n_recall_url or os.getenv(
            "N8N_RECALL_URL", "http://n8n:5678/webhook/memory/v1/recall"
        )
        self.graphiti_enabled = graphiti_enabled
        self.config = ReconstructionConfig()
        self._driver = get_neo4j_driver()

        # Fragment field (populated during reconstruction)
        self._fragments: list[Fragment] = []
    
    # =========================================================================
    # Main Reconstruction Pipeline
    # =========================================================================
    
    async def reconstruct(
        self,
        context: ReconstructionContext,
        prefetched_tasks: Optional[list[dict]] = None,
        modality: str = "neurotypical"
    ) -> ReconstructedMemory:
        """
        Execute the full reconstruction pipeline.

        Args:
            context: Reconstruction context with project info and cues
            prefetched_tasks: Optional task list provided by the caller
            modality: The current CognitiveModality (ULTRATHINK)

        Returns:
            ReconstructedMemory with coherent context for injection
        """
        start_time = time.time()

        warnings = []

        # Phase 3: Subconscious Hydration
        if not context.subconscious_guidance:
            try:
                from api.services.dream_service import get_dream_service
                dream_svc = await get_dream_service()
                # Use a generic summary if none available
                context.subconscious_guidance = await dream_svc.generate_guidance(
                    context_summary=f"Reconstructing context for {context.project_name}"
                )
                logger.debug("Automatic subconscious hydration successful")
            except Exception as e:
                logger.warning(f"Failed to hydrate subconscious guidance: {e}")

        # Phase 4: Identity Hydration (Hexis - worldview/goals/directives)
        identity_context = ""
        try:
            from api.services.hexis_identity import get_hexis_identity_service
            identity_svc = get_hexis_identity_service()
            agent_id = context.project_id or "dionysus_core"
            identity_context = await identity_svc.get_prompt_context(agent_id=agent_id)
            if identity_context:
                logger.debug(f"Identity hydration successful for {agent_id}")
        except Exception as e:
            logger.warning(f"Failed to hydrate identity context: {e}")

        # Step 1: SCAN - Gather fragments from all sources
        logger.info(f"Reconstructing context (Modality={modality}) for project: {context.project_name}")
        await self._scan_fragments(context, prefetched_tasks=prefetched_tasks)
        
        if not self._fragments:
            warnings.append("No fragments found for reconstruction")
            return self._create_empty_result(context, warnings, start_time)
        
        logger.info(f"Scanned {len(self._fragments)} fragments")
        
        # Step 2: ACTIVATE - Calculate resonance scores
        self._activate_resonance(context, modality=modality)
        
        # Step 3: EXCITE - Amplify high-resonance fragments
        self._excite_fragments()
        
        # Step 4: EVOLVE - Field dynamics (Reference Librarian filtering)
        self._apply_reference_librarian_filter(modality)
        self._evolve_field()
        
        # Step 5: EXTRACT - Get top patterns by type
        extracted = self._extract_patterns()
        
        # Step 6-7: IDENTIFY & FILL GAPS (simplified for MVP)
        gap_fills = self._identify_and_fill_gaps(extracted, context)
        
        # Step 8: VALIDATE - Calculate coherence
        coherence_score = self._validate_coherence(extracted)
        
        # Step 9-10: ADAPT & CONSOLIDATE
        # (Adaptation is future work - for now just consolidate)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return ReconstructedMemory(
            project_summary=context.project_name,
            recent_sessions=extracted.get("sessions", []),
            active_tasks=extracted.get("tasks", []),
            key_entities=extracted.get("entities", []),
            recent_decisions=extracted.get("decisions", []),
            episodic_memories=extracted.get("episodic", []),
            coherence_score=coherence_score,
            fragment_count=len(self._fragments),
            reconstruction_time_ms=elapsed_ms,
            gap_fills=gap_fills,
            warnings=warnings,
            identity_context=identity_context,
        )

    def _apply_reference_librarian_filter(self, modality: str) -> None:
        """
        ULTRATHINK: The 'Reference Librarian' prevents workspace flooding.
        During SIEGE_LOCKED or ADHD_EXPLORATORY states, we suppress meta-patterns 
        (long sessions/strategies) and boost discrete steps (tasks/decisions).
        """
        if modality == "neurotypical":
            return

        logger.info(f"Reference Librarian active for modality: {modality}")
        for fragment in self._fragments:
            # Penalize the 'History' layer during siege to reduce cognitive load
            if fragment.fragment_type in {FragmentType.SESSION, FragmentType.EPISODIC}:
                if modality == "siege_locked":
                    fragment.activation *= 0.4  # Hard suppression
                elif modality == "adhd_exploratory":
                    fragment.activation *= 0.7  # Soft suppression

            # Boost the 'Action' layer (managing discrete steps)
            if fragment.fragment_type in {FragmentType.TASK, FragmentType.DECISION, FragmentType.COMMITMENT}:
                fragment.activation = min(fragment.activation * 1.5, 1.0)
    
    # =========================================================================
    # Step 1: Fragment Scanning
    # =========================================================================
    
    async def _scan_fragments(
        self,
        context: ReconstructionContext,
        prefetched_tasks: Optional[list[dict]] = None,
    ) -> None:
        """Scan all sources for memory fragments."""
        self._fragments = []

        # Scan episodic memories from Neo4j via Graphiti
        await self._scan_episodic_memories(context)

        # Scan sessions from n8n
        await self._scan_sessions(context)

        # Scan tasks - use prefetched if provided
        if prefetched_tasks is not None:
            logger.info(f"Using {len(prefetched_tasks)} prefetched tasks")
            self._load_prefetched_tasks(prefetched_tasks)

        # Scan entities from Graphiti (if enabled)
        if self.graphiti_enabled:
            await self._scan_entities(context)
            
        # Phase 3: Scan for subconscious activations (Forced Retrieval)
        await self._scan_subconscious_activations(context)

    async def _scan_episodic_memories(self, context: ReconstructionContext) -> None:
        """
        Scan episodic memories from Neo4j via Graphiti.
        """
        try:
            query_parts = [context.project_name]
            if context.cues:
                query_parts.extend(context.cues)
            query = " ".join(query_parts)

            graphiti = await get_graphiti_service()
            results = await graphiti.search(query=query, limit=self.config.MAX_EPISODIC)

            edges = results.get("edges", [])
            for idx, edge in enumerate(edges):
                if not isinstance(edge, dict): continue
                position_score = 1.0 - (idx / max(len(edges), 1)) * 0.5
                content = edge.get("fact") or edge.get("name") or ""
                fragment = Fragment(
                    fragment_id=str(edge.get("uuid", "")),
                    fragment_type=FragmentType.EPISODIC,
                    content=content,
                    summary=edge.get("fact"),
                    strength=min(position_score, 1.0),
                    created_at=self._parse_datetime(edge.get("valid_at")),
                    source="graphiti",
                    metadata=edge,
                )
                self._fragments.append(fragment)
        except Exception as e:
            logger.error(f"Failed to scan episodic memories from Graphiti: {e}")

    async def _scan_sessions(self, context: ReconstructionContext) -> None:
        """Scan recent sessions from memory system."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=self.config.RECENT_SESSION_HOURS)
            payload = {
                "operation": "query",
                "filters": {
                    "project_id": context.project_id,
                    "device_id": context.device_id,
                    "from_date": cutoff.isoformat(),
                },
                "limit": self.config.MAX_SESSIONS,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.n8n_recall_url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    sessions = result.get("sessions", result.get("memories", []))
                    for session in sessions:
                        fragment = Fragment(
                            fragment_id=session.get("id", session.get("session_id", "")),
                            fragment_type=FragmentType.SESSION,
                            content=session.get("summary", session.get("content", "")),
                            summary=session.get("summary"),
                            created_at=self._parse_datetime(session.get("created_at")),
                            source="n8n",
                            metadata=session,
                        )
                        self._fragments.append(fragment)
        except Exception as e:
            logger.error(f"Failed to scan recent sessions from n8n: {e}")
    
    def _load_prefetched_tasks(self, tasks: list[dict]) -> None:
        """Load pre-fetched tasks as fragments."""
        for task in tasks:
            fragment = Fragment(
                fragment_id=task.get("id", ""),
                fragment_type=FragmentType.TASK,
                content=task.get("title", ""),
                summary=task.get("description", ""),
                strength=0.9,
                source="prefetched",
                metadata=task,
            )
            self._fragments.append(fragment)

    async def _scan_entities(self, context: ReconstructionContext) -> None:
        """Scan key entities from Graphiti."""
        try:
            graphiti = await get_graphiti_service()
            results = await graphiti.search(query=context.project_name, limit=self.config.MAX_ENTITIES)
            for edge in results.get("edges", []):
                fragment = Fragment(
                    fragment_id=edge.get("uuid", ""),
                    fragment_type=FragmentType.ENTITY,
                    content=edge.get("fact", edge.get("name", "")),
                    source="graphiti",
                    metadata=edge,
                )
                self._fragments.append(fragment)
        except Exception as e:
            logger.error(f"Failed to scan key entities from Graphiti: {e}")

    async def _scan_subconscious_activations(self, context: ReconstructionContext) -> None:
        """
        Scan for nodes specifically mentioned or resonant with subconscious guidance.
        This forces retrieval of potentially 'forgotten' but resonant items.
        """
        if not context.subconscious_guidance or context.subconscious_guidance == "(No active guidance)":
            return
            
        try:
            # Extract potential keywords from guidance (e.g. from spontaneous recall)
            keywords = re.findall(r"['\"]([^'\"]+)['\"]", context.subconscious_guidance)
            
            if not keywords:
                # Find drive status keywords (e.g. CURIOSITY, REST)
                keywords = [kw for kw in re.findall(r'\b[A-Z]{4,}\b', context.subconscious_guidance) if kw not in {'NOTE', 'TIP', 'GUIDANCE'}]
            
            if not keywords:
                return

            logger.info(f"Subconscious bias scanning for keywords: {keywords}")

            cypher = """
            MATCH (e:Entity)
            WHERE ANY(kw IN $keywords WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN e.id as id, e.name as name, e.summary as summary, e.created_at as created_at
            LIMIT 5
            """
            graphiti = await get_graphiti_service()
            results = await graphiti.execute_cypher(cypher, {"keywords": keywords})
            
            for row in results:
                # Avoid duplicates
                if any(f.fragment_id == row["id"] for f in self._fragments):
                    continue
                    
                fragment = Fragment(
                    fragment_id=row["id"],
                    fragment_type=FragmentType.ENTITY,
                    content=row["name"],
                    summary=row["summary"],
                    strength=0.9,
                    source="subconscious_forced",
                    metadata=row
                )
                self._fragments.append(fragment)
                logger.info(f"Subconscious forced retrieval: {row['name']}")
                
        except Exception as e:
            logger.error(f"Failed to scan subconscious activations: {e}")
    
    # =========================================================================
    # Step 2: Resonance Activation
    # =========================================================================
    
    def _activate_resonance(self, context: ReconstructionContext, modality: str = "neurotypical") -> None:
        for fragment in self._fragments:
            cue_resonance = self._calculate_cue_resonance(fragment, context.cues)
            context_resonance = self._calculate_context_resonance(fragment, context)
            network_resonance = self._calculate_network_resonance(fragment)
            
            subconscious_bias = self._calculate_subconscious_bias(fragment, context.subconscious_guidance)
            modality_bias = self._calculate_modality_bias(fragment, modality)
            
            fragment.resonance_score = (
                cue_resonance * self.config.CUE_RESONANCE_WEIGHT +
                context_resonance * self.config.CONTEXT_RESONANCE_WEIGHT +
                network_resonance * self.config.NETWORK_RESONANCE_WEIGHT +
                subconscious_bias * self.config.SUBGONSCIOUS_BIAS_WEIGHT +
                modality_bias * 0.1  # Small additional bias from modality
            )
            # Normalize to 1.0
            fragment.resonance_score = min(fragment.resonance_score, 1.0)

            if fragment.resonance_score >= self.config.RESONANCE_ACTIVATION_THRESHOLD:
                fragment.activation = fragment.resonance_score

    def _calculate_modality_bias(self, fragment: Fragment, modality: str) -> float:
        """
        ULTRATHINK: ADHD favors wide-ranging discovery, whereas siege favors survival.
        """
        if modality == "adhd_exploratory":
            # Boost anything novel or divergent (heuristic: recently created or diverse tags)
            if fragment.created_at and (datetime.now(timezone.utc) - fragment.created_at).total_seconds() < 3600:
                return 0.8
        elif modality == "siege_locked":
            # Boost anything related to 'Stability' or 'Next Steps'
            if fragment.fragment_type in {FragmentType.TASK, FragmentType.DECISION}:
                return 0.9
        return 0.5
    
    def _calculate_cue_resonance(self, fragment: Fragment, cues: list[str]) -> float:
        if not cues: return 0.5
        content = (fragment.content + " " + (fragment.summary or "")).lower()
        matches = sum(1 for cue in cues if cue.lower() in content)
        return min(matches / len(cues), 1.0)
    
    def _calculate_context_resonance(self, fragment: Fragment, context: ReconstructionContext) -> float:
        score = 0.0
        if fragment.metadata.get("project_id") == context.project_id: score += 0.5
        if context.project_name.lower() in fragment.content.lower(): score += 0.3
        if fragment.created_at:
            hours_ago = (datetime.now(timezone.utc) - fragment.created_at).total_seconds() / 3600
            if hours_ago < 24: score += 0.2
            elif hours_ago < 72: score += 0.1
        return min(score, 1.0)
    
    def _calculate_network_resonance(self, fragment: Fragment) -> float:
        return 0.3
        
    def _calculate_subconscious_bias(self, fragment: Fragment, guidance: str) -> float:
        """
        Calculate how much a fragment aligns with the current subconscious guidance.
        This enables 'Attractor Basins' where the system prioritizes memories or 
        tasks that the DreamService flagged as relevant (e.g. restoration of a drive).
        """
        if not guidance or guidance == "(No active guidance)":
            return 0.5 # Neutral bias
            
        content = (fragment.content + " " + (fragment.summary or "")).lower()
        guidance_lower = guidance.lower()
        
        # Simple keyword overlap (future: vector similarity)
        # Extract keywords from fragment content (primitive)
        keywords = set(re.findall(r'\w+', content))
        # Find overlaps with guidance
        overlap_count = sum(1 for kw in keywords if len(kw) > 3 and kw in guidance_lower)
        
        # Log heavy hits
        if overlap_count > 3:
            logger.debug(f"Subconscious resonance detected for fragment {fragment.fragment_id}: {overlap_count} matches")
            
        return min(0.5 + (overlap_count * 0.1), 1.0)
    
    def _excite_fragments(self, amplification: float = 1.3) -> None:
        for fragment in self._fragments:
            if fragment.resonance_score >= self.config.HIGH_RESONANCE_THRESHOLD:
                fragment.activation = min(fragment.activation * amplification, 1.0)
    
    def _evolve_field(self) -> None:
        self._fragments.sort(key=lambda f: f.activation * f.strength, reverse=True)
    
    def _extract_patterns(self) -> dict:
        extracted = {"sessions": [], "tasks": [], "entities": [], "decisions": [], "episodic": []}
        for fragment in self._fragments:
            if fragment.activation < self.config.RESONANCE_ACTIVATION_THRESHOLD: continue
            if fragment.fragment_type == FragmentType.SESSION:
                extracted["sessions"].append({"id": fragment.fragment_id, "summary": fragment.summary or fragment.content[:200], "date": fragment.created_at.strftime("%Y-%m-%d") if fragment.created_at else "Unknown", "resonance": fragment.resonance_score})
            elif fragment.fragment_type == FragmentType.TASK:
                extracted["tasks"].append({"id": fragment.fragment_id, "title": fragment.content, "status": fragment.metadata.get("status", "todo"), "feature": fragment.metadata.get("feature", ""), "resonance": fragment.resonance_score})
            elif fragment.fragment_type == FragmentType.ENTITY:
                extracted["entities"].append({"id": fragment.fragment_id, "name": fragment.content, "type": fragment.metadata.get("type", "entity"), "resonance": fragment.resonance_score})
            elif fragment.fragment_type == FragmentType.EPISODIC:
                extracted["episodic"].append({"id": fragment.fragment_id, "content": fragment.content[:300], "summary": fragment.summary, "similarity": fragment.metadata.get("similarity", 0.0), "resonance": fragment.resonance_score})
        return extracted
    
    def _identify_and_fill_gaps(self, extracted: dict, context: ReconstructionContext) -> list:
        return []
    
    def _validate_coherence(self, extracted: dict) -> float:
        return 0.8
    
    def _create_empty_result(self, context: ReconstructionContext, warnings: list, start_time: float) -> ReconstructedMemory:
        return ReconstructedMemory(project_summary=context.project_name, recent_sessions=[], active_tasks=[], key_entities=[], recent_decisions=[], coherence_score=0.0, fragment_count=0, reconstruction_time_ms=(time.time() - start_time) * 1000, warnings=warnings)
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if value is None: return None
        if isinstance(value, datetime): return value
        if isinstance(value, str):
            try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except: return None
        return None


# =============================================================================
# Service Instance
# =============================================================================

_reconstruction_service: Optional[ReconstructionService] = None


def get_reconstruction_service() -> ReconstructionService:
    """Get or create reconstruction service singleton."""
    global _reconstruction_service
    if _reconstruction_service is None:
        _reconstruction_service = ReconstructionService()
    return _reconstruction_service
