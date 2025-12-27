"""
Legacy component discovery and scoring.

Lightweight port of the Dionysus 2.0 discovery logic: scans Python files,
detects awareness/inference/memory patterns, applies strategic value signals,
and produces composite scores + migration recommendations.
"""

from __future__ import annotations

import ast
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ConsciousnessFunctionality:
    awareness_patterns: List[str] = field(default_factory=list)
    inference_patterns: List[str] = field(default_factory=list)
    memory_patterns: List[str] = field(default_factory=list)

    @property
    def awareness_score(self) -> float:
        return min(1.0, len(self.awareness_patterns) / 5.0)

    @property
    def inference_score(self) -> float:
        return min(1.0, len(self.inference_patterns) / 5.0)

    @property
    def memory_score(self) -> float:
        return min(1.0, len(self.memory_patterns) / 5.0)

    @property
    def composite_score(self) -> float:
        # Equal weight within functionality
        return (self.awareness_score + self.inference_score + self.memory_score) / 3.0


@dataclass
class StrategicValue:
    uniqueness_score: float = 0.0
    reusability_score: float = 0.0
    framework_alignment_score: float = 0.0
    dependency_burden: float = 0.0  # 0-1, higher is worse

    @property
    def composite_score(self) -> float:
        # Higher reusability/alignment help; invert dependency burden
        return min(1.0, (
            self.uniqueness_score
            + self.reusability_score
            + self.framework_alignment_score
            + (1.0 - self.dependency_burden)
        ) / 4.0)


@dataclass
class ComponentAssessment:
    component_id: str
    name: str
    file_path: str
    consciousness: ConsciousnessFunctionality
    strategic: StrategicValue
    composite_score: float
    migration_recommended: bool
    enhancement_opportunities: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class DiscoveryConfig:
    quality_threshold: float = 0.55
    consciousness_weight: float = 0.7
    strategic_weight: float = 0.3
    max_files: int = 800  # safeguard against runaway scans


def _hash_component(file_path: str, source: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(file_path.encode("utf-8", "ignore"))
    hasher.update(source.encode("utf-8", "ignore"))
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DiscoveryService:
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        self.config = config or DiscoveryConfig()
        self.logger = logging.getLogger(__name__)

    def discover_components(self, codebase_path: str) -> List[ComponentAssessment]:
        """Scan a codebase for components with consciousness/strategic signals."""
        trace_id = str(uuid.uuid4())
        base = Path(codebase_path)
        if not base.exists():
            raise ValueError(f"Codebase path does not exist: {codebase_path}")

        assessments: List[ComponentAssessment] = []
        python_files = list(base.rglob("*.py"))[: self.config.max_files]

        self.logger.info(
            "discovery_start",
            extra={"trace_id": trace_id, "codebase": str(base), "file_count": len(python_files)},
        )

        for file_path in python_files:
            assessments.extend(self._analyze_file(file_path))

        # Sort high-score first
        assessments.sort(key=lambda a: a.composite_score, reverse=True)

        self.logger.info(
            "discovery_complete",
            extra={
                "trace_id": trace_id,
                "codebase": str(base),
                "components": len(assessments),
                "top_score": assessments[0].composite_score if assessments else 0.0,
            },
        )
        return assessments

    def _analyze_file(self, file_path: Path) -> List[ComponentAssessment]:
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        results: List[ComponentAssessment] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if not getattr(node, "name", None):
                    continue
                component_source = ast.get_source_segment(source, node) or ""
                assessment = self._assess_component(node.name, file_path, component_source)
                if assessment:
                    results.append(assessment)
        return results

    def _assess_component(
        self,
        name: str,
        file_path: Path,
        source: str,
    ) -> Optional[ComponentAssessment]:
        consciousness = self._analyze_consciousness(source)
        strategic = self._analyze_strategic(source)

        # Basic guard: require at least one pattern to avoid noise
        if not (consciousness.awareness_patterns or consciousness.inference_patterns or consciousness.memory_patterns):
            return None

        composite_score = self._composite_score(consciousness, strategic)
        migration_recommended = composite_score >= self.config.quality_threshold

        enhancements = self._derive_enhancements(consciousness)
        risks = self._derive_risks(consciousness, strategic)

        component_id = _hash_component(str(file_path), source)

        return ComponentAssessment(
            component_id=component_id,
            name=name,
            file_path=str(file_path),
            consciousness=consciousness,
            strategic=strategic,
            composite_score=composite_score,
            migration_recommended=migration_recommended,
            enhancement_opportunities=enhancements,
            risk_factors=risks,
        )

    def _analyze_consciousness(self, source: str) -> ConsciousnessFunctionality:
        lower = source.lower()

        def find_patterns(keywords: List[str]) -> List[str]:
            return [kw for kw in keywords if kw in lower]

        awareness = find_patterns(["awareness", "conscious", "attention", "observe", "orient"])
        inference = find_patterns(["infer", "reason", "predict", "decide", "plan"])
        memory = find_patterns(["memory", "recall", "episodic", "semantic", "procedural", "graphiti"])

        return ConsciousnessFunctionality(
            awareness_patterns=awareness,
            inference_patterns=inference,
            memory_patterns=memory,
        )

    def _analyze_strategic(self, source: str) -> StrategicValue:
        lower = source.lower()
        uniqueness = 0.6 if "agent" in lower or "smol" in lower else 0.3
        reusability = 0.7 if "class " in lower and "def " in lower else 0.4
        alignment = 0.6 if "fastapi" in lower or "tool" in lower else 0.3
        dependency_burden = 0.2 if "import" in lower and lower.count("import") <= 5 else 0.5
        return StrategicValue(
            uniqueness_score=uniqueness,
            reusability_score=reusability,
            framework_alignment_score=alignment,
            dependency_burden=dependency_burden,
        )

    def _composite_score(
        self,
        consciousness: ConsciousnessFunctionality,
        strategic: StrategicValue,
    ) -> float:
        return (
            consciousness.composite_score * self.config.consciousness_weight
            + strategic.composite_score * self.config.strategic_weight
        )

    def _derive_enhancements(self, consciousness: ConsciousnessFunctionality) -> List[str]:
        opportunities: List[str] = []
        if consciousness.awareness_score > 0.4:
            opportunities.append("awareness_amplification")
        if consciousness.inference_score > 0.4:
            opportunities.append("active_inference_integration")
        if consciousness.memory_score > 0.4:
            opportunities.append("memory_system_enhancement")
        return opportunities

    def _derive_risks(self, consciousness: ConsciousnessFunctionality, strategic: StrategicValue) -> List[str]:
        risks: List[str] = []
        if not (consciousness.awareness_patterns or consciousness.inference_patterns or consciousness.memory_patterns):
            risks.append("no_consciousness_signals")
        if strategic.dependency_burden > 0.4:
            risks.append("high_dependency_complexity")
        if strategic.framework_alignment_score < 0.4:
            risks.append("low_framework_compatibility")
        return risks


def get_discovery_service() -> DiscoveryService:
    return DiscoveryService()
