"""
Dream Service (Subconscious Maintenance)
Feature: 069-hexis-subconscious-integration

Implements 'Subconscious Maintenance' logic inspired by Hexis.
- Clusters memories into Neighborhoods.
- Decays and updates Drive states.
- Prunes stale or disconnected nodes.
"""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from api.models.hexis_ontology import Neighborhood, NeighborhoodType, DriveState, DriveType, SubconsciousState
from api.services.graphiti_service import GraphitiService

logger = logging.getLogger(__name__)

class DreamService:
    """
    Manages background cognitive maintenance tasks.
    """
    
    def __init__(self, graphiti: GraphitiService):
        self.graphiti = graphiti
        self._state = SubconsciousState(
            drives={
                d: DriveState(drive_type=d, level=0.5) 
                for d in DriveType
            }
        )

    async def run_maintenance_cycle(self) -> dict:
        """
        Executes a full maintenance cycle (The "Dream").
        """
        logger.info("Starting Subconscious Maintenance Cycle...")
        
        # 1. Update Drives (Decay)
        self._decay_drives()
        
        # 2. Cluster Neighborhoods (Heavy Op)
        neighborhoods = await self._supervise_clustering()
        
        # 3. Prune Ghosts (Garbage Collection)
        pruned = await self._prune_disconnected_nodes()
        
        self._state.last_maintenance = datetime.utcnow()
        
        return {
            "drives": {k.value: v.level for k,v in self._state.drives.items()},
            "neighborhoods_updated": len(neighborhoods),
            "nodes_pruned": pruned
        }

    def _decay_drives(self):
        """
        Apply temporal decay to all drives.
        """
        now = datetime.utcnow()
        for drive in self._state.drives.values():
            hours_passed = (now - drive.last_updated).total_seconds() / 3600.0
            if hours_passed > 0:
                decay = drive.decay_rate * hours_passed
                drive.level = max(0.0, drive.level - decay)
                drive.last_updated = now

    async def _supervise_clustering(self) -> List[Neighborhood]:
        """
        Identify semantic clusters and reify them as Neighborhood nodes.
        Reference: Hexis `memory_neighborhoods` logic.
        """
        # TODO: Implement vector-based clustering using Graphiti's search
        # For Phase 1, we will stub this with a simple "Recent Topic" cluster
        
        # Placeholder: Retrieve recent concepts and group by generic 'topic'
        # In a real implementation, this would use sklearn.cluster.DBSCAN on embeddings
        return []

    async def _prune_disconnected_nodes(self) -> int:
        """
        Archive or delete nodes with low utility and high uncertainty.
        Reference: Hexis `subconscious_maintenance`.
        """
        # TODO: Implement Cypher query to find orphan nodes
        return 0
    
    async def generate_guidance(self, context_summary: str = "") -> str:
        """
        Generates the full 'Subconscious Context' by hydrating all Memory Blocks.
        """
        lines = []
        
        # 1. Update the 'Guidance' Block dynamically
        guidance_lines = []
        urgent_drives = [d for d in self._state.drives.values() if d.level < 0.3]
        
        if urgent_drives:
            guidance_lines.append("## Drive Alerts")
            for d in urgent_drives:
                 guidance_lines.append(f"- **{d.drive_type.value.upper()}** is low ({d.level:.2f}). consider actions to restore.")
        
        if not self._state.last_maintenance or (datetime.utcnow() - self._state.last_maintenance).total_seconds() > 3600:
             guidance_lines.append("\n> [!TIP]\n> Subconscious needs maintenance cycle (Dream).")
             
        self._state.blocks["guidance"].value = "\n".join(guidance_lines) if guidance_lines else "(No active guidance)"

        if self._state.active_goals:
            self._state.blocks["pending_items"].value = "\n".join([f"- [{g.priority.value.upper()}] {g.title}" for g in self._state.active_goals])

        # 2. Update 'Project Context' (Stub for Graphiti Query)
        if context_summary:
            self._state.blocks["project_context"].value = f"Context: {context_summary}"
            
        # 3. Spontaneous Recall (Serendipity)
        # Using Graphiti, we would find nodes with high 'surprise' or 'resonance' but low current activation
        # Stub logic:
        spontaneous = "No spontaneous memories surfaced."
        if self._state.global_sentiment > 0.5:
             spontaneous = "Surfaced Memory: 'The initial breakthrough on the Daedalus project.'"
        
        # We can append this to guidance or a new block? Let's assume Letta doesn't have a 'spontaneous' block standard, 
        # so we append to Guidance or Project Context. Let's create a dynamic section in Guidance.
        if spontaneous != "No spontaneous memories surfaced.":
            self._state.blocks["guidance"].value += f"\n\n> [!NOTE]\n> **Spontaneous Recall**: {spontaneous}"

        # 3. Render All Blocks (Letta Style)
        lines.append("# Subconscious Context (Dionysus)")
        
        # Identity / Drives First
        lines.append("## System Drives")
        for d in self._state.drives.values():
            status = "Satisfied" if d.level > 0.7 else ("Need Action" if d.level < 0.3 else "Neutral")
            lines.append(f"- **{d.drive_type.value.upper()}**: {d.level:.2f} [{status}]")

        # Render Blocks
        for label, block in self._state.blocks.items():
            lines.append(f"\n## {label.upper().replace('_', ' ')}")
            lines.append(f"_{block.description}_")
            lines.append(f"\n{block.value}")
            
        return "\n".join(lines)

    async def get_subconscious_state(self) -> SubconsciousState:

        return self._state

# Singleton Management
_dream_service: Optional[DreamService] = None

async def get_dream_service() -> DreamService:
    global _dream_service
    if _dream_service is None:
        graphiti = await GraphitiService.get_instance()
        _dream_service = DreamService(graphiti)
    return _dream_service
