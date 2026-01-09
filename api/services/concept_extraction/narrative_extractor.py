"""
Narrative Structure Extractor (Level 5).

Extracts argument flows, story progressions, and methodologies.
The highest level of abstraction, building on all lower levels.
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


NARRATIVE_EXTRACTION_PROMPT = """You are an expert at identifying narrative structures and argument flows.

Given the text and previously identified concepts, extract narrative structures:
- Argument progressions and logical flows
- Story arcs and progressions
- Methodological sequences
- Persuasive strategies
- Knowledge building patterns

For each narrative, provide:
- name: Narrative structure name
- narrative_type: Type [progressive_argument, dialectic, story_arc, methodology, exposition]
- summary: Summary of the narrative flow
- argument_flow: List of stages in order [premise, evidence, reasoning, conclusion]
- persuasive_strategy: Main persuasive approach
- confidence: Your confidence 0.0-1.0

Return ONLY a valid JSON object:
{
  "narratives": [
    {
      "name": "narrative name",
      "narrative_type": "progressive_argument|dialectic|story_arc|methodology|exposition",
      "summary": "brief summary",
      "argument_flow": ["stage1", "stage2", "stage3"],
      "persuasive_strategy": "logical_progression|emotional_appeal|authority|evidence_based",
      "confidence": 0.82
    }
  ]
}"""


class NarrativeStructureExtractor(BaseLevelExtractor):
    """Level 5: Extract argument flows, story progressions, and methodologies."""

    level = ConceptExtractionLevel.NARRATIVE
    description = "Extracts argument flows, story progressions, and methodologies"

    def __init__(self, model: str = GPT5_NANO):
        super().__init__(model=model)

    async def extract(
        self,
        content: str,
        context: dict,
        lower_level_concepts: Optional[list[ExtractedConcept]] = None,
    ) -> LevelExtractionResult:
        """Extract narrative structures from content."""
        start_time = time.time()

        concept_context = self._build_prompt_context(lower_level_concepts)

        prompt = NARRATIVE_EXTRACTION_PROMPT
        if concept_context:
            prompt += f"\n\n{concept_context}"

        messages = [{"role": "user", "content": f"{prompt}\n\nText:\n{content}"}]

        try:
            response = await chat_completion(
                messages=messages,
                system_prompt="You are a precise narrative extraction system. Return only valid JSON.",
                model=self.model,
                max_tokens=2048,
            )

            concepts = self._parse_response(response, lower_level_concepts or [], context)

        except Exception as e:
            logger.error(f"Narrative extraction failed: {e}")
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

        logger.info(f"Narrative extraction: {len(filtered)} narratives in {processing_time:.2f}s")
        return result

    def _parse_response(
        self,
        response: str,
        lower_concepts: list[ExtractedConcept],
        context: dict,
    ) -> list[ExtractedConcept]:
        """Parse LLM response into narrative concepts."""
        concepts = []

        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            data = json.loads(clean_response)
            narratives = data.get("narratives", [])

            for nar in narratives:
                concept = ExtractedConcept(
                    concept_id=str(uuid.uuid4()),
                    level=self.level,
                    name=nar.get("name", "Unknown Narrative"),
                    description=nar.get("summary", ""),
                    concept_type="narrative",
                    confidence=float(nar.get("confidence", 0.0)),
                    extraction_method="llm_narrative",
                    narrative_elements={
                        "narrative_type": nar.get("narrative_type", "exposition"),
                        "argument_flow": nar.get("argument_flow", []),
                        "persuasive_strategy": nar.get("persuasive_strategy", "unknown"),
                    },
                )
                concepts.append(concept)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse narrative response: {e}")
        except Exception as e:
            logger.warning(f"Error processing narratives: {e}")

        return concepts
