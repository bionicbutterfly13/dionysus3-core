"""
Cross-Domain Mapper.

Maps concepts between neuroscience and AI domains,
finding functional and mechanistic analogies.

Migrated from Dionysus 2.0 domain_specialization.py.
"""

import logging
from typing import Any, Optional

from api.models.domain_specialization import (
    CrossDomainMapping,
    DomainBridge,
    DomainType,
)
from .neuroscience_db import NeuroscienceTerminologyDatabase
from .ai_db import AITerminologyDatabase

logger = logging.getLogger(__name__)


class CrossDomainMapper:
    """Maps concepts between neuroscience and AI domains."""

    def __init__(
        self,
        neuro_db: NeuroscienceTerminologyDatabase,
        ai_db: AITerminologyDatabase,
    ):
        self.neuro_db = neuro_db
        self.ai_db = ai_db
        self.mappings: dict[str, dict[str, Any]] = {}
        self._initialize_cross_domain_mappings()

    def _initialize_cross_domain_mappings(self) -> None:
        """Initialize bidirectional concept mappings."""

        # Core mappings between biological and artificial concepts
        core_mappings = [
            {
                "neuro_concept": "neuron",
                "ai_concept": "neural_network",
                "mapping_type": "functional_analogy",
                "strength": 0.85,
                "description": "Both are basic processing units that receive, process, and transmit information",
                "similarities": ["information_processing", "connectivity", "activation"],
                "differences": [
                    "biological_vs_artificial",
                    "complexity",
                    "plasticity_mechanisms",
                ],
            },
            {
                "neuro_concept": "synapse",
                "ai_concept": "weight",
                "mapping_type": "functional_analogy",
                "strength": 0.80,
                "description": "Both represent connection strength between processing units",
                "similarities": [
                    "connection_strength",
                    "modifiability",
                    "information_transmission",
                ],
                "differences": [
                    "chemical_vs_numerical",
                    "bidirectional_vs_unidirectional",
                ],
            },
            {
                "neuro_concept": "synaptic_plasticity",
                "ai_concept": "backpropagation",
                "mapping_type": "mechanistic_analogy",
                "strength": 0.75,
                "description": "Both are learning mechanisms that modify connection strengths",
                "similarities": ["learning", "weight_modification", "experience_dependent"],
                "differences": [
                    "local_vs_global",
                    "biological_vs_algorithmic",
                    "speed",
                ],
            },
            {
                "neuro_concept": "action_potential",
                "ai_concept": "activation_function",
                "mapping_type": "functional_analogy",
                "strength": 0.70,
                "description": "Both determine when and how strongly a unit responds to inputs",
                "similarities": [
                    "threshold_based",
                    "nonlinear_response",
                    "signal_transformation",
                ],
                "differences": [
                    "temporal_vs_instantaneous",
                    "all_or_none_vs_continuous",
                ],
            },
            {
                "neuro_concept": "long_term_potentiation",
                "ai_concept": "gradient_descent",
                "mapping_type": "learning_analogy",
                "strength": 0.65,
                "description": "Both strengthen connections to improve performance",
                "similarities": [
                    "iterative_improvement",
                    "strengthening_connections",
                    "memory_formation",
                ],
                "differences": ["local_vs_global", "biological_vs_mathematical"],
            },
            {
                "neuro_concept": "plasticity",
                "ai_concept": "weight",
                "mapping_type": "functional_analogy",
                "strength": 0.85,
                "description": "Both represent modifiable connection properties that enable learning",
                "similarities": ["modifiability", "learning_basis", "experience_dependent"],
                "differences": ["biological_vs_numerical", "continuous_vs_discrete"],
            },
            {
                "neuro_concept": "hebbian",
                "ai_concept": "gradient_descent",
                "mapping_type": "learning_analogy",
                "strength": 0.70,
                "description": "Both are learning rules that strengthen beneficial connections",
                "similarities": ["learning_rule", "strengthening_mechanism", "iterative"],
                "differences": ["local_vs_global", "unsupervised_vs_supervised"],
            },
        ]

        # Store mappings bidirectionally
        for mapping in core_mappings:
            neuro_term = mapping["neuro_concept"]
            ai_term = mapping["ai_concept"]

            # Neuroscience -> AI mapping
            self.mappings[neuro_term] = {
                "target_domain": DomainType.ARTIFICIAL_INTELLIGENCE,
                "target_concept": ai_term,
                "mapping_type": mapping["mapping_type"],
                "strength": mapping["strength"],
                "description": mapping["description"],
                "similarities": mapping["similarities"],
                "differences": mapping["differences"],
            }

            # AI -> Neuroscience mapping
            self.mappings[ai_term] = {
                "target_domain": DomainType.NEUROSCIENCE,
                "target_concept": neuro_term,
                "mapping_type": mapping["mapping_type"],
                "strength": mapping["strength"],
                "description": mapping["description"],
                "similarities": mapping["similarities"],
                "differences": mapping["differences"],
            }

        logger.info(
            f"Initialized cross-domain mapper with {len(self.mappings)} mappings"
        )

    def find_cross_domain_equivalent(
        self, term: str, source_domain: DomainType
    ) -> Optional[dict[str, Any]]:
        """Find equivalent concept in the other domain."""
        if term in self.mappings:
            mapping = self.mappings[term]
            if mapping["target_domain"] != source_domain:
                return mapping
        return None

    def get_mapping(self, term: str) -> Optional[CrossDomainMapping]:
        """Get mapping as a CrossDomainMapping model."""
        if term not in self.mappings:
            return None

        mapping_data = self.mappings[term]

        # Determine source domain based on which DB has the term
        if self.neuro_db.find_concept(term):
            source_domain = DomainType.NEUROSCIENCE
        elif self.ai_db.find_concept(term):
            source_domain = DomainType.ARTIFICIAL_INTELLIGENCE
        else:
            # Unknown source, infer from target
            source_domain = (
                DomainType.NEUROSCIENCE
                if mapping_data["target_domain"] == DomainType.ARTIFICIAL_INTELLIGENCE
                else DomainType.ARTIFICIAL_INTELLIGENCE
            )

        return CrossDomainMapping(
            source_concept=term,
            source_domain=source_domain,
            target_concept=mapping_data["target_concept"],
            target_domain=mapping_data["target_domain"],
            mapping_type=mapping_data["mapping_type"],
            strength=mapping_data["strength"],
            description=mapping_data["description"],
            similarities=mapping_data["similarities"],
            differences=mapping_data["differences"],
        )

    def get_domain_bridges(self, text: str) -> list[DomainBridge]:
        """Find cross-domain concept bridges in text."""
        bridges = []
        text_lower = text.lower()

        # Find concepts from both domains in the text
        neuro_concepts_found = []
        ai_concepts_found = []

        for term in self.neuro_db.concepts:
            if term in text_lower:
                neuro_concepts_found.append(term)

        for term in self.ai_db.concepts:
            if term in text_lower:
                ai_concepts_found.append(term)

        # Find mappings between found concepts
        for neuro_term in neuro_concepts_found:
            mapping_data = self.find_cross_domain_equivalent(
                neuro_term, DomainType.NEUROSCIENCE
            )
            if mapping_data and mapping_data["target_concept"] in ai_concepts_found:
                mapping = self.get_mapping(neuro_term)
                if mapping:
                    bridge = DomainBridge(
                        neuro_concept=neuro_term,
                        ai_concept=mapping_data["target_concept"],
                        mapping=mapping,
                        bridge_strength=mapping_data["strength"],
                        context="both_domains_present",
                    )
                    bridges.append(bridge)

        return bridges

    def get_all_mappings(self) -> list[CrossDomainMapping]:
        """Get all cross-domain mappings."""
        mappings = []
        seen = set()

        for term in self.mappings:
            mapping = self.get_mapping(term)
            if mapping:
                # Avoid duplicates (since we store bidirectionally)
                key = tuple(
                    sorted([mapping.source_concept, mapping.target_concept])
                )
                if key not in seen:
                    seen.add(key)
                    mappings.append(mapping)

        return mappings

    def find_bridges_by_type(
        self, mapping_type: str
    ) -> list[CrossDomainMapping]:
        """Find all mappings of a specific type."""
        return [
            m for m in self.get_all_mappings() if m.mapping_type == mapping_type
        ]

    def get_strongest_bridges(self, limit: int = 5) -> list[CrossDomainMapping]:
        """Get the strongest cross-domain bridges."""
        mappings = self.get_all_mappings()
        return sorted(mappings, key=lambda m: m.strength, reverse=True)[:limit]
