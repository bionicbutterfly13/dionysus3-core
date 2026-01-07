"""
Hyper-model precision forecasting and learning service.
"""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from api.models.beautiful_loop import HyperModelConfig, PrecisionError, PrecisionProfile
from api.utils.event_bus import get_event_bus
from api.services.embedding import EMBEDDING_DIMENSIONS

logger = logging.getLogger("dionysus.hyper_model")


@dataclass
class _ForecastContext:
    context: Dict[str, Any]
    internal_states: Dict[str, Any]
    recent_errors: List[PrecisionError]


class HyperModelService:
    """Forecasts and updates precision profiles (phi)."""

    def __init__(self, config: Optional[HyperModelConfig] = None):
        self.config = config or HyperModelConfig()
        self._current_profile: Optional[PrecisionProfile] = None
        self._layer_bias: Dict[str, float] = {layer: 0.0 for layer in self.config.default_layers}
        self._modality_bias: Dict[str, float] = {mod: 0.0 for mod in self.config.default_modalities}
        self._error_history: List[PrecisionError] = []
        self._last_context: Optional[_ForecastContext] = None

    def get_current_profile(self) -> PrecisionProfile:
        if self._current_profile is None:
            self._current_profile = self.forecast_precision_profile({}, {})
        return self._current_profile

    def forecast_precision_profile(
        self,
        context: Dict[str, Any],
        internal_states: Optional[Dict[str, Any]] = None,
        recent_errors: Optional[List[PrecisionError]] = None,
    ) -> PrecisionProfile:
        internal_states = internal_states or {}
        recent_errors = recent_errors or []

        focus = self._infer_focus(context)
        temporal_depth = self._infer_temporal_depth(context)

        layer_precisions = self._base_layer_precisions(focus, context)
        modality_precisions = self._base_modality_precisions(focus, context)

        layer_precisions = self._apply_biases(layer_precisions, self._layer_bias)
        modality_precisions = self._apply_biases(modality_precisions, self._modality_bias)

        if recent_errors:
            layer_precisions = self._apply_recent_errors(layer_precisions, recent_errors)

        meta_precision = self._infer_meta_precision(recent_errors)
        context_embedding = self._hash_embedding(context)

        profile = PrecisionProfile(
            layer_precisions=layer_precisions,
            modality_precisions=modality_precisions,
            temporal_depth=temporal_depth,
            meta_precision=meta_precision,
            context_embedding=context_embedding,
        )

        self._current_profile = profile
        self._last_context = _ForecastContext(context=context, internal_states=internal_states, recent_errors=recent_errors)
        return profile

    def record_precision_errors(self, errors: List[PrecisionError]) -> float:
        if not errors:
            return 0.0
        self._error_history.extend(errors)
        if len(self._error_history) > 200:
            self._error_history = self._error_history[-200:]
        _, learning_delta = self.update_hyper_model(errors)
        return learning_delta

    def update_hyper_model(self, errors: List[PrecisionError]) -> Tuple[PrecisionProfile, float]:
        if not errors:
            return self.get_current_profile(), 0.0

        avg_error = sum(err.error_magnitude for err in errors) / len(errors)
        learning_rate = self._bounded_learning_rate(avg_error)

        deltas: List[float] = []
        for error in errors:
            direction = 1.0 if error.error_direction == "under_confident" else -1.0
            delta = direction * error.error_magnitude * learning_rate
            deltas.append(abs(delta))
            self._layer_bias[error.layer_id] = self._clamp_bias(
                self._layer_bias.get(error.layer_id, 0.0) + delta
            )

        learning_delta = sum(deltas) / len(deltas) if deltas else 0.0
        if self._last_context:
            profile = self.forecast_precision_profile(
                self._last_context.context,
                self._last_context.internal_states,
                self._last_context.recent_errors,
            )
        else:
            profile = self.get_current_profile()

        try:
            event_bus = get_event_bus()
            coro = event_bus.emit_system_event(
                source="hyper_model_service",
                event_type="precision_update",
                summary=f"Updated precision profile (delta={learning_delta:.4f})",
                metadata={"learning_delta": learning_delta},
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(coro)
            except RuntimeError:
                asyncio.run(coro)
        except Exception as exc:
            logger.warning(f"Failed to emit precision update event: {exc}")

        return profile, learning_delta

    def create_focused_attention_profile(self) -> PrecisionProfile:
        base_layers = {layer: 0.4 for layer in self.config.default_layers}
        base_layers["reasoning"] = 0.85
        base_layers["perception"] = 0.75
        base_modalities = {mod: 0.4 for mod in self.config.default_modalities}
        base_modalities["semantic"] = 0.85
        base_modalities["procedural"] = 0.6
        profile = PrecisionProfile(
            layer_precisions=base_layers,
            modality_precisions=base_modalities,
            temporal_depth=0.4,
            meta_precision=0.7,
            context_embedding=self._hash_embedding({"preset": "focused_attention"}),
        )
        self._current_profile = profile
        return profile

    def create_open_awareness_profile(self) -> PrecisionProfile:
        base_layers = {layer: 0.55 for layer in self.config.default_layers}
        base_modalities = {mod: 0.55 for mod in self.config.default_modalities}
        profile = PrecisionProfile(
            layer_precisions=base_layers,
            modality_precisions=base_modalities,
            temporal_depth=0.7,
            meta_precision=0.55,
            context_embedding=self._hash_embedding({"preset": "open_awareness"}),
        )
        self._current_profile = profile
        return profile

    def create_minimal_phenomenal_profile(self) -> PrecisionProfile:
        base_layers = {layer: 0.2 for layer in self.config.default_layers}
        base_modalities = {mod: 0.2 for mod in self.config.default_modalities}
        profile = PrecisionProfile(
            layer_precisions=base_layers,
            modality_precisions=base_modalities,
            temporal_depth=0.5,
            meta_precision=0.9,
            context_embedding=self._hash_embedding({"preset": "minimal_phenomenal"}),
        )
        self._current_profile = profile
        return profile

    def apply_preset_profile(self, preset_name: str) -> PrecisionProfile:
        presets = {
            "focused_attention": self.create_focused_attention_profile,
            "open_awareness": self.create_open_awareness_profile,
            "minimal_phenomenal": self.create_minimal_phenomenal_profile,
        }
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        return presets[preset_name]()

    def _infer_focus(self, context: Dict[str, Any]) -> float:
        text = json.dumps(context, sort_keys=True).lower()
        focus_keywords = ["focus", "analysis", "debug", "optimize", "precision", "detail"]
        diffuse_keywords = ["brainstorm", "explore", "diverge", "ideate", "open"]
        focus_hits = sum(1 for word in focus_keywords if word in text)
        diffuse_hits = sum(1 for word in diffuse_keywords if word in text)
        if focus_hits > diffuse_hits:
            return 0.8
        if diffuse_hits > focus_hits:
            return 0.3
        return 0.5

    def _infer_temporal_depth(self, context: Dict[str, Any]) -> float:
        text = json.dumps(context, sort_keys=True).lower()
        if "long-term" in text or "roadmap" in text:
            return 0.75
        if "immediate" in text or "urgent" in text:
            return 0.35
        return 0.5

    def _base_layer_precisions(self, focus: float, context: Dict[str, Any]) -> Dict[str, float]:
        base = {layer: 0.5 for layer in self.config.default_layers}
        if focus > 0.6:
            base["reasoning"] = 0.7
            base["perception"] = 0.65
            base["action"] = 0.45
            base["metacognition"] = 0.55
        elif focus < 0.4:
            base = {layer: 0.45 for layer in self.config.default_layers}
        text = json.dumps(context, sort_keys=True).lower()
        if "reflect" in text or "metacognition" in text:
            base["metacognition"] = max(base["metacognition"], 0.7)
        return base

    def _base_modality_precisions(self, focus: float, context: Dict[str, Any]) -> Dict[str, float]:
        base = {modality: 0.5 for modality in self.config.default_modalities}
        text = json.dumps(context, sort_keys=True).lower()
        if "visual" in text:
            base["visual"] = 0.7
        if "memory" in text or "episodic" in text:
            base["episodic"] = 0.65
        if "procedure" in text or "workflow" in text:
            base["procedural"] = 0.65
        if "semantic" in text or "concept" in text:
            base["semantic"] = 0.7
        if focus < 0.4:
            base = {key: min(0.6, value) for key, value in base.items()}
        return base

    def _apply_biases(self, base: Dict[str, float], biases: Dict[str, float]) -> Dict[str, float]:
        updated: Dict[str, float] = {}
        for key, value in base.items():
            updated[key] = self._clamp_precision(value + biases.get(key, 0.0))
        return updated

    def _apply_recent_errors(self, base: Dict[str, float], errors: List[PrecisionError]) -> Dict[str, float]:
        adjusted = base.copy()
        for error in errors:
            direction = 1.0 if error.error_direction == "under_confident" else -1.0
            delta = direction * error.error_magnitude * 0.5
            adjusted[error.layer_id] = self._clamp_precision(adjusted.get(error.layer_id, 0.5) + delta)
        return adjusted

    def _infer_meta_precision(self, errors: List[PrecisionError]) -> float:
        if not errors:
            return 0.6
        avg_error = sum(err.error_magnitude for err in errors) / len(errors)
        return self._clamp_precision(1.0 - (avg_error * 0.6))

    def _bounded_learning_rate(self, avg_error: float) -> float:
        raw = self.config.base_learning_rate * (1.0 + avg_error)
        return max(self.config.min_learning_rate, min(self.config.max_learning_rate, raw))

    def _clamp_precision(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _clamp_bias(self, value: float) -> float:
        return max(-0.5, min(0.5, value))

    def _hash_embedding(self, context: Dict[str, Any]) -> List[float]:
        payload = json.dumps(context, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        values: List[float] = []
        for i in range(EMBEDDING_DIMENSIONS):
            byte = digest[i % len(digest)]
            values.append(byte / 255.0)
        return values


_hyper_model_service: Optional[HyperModelService] = None


def get_hyper_model_service() -> HyperModelService:
    global _hyper_model_service
    if _hyper_model_service is None:
        _hyper_model_service = HyperModelService()
    return _hyper_model_service
