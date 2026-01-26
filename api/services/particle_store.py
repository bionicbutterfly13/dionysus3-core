import logging
import asyncio
from typing import List, Optional
from api.models.metacognitive_particle import MetacognitiveParticle
from api.services.graphiti_service import get_graphiti_service, GraphitiService

logger = logging.getLogger("dionysus.particle_store")

class ParticleStore:
    """
    In-memory working memory for Metacognitive Particles.
    
    Acts as a short-term buffer for active thoughts.
    Supports decay (forgetting) and retrieval by resonance.
    
    INTEGRATION:
    - Host: ConsciousnessManager
    - Persistence: Graphiti (Neo4j) for high-resonance particles/
    """
    
    def __init__(self, capacity: int = 50, graphiti: Optional[GraphitiService] = None):
        self._particles: List[MetacognitiveParticle] = []
        self._capacity = capacity
        # Lazy load if not provided, to avoid circular import loops at module level
        self._graphiti = graphiti 

    async def add_particle(self, particle: MetacognitiveParticle) -> None:
        """
        Add a particle to working memory. 
        Enforces capacity via resonance eviction.
        Triggers async persistence if resonance is high.
        """
        if len(self._particles) >= self._capacity:
            self._evict_low_resonance()
        
        self._particles.append(particle)
        # Sort by resonance desc
        self._sort_particles()
        
        # PERSISTENCE CHECK (The Basin)
        if particle.resonance_score >= 0.8:
            await self._persist_to_graphiti(particle)

    async def _persist_to_graphiti(self, particle: MetacognitiveParticle):
        """Persist high-resonance particle to the Knowledge Graph."""
        try:
            if not self._graphiti:
                self._graphiti = await get_graphiti_service()
            
            node_data = particle.to_graphiti_node()
            # We use 'add_node' from Graphiti. 
            # Note: GraphitiService usually expects 'name' and 'type'.
            await self._graphiti.add_node(node_data)
            logger.info(f"Persisted Resonant Particle: {particle.id} (Score: {particle.resonance_score:.2f})")
        except Exception as e:
            logger.error(f"Failed to persist particle {particle.id}: {e}")

    def get_active_particles(self, min_resonance: float = 0.1) -> List[MetacognitiveParticle]:
        """Get currently active particles above a resonance threshold."""
        return [p for p in self._particles if p.is_active and p.resonance_score >= min_resonance]

    def decay_all(self, rate: float = 0.05) -> int:
        """Apply decay to all particles. Returns number of particles that realized (died)."""
        died = 0
        for p in self._particles:
            was_active = p.is_active
            p.decay(rate)
            if was_active and not p.is_active:
                died += 1
        
        # Cleanup inactive
        self._cleanup()
        return died

    def _evict_low_resonance(self):
        """Remove the lowest resonance particle to make room."""
        if not self._particles:
            return
        # Assumes sorted desc, so last is lowest
        popped = self._particles.pop()
        logger.debug(f"Evicted particle: {popped.content[:20]}... (Res: {popped.resonance_score:.2f})")

    def _sort_particles(self):
        """Sort particles by resonance (High to Low)."""
        self._particles.sort(key=lambda p: p.resonance_score, reverse=True)

    def _cleanup(self):
        """Remove inactive particles from store."""
        initial_count = len(self._particles)
        self._particles = [p for p in self._particles if p.is_active]
        removed = initial_count - len(self._particles)
        if removed > 0:
            logger.debug(f"Cleaned up {removed} inactive particles.")
            
# Singleton
_store_instance: Optional[ParticleStore] = None

def get_particle_store() -> ParticleStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = ParticleStore()
    return _store_instance
