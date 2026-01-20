"""
Unified Reality Model service for Beautiful Loop.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import math

from api.models.beautiful_loop import BoundInference, ResonanceSignal, UnifiedRealityModel
from api.models.metacognitive_particle import MetacognitiveParticle


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) != len(vec_b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / math.sqrt(norm_a * norm_b)


class UnifiedRealityModelService:
    """Maintains a unified reality model state container."""

    def __init__(self):
        self._model = UnifiedRealityModel()

    def get_model(self) -> UnifiedRealityModel:
        return self._model

    def update_context(self, context: Dict[str, Any], cycle_id: Optional[str] = None) -> None:
        self._model.current_context = context
        self._model.cycle_id = cycle_id
        self._touch()

    def update_belief_states(self, belief_states: List[Any]) -> None:
        self._model.belief_states = belief_states
        self._touch()

    def update_active_inference_states(self, states: List[Any]) -> None:
        self._model.active_inference_states = states
        self._touch()

    def update_metacognitive_particles(self, particles: List[Any]) -> None:
        self._model.metacognitive_particles = particles
        self._touch()

    def update_bound_inferences(self, bound_inferences: List[BoundInference], cycle_id: Optional[str] = None) -> None:
        self._model.bound_inferences = bound_inferences
        self._model.cycle_id = cycle_id or self._model.cycle_id
        self._model.coherence_score = self._compute_coherence(bound_inferences)
        self._model.epistemic_affordances = self._derive_affordances(bound_inferences)
        self._touch()

    def _compute_coherence(self, bound_inferences: List[BoundInference]) -> float:
        if len(bound_inferences) < 2:
            return 1.0 if bound_inferences else 0.0
        similarities: List[float] = []
        for idx, inf_a in enumerate(bound_inferences):
            for inf_b in bound_inferences[idx + 1:]:
                similarities.append(_cosine_similarity(inf_a.embedding, inf_b.embedding))
        if not similarities:
            return 0.0
        avg = sum(similarities) / len(similarities)
        return max(0.0, min(1.0, (avg + 1.0) / 2.0))

    def _derive_affordances(self, bound_inferences: Iterable[BoundInference]) -> List[str]:
        affordances: List[str] = []
        for inference in bound_inferences:
            content = inference.content or {}
            for key in ("affordance", "action", "next_action", "decision"):
                value = content.get(key)
                if isinstance(value, str) and value.strip():
                    affordances.append(value.strip())
        return sorted(set(affordances))

    def update_resonance(self, signal: ResonanceSignal) -> None:
        """Store resonance signal in model (FR-020, FR-021)."""
        self._model.resonance = signal
        self._touch()

    def add_metacognitive_particle(self, particle: MetacognitiveParticle) -> None:
        """Append metacognitive particle to accumulator (FR-030, FR-031)."""
        self._model.metacognitive_particles.append(particle)
        self._touch()

    def clear_cycle_state(self) -> None:
        """Reset transient state for new cycle (keeps bound_inferences and context)."""
        self._model.metacognitive_particles = []
        self._model.active_inference_states = []
        self._model.resonance = None
        self._touch()

    def _touch(self) -> None:
        self._model.last_updated = datetime.utcnow()


_unified_reality_model: Optional[UnifiedRealityModelService] = None


def get_unified_reality_model() -> UnifiedRealityModelService:
    global _unified_reality_model
    if _unified_reality_model is None:
        _unified_reality_model = UnifiedRealityModelService()
    return _unified_reality_model
