"""
Meta-ToT Decision Service
Feature: 041-meta-tot-engine
"""

from __future__ import annotations

import os
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from api.models.meta_tot import MetaToTDecision
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger("dionysus.meta_tot_decision")


@dataclass
class MetaToTDecisionConfig:
    complexity_threshold: float = 0.7
    uncertainty_threshold: float = 0.6
    min_token_threshold: int = 160
    always_on: bool = False

    @classmethod
    def from_env(cls) -> "MetaToTDecisionConfig":
        return cls(
            complexity_threshold=float(os.getenv("META_TOT_COMPLEXITY_THRESHOLD", 0.7)),
            uncertainty_threshold=float(os.getenv("META_TOT_UNCERTAINTY_THRESHOLD", 0.6)),
            min_token_threshold=int(os.getenv("META_TOT_MIN_TOKENS", 160)),
            always_on=os.getenv("META_TOT_ALWAYS_ON", "false").lower() == "true",
        )


@dataclass
class MetaToTAdaptiveState:
    complexity_threshold: float
    uncertainty_threshold: float
    min_token_threshold: int
    ema_utility: float = 0.5
    sample_count: int = 0
    updated_at: datetime = field(default_factory=datetime.utcnow)


class MetaToTDecisionService:
    _STATE_NODE_ID = "meta_tot_global"
    _THRESHOLD_MIN = 0.3
    _THRESHOLD_MAX = 0.9
    _ADJUST_STEP = 0.02
    _UTILITY_LOW = 0.4
    _UTILITY_HIGH = 0.6
    _EMA_ALPHA = 0.1
    _WARMUP_TIMEOUT = float(os.getenv("META_TOT_WARMUP_TIMEOUT", "5"))

    def __init__(self, config: Optional[MetaToTDecisionConfig] = None):
        self.config = config or MetaToTDecisionConfig.from_env()
        self._state: Optional[MetaToTAdaptiveState] = None
        self._loading_task: Optional[asyncio.Task] = None

    def decide(self, task: str, context: Optional[Dict[str, Any]] = None) -> MetaToTDecision:
        context = context or {}
        self._ensure_state_loaded()
        if context.get("disable_meta_tot"):
            return MetaToTDecision(
                use_meta_tot=False,
                complexity_score=0.0,
                uncertainty_score=0.0,
                thresholds=self._thresholds(),
                rationale="Meta-ToT disabled by context flag.",
            )

        complexity = self._score_complexity(task, context)
        uncertainty = self._score_uncertainty(task, context)
        thresholds = self._thresholds()

        use_meta_tot = self.config.always_on
        if context.get("force_meta_tot"):
            use_meta_tot = True
        if not use_meta_tot:
            use_meta_tot = (
                complexity >= self.config.complexity_threshold
                or uncertainty >= self.config.uncertainty_threshold
            )

        rationale = (
            f"complexity={complexity:.2f} (threshold {self.config.complexity_threshold:.2f}), "
            f"uncertainty={uncertainty:.2f} (threshold {self.config.uncertainty_threshold:.2f})"
        )

        return MetaToTDecision(
            use_meta_tot=use_meta_tot,
            complexity_score=complexity,
            uncertainty_score=uncertainty,
            thresholds=thresholds,
            rationale=rationale,
        )

    def _score_complexity(self, task: str, context: Dict[str, Any]) -> float:
        tokens = len(task.split())
        length_score = min(tokens / max(self._min_token_threshold(), 1), 1.0)

        constraint_terms = ["must", "should", "constraint", "tradeoff", "risk"]
        constraint_hits = sum(term in task.lower() for term in constraint_terms)
        constraint_score = min(constraint_hits / 5.0, 1.0)

        domain_terms = ["strategy", "plan", "marketing", "evolution", "architecture"]
        domain_hits = sum(term in task.lower() for term in domain_terms)
        domain_score = min(domain_hits / 5.0, 1.0)

        context_complexity = float(context.get("complexity_score", 0.0))

        score = 0.5 * length_score + 0.25 * constraint_score + 0.15 * domain_score + 0.10 * context_complexity
        return min(score, 1.0)

    def _score_uncertainty(self, task: str, context: Dict[str, Any]) -> float:
        if "uncertainty_level" in context:
            return min(max(float(context["uncertainty_level"]), 0.0), 1.0)

        goal_alignment = float(context.get("goal_alignment", 0.5))
        unknowns = context.get("unknowns", [])
        unknowns_score = min(len(unknowns) / 5.0, 1.0) if isinstance(unknowns, list) else 0.0

        question_marks = task.count("?")
        question_score = min(question_marks / 3.0, 1.0)

        score = 0.5 * (1.0 - goal_alignment) + 0.25 * unknowns_score + 0.25 * question_score
        return min(max(score, 0.0), 1.0)

    def _thresholds(self) -> Dict[str, float]:
        state = self._state
        return {
            "complexity_threshold": (state.complexity_threshold if state else self.config.complexity_threshold),
            "uncertainty_threshold": (state.uncertainty_threshold if state else self.config.uncertainty_threshold),
            "min_token_threshold": float(state.min_token_threshold if state else self.config.min_token_threshold),
            "ema_utility": float(state.ema_utility) if state else 0.5,
        }

    def _min_token_threshold(self) -> int:
        return self._state.min_token_threshold if self._state else self.config.min_token_threshold

    def _ensure_state_loaded(self) -> None:
        if self._state is not None or self._loading_task is not None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._loading_task = loop.create_task(self._load_state())

    async def warmup(self) -> None:
        if self._state is not None:
            return
        if self._loading_task is not None:
            await self._loading_task
            return
        try:
            await asyncio.wait_for(self._load_state(), timeout=self._WARMUP_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Meta-ToT threshold warmup timed out.")

    async def get_thresholds_snapshot(self) -> Dict[str, float]:
        if self._state is not None:
            return self._thresholds()
        if self._loading_task is not None:
            await self._loading_task
            return self._thresholds()
        await asyncio.wait_for(self._load_state(), timeout=self._WARMUP_TIMEOUT)
        return self._thresholds()

    async def _load_state(self) -> None:
        try:
            graphiti = await get_graphiti_service()
            rows = await graphiti.execute_cypher(
                """
                MATCH (t:MetaToTThreshold {id: $id})
                RETURN t
                LIMIT 1
                """,
                {"id": self._STATE_NODE_ID},
            )
            if rows:
                node = rows[0].get("t") or {}
                self._state = MetaToTAdaptiveState(
                    complexity_threshold=float(node.get("complexity_threshold", self.config.complexity_threshold)),
                    uncertainty_threshold=float(node.get("uncertainty_threshold", self.config.uncertainty_threshold)),
                    min_token_threshold=int(node.get("min_token_threshold", self.config.min_token_threshold)),
                    ema_utility=float(node.get("ema_utility", 0.5)),
                    sample_count=int(node.get("sample_count", 0)),
                )
                self._clamp_state(self._state)
            else:
                self._state = MetaToTAdaptiveState(
                    complexity_threshold=self.config.complexity_threshold,
                    uncertainty_threshold=self.config.uncertainty_threshold,
                    min_token_threshold=self.config.min_token_threshold,
                )
                await self._persist_state(self._state)
        except Exception as exc:
            logger.warning(f"Meta-ToT threshold load failed: {exc}")
        finally:
            self._loading_task = None

    async def update_from_result(self, decision: Optional[MetaToTDecision], result) -> None:
        if decision is None or not decision.use_meta_tot:
            return
        try:
            metrics = getattr(result, "metrics", {}) or {}
            confidence = float(getattr(result, "confidence", 0.0))
            processing_time = float(metrics.get("processing_time", 0.0))
            time_budget = float(metrics.get("time_budget_seconds", 5.0))
            if time_budget <= 0:
                time_budget = 5.0

            utility = confidence - min(processing_time / time_budget, 1.0)
            utility = max(0.0, min(1.0, utility))

            if self._state is None:
                await self._load_state()
            if self._state is None:
                return

            state = self._state
            state.ema_utility = (self._EMA_ALPHA * utility) + ((1 - self._EMA_ALPHA) * state.ema_utility)
            state.sample_count += 1
            state.updated_at = datetime.utcnow()

            if state.ema_utility > self._UTILITY_HIGH:
                state.complexity_threshold -= self._ADJUST_STEP
                state.uncertainty_threshold -= self._ADJUST_STEP
            elif state.ema_utility < self._UTILITY_LOW:
                state.complexity_threshold += self._ADJUST_STEP
                state.uncertainty_threshold += self._ADJUST_STEP

            self._clamp_state(state)
            await self._persist_state(state)
        except Exception as exc:
            logger.warning(f"Meta-ToT adaptive threshold update skipped: {exc}")

    def _clamp_state(self, state: MetaToTAdaptiveState) -> None:
        state.complexity_threshold = float(
            max(self._THRESHOLD_MIN, min(self._THRESHOLD_MAX, state.complexity_threshold))
        )
        state.uncertainty_threshold = float(
            max(self._THRESHOLD_MIN, min(self._THRESHOLD_MAX, state.uncertainty_threshold))
        )

    async def _persist_state(self, state: MetaToTAdaptiveState) -> None:
        graphiti = await get_graphiti_service()
        await graphiti.execute_cypher(
            """
            MERGE (t:MetaToTThreshold {id: $id})
            SET t.complexity_threshold = $complexity_threshold,
                t.uncertainty_threshold = $uncertainty_threshold,
                t.min_token_threshold = $min_token_threshold,
                t.ema_utility = $ema_utility,
                t.sample_count = $sample_count,
                t.updated_at = $updated_at
            """,
            {
                "id": self._STATE_NODE_ID,
                "complexity_threshold": state.complexity_threshold,
                "uncertainty_threshold": state.uncertainty_threshold,
                "min_token_threshold": state.min_token_threshold,
                "ema_utility": state.ema_utility,
                "sample_count": state.sample_count,
                "updated_at": state.updated_at.isoformat(),
            },
        )


_meta_tot_decision_service: Optional[MetaToTDecisionService] = None


def get_meta_tot_decision_service() -> MetaToTDecisionService:
    global _meta_tot_decision_service
    if _meta_tot_decision_service is None:
        _meta_tot_decision_service = MetaToTDecisionService()
    return _meta_tot_decision_service
