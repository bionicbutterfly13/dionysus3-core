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
        Apply temporal decay to all drives, modulated by system arousal.
        Prevents 'debt spirals' when the system is offline by scaling decay by arousal.
        """
        now = datetime.utcnow()
        # Arousal acts as a metabolic scaler. 
        # If arousal is 0, decay is minimal (hibernation).
        # Default to 0.5 (normal operation) if not specified.
        metabolic_rate = max(0.1, self._state.arousal) 
        
        for drive in self._state.drives.values():
            hours_passed = (now - drive.last_updated).total_seconds() / 3600.0
            if hours_passed > 0:
                # Actual decay = (Rate * Time) * MetabolicScaler
                decay = (drive.decay_rate * hours_passed) * metabolic_rate
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
        # Find a resonant but currently inactive node to surface (Serendipity)
        spontaneous = "No spontaneous memories surfaced."
        try:
             # Find highly connected entities that haven't been mentioned in the last 5 episodes
             # or nodes with a high 'resonance' score (if we had one, for now we use degree)
             cypher = """
             MATCH (e:Entity)
             WHERE NOT (e)-[:MENTIONED_IN]->(:Episode) # Simplified: ignored recently mentioned
             WITH e, COUNT { (e)--() } as degree
             ORDER BY degree DESC, e.created_at DESC
             LIMIT 1
             RETURN e.name as name, e.summary as summary
             """
             results = await self.graphiti.execute_cypher(cypher)
             if results and results[0].get("name"):
                  name = results[0]["name"]
                  summary = results[0].get("summary", "No details available.")
                  spontaneous = f"'{name}' - {summary}"
        except Exception as e:
             logger.warning(f"Spontaneous recall query failed: {e}")
        
        if spontaneous != "No spontaneous memories surfaced.":
            self._state.blocks["guidance"].value += f"\n\n> [!NOTE]\n> **Spontaneous Recall**: {spontaneous}"

        # 4. Render All Blocks (Letta Style)
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

    async def save_state(self):
        """
        Persist the subconscious state to Neo4j.
        """
        logger.info("Persisting Subconscious State to Neo4j...")
        
        # 1. Prepare properties for the :Subconscious node
        props = {
            "last_maintenance": self._state.last_maintenance.isoformat() if self._state.last_maintenance else None,
            "global_sentiment": self._state.global_sentiment,
            "arousal": self._state.arousal,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Flatten drives into properties: drive_curiosity_level, etc.
        for drive_type, state in self._state.drives.items():
            props[f"drive_{drive_type.value}_level"] = state.level
            props[f"drive_{drive_type.value}_last_updated"] = state.last_updated.isoformat()
            
        # 2. Persist to Neo4j
        cypher = """
        MERGE (s:Subconscious {singleton_id: 'main'})
        SET s += $props
        """
        try:
            await self.graphiti.execute_cypher(cypher, {"props": props})
            
            # 3. Persist Blocks as connected nodes
            for label, block in self._state.blocks.items():
                block_cypher = """
                MATCH (s:Subconscious {singleton_id: 'main'})
                MERGE (b:MemoryBlock {label: $label})
                SET b.value = $value,
                    b.description = $description,
                    b.last_updated = datetime($last_updated)
                MERGE (s)-[:HAS_BLOCK]->(b)
                """
                await self.graphiti.execute_cypher(block_cypher, {
                    "label": label,
                    "value": block.value,
                    "description": block.description,
                    "last_updated": block.last_updated.isoformat()
                })
        except Exception as e:
            logger.error(f"Failed to persist subconscious state: {e}")

    async def load_state(self):
        """
        Load the subconscious state from Neo4j.
        """
        logger.info("Loading Subconscious State from Neo4j...")
        cypher = "MATCH (s:Subconscious {singleton_id: 'main'}) RETURN s"
        try:
            results = await self.graphiti.execute_cypher(cypher)
            if results:
                s_props = results[0]
                self._state.global_sentiment = s_props.get("global_sentiment", 0.0)
                self._state.arousal = s_props.get("arousal", 0.5)
                if s_props.get("last_maintenance"):
                    self._state.last_maintenance = datetime.fromisoformat(s_props["last_maintenance"])
                
                # Load drives
                for drive_type in DriveType:
                    level_key = f"drive_{drive_type.value}_level"
                    updated_key = f"drive_{drive_type.value}_last_updated"
                    if level_key in s_props:
                        self._state.drives[drive_type].level = s_props[level_key]
                    if updated_key in s_props:
                        self._state.drives[drive_type].last_updated = datetime.fromisoformat(s_props[updated_key])
                        
            # Load blocks
            block_cypher = "MATCH (:Subconscious {singleton_id: 'main'})-[:HAS_BLOCK]->(b:MemoryBlock) RETURN b"
            block_results = await self.graphiti.execute_cypher(block_cypher)
            for row in block_results:
                label = row.get("label")
                if label in self._state.blocks:
                    self._state.blocks[label].value = row.get("value", "")
                    self._state.blocks[label].description = row.get("description")
                    if row.get("last_updated"):
                         # Neo4j DateTime normalize to string via _normalize_neo4j_value
                         val = row["last_updated"]
                         self._state.blocks[label].last_updated = datetime.fromisoformat(val) if isinstance(val, str) else val

        except Exception as e:
            logger.error(f"Failed to load subconscious state: {e}")

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
