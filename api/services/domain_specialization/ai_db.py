"""
AI/ML Terminology Database.

Comprehensive database of artificial intelligence and machine learning
concepts with metadata for domain-specific content analysis.

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


class AITerminologyDatabase:
    """Comprehensive AI/ML terminology database."""

    def __init__(self):
        self.concepts: dict[str, DomainConcept] = {}
        self._initialize_ai_database()

    def _initialize_ai_database(self) -> None:
        """Initialize with core AI/ML concepts."""

        # Algorithmic concepts
        algorithmic_concepts = [
            {
                "term": "backpropagation",
                "definition": "Algorithm for training neural networks by propagating error gradients backward through layers",
                "category": ConceptCategory.ALGORITHMIC,
                "synonyms": ["error_backpropagation", "backprop"],
                "abbreviations": ["BP"],
                "algorithm_family": "gradient_descent",
                "related_terms": [
                    "gradient",
                    "chain_rule",
                    "weight_update",
                    "learning_rate",
                ],
                "complexity_level": 4,
                "importance_score": 0.95,
            },
            {
                "term": "gradient_descent",
                "definition": "Optimization algorithm that iteratively moves toward the minimum of a loss function",
                "category": ConceptCategory.ALGORITHMIC,
                "synonyms": ["steepest_descent", "gradient_optimization"],
                "algorithm_family": "optimization",
                "related_terms": [
                    "learning_rate",
                    "loss_function",
                    "convergence",
                    "local_minimum",
                ],
                "complexity_level": 3,
                "importance_score": 0.90,
            },
            {
                "term": "neural_network",
                "definition": "Computational model inspired by biological neural networks for pattern recognition and learning",
                "category": ConceptCategory.ARCHITECTURAL,
                "synonyms": ["artificial_neural_network", "ANN"],
                "abbreviations": ["NN", "ANN"],
                "related_terms": ["layer", "neuron", "weight", "activation_function"],
                "complexity_level": 3,
                "importance_score": 0.95,
            },
        ]

        # Architectural concepts
        architectural_concepts = [
            {
                "term": "convolutional_neural_network",
                "definition": "Deep learning architecture using convolution operations, particularly effective for image processing",
                "category": ConceptCategory.ARCHITECTURAL,
                "synonyms": ["CNN", "ConvNet"],
                "abbreviations": ["CNN"],
                "algorithm_family": "deep_learning",
                "related_terms": ["convolution", "pooling", "filter", "feature_map"],
                "complexity_level": 4,
                "importance_score": 0.88,
            },
            {
                "term": "transformer",
                "definition": "Neural network architecture based on self-attention mechanisms for sequence modeling",
                "category": ConceptCategory.ARCHITECTURAL,
                "algorithm_family": "attention_based",
                "related_terms": ["attention", "self_attention", "encoder", "decoder"],
                "complexity_level": 5,
                "importance_score": 0.92,
            },
            {
                "term": "convolutional",
                "definition": "Type of neural network layer using convolution operations",
                "category": ConceptCategory.ARCHITECTURAL,
                "synonyms": ["conv", "convolution"],
                "algorithm_family": "cnn",
                "complexity_level": 4,
                "importance_score": 0.85,
            },
        ]

        # Theoretical concepts
        theoretical_concepts = [
            {
                "term": "machine_learning",
                "definition": "Field of study that gives computers ability to learn without being explicitly programmed",
                "category": ConceptCategory.THEORETICAL,
                "synonyms": ["ML"],
                "abbreviations": ["ML"],
                "related_terms": [
                    "supervised_learning",
                    "unsupervised_learning",
                    "reinforcement_learning",
                ],
                "complexity_level": 2,
                "importance_score": 0.95,
            },
            {
                "term": "deep_learning",
                "definition": "Machine learning using neural networks with multiple hidden layers",
                "category": ConceptCategory.THEORETICAL,
                "synonyms": ["DL"],
                "abbreviations": ["DL"],
                "algorithm_family": "neural_networks",
                "related_terms": [
                    "neural_network",
                    "representation_learning",
                    "feature_learning",
                ],
                "complexity_level": 4,
                "importance_score": 0.92,
            },
        ]

        # Additional AI concepts
        additional_ai_concepts = [
            {
                "term": "weight",
                "definition": "Parameter in neural networks representing connection strength",
                "category": ConceptCategory.ALGORITHMIC,
                "synonyms": ["weights", "parameters"],
                "algorithm_family": "neural_networks",
                "complexity_level": 2,
                "importance_score": 0.90,
            },
            {
                "term": "activation_function",
                "definition": "Non-linear function applied to neural network outputs to introduce non-linearity",
                "category": ConceptCategory.ALGORITHMIC,
                "synonyms": ["activation"],
                "algorithm_family": "neural_networks",
                "related_terms": ["ReLU", "sigmoid", "tanh", "softmax"],
                "complexity_level": 3,
                "importance_score": 0.85,
            },
            {
                "term": "loss_function",
                "definition": "Function that measures the difference between predicted and actual outputs",
                "category": ConceptCategory.ALGORITHMIC,
                "synonyms": ["cost_function", "objective_function"],
                "algorithm_family": "optimization",
                "related_terms": [
                    "cross_entropy",
                    "mean_squared_error",
                    "gradient_descent",
                ],
                "complexity_level": 3,
                "importance_score": 0.88,
            },
            {
                "term": "attention",
                "definition": "Mechanism allowing models to focus on relevant parts of input when producing output",
                "category": ConceptCategory.ARCHITECTURAL,
                "synonyms": ["attention_mechanism"],
                "algorithm_family": "attention_based",
                "related_terms": ["self_attention", "transformer", "query", "key", "value"],
                "complexity_level": 4,
                "importance_score": 0.90,
            },
        ]

        # Add all concepts to database
        all_concepts = (
            algorithmic_concepts
            + architectural_concepts
            + theoretical_concepts
            + additional_ai_concepts
        )

        for concept_data in all_concepts:
            concept = DomainConcept(
                term=concept_data["term"],
                definition=concept_data["definition"],
                domain=DomainType.ARTIFICIAL_INTELLIGENCE,
                category=concept_data["category"],
                synonyms=concept_data.get("synonyms", []),
                abbreviations=concept_data.get("abbreviations", []),
                related_terms=concept_data.get("related_terms", []),
                algorithm_family=concept_data.get("algorithm_family"),
                complexity_level=concept_data.get("complexity_level", 1),
                importance_score=concept_data.get("importance_score", 0.5),
                source="ai_database",
            )
            self.concepts[concept.term] = concept

        logger.info(f"Initialized AI database with {len(self.concepts)} concepts")

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

    def get_concepts_by_algorithm_family(
        self, algorithm_family: str
    ) -> list[DomainConcept]:
        """Get all concepts in an algorithm family."""
        return [
            c
            for c in self.concepts.values()
            if c.algorithm_family == algorithm_family
        ]

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
