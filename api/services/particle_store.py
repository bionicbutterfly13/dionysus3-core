import logging
from typing import List, Optional
from api.models.metacognitive_particle import MetacognitiveParticle

logger = logging.getLogger("dionysus.particle_store")

class ParticleStore:
    """
    In-memory working memory for Metacognitive Particles.
    
    Acts as a short-term buffer for active thoughts.
    Supports decay (forgetting) and retrieval by resonance.
    """
    
    def __init__(self, capacity: int = 50):
        self._particles: List[MetacognitiveParticle] = []
        self._capacity = capacity

    def add_particle(self, particle: MetacognitiveParticle) -> None:
        """Add a particle to working memory. Enforces capacity via resonance eviction."""
        if len(self._particles) >= self._capacity:
            self._evict_low_resonance()
        
        self._particles.append(particle)
        # Sort by resonance desc
        self._sort_particles()

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
