"""
Bayesian binding service for Beautiful Loop.
"""

from __future__ import annotations

from typing import List, Optional

from api.models.beautiful_loop import (
    BindingConfig,
    BindingEvaluationResponse,
    BoundInference,
    InferenceCandidate,
    PrecisionProfile,
)
from api.services.unified_reality_model import get_unified_reality_model, _cosine_similarity


class BayesianBinder:
    """Selects bound inferences via precision-weighted competition."""

    def __init__(self, config: Optional[BindingConfig] = None):
        self.config = config or BindingConfig()
        self._last_rejected_ids: List[str] = []

    @property
    def last_rejected_ids(self) -> List[str]:
        return self._last_rejected_ids

    def evaluate(
        self,
        candidates: List[InferenceCandidate],
        precision_profile: Optional[PrecisionProfile] = None,
        binding_capacity: Optional[int] = None,
        cycle_id: Optional[str] = None,
    ) -> BindingEvaluationResponse:
        reality_model = get_unified_reality_model().get_model()
        bound_candidates: List[BoundInference] = []
        rejected_ids: List[str] = []

        capacity = binding_capacity or self.config.default_capacity

        for candidate in candidates:
            precision_score = self._precision_score(candidate, precision_profile)
            coherence_score = self._coherence_score(candidate, reality_model.bound_inferences)
            uncertainty_reduction = self._estimate_uncertainty_reduction(
                candidate,
                precision_score,
                coherence_score,
            )

            meets_thresholds = (
                precision_score >= self.config.precision_threshold
                and coherence_score >= self.config.coherence_threshold
                and uncertainty_reduction > 0.0
            )

            if not meets_thresholds:
                rejected_ids.append(candidate.inference_id)
                continue

            bound_candidates.append(
                BoundInference(
                    inference_id=candidate.inference_id,
                    source_layer=candidate.source_layer,
                    content=candidate.content,
                    embedding=candidate.embedding,
                    precision_score=precision_score,
                    coherence_score=coherence_score,
                    uncertainty_reduction=uncertainty_reduction,
                    cycle_id=cycle_id,
                )
            )

        bound_candidates.sort(key=lambda item: item.binding_strength, reverse=True)
        selected = bound_candidates[:capacity]
        rejected_ids.extend(
            [item.inference_id for item in bound_candidates[capacity:]]
        )

        self._last_rejected_ids = rejected_ids
        if selected:
            get_unified_reality_model().update_bound_inferences(selected, cycle_id=cycle_id)

        average_strength = (
            sum(item.binding_strength for item in selected) / len(selected)
            if selected
            else 0.0
        )

        return BindingEvaluationResponse(
            bound_inferences=selected,
            rejected_count=len(rejected_ids),
            average_binding_strength=average_strength,
        )

    def _precision_score(
        self,
        candidate: InferenceCandidate,
        precision_profile: Optional[PrecisionProfile],
    ) -> float:
        if not precision_profile:
            return 0.5
        base = precision_profile.layer_precisions.get(candidate.source_layer, 0.5)
        return max(0.0, min(1.0, base * precision_profile.meta_precision))

    def _coherence_score(
        self,
        candidate: InferenceCandidate,
        bound_inferences: List[BoundInference],
    ) -> float:
        if not bound_inferences:
            return 1.0
        similarities = [
            _cosine_similarity(candidate.embedding, bound.embedding)
            for bound in bound_inferences
        ]
        if not similarities:
            return 0.0
        avg = sum(similarities) / len(similarities)
        return max(0.0, min(1.0, (avg + 1.0) / 2.0))

    def _estimate_uncertainty_reduction(
        self,
        candidate: InferenceCandidate,
        precision_score: float,
        coherence_score: float,
    ) -> float:
        content = candidate.content or {}
        if isinstance(content, dict):
            if "uncertainty_reduction" in content:
                return float(content.get("uncertainty_reduction") or 0.0)
            if "entropy_before" in content and "entropy_after" in content:
                before = float(content.get("entropy_before") or 0.0)
                after = float(content.get("entropy_after") or 0.0)
                if before > 0:
                    return (before - after) / before
                return 0.0
            if "prediction_error" in content:
                error = float(content.get("prediction_error") or 0.0)
                return 1.0 / (1.0 + max(0.0, error))
            if "surprise" in content:
                surprise = float(content.get("surprise") or 0.0)
                return 1.0 / (1.0 + max(0.0, surprise))
        # Fall back to a coherence/precision blend when no uncertainty signal exists.
        return max(0.0, min(1.0, 1.0 - ((1.0 - coherence_score) * (1.0 - precision_score))))


_binder: Optional[BayesianBinder] = None


def get_bayesian_binder() -> BayesianBinder:
    global _binder
    if _binder is None:
        _binder = BayesianBinder()
    return _binder
