"""
Domain Specialization Service.

Main orchestration service for neuroscience/AI domain specialization:
- Domain concept detection
- Academic structure analysis
- Cross-domain mapping
- Specialized prompt generation

Migrated from Dionysus 2.0 domain_specialization.py.
"""

import logging
import time
from typing import Any, Optional

from api.models.domain_specialization import (
    DomainAnalysisResult,
    DomainType,
)
from .neuroscience_db import NeuroscienceTerminologyDatabase
from .ai_db import AITerminologyDatabase
from .cross_domain_mapper import CrossDomainMapper
from .academic_structure import AcademicStructureRecognizer

logger = logging.getLogger(__name__)

# Module-level singleton
_service_instance: Optional["DomainSpecializationService"] = None


class DomainSpecificPromptGenerator:
    """Generates domain-specific prompts for LLM processing."""

    def __init__(
        self,
        neuro_db: NeuroscienceTerminologyDatabase,
        ai_db: AITerminologyDatabase,
        cross_mapper: CrossDomainMapper,
    ):
        self.neuro_db = neuro_db
        self.ai_db = ai_db
        self.cross_mapper = cross_mapper

    def generate_extraction_prompt(
        self, text: str, extraction_type: str, domain_focus: list[str]
    ) -> str:
        """Generate domain-specific extraction prompt."""

        # Detect domain context
        neuro_concepts = self._find_domain_concepts(text, DomainType.NEUROSCIENCE)
        ai_concepts = self._find_domain_concepts(
            text, DomainType.ARTIFICIAL_INTELLIGENCE
        )

        # Build domain-specific prompt
        if extraction_type == "atomic_concepts":
            return self._generate_atomic_prompt(
                text, neuro_concepts, ai_concepts, domain_focus
            )
        elif extraction_type == "relationships":
            return self._generate_relationship_prompt(
                text, neuro_concepts, ai_concepts, domain_focus
            )
        elif extraction_type == "cross_domain":
            return self._generate_cross_domain_prompt(text, neuro_concepts, ai_concepts)
        else:
            return self._generate_general_prompt(text, extraction_type, domain_focus)

    def _find_domain_concepts(self, text: str, domain: DomainType) -> list[str]:
        """Find domain-specific concepts in text."""
        concepts_found = []
        text_lower = text.lower()

        if domain == DomainType.NEUROSCIENCE:
            for term in self.neuro_db.concepts:
                if term in text_lower:
                    concepts_found.append(term)
        elif domain == DomainType.ARTIFICIAL_INTELLIGENCE:
            for term in self.ai_db.concepts:
                if term in text_lower:
                    concepts_found.append(term)

        return concepts_found[:10]  # Limit for prompt size

    def _generate_atomic_prompt(
        self,
        text: str,
        neuro_concepts: list[str],
        ai_concepts: list[str],
        domain_focus: list[str],
    ) -> str:
        """Generate atomic concept extraction prompt."""

        prompt = f"""Extract atomic concepts from the following neuroscience/AI text with high precision.

TEXT: {text[:1000]}...

DOMAIN CONTEXT:
- Neuroscience concepts detected: {', '.join(neuro_concepts[:5])}
- AI concepts detected: {', '.join(ai_concepts[:5])}
- Focus domains: {', '.join(domain_focus)}

EXTRACTION GUIDELINES:
1. Identify individual terms, entities, and definitions
2. Prioritize domain-specific terminology
3. Include anatomical structures, molecular components, algorithms, and architectures
4. Provide confidence scores (0.0-1.0)
5. Classify by category: anatomical, physiological, molecular, algorithmic, architectural, theoretical

EXPECTED CATEGORIES:
- Neuroscience: neurons, synapses, neurotransmitters, brain regions, mechanisms
- AI/ML: algorithms, architectures, optimization methods, learning paradigms

Return structured JSON with: name, definition, category, confidence, domain_tags"""

        return prompt

    def _generate_relationship_prompt(
        self,
        text: str,
        neuro_concepts: list[str],
        ai_concepts: list[str],
        domain_focus: list[str],
    ) -> str:
        """Generate relationship extraction prompt."""

        prompt = f"""Extract relationships between concepts in this neuroscience/AI text.

TEXT: {text[:1000]}...

CONCEPTS PRESENT:
- Neuroscience: {', '.join(neuro_concepts[:5])}
- AI/ML: {', '.join(ai_concepts[:5])}

RELATIONSHIP TYPES TO IDENTIFY:
1. Causal relationships (A causes B, A leads to B)
2. Structural relationships (A contains B, A is part of B)
3. Functional relationships (A enables B, A regulates B)
4. Temporal relationships (A occurs before B)
5. Analogical relationships (A is similar to B)

DOMAIN-SPECIFIC PATTERNS:
- Neural mechanisms and their effects
- Algorithm inputs/outputs and dependencies
- Biological-artificial correspondences
- Learning processes and outcomes

Return structured JSON with: source_concept, target_concept, relationship_type, confidence, evidence"""

        return prompt

    def _generate_cross_domain_prompt(
        self, text: str, neuro_concepts: list[str], ai_concepts: list[str]
    ) -> str:
        """Generate cross-domain mapping prompt."""

        bridges = self.cross_mapper.get_domain_bridges(text)

        prompt = f"""Identify cross-domain connections between neuroscience and AI concepts in this text.

TEXT: {text[:1000]}...

NEUROSCIENCE CONCEPTS: {', '.join(neuro_concepts)}
AI CONCEPTS: {', '.join(ai_concepts)}

KNOWN MAPPINGS:
"""

        for bridge in bridges[:3]:
            prompt += f"- {bridge.neuro_concept} ↔ {bridge.ai_concept} (strength: {bridge.bridge_strength:.2f})\n"

        prompt += """
FIND ADDITIONAL MAPPINGS:
1. Functional analogies (similar purposes)
2. Mechanistic analogies (similar processes)
3. Structural analogies (similar organization)
4. Inspirational relationships (one inspired by the other)

Return JSON with: neuro_concept, ai_concept, mapping_type, strength, similarities, differences"""

        return prompt

    def _generate_general_prompt(
        self, text: str, extraction_type: str, domain_focus: list[str]
    ) -> str:
        """Generate general domain-aware prompt."""

        return f"""Extract {extraction_type} from this scientific text with focus on {', '.join(domain_focus)} domains.

TEXT: {text[:1000]}...

Apply domain expertise to identify relevant concepts, relationships, and structures.
Return structured JSON with appropriate metadata and confidence scores."""


