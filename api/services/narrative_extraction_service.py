"""
Narrative Extraction Service.

Primary: Text2Story (English-only)
Fallback: LLM NarrativeStructureExtractor

Track 002: Jungian Archetypes - Archetype evidence extraction from narratives
"""

from __future__ import annotations

import importlib
import logging
import re
from typing import Any, Optional, List, Dict

from api.models.concept_extraction import ConceptExtractionLevel, ExtractedConcept
from api.models.autobiographical import (
    ArchetypeEvidence,
    ARCHETYPE_MOTIF_PATTERNS,
    ARCHETYPE_SVO_PATTERNS,
)
from api.services.concept_extraction import NarrativeStructureExtractor

logger = logging.getLogger(__name__)


class Text2StoryExtractor:
    """Best-effort Text2Story wrapper with English-only defaults."""

    def __init__(self, language: str = "en"):
        self._language = language
        self._module = None

    def _load(self) -> Any:
        if self._module is not None:
            return self._module
        try:
            self._module = importlib.import_module("text2story")
        except Exception as exc:
            raise RuntimeError("text2story unavailable") from exc
        return self._module

    def _extract_raw(self, text: str) -> Any:
        module = self._load()
        if hasattr(module, "extract"):
            return module.extract(text, language=self._language)
        if hasattr(module, "Text2Story"):
            extractor = module.Text2Story(language=self._language)
            return extractor(text)
        if hasattr(module, "Pipeline"):
            pipeline = module.Pipeline(language=self._language)
            return pipeline(text)
        raise RuntimeError("text2story API not detected")

    async def extract_relationships(self, content: str) -> list[dict]:
        raw = self._extract_raw(content)
        return _relationships_from_text2story(raw)


class NarrativeExtractionService:
    """Runs Text2Story first, then falls back to LLM narrative extraction."""

    def __init__(
        self,
        *,
        text2story_extractor: Optional[Text2StoryExtractor] = None,
        llm_extractor: Optional[NarrativeStructureExtractor] = None,
        min_confidence: float = 0.6,
    ):
        self._text2story_extractor = text2story_extractor or Text2StoryExtractor()
        self._llm_extractor = llm_extractor or NarrativeStructureExtractor()
        self._min_confidence = min_confidence

    async def extract_relationships(self, content: str) -> list[dict]:
        if not content or not content.strip():
            return []

        try:
            relationships = await self._text2story_extractor.extract_relationships(content)
            if relationships:
                return relationships
        except Exception as exc:
            logger.warning(f"Text2Story extraction failed, falling back to LLM: {exc}")

        return await self._extract_from_llm(content)

    async def _extract_from_llm(self, content: str) -> list[dict]:
        result = await self._llm_extractor.extract(
            content=content,
            context={"min_confidence": self._min_confidence},
            lower_level_concepts=None,
        )
        return _relationships_from_narratives(result.concepts, min_confidence=self._min_confidence)

    # =========================================================================
    # Track 002: Archetype Evidence Extraction
    # =========================================================================

    def extract_archetype_evidence(self, content: str) -> List[ArchetypeEvidence]:
        """
        Extract archetype evidence from narrative content.

        Track 002: Jungian Cognitive Archetypes

        Integration (IO Map):
        - Inlets: Raw narrative content from route_memory() or extract_relationships()
        - Outlets: ArchetypeEvidence list → EFEEngine.update_archetype_precision_bayesian()

        Args:
            content: Narrative text to analyze

        Returns:
            List of ArchetypeEvidence instances
        """
        if not content or not content.strip():
            return []

        evidence_list: List[ArchetypeEvidence] = []
        content_lower = content.lower()

        # Extract from motif patterns
        for archetype, patterns in ARCHETYPE_MOTIF_PATTERNS.items():
            for pattern, weight in patterns:
                try:
                    if re.search(pattern, content_lower, re.IGNORECASE):
                        evidence_list.append(
                            ArchetypeEvidence(
                                archetype=archetype,
                                weight=weight,
                                source="motif",
                                pattern=pattern,
                                context=content[:100],
                            )
                        )
                except re.error:
                    logger.warning(f"Invalid regex pattern for {archetype}: {pattern}")

        # Extract from SVO patterns
        for archetype, patterns in ARCHETYPE_SVO_PATTERNS.items():
            for pattern, weight in patterns:
                try:
                    if re.search(pattern, content_lower, re.IGNORECASE):
                        evidence_list.append(
                            ArchetypeEvidence(
                                archetype=archetype,
                                weight=weight,
                                source="svo",
                                pattern=pattern,
                                context=content[:100],
                            )
                        )
                except re.error:
                    logger.warning(f"Invalid SVO pattern for {archetype}: {pattern}")

        if evidence_list:
            logger.debug(
                f"Archetype evidence extracted: {len(evidence_list)} items, "
                f"archetypes={set(e.archetype for e in evidence_list)}"
            )

        return evidence_list

    def aggregate_archetype_evidence(
        self,
        evidence_list: List[ArchetypeEvidence]
    ) -> Dict[str, float]:
        """
        Aggregate evidence weights by archetype.

        Args:
            evidence_list: List of ArchetypeEvidence

        Returns:
            Dict of archetype_name -> cumulative_weight
        """
        aggregated: Dict[str, float] = {}

        for evidence in evidence_list:
            current = aggregated.get(evidence.archetype, 0.0)
            # Use max(current, new) instead of sum to avoid inflation
            # Or use sum with cap: min(1.0, current + evidence.weight)
            aggregated[evidence.archetype] = min(1.0, current + evidence.weight)

        return aggregated

    async def extract_relationships_with_archetypes(
        self,
        content: str
    ) -> tuple[list[dict], List[ArchetypeEvidence]]:
        """
        Extract relationships and archetype evidence together.

        Track 002: Combined narrative + archetype extraction

        Args:
            content: Narrative text

        Returns:
            Tuple of (relationships, archetype_evidence)
        """
        relationships = await self.extract_relationships(content)
        archetype_evidence = self.extract_archetype_evidence(content)

        return relationships, archetype_evidence


