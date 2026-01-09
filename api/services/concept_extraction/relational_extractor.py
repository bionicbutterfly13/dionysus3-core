"""
Relational Concept Extractor (Level 2).

Extracts connections, causality, and dependencies between concepts.
Builds upon atomic concepts from Level 1.
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


RELATIONAL_EXTRACTION_PROMPT = """You are an expert at identifying relationships between concepts.

Given the text and previously identified atomic concepts, extract relationships:
- Causal relationships (causes, leads to, results in)
- Dependencies (requires, depends on, enables)
- Associations (related to, connected with, similar to)
- Hierarchies (contains, part of, example of)

For each relationship, provide:
- name: A descriptive name for this relationship
- source_concept: The source concept name
- target_concept: The target concept name
- relationship_type: One of [causes, enables, requires, contains, exemplifies, opposes, relates_to]
- strength: Confidence in this relationship 0.0-1.0
- description: Brief explanation of the relationship

Return ONLY a valid JSON object:
{
  "relationships": [
    {
      "name": "relationship name",
      "source_concept": "concept A",
      "target_concept": "concept B",
      "relationship_type": "causes|enables|requires|contains|exemplifies|opposes|relates_to",
      "strength": 0.85,
      "description": "explanation"
    }
  ]
}"""


class RelationalConceptExtractor(BaseLevelExtractor):
    """Level 2: Extract relationships between concepts."""

    level = ConceptExtractionLevel.RELATIONAL
    description = "Extracts connections, causality, and dependencies"

    def __init__(self, model: str = GPT5_NANO):
        super().__init__(model=model)

    async def extract(
        self,
        content: str,
        context: dict,
        lower_level_concepts: Optional[list[ExtractedConcept]] = None,
    ) -> LevelExtractionResult:
        """Extract relational concepts from content.

        Args:
            content: Text to extract relationships from.
            context: Extraction context.
            lower_level_concepts: Atomic concepts from Level 1.

        Returns:
            LevelExtractionResult with extracted relationships.
        """
        start_time = time.time()

        # Build context from lower-level concepts
        concept_context = self._build_prompt_context(lower_level_concepts)

        prompt = RELATIONAL_EXTRACTION_PROMPT
        if concept_context:
            prompt += f"\n\n{concept_context}"

        messages = [{"role": "user", "content": f"{prompt}\n\nText:\n{content}"}]

        try:
            response = await chat_completion(
                messages=messages,
                system_prompt="You are a precise relationship extraction system. Return only valid JSON.",
                model=self.model,
                max_tokens=2048,
            )

            concepts = self._parse_response(response, lower_level_concepts or [], context)

        except Exception as e:
            logger.error(f"Relational extraction failed: {e}")
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

        logger.info(f"Relational extraction: {len(filtered)} relationships in {processing_time:.2f}s")
        return result

    def _parse_response(
        self,
        response: str,
        lower_concepts: list[ExtractedConcept],
        context: dict,
    ) -> list[ExtractedConcept]:
        """Parse LLM response into relationship concepts."""
        concepts = []
        concept_map = {c.name.lower(): c.concept_id for c in lower_concepts}

        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            data = json.loads(clean_response)
            relationships = data.get("relationships", [])

            for rel in relationships:
                source_name = rel.get("source_concept", "")
                target_name = rel.get("target_concept", "")

                concept = ExtractedConcept(
                    concept_id=str(uuid.uuid4()),
                    level=self.level,
                    name=rel.get("name", f"{source_name} -> {target_name}"),
                    description=rel.get("description", ""),
                    concept_type="relationship",
                    confidence=float(rel.get("strength", 0.0)),
                    extraction_method="llm_relational",
                    related_concepts=[
                        concept_map.get(source_name.lower(), source_name),
                        concept_map.get(target_name.lower(), target_name),
                    ],
                    relationship_data={
                        "source_concept": source_name,
                        "target_concept": target_name,
                        "relationship_type": rel.get("relationship_type", "relates_to"),
                        "strength": rel.get("strength", 0.5),
                    },
                )
                concepts.append(concept)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse relational response: {e}")
        except Exception as e:
            logger.warning(f"Error processing relationships: {e}")

        return concepts