class DomainSpecializationService:
    """Main service coordinating domain specialization."""

    def __init__(self):
        self.neuro_db = NeuroscienceTerminologyDatabase()
        self.ai_db = AITerminologyDatabase()
        self.cross_mapper = CrossDomainMapper(self.neuro_db, self.ai_db)
        self.structure_recognizer = AcademicStructureRecognizer()
        self.prompt_generator = DomainSpecificPromptGenerator(
            self.neuro_db, self.ai_db, self.cross_mapper
        )

        self.processing_history: list[dict[str, Any]] = []

    async def analyze_domain_content(
        self, text: str, context: Optional[dict[str, Any]] = None
    ) -> DomainAnalysisResult:
        """Comprehensive domain analysis of text content."""

        start_time = time.time()
        result = DomainAnalysisResult()

        try:
            # 1. Domain concept detection
            neuro_concepts = self._detect_neuroscience_concepts(text)
            ai_concepts = self._detect_ai_concepts(text)

            result.neuroscience_concepts = neuro_concepts
            result.ai_concepts = ai_concepts
            result.primary_domain = self._determine_primary_domain(
                neuro_concepts, ai_concepts
            )
            result.domain_mix_ratio = (
                len(neuro_concepts) / (len(neuro_concepts) + len(ai_concepts))
                if (neuro_concepts or ai_concepts)
                else 0.5
            )

            # 2. Academic structure analysis
            academic_structure = self.structure_recognizer.analyze_structure(text)
            result.academic_structure = academic_structure

            # 3. Cross-domain mapping analysis
            cross_domain_bridges = self.cross_mapper.get_domain_bridges(text)
            result.cross_domain_mappings = [
                {
                    "neuro_concept": bridge.neuro_concept,
                    "ai_concept": bridge.ai_concept,
                    "mapping_strength": bridge.bridge_strength,
                    "mapping_type": bridge.mapping.mapping_type,
                }
                for bridge in cross_domain_bridges
            ]

            # 4. Generate specialized prompts
            domain_focus = (
                context.get("domain_focus", ["neuroscience", "artificial_intelligence"])
                if context
                else ["neuroscience", "artificial_intelligence"]
            )

            result.specialized_prompts = {
                "atomic_extraction": self.prompt_generator.generate_extraction_prompt(
                    text, "atomic_concepts", domain_focus
                ),
                "relationship_extraction": self.prompt_generator.generate_extraction_prompt(
                    text, "relationships", domain_focus
                ),
                "cross_domain_analysis": self.prompt_generator.generate_extraction_prompt(
                    text, "cross_domain", domain_focus
                ),
            }

            # 5. Calculate quality metrics
            result.domain_specificity = (len(neuro_concepts) + len(ai_concepts)) / max(
                1, len(text.split()) // 10
            )
            result.cross_domain_connectivity = len(cross_domain_bridges)
            result.academic_completeness = academic_structure.structure_completeness
            result.terminology_density = self._calculate_terminology_density(
                text, neuro_concepts, ai_concepts
            )
            result.complexity_score = self._calculate_complexity_score(
                neuro_concepts, ai_concepts
            )

            result.processing_time = time.time() - start_time
            result.success = True

            logger.info(
                f"Domain analysis completed in {result.processing_time:.3f}s"
            )
            logger.info(
                f"Found {len(neuro_concepts)} neuroscience and {len(ai_concepts)} AI concepts"
            )
            logger.info(
                f"Detected {len(cross_domain_bridges)} cross-domain bridges"
            )

        except Exception as e:
            logger.error(f"Domain specialization analysis failed: {e}")
            result.success = False
            result.error = str(e)

        return result

    def _detect_neuroscience_concepts(self, text: str) -> list[dict[str, Any]]:
        """Detect neuroscience concepts in text."""
        concepts_found = []
        text_lower = text.lower()

        for term, concept in self.neuro_db.concepts.items():
            if term in text_lower:
                concepts_found.append(
                    {
                        "term": concept.term,
                        "definition": concept.definition,
                        "category": concept.category.value,
                        "importance": concept.importance_score,
                        "complexity": concept.complexity_level,
                    }
                )

            # Also check synonyms and abbreviations
            for synonym in concept.synonyms:
                if synonym.lower() in text_lower and not any(
                    c["term"] == concept.term for c in concepts_found
                ):
                    concepts_found.append(
                        {
                            "term": concept.term,
                            "definition": concept.definition,
                            "category": concept.category.value,
                            "importance": concept.importance_score,
                            "complexity": concept.complexity_level,
                            "matched_as": synonym,
                        }
                    )
                    break

        return concepts_found

    def _detect_ai_concepts(self, text: str) -> list[dict[str, Any]]:
        """Detect AI concepts in text."""
        concepts_found = []
        text_lower = text.lower()

        for term, concept in self.ai_db.concepts.items():
            if term in text_lower:
                concepts_found.append(
                    {
                        "term": concept.term,
                        "definition": concept.definition,
                        "category": concept.category.value,
                        "importance": concept.importance_score,
                        "complexity": concept.complexity_level,
                    }
                )

            # Also check synonyms and abbreviations
            for synonym in concept.synonyms:
                if synonym.lower() in text_lower and not any(
                    c["term"] == concept.term for c in concepts_found
                ):
                    concepts_found.append(
                        {
                            "term": concept.term,
                            "definition": concept.definition,
                            "category": concept.category.value,
                            "importance": concept.importance_score,
                            "complexity": concept.complexity_level,
                            "matched_as": synonym,
                        }
                    )
                    break

        return concepts_found

    def _determine_primary_domain(
        self, neuro_concepts: list[dict], ai_concepts: list[dict]
    ) -> str:
        """Determine the primary domain of the text."""
        neuro_score = sum(c["importance"] for c in neuro_concepts)
        ai_score = sum(c["importance"] for c in ai_concepts)

        if neuro_score > ai_score * 1.2:
            return "neuroscience_primary"
        elif ai_score > neuro_score * 1.2:
            return "ai_primary"
        else:
            return "interdisciplinary"

    def _calculate_terminology_density(
        self, text: str, neuro_concepts: list[dict], ai_concepts: list[dict]
    ) -> float:
        """Calculate density of domain-specific terminology."""
        total_words = len(text.split())
        total_concepts = len(neuro_concepts) + len(ai_concepts)
        return total_concepts / max(1, total_words // 20)  # Concepts per 20 words

    def _calculate_complexity_score(
        self, neuro_concepts: list[dict], ai_concepts: list[dict]
    ) -> float:
        """Calculate overall complexity score."""
        all_concepts = neuro_concepts + ai_concepts
        if not all_concepts:
            return 0.0

        avg_complexity = sum(c["complexity"] for c in all_concepts) / len(all_concepts)
        return avg_complexity / 5.0  # Normalize to 0-1 scale

    def find_concept(self, term: str) -> Optional[dict[str, Any]]:
        """Find a concept by term in either database."""
        # Check neuroscience DB
        concept = self.neuro_db.find_concept(term)
        if concept:
            return {
                "term": concept.term,
                "definition": concept.definition,
                "domain": concept.domain.value,
                "category": concept.category.value,
                "importance": concept.importance_score,
                "complexity": concept.complexity_level,
            }

        # Check AI DB
        concept = self.ai_db.find_concept(term)
        if concept:
            return {
                "term": concept.term,
                "definition": concept.definition,
                "domain": concept.domain.value,
                "category": concept.category.value,
                "importance": concept.importance_score,
                "complexity": concept.complexity_level,
            }

        return None

    def get_cross_domain_equivalent(
        self, term: str
    ) -> Optional[dict[str, Any]]:
        """Get cross-domain equivalent for a concept."""
        mapping = self.cross_mapper.get_mapping(term)
        if mapping:
            return {
                "source": mapping.source_concept,
                "source_domain": mapping.source_domain.value,
                "target": mapping.target_concept,
                "target_domain": mapping.target_domain.value,
                "mapping_type": mapping.mapping_type,
                "strength": mapping.strength,
                "description": mapping.description,
            }
        return None


async def get_domain_specialization_service() -> DomainSpecializationService:
    """Get or create the singleton domain specialization service.

    Returns:
        The DomainSpecializationService singleton.
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = DomainSpecializationService()

    return _service_instance
