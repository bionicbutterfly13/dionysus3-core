"""
Atomic Concept Extractor (Level 1).

Extracts individual terms, entities, and definitions from text.
This is the foundational level that identifies discrete concepts.
"""

import json
import logging
import time
import uuid
from typing import Optional

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    ExtractedConcept,
    LevelExtractionResult,
)
from api.services.llm_service import chat_completion, GPT5_NANO
from .base import BaseLevelExtractor

logger = logging.getLogger(__name__)


ATOMIC_EXTRACTION_PROMPT = """You are an expert concept extractor. Extract atomic concepts from the provided text.

Atomic concepts are individual, discrete units of meaning:
- Named entities (people, places, organizations, concepts)
- Key terms and technical vocabulary
- Definitions and their terms
- Individual ideas that can stand alone

For each concept, provide:
- name: The concept name/term
- definition: A brief definition or description
- concept_type: One of [entity, term, definition, idea, principle, method]
- confidence: Your confidence 0.0-1.0
- source_span: The exact text span where this concept appears

Return ONLY a valid JSON object in this format:
{
  "concepts": [
    {
      "name": "concept name",
      "definition": "brief definition",
      "concept_type": "entity|term|definition|idea|principle|method",
      "confidence": 0.95,
      "source_span": "exact text span"
    }
  ]
}"""


class AtomicConceptExtractor(BaseLevelExtractor):
    """Level 1: Extract atomic (individual) concepts from text."""

    level = ConceptExtractionLevel.ATOMIC
    description = "Extracts individual terms, entities, and definitions"

    def __init__(self, model: str = GPT5_NANO):
        super().__init__(model=model)

    async def extract(
        self,
        content: str,
        context: dict,
        lower_level_concepts: Optional[list[ExtractedConcept]] = None,
    ) -> LevelExtractionResult:
        """Extract atomic concepts from content.

        Args:
            content: Text to extract concepts from.
            context: Extraction context with optional keys:
                - domain_focus: List of domain tags to focus on
                - min_confidence: Minimum confidence threshold
            lower_level_concepts: Not used at atomic level (base level).

        Returns:
            LevelExtractionResult with extracted atomic concepts.
        """
        start_time = time.time()

        # Build prompt
        domain_focus = context.get("domain_focus", [])
        prompt = ATOMIC_EXTRACTION_PROMPT
        if domain_focus:
            prompt += f"\n\nFocus on domains: {', '.join(domain_focus)}"

        # Call LLM for extraction
        messages = [{"role": "user", "content": f"{prompt}\n\n{content}"}]

        try:
            response = await chat_completion(
                messages=messages,
                system_prompt="You are a precise concept extraction system. Return only valid JSON.",
                model=self.model,
                max_tokens=2048,
            )

            concepts = self._parse_response(response, content, context)

        except Exception as e:
            logger.error(f"Atomic extraction failed: {e}")
            concepts = []

        # Build result
        processing_time = time.time() - start_time
        min_confidence = context.get("min_confidence", 0.5)

        # Filter by confidence threshold
        filtered_concepts = [c for c in concepts if c.confidence >= min_confidence]

        result = LevelExtractionResult(
            level=self.level,
            concepts=filtered_concepts,
            extraction_time=processing_time,
            content_length=len(content),
            successful_extractions=len(filtered_concepts),
            failed_extractions=len(concepts) - len(filtered_concepts),
        )

        logger.info(
            f"Atomic extraction: {len(filtered_concepts)} concepts in {processing_time:.2f}s"
        )
        return result

    def _parse_response(
        self, response: str, content: str, context: dict
    ) -> list[ExtractedConcept]:
        """Parse LLM response into ExtractedConcept objects.

        Args:
            response: Raw LLM response string.
            content: Original content (for fallback source spans).
            context: Extraction context.

        Returns:
            List of parsed ExtractedConcept objects.
        """
        concepts = []

        try:
            # Clean response - handle markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Remove markdown code fence
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            data = json.loads(clean_response)
            raw_concepts = data.get("concepts", [])

            for raw in raw_concepts:
                concept = ExtractedConcept(
                    concept_id=str(uuid.uuid4()),
                    level=self.level,
                    name=raw.get("name", "Unknown"),
                    description=raw.get("definition", ""),
                    concept_type=raw.get("concept_type", "term"),
                    confidence=float(raw.get("confidence", 0.0)),
                    source_span=raw.get("source_span", ""),
                    domain_tags=context.get("domain_focus", []),
                    extraction_method="llm_atomic",
                    atomic_properties={
                        "original_type": raw.get("concept_type"),
                        "frequency": 1,
                    },
                )
                concepts.append(concept)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse atomic extraction response: {e}")
        except Exception as e:
            logger.warning(f"Error processing atomic concepts: {e}")

        return concepts