def _relationships_from_narratives(
    concepts: list[ExtractedConcept],
    *,
    min_confidence: float,
) -> list[dict]:
    relationships: list[dict] = []
    for concept in concepts:
        if concept.level != ConceptExtractionLevel.NARRATIVE:
            continue

        name = concept.name.strip() if concept.name else "Unknown Narrative"
        source = f"Narrative:{name}"
        confidence = float(concept.confidence or 0.0)
        status = "approved" if confidence >= min_confidence else "pending_review"

        narrative_elements = concept.narrative_elements or {}
        stages = narrative_elements.get("argument_flow") or []
        strategy = narrative_elements.get("persuasive_strategy")
        narrative_type = narrative_elements.get("narrative_type")
        evidence = concept.description or ""

        for stage in stages:
            relationships.append(
                {
                    "source": source,
                    "target": f"Stage:{stage}",
                    "relation_type": "HAS_STAGE",
                    "confidence": confidence,
                    "status": status,
                    "evidence": evidence,
                }
            )

        if strategy:
            relationships.append(
                {
                    "source": source,
                    "target": f"Strategy:{strategy}",
                    "relation_type": "USES_STRATEGY",
                    "confidence": confidence,
                    "status": status,
                    "evidence": evidence,
                }
            )

        if narrative_type:
            relationships.append(
                {
                    "source": source,
                    "target": f"NarrativeType:{narrative_type}",
                    "relation_type": "IS_TYPE",
                    "confidence": confidence,
                    "status": status,
                    "evidence": evidence,
                }
            )

    return relationships


def _relationships_from_text2story(raw: Any) -> list[dict]:
    if raw is None:
        return []

    data = raw
    if hasattr(raw, "to_dict"):
        data = raw.to_dict()

    if not isinstance(data, dict):
        return []

    relationships: list[dict] = []

    raw_relations = data.get("relations") or data.get("relationships") or []
    for rel in raw_relations:
        if not isinstance(rel, dict):
            continue
        source = rel.get("source") or rel.get("head") or rel.get("subject")
        target = rel.get("target") or rel.get("tail") or rel.get("object")
        relation_type = rel.get("relation") or rel.get("type") or rel.get("predicate")
        if not (source and target and relation_type):
            continue
        relationships.append(
            {
                "source": str(source),
                "target": str(target),
                "relation_type": str(relation_type).upper().replace(" ", "_"),
                "confidence": float(rel.get("confidence", 0.7)),
                "status": rel.get("status", "approved"),
                "evidence": rel.get("evidence", ""),
            }
        )

    events = data.get("events") or []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_name = event.get("name") or event.get("text") or event.get("event")
        if not event_name:
            continue
        event_id = f"Event:{event_name}"
        participants = event.get("participants") or event.get("agents") or []
        for participant in participants:
            if not participant:
                continue
            relationships.append(
                {
                    "source": event_id,
                    "target": f"Actor:{participant}",
                    "relation_type": "PARTICIPATED_IN",
                    "confidence": float(event.get("confidence", 0.7)),
                    "status": "approved",
                    "evidence": event.get("evidence", ""),
                }
            )

    return relationships


_narrative_service: Optional[NarrativeExtractionService] = None


def get_narrative_extraction_service() -> NarrativeExtractionService:
    global _narrative_service
    if _narrative_service is None:
        _narrative_service = NarrativeExtractionService()
    return _narrative_service
