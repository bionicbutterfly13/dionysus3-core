"""
Base Level Extractor.

Abstract base class for all concept extraction levels. Each level
implements its own extraction logic via the `extract` method.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    ExtractedConcept,
    LevelExtractionResult,
)

logger = logging.getLogger(__name__)


class BaseLevelExtractor(ABC):
    """Abstract base class for concept extractors at each level."""

    level: ConceptExtractionLevel
    description: str = ""

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize extractor with LLM model name.

        Args:
            model: LLM model identifier for extraction calls.
        """
        self.model = model

    @abstractmethod
    async def extract(
        self,
        content: str,
        context: dict,
        lower_level_concepts: Optional[list[ExtractedConcept]] = None,
    ) -> LevelExtractionResult:
        """Extract concepts at this level.

        Args:
            content: Text content to extract concepts from.
            context: Extraction context (domain hints, min_confidence, etc.).
            lower_level_concepts: Concepts from lower levels to build upon.

        Returns:
            LevelExtractionResult with extracted concepts.
        """
        pass

    def _build_prompt_context(
        self, lower_concepts: Optional[list[ExtractedConcept]]
    ) -> str:
        """Build prompt context from lower-level concepts.

        Args:
            lower_concepts: List of concepts from lower extraction levels.

        Returns:
            Formatted string describing lower-level concepts.
        """
        if not lower_concepts:
            return ""

        lines = ["Previously extracted concepts:"]
        for c in lower_concepts[:20]:  # Limit to avoid prompt overflow
            lines.append(f"- {c.name}: {c.description[:100] if c.description else 'N/A'}")

        return "\n".join(lines)

    def _validate_concepts(
        self, concepts: list[ExtractedConcept], min_confidence: float = 0.0
    ) -> list[ExtractedConcept]:
        """Filter concepts by minimum confidence threshold.

        Args:
            concepts: List of extracted concepts.
            min_confidence: Minimum confidence threshold (0.0-1.0).

        Returns:
            Filtered list of concepts meeting threshold.
        """
        return [c for c in concepts if c.confidence >= min_confidence]
