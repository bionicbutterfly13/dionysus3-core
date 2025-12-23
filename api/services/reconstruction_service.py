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
from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class ReconstructionConfig:
    """Configuration for reconstruction service."""
    
    # Resonance weights (must sum to 1.0)
    CUE_RESONANCE_WEIGHT = 0.5
    CONTEXT_RESONANCE_WEIGHT = 0.3
    NETWORK_RESONANCE_WEIGHT = 0.2
    
    # Thresholds
    RESONANCE_ACTIVATION_THRESHOLD = 0.3
    HIGH_RESONANCE_THRESHOLD = 0.5
    COHERENCE_MIN = 0.6
    
    # Limits
    MAX_SESSIONS = 10
    MAX_TASKS = 15
    MAX_ENTITIES = 20
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
    
    # Summary sections
    project_summary: str
    recent_sessions: list[dict]
    active_tasks: list[dict]
    key_entities: list[dict]
    recent_decisions: list[dict]
    
    # Metadata
    coherence_score: float
    fragment_count: int
    reconstruction_time_ms: float
    
    # Gap fills (if any)
    gap_fills: list[dict] = field(default_factory=list)
    
    # Warnings
    warnings: list[str] = field(default_factory=list)
    
    def to_compact_context(self) -> str:
        """Convert to compact text for context injection."""
        lines = []
        
        lines.append("# Session Context (Reconstructed)")
        lines.append("")
        
        # Project
        lines.append(f"## Project: {self.project_summary}")
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
        archon_url: Optional[str] = None,
        n8n_recall_url: Optional[str] = None,
        graphiti_enabled: bool = False,
    ):
        self.archon_url = archon_url or os.getenv(
            "ARCHON_API_URL", "http://localhost:8100"
        )
        self.n8n_recall_url = n8n_recall_url or os.getenv(
            "N8N_RECALL_URL", "http://localhost:5678/webhook/memory/v1/recall"
        )
        self.graphiti_enabled = graphiti_enabled
        self.config = ReconstructionConfig()
        
        # Fragment field (populated during reconstruction)
        self._fragments: list[Fragment] = []
    
    # =========================================================================
    # Main Reconstruction Pipeline
    # =========================================================================
    
    async def reconstruct(
        self,
        context: ReconstructionContext,
    ) -> ReconstructedMemory:
        """
        Execute the full reconstruction pipeline.
        
        Args:
            context: Reconstruction context with project info and cues
            
        Returns:
            ReconstructedMemory with coherent context for injection
        """
        import time
        start_time = time.time()
        
        warnings = []
        
        # Step 1: SCAN - Gather fragments from all sources
        logger.info(f"Reconstructing context for project: {context.project_name}")
        await self._scan_fragments(context)
        
        if not self._fragments:
            warnings.append("No fragments found for reconstruction")
            return self._create_empty_result(context, warnings, start_time)
        
        logger.info(f"Scanned {len(self._fragments)} fragments")
        
        # Step 2: ACTIVATE - Calculate resonance scores
        self._activate_resonance(context)
        
        # Step 3: EXCITE - Amplify high-resonance fragments
        self._excite_fragments()
        
        # Step 4: EVOLVE - Field dynamics (simplified: sort by activation)
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
            coherence_score=coherence_score,
            fragment_count=len(self._fragments),
            reconstruction_time_ms=elapsed_ms,
            gap_fills=gap_fills,
            warnings=warnings,
        )
    
    # =========================================================================
    # Step 1: Fragment Scanning
    # =========================================================================
    
    async def _scan_fragments(self, context: ReconstructionContext) -> None:
        """Scan all sources for memory fragments."""
        self._fragments = []
        
        # Scan sessions from PostgreSQL/n8n
        await self._scan_sessions(context)
        
        # Scan tasks from Archon
        await self._scan_tasks(context)
        
        # Scan entities from Graphiti (if enabled)
        if self.graphiti_enabled:
            await self._scan_entities(context)
    
    async def _scan_sessions(self, context: ReconstructionContext) -> None:
        """Scan recent sessions from memory system."""
        try:
            # Query n8n recall webhook for recent sessions
            cutoff = datetime.utcnow() - timedelta(
                hours=self.config.RECENT_SESSION_HOURS
            )
            
            payload = {
                "operation": "query",
                "filters": {
                    "project_id": context.project_id,
                    "from_date": cutoff.isoformat(),
                },
                "limit": self.config.MAX_SESSIONS,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.n8n_recall_url,
                    json=payload,
                )
                
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
            logger.warning(f"Failed to scan sessions: {e}")
    
    async def _scan_tasks(self, context: ReconstructionContext) -> None:
        """Scan active tasks from Archon."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get todo tasks
                response = await client.get(
                    f"{self.archon_url}/api/tasks",
                    params={
                        "filter_by": "status",
                        "filter_value": "todo",
                        "per_page": self.config.MAX_TASKS,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tasks = result.get("tasks", [])
                    
                    for task in tasks:
                        fragment = Fragment(
                            fragment_id=task.get("id", ""),
                            fragment_type=FragmentType.TASK,
                            content=task.get("title", ""),
                            summary=task.get("description", ""),
                            strength=self._task_priority_to_strength(
                                task.get("task_order", 50)
                            ),
                            source="archon",
                            metadata={
                                "status": task.get("status"),
                                "feature": task.get("feature"),
                                "project_id": task.get("project_id"),
                            },
                        )
                        self._fragments.append(fragment)
                
                # Also get in-progress tasks
                response = await client.get(
                    f"{self.archon_url}/api/tasks",
                    params={
                        "filter_by": "status",
                        "filter_value": "doing",
                        "per_page": 5,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tasks = result.get("tasks", [])
                    
                    for task in tasks:
                        fragment = Fragment(
                            fragment_id=task.get("id", ""),
                            fragment_type=FragmentType.TASK,
                            content=task.get("title", ""),
                            summary=task.get("description", ""),
                            strength=0.9,  # In-progress tasks are high priority
                            source="archon",
                            metadata={
                                "status": "doing",
                                "feature": task.get("feature"),
                                "project_id": task.get("project_id"),
                            },
                        )
                        self._fragments.append(fragment)
                        
        except Exception as e:
            logger.warning(f"Failed to scan tasks from Archon: {e}")
    
    async def _scan_entities(self, context: ReconstructionContext) -> None:
        """Scan key entities from Graphiti."""
        try:
            from api.services.graphiti_service import get_graphiti_service
            
            graphiti = await get_graphiti_service()
            
            # Search for entities related to this project
            results = await graphiti.search(
                query=context.project_name,
                limit=self.config.MAX_ENTITIES,
            )
            
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
            logger.warning(f"Failed to scan entities from Graphiti: {e}")
    
    # =========================================================================
    # Step 2: Resonance Activation
    # =========================================================================
    
    def _activate_resonance(self, context: ReconstructionContext) -> None:
        """Calculate resonance scores for all fragments."""
        for fragment in self._fragments:
            # Calculate cue resonance
            cue_resonance = self._calculate_cue_resonance(fragment, context.cues)
            
            # Calculate context resonance
            context_resonance = self._calculate_context_resonance(
                fragment, context
            )
            
            # Calculate network resonance
            network_resonance = self._calculate_network_resonance(fragment)
            
            # Combine using weights
            fragment.resonance_score = (
                cue_resonance * self.config.CUE_RESONANCE_WEIGHT +
                context_resonance * self.config.CONTEXT_RESONANCE_WEIGHT +
                network_resonance * self.config.NETWORK_RESONANCE_WEIGHT
            )
            
            # Activate if above threshold
            if fragment.resonance_score >= self.config.RESONANCE_ACTIVATION_THRESHOLD:
                fragment.activation = fragment.resonance_score
    
    def _calculate_cue_resonance(
        self, 
        fragment: Fragment, 
        cues: list[str]
    ) -> float:
        """Calculate resonance between fragment and explicit cues."""
        if not cues:
            return 0.5  # Neutral if no cues
        
        content = (fragment.content + " " + (fragment.summary or "")).lower()
        
        matches = sum(1 for cue in cues if cue.lower() in content)
        return min(matches / len(cues), 1.0)
    
    def _calculate_context_resonance(
        self,
        fragment: Fragment,
        context: ReconstructionContext,
    ) -> float:
        """Calculate resonance with current project context."""
        score = 0.0
        
        # Check project match
        if fragment.metadata.get("project_id") == context.project_id:
            score += 0.5
        
        # Check project name in content
        if context.project_name.lower() in fragment.content.lower():
            score += 0.3
        
        # Recency bonus
        if fragment.created_at:
            hours_ago = (datetime.utcnow() - fragment.created_at).total_seconds() / 3600
            if hours_ago < 24:
                score += 0.2
            elif hours_ago < 72:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_network_resonance(self, fragment: Fragment) -> float:
        """Calculate resonance based on connections to other activated fragments."""
        if not fragment.connections:
            return 0.3  # Base network score
        
        # Count connections to other fragments
        connected_activations = []
        for conn_id in fragment.connections:
            for other in self._fragments:
                if other.fragment_id == conn_id and other.activation > 0:
                    connected_activations.append(other.activation)
        
        if not connected_activations:
            return 0.3
        
        return min(sum(connected_activations) / len(connected_activations) + 0.3, 1.0)
    
    # =========================================================================
    # Step 3: Excitation
    # =========================================================================
    
    def _excite_fragments(self, amplification: float = 1.3) -> None:
        """Amplify high-resonance fragments."""
        for fragment in self._fragments:
            if fragment.resonance_score >= self.config.HIGH_RESONANCE_THRESHOLD:
                fragment.activation *= amplification
                fragment.activation = min(fragment.activation, 1.0)
    
    # =========================================================================
    # Step 4: Field Evolution
    # =========================================================================
    
    def _evolve_field(self, steps: int = 3) -> None:
        """Evolve field dynamics - simplified as sorting by activation."""
        # In a full implementation, this would run attractor dynamics
        # For MVP, we sort by activation * strength
        self._fragments.sort(
            key=lambda f: f.activation * f.strength,
            reverse=True
        )
    
    # =========================================================================
    # Step 5: Pattern Extraction
    # =========================================================================
    
    def _extract_patterns(self) -> dict[str, list[dict]]:
        """Extract coherent patterns from activated field."""
        extracted = {
            "sessions": [],
            "tasks": [],
            "entities": [],
            "decisions": [],
        }
        
        for fragment in self._fragments:
            if fragment.activation < self.config.RESONANCE_ACTIVATION_THRESHOLD:
                continue
            
            if fragment.fragment_type == FragmentType.SESSION:
                extracted["sessions"].append({
                    "id": fragment.fragment_id,
                    "summary": fragment.summary or fragment.content[:200],
                    "date": fragment.created_at.strftime("%Y-%m-%d") if fragment.created_at else "Unknown",
                    "resonance": fragment.resonance_score,
                })
            
            elif fragment.fragment_type == FragmentType.TASK:
                extracted["tasks"].append({
                    "id": fragment.fragment_id,
                    "title": fragment.content,
                    "status": fragment.metadata.get("status", "todo"),
                    "feature": fragment.metadata.get("feature", ""),
                    "resonance": fragment.resonance_score,
                })
            
            elif fragment.fragment_type == FragmentType.ENTITY:
                extracted["entities"].append({
                    "id": fragment.fragment_id,
                    "name": fragment.content,
                    "type": fragment.metadata.get("type", "entity"),
                    "resonance": fragment.resonance_score,
                })
            
            elif fragment.fragment_type == FragmentType.DECISION:
                extracted["decisions"].append({
                    "id": fragment.fragment_id,
                    "content": fragment.content,
                    "date": fragment.created_at.strftime("%Y-%m-%d") if fragment.created_at else "Unknown",
                    "resonance": fragment.resonance_score,
                })
        
        # Limit each category
        extracted["sessions"] = extracted["sessions"][:self.config.MAX_SESSIONS]
        extracted["tasks"] = extracted["tasks"][:self.config.MAX_TASKS]
        extracted["entities"] = extracted["entities"][:self.config.MAX_ENTITIES]
        extracted["decisions"] = extracted["decisions"][:5]
        
        return extracted
    
    # =========================================================================
    # Steps 6-7: Gap Identification and Filling
    # =========================================================================
    
    def _identify_and_fill_gaps(
        self,
        extracted: dict[str, list[dict]],
        context: ReconstructionContext,
    ) -> list[dict]:
        """Identify and fill gaps in extracted patterns."""
        gap_fills = []
        
        # Check for missing session context
        if not extracted["sessions"]:
            gap_fills.append({
                "gap_type": "missing_sessions",
                "fill": "No recent session history found for this project.",
                "confidence": 0.9,
            })
        
        # Check for missing tasks
        if not extracted["tasks"]:
            gap_fills.append({
                "gap_type": "missing_tasks",
                "fill": "No active tasks found. Consider checking Archon for task status.",
                "confidence": 0.9,
            })
        
        return gap_fills
    
    # =========================================================================
    # Step 8: Coherence Validation
    # =========================================================================
    
    def _validate_coherence(self, extracted: dict[str, list[dict]]) -> float:
        """Calculate coherence score for extracted patterns."""
        scores = []
        
        # Check if we have content in each category
        if extracted["sessions"]:
            scores.append(0.8)
        if extracted["tasks"]:
            scores.append(0.9)
        if extracted["entities"]:
            scores.append(0.7)
        
        # Check resonance distribution
        all_resonances = []
        for category in extracted.values():
            for item in category:
                if "resonance" in item:
                    all_resonances.append(item["resonance"])
        
        if all_resonances:
            avg_resonance = sum(all_resonances) / len(all_resonances)
            scores.append(avg_resonance)
        
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def _create_empty_result(
        self,
        context: ReconstructionContext,
        warnings: list[str],
        start_time: float,
    ) -> ReconstructedMemory:
        """Create empty result when no fragments found."""
        import time
        elapsed_ms = (time.time() - start_time) * 1000
        
        return ReconstructedMemory(
            project_summary=context.project_name,
            recent_sessions=[],
            active_tasks=[],
            key_entities=[],
            recent_decisions=[],
            coherence_score=0.0,
            fragment_count=0,
            reconstruction_time_ms=elapsed_ms,
            warnings=warnings,
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
    
    def _task_priority_to_strength(self, task_order: int) -> float:
        """Convert task_order (0-100, higher = more priority) to strength."""
        return min(task_order / 100, 1.0)


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
