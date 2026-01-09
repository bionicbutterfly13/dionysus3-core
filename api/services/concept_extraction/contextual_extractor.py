"""
Contextual Framework Extractor (Level 4).

Extracts domain paradigms and theoretical frameworks from text.
Builds upon atomic, relational, and composite concepts.
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


CONTEXTUAL_EXTRACTION_PROMPT = """You are an expert at identifying theoretical frameworks and domain paradigms.

Given the text and previously identified concepts, extract contextual frameworks:
- Theoretical frameworks and paradigms
- Domain-specific knowledge structures
- Methodological approaches
- Epistemological perspectives
- Schools of thought and traditions

For each framework, provide:
- name: Framework or paradigm name
- description: Description of the framework
- domain: Primary domain (neuroscience, philosophy, ai, psychology, etc.)
- paradigm: The paradigm type (computational, phenomenological, constructivist, etc.)
- key_principles: List of core principles
- confidence: Your confidence 0.0-1.0

Return ONLY a valid JSON object:
{
  "frameworks": [
    {
      "name": "framework name",
      "description": "framework description",
      "domain": "domain name",
      "paradigm": "paradigm type",
      "key_principles": ["principle1", "principle2"],
      "confidence": 0.85
    }
  ]
}"""


class ContextualFrameworkExtractor(BaseLevelExtractor):
    """Level 4: Extract domain paradigms and theoretical frameworks."""

    level = ConceptExtractionLevel.CONTEXTUAL
    description = "Extracts domain paradigms and theoretical frameworks"

    def __init__(self, model: str = GPT5_NANO):
        super().__init__(model=model)

    async def extract(
        self,
        content: str,
        context: dict,
        lower_level_concepts: Optional[list[ExtractedConcept]] = None,
    ) -> LevelExtractionResult:
        """Extract contextual frameworks from content."""
        start_time = time.time()

        concept_context = self._build_prompt_context(lower_level_concepts)

        prompt = CONTEXTUAL_EXTRACTION_PROMPT
        if concept_context:
            prompt += f"\n\n{concept_context}"

        messages = [{"role": "user", "content": f"{prompt}\n\nText:\n{content}"}]

        try:
            response = await chat_completion(
                messages=messages,
                system_prompt="You are a precise framework extraction system. Return only valid JSON.",
                model=self.model,
                max_tokens=2048,
            )

            concepts = self._parse_response(response, lower_level_concepts or [], context)

        except Exception as e:
            logger.error(f"Contextual extraction failed: {e}")
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

        logger.info(f"Contextual extraction: {len(filtered)} frameworks in {processing_time:.2f}s")
        return result

    def _parse_response(
        self,
        response: str,
        lower_concepts: list[ExtractedConcept],
        context: dict,
    ) -> list[ExtractedConcept]:
        """Parse LLM response into contextual framework concepts."""
        concepts = []

        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            data = json.loads(clean_response)
            frameworks = data.get("frameworks", [])

            for fw in frameworks:
                concept = ExtractedConcept(
                    concept_id=str(uuid.uuid4()),
                    level=self.level,
                    name=fw.get("name", "Unknown Framework"),
                    description=fw.get("description", ""),
                    concept_type="framework",
                    confidence=float(fw.get("confidence", 0.0)),
                    extraction_method="llm_contextual",
                    domain_tags=[fw.get("domain", "general")],
                    contextual_framework={
                        "domain": fw.get("domain", "general"),
                        "paradigm": fw.get("paradigm", "unknown"),
                        "key_principles": fw.get("key_principles", []),
                    },
                )
                concepts.append(concept)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse contextual response: {e}")
        except Exception as e:
            logger.warning(f"Error processing frameworks: {e}")

        return concepts
