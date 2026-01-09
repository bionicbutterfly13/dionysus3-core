"""
Composite Concept Extractor (Level 3).

Extracts complex multi-part ideas and systems from text.
Builds upon atomic and relational concepts.
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


COMPOSITE_EXTRACTION_PROMPT = """You are an expert at identifying composite concepts - complex ideas built from simpler parts.

Given the text and previously identified concepts, extract composite concepts:
- Systems composed of multiple components
- Complex processes with multiple steps
- Multi-faceted ideas combining several concepts
- Integrated frameworks combining principles

For each composite concept, provide:
- name: The composite concept name
- description: Full description of the composite
- component_concepts: List of component concept names
- integration_type: How components are integrated [system, process, framework, theory, method]
- confidence: Your confidence 0.0-1.0

Return ONLY a valid JSON object:
{
  "composite_concepts": [
    {
      "name": "composite name",
      "description": "full description",
      "component_concepts": ["concept1", "concept2"],
      "integration_type": "system|process|framework|theory|method",
      "confidence": 0.88
    }
  ]
}"""


class CompositeConceptExtractor(BaseLevelExtractor):
    """Level 3: Extract complex multi-part ideas and systems."""

    level = ConceptExtractionLevel.COMPOSITE
    description = "Extracts complex multi-part ideas and systems"

    def __init__(self, model: str = GPT5_NANO):
        super().__init__(model=model)

    async def extract(
        self,
        content: str,
        context: dict,
        lower_level_concepts: Optional[list[ExtractedConcept]] = None,
    ) -> LevelExtractionResult:
        """Extract composite concepts from content."""
        start_time = time.time()

        concept_context = self._build_prompt_context(lower_level_concepts)

        prompt = COMPOSITE_EXTRACTION_PROMPT
        if concept_context:
            prompt += f"\n\n{concept_context}"

        messages = [{"role": "user", "content": f"{prompt}\n\nText:\n{content}"}]

        try:
            response = await chat_completion(
                messages=messages,
                system_prompt="You are a precise composite concept extraction system. Return only valid JSON.",
                model=self.model,
                max_tokens=2048,
            )

            concepts = self._parse_response(response, lower_level_concepts or [], context)

        except Exception as e:
            logger.error(f"Composite extraction failed: {e}")
            concepts = []

        processing_time = time.time() - start_time
        min_confidence = context.get("min_confidence", 0.5)
        filtered = [c for c in concepts if c.confidence >= min_confidence]

        result = LevelExtractionResult(
            level=self.level,
            concepts=filtered,
            extraction_time=processing_time,
            content_length=len(content),
            successful_extractions=len(filtered),
            failed_extractions=len(concepts) - len(filtered),
        )

        logger.info(f"Composite extraction: {len(filtered)} composites in {processing_time:.2f}s")
        return result

    def _parse_response(
        self,
        response: str,
        lower_concepts: list[ExtractedConcept],
        context: dict,
    ) -> list[ExtractedConcept]:
        """Parse LLM response into composite concepts."""
        concepts = []
        concept_map = {c.name.lower(): c.concept_id for c in lower_concepts}

        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            data = json.loads(clean_response)
            composites = data.get("composite_concepts", [])

            for comp in composites:
                component_names = comp.get("component_concepts", [])
                component_ids = [
                    concept_map.get(name.lower(), name) for name in component_names
                ]

                concept = ExtractedConcept(
                    concept_id=str(uuid.uuid4()),
                    level=self.level,
                    name=comp.get("name", "Unknown Composite"),
                    description=comp.get("description", ""),
                    concept_type="composite",
                    confidence=float(comp.get("confidence", 0.0)),
                    extraction_method="llm_composite",
                    child_concepts=component_ids,
                    composite_structure={
                        "component_concepts": component_names,
                        "integration_type": comp.get("integration_type", "system"),
                        "component_count": len(component_names),
                    },
                )
                concepts.append(concept)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse composite response: {e}")
        except Exception as e:
            logger.warning(f"Error processing composites: {e}")

        return concepts
