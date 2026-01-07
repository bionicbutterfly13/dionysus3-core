"""
Epistemic field service for luminosity metrics.
"""

from __future__ import annotations

from typing import Dict, Optional

from api.models.beautiful_loop import EpistemicState
from api.services.bayesian_binder import get_bayesian_binder
from api.services.hyper_model_service import get_hyper_model_service
from api.services.unified_reality_model import get_unified_reality_model


class EpistemicFieldService:
    """Computes epistemic depth and luminosity factors."""

    def __init__(self):
        """Initialize tracking state for sharing depth."""
        self._layer_sharing_depth: dict[str, int] = {}  # Track sharing depth per layer

    def track_sharing_depth(self, layer_id: str, depth: int) -> None:
        """
        Track recursive sharing depth for a layer.

        Args:
            layer_id: ID of the inference layer
            depth: Number of recursive precision exchanges

        FR-017: Track recursive sharing depth (how many layers exchange precision information).
        """
        self._layer_sharing_depth[layer_id] = depth

    def get_sharing_depth(self, layer_id: str) -> int:
        """Get the current sharing depth for a layer."""
        return self._layer_sharing_depth.get(layer_id, 0)

    def classify_process(self, process_id: str, is_bound: bool) -> str:
        """
        Classify process as 'aware' (bound) or 'transparent' (unbound).

        Args:
            process_id: ID of the process to classify
            is_bound: Whether process is bound into consciousness

        Returns:
            "aware" if bound, "transparent" if unbound

        FR-019: Distinguish between "aware" processes (bound) and "transparent" processes (unbound).
        """
        return "aware" if is_bound else "transparent"

    def get_epistemic_state(self) -> EpistemicState:
        hyper_model = get_hyper_model_service()
        binder = get_bayesian_binder()
        reality_model = get_unified_reality_model().get_model()

        profile = hyper_model.get_current_profile()
        active_bindings = [inf.inference_id for inf in reality_model.bound_inferences]

        luminosity_factors: Dict[str, float] = {
            "hyper_model_active": 1.0 if profile else 0.0,
            "bidirectional_sharing": self._sharing_factor(profile),
            "meta_precision_level": profile.meta_precision if profile else 0.0,
            "binding_coherence": reality_model.coherence_score,
        }

        depth_score = (
            sum(luminosity_factors.values()) / len(luminosity_factors)
            if luminosity_factors
            else 0.0
        )

        return EpistemicState(
            depth_score=depth_score,
            reality_model_coherence=reality_model.coherence_score,
            active_bindings=active_bindings,
            transparent_processes=binder.last_rejected_ids,
            luminosity_factors=luminosity_factors,
        )

    def _sharing_factor(self, profile) -> float:
        if not profile:
            return 0.0
        layers = profile.layer_precisions
        if not layers:
            return 0.0
        active = [value for value in layers.values() if value >= 0.5]
        return len(active) / max(1, len(layers))


_epistemic_field_service: Optional[EpistemicFieldService] = None


def get_epistemic_field_service() -> EpistemicFieldService:
    global _epistemic_field_service
    if _epistemic_field_service is None:
        _epistemic_field_service = EpistemicFieldService()
    return _epistemic_field_service
