"""
Neuroscience Terminology Database.

Comprehensive database of neuroscience concepts with metadata
for domain-specific content analysis.

Migrated from Dionysus 2.0 domain_specialization.py.
"""

import logging
from typing import Optional

from api.models.domain_specialization import (
    ConceptCategory,
    DomainConcept,
    DomainType,
)

logger = logging.getLogger(__name__)


class NeuroscienceTerminologyDatabase:
    """Comprehensive neuroscience terminology database."""

    def __init__(self):
        self.concepts: dict[str, DomainConcept] = {}
        self._initialize_neuroscience_database()

    def _initialize_neuroscience_database(self) -> None:
        """Initialize with core neuroscience concepts."""

        # Anatomical concepts
        anatomical_concepts = [
            {
                "term": "neuron",
                "definition": "A specialized cell that transmits electrical and chemical signals in the nervous system",
                "category": ConceptCategory.ANATOMICAL,
                "synonyms": ["nerve cell", "neural cell"],
                "abbreviations": ["N"],
                "anatomical_location": "nervous_system",
                "related_terms": ["dendrite", "axon", "soma", "synapse"],
                "complexity_level": 2,
                "importance_score": 0.95,
            },
            {
                "term": "synapse",
                "definition": "The junction between two nerve cells where neurotransmitter signals are transmitted",
                "category": ConceptCategory.ANATOMICAL,
                "synonyms": ["synaptic junction", "neural junction"],
                "anatomical_location": "neural_interface",
                "related_terms": [
                    "neurotransmitter",
                    "synaptic_cleft",
                    "postsynaptic",
                    "presynaptic",
                ],
                "complexity_level": 3,
                "importance_score": 0.92,
            },
            {
                "term": "dendrite",
                "definition": "Branched extensions of neurons that receive signals from other neurons",
                "category": ConceptCategory.ANATOMICAL,
                "anatomical_location": "neuron",
                "related_terms": ["dendritic_tree", "dendritic_spine", "synaptic_input"],
                "complexity_level": 2,
                "importance_score": 0.85,
            },
            {
                "term": "axon",
                "definition": "Long projection of nerve cells that conducts electrical impulses away from the cell body",
                "category": ConceptCategory.ANATOMICAL,
                "anatomical_location": "neuron",
                "related_terms": ["action_potential", "axon_terminal", "myelin"],
                "complexity_level": 2,
                "importance_score": 0.88,
            },
        ]

        # Physiological concepts
        physiological_concepts = [
            {
                "term": "action_potential",
                "definition": "A rapid change in electrical potential across a neural membrane that propagates signals",
                "category": ConceptCategory.PHYSIOLOGICAL,
                "synonyms": ["nerve_impulse", "spike"],
                "abbreviations": ["AP"],
                "neural_mechanism": "electrical_signaling",
                "related_terms": ["depolarization", "repolarization", "threshold"],
                "complexity_level": 3,
                "importance_score": 0.90,
            },
            {
                "term": "synaptic_plasticity",
                "definition": "The ability of synapses to strengthen or weaken over time based on activity patterns",
                "category": ConceptCategory.PHYSIOLOGICAL,
                "neural_mechanism": "synaptic_modification",
                "related_terms": ["LTP", "LTD", "Hebbian_learning", "NMDA", "plasticity"],
                "complexity_level": 4,
                "importance_score": 0.95,
            },
            {
                "term": "long_term_potentiation",
                "definition": "A persistent strengthening of synapses based on recent patterns of activity",
                "category": ConceptCategory.PHYSIOLOGICAL,
                "synonyms": ["LTP"],
                "abbreviations": ["LTP"],
                "neural_mechanism": "synaptic_strengthening",
                "related_terms": ["NMDA_receptor", "calcium", "protein_synthesis"],
                "complexity_level": 4,
                "importance_score": 0.92,
            },
        ]

        # Molecular concepts
        molecular_concepts = [
            {
                "term": "neurotransmitter",
                "definition": "Chemical messengers that transmit signals across synapses between neurons",
                "category": ConceptCategory.MOLECULAR,
                "related_terms": ["dopamine", "serotonin", "acetylcholine", "GABA"],
                "molecular_pathway": "synaptic_transmission",
                "complexity_level": 3,
                "importance_score": 0.90,
            },
            {
                "term": "NMDA_receptor",
                "definition": "Glutamate receptor critical for synaptic plasticity and memory formation",
                "category": ConceptCategory.MOLECULAR,
                "abbreviations": ["NMDAR"],
                "molecular_pathway": "glutamatergic_signaling",
                "related_terms": ["glutamate", "calcium", "magnesium", "plasticity"],
                "complexity_level": 4,
                "importance_score": 0.88,
            },
        ]

        # Additional concepts
        additional_concepts = [
            {
                "term": "plasticity",
                "definition": "The ability of neural structures to change and adapt",
                "category": ConceptCategory.PHYSIOLOGICAL,
                "synonyms": ["neural_plasticity", "brain_plasticity"],
                "neural_mechanism": "structural_modification",
                "complexity_level": 3,
                "importance_score": 0.93,
            },
            {
                "term": "hebbian",
                "definition": "Learning rule where connections strengthen when neurons fire together",
                "category": ConceptCategory.THEORETICAL,
                "synonyms": ["hebbian_learning"],
                "neural_mechanism": "associative_learning",
                "complexity_level": 4,
                "importance_score": 0.89,
            },
            {
                "term": "calcium",
                "definition": "Essential ion for synaptic plasticity and neurotransmitter release",
                "category": ConceptCategory.MOLECULAR,
                "molecular_pathway": "calcium_signaling",
                "complexity_level": 3,
                "importance_score": 0.85,
            },
            {
                "term": "protein_synthesis",
                "definition": "Production of proteins necessary for long-term synaptic changes",
                "category": ConceptCategory.MOLECULAR,
                "molecular_pathway": "protein_synthesis",
                "complexity_level": 4,
                "importance_score": 0.82,
            },
        ]

        # Add all concepts to database
        all_concepts = (
            anatomical_concepts
            + physiological_concepts
            + molecular_concepts
            + additional_concepts
        )

        for concept_data in all_concepts:
            concept = DomainConcept(
                term=concept_data["term"],
                definition=concept_data["definition"],
                domain=DomainType.NEUROSCIENCE,
                category=concept_data["category"],
                synonyms=concept_data.get("synonyms", []),
                abbreviations=concept_data.get("abbreviations", []),
                related_terms=concept_data.get("related_terms", []),
                anatomical_location=concept_data.get("anatomical_location"),
                molecular_pathway=concept_data.get("molecular_pathway"),
                neural_mechanism=concept_data.get("neural_mechanism"),
                complexity_level=concept_data.get("complexity_level", 1),
                importance_score=concept_data.get("importance_score", 0.5),
                source="neuroscience_database",
            )
            self.concepts[concept.term] = concept

        logger.info(f"Initialized neuroscience database with {len(self.concepts)} concepts")

    def find_concept(self, term: str) -> Optional[DomainConcept]:
        """Find concept by term, synonym, or abbreviation."""
        term_lower = term.lower()

        # Direct match
        if term_lower in self.concepts:
            return self.concepts[term_lower]

        # Search synonyms and abbreviations
        for concept in self.concepts.values():
            if term_lower in [s.lower() for s in concept.synonyms] or term_lower in [
                a.lower() for a in concept.abbreviations
            ]:
                return concept

        return None

    def get_related_concepts(self, term: str) -> list[DomainConcept]:
        """Get concepts related to a given term."""
        concept = self.find_concept(term)
        if not concept:
            return []

        related = []
        for related_term in concept.related_terms:
            related_concept = self.find_concept(related_term)
            if related_concept:
                related.append(related_concept)

        return related

    def get_concepts_by_category(
        self, category: ConceptCategory
    ) -> list[DomainConcept]:
        """Get all concepts in a category."""
        return [c for c in self.concepts.values() if c.category == category]

    def search_concepts(self, query: str) -> list[DomainConcept]:
        """Search concepts by term, definition, or related terms."""
        query_lower = query.lower()
        matches = []

        for concept in self.concepts.values():
            # Check term
            if query_lower in concept.term.lower():
                matches.append(concept)
                continue

            # Check definition
            if query_lower in concept.definition.lower():
                matches.append(concept)
                continue

            # Check synonyms
            if any(query_lower in s.lower() for s in concept.synonyms):
                matches.append(concept)
                continue

            # Check related terms
            if any(query_lower in r.lower() for r in concept.related_terms):
                matches.append(concept)

        return matches
