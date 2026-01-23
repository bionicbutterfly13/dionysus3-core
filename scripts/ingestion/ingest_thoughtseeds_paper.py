#!/usr/bin/env python3
"""
Ingest Thoughtseeds paper into Neo4j knowledge graph via Graphiti.

Extracts key concepts, equations, and relationships from Kavi et al. (2024)
"Thoughtseeds: Evolutionary Priors, Nested Markov Blankets, and the Emergence of Embodied Cognition"
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Key concepts from the paper
THOUGHTSEEDS_CONCEPTS = [
    # Core framework concepts
    {
        "name": "Thoughtseed",
        "type": "concept",
        "description": "Higher-order transient Markov-blanketed construct with agency that generates content of consciousness projected on Inner Screen",
    },
    {
        "name": "Neuronal Packet",
        "type": "concept",
        "description": "Fundamental unit of neuronal representation - self-organizing ensemble of neurons encoding specific features",
    },
    {
        "name": "Superordinate Ensemble",
        "type": "concept",
        "description": "Higher-level organization emerging from coordinated activity of multiple neuronal packets",
    },
    {
        "name": "Neuronal Packet Domain",
        "type": "concept",
        "description": "Functional unit comprising interconnected superordinate ensembles specialized for specific cognitive processes",
    },
    {
        "name": "Knowledge Domain",
        "type": "concept",
        "description": "Large-scale organized structure representing interconnected networks of concepts, categories, and relationships",
    },
    {
        "name": "Inner Screen",
        "type": "concept",
        "description": "Locus of conscious experience where dominant thoughtseed content is projected - active mental workspace",
    },
    {
        "name": "Markov Blanket",
        "type": "concept",
        "description": "Statistical boundary separating internal states from external world enabling conditional independence",
    },
    {
        "name": "Core Attractor",
        "type": "concept",
        "description": "Most probable and stable pattern of neural activity within a manifested neuronal packet",
    },
    {
        "name": "Subordinate Attractor",
        "type": "concept",
        "description": "Less dominant patterns of neural activity offering flexibility and adaptability",
    },
    # Free Energy concepts
    {
        "name": "Variational Free Energy",
        "type": "concept",
        "description": "VFE - Proxy for surprise measuring discrepancy between predictions and observations",
    },
    {
        "name": "Expected Free Energy",
        "type": "concept",
        "description": "EFE - Guides policy selection quantifying expected surprise with epistemic and pragmatic components",
    },
    {
        "name": "Generalized Free Energy",
        "type": "concept",
        "description": "GFE - Extends VFE to incorporate expected consequences of actions over time horizon",
    },
    # Prior types
    {
        "name": "Basal Prior",
        "type": "concept",
        "description": "Fundamental species-wide biases from evolutionary history - core needs and behaviors",
    },
    {
        "name": "Lineage-Specific Prior",
        "type": "concept",
        "description": "Adaptations specific to lineage including ancestor priors passed through generations",
    },
    {
        "name": "Dispositional Prior",
        "type": "concept",
        "description": "Individual predispositions from genetics and development",
    },
    {
        "name": "Learned Prior",
        "type": "concept",
        "description": "Dynamic biases shaped by individual experiences throughout lifetime",
    },
    # States and processes
    {
        "name": "Active Thoughtseed Pool",
        "type": "concept",
        "description": "Set of thoughtseeds whose activation levels surpass activation threshold at given time",
    },
    {
        "name": "Dominant Thoughtseed",
        "type": "concept",
        "description": "Thoughtseed with highest activation level primarily shaping content of consciousness",
    },
    {
        "name": "Epistemic Affordance",
        "type": "concept",
        "description": "Opportunities for information gain through exploration",
    },
    {
        "name": "Pragmatic Affordance",
        "type": "concept",
        "description": "Opportunities for goal fulfillment via exploitation",
    },
    {
        "name": "Pullback Attractor",
        "type": "concept",
        "description": "Dynamic attractor integrating information from multiple sources to form coherent representations",
    },
    # Authors
    {
        "name": "Prakash Chandra Kavi",
        "type": "person",
        "description": "Lead author, Universitat Pompeu Fabra Barcelona",
    },
    {
        "name": "Gorka Zamora Lopez",
        "type": "person",
        "description": "Co-author, Center for Brain and Cognition UPF Barcelona",
    },
    {
        "name": "Daniel Ari Friedman",
        "type": "person",
        "description": "Co-author, Active Inference Institute Davis California",
    },
    # Related frameworks
    {
        "name": "Free Energy Principle",
        "type": "concept",
        "description": "Framework for understanding how organisms maintain stability by minimizing surprise (Friston)",
    },
    {
        "name": "Active Inference",
        "type": "concept",
        "description": "Process of proactively refining internal models and taking actions to minimize prediction errors",
    },
    {
        "name": "Embodied Cognition",
        "type": "concept",
        "description": "View that cognition arises from deep interdependence between brain, body, and environment",
    },
]

THOUGHTSEEDS_RELATIONSHIPS = [
    # Hierarchy
    {"source": "Neuronal Packet", "target": "Superordinate Ensemble", "type": "COMPOSES", "confidence": 0.95, "evidence": "Multiple NPs dynamically interact to form SEs (Section 4.1)"},
    {"source": "Superordinate Ensemble", "target": "Neuronal Packet Domain", "type": "COMPOSES", "confidence": 0.95, "evidence": "NPDs are comprised of interconnected SEs (Layer 1)"},
    {"source": "Neuronal Packet Domain", "target": "Knowledge Domain", "type": "PROJECTS_TO", "confidence": 0.9, "evidence": "NPDs project sensory data that KDs interpret (Figure 4)"},
    {"source": "Knowledge Domain", "target": "Thoughtseed", "type": "GENERATES", "confidence": 0.9, "evidence": "Thoughtseeds emerge from coordinated activity across KDs (Layer 3)"},
    {"source": "Thoughtseed", "target": "Inner Screen", "type": "PROJECTS_CONTENT", "confidence": 0.95, "evidence": "Dominant thoughtseed content projected onto Inner Screen (Section 4.4)"},

    # Markov blanket nesting
    {"source": "Markov Blanket", "target": "Neuronal Packet", "type": "BOUNDS", "confidence": 0.9, "evidence": "Each NP has its own Markov blanket (Section 4.1)"},
    {"source": "Markov Blanket", "target": "Superordinate Ensemble", "type": "BOUNDS", "confidence": 0.9, "evidence": "SE Markov blankets nest NP blankets (Section 4.1)"},
    {"source": "Markov Blanket", "target": "Thoughtseed", "type": "BOUNDS", "confidence": 0.95, "evidence": "Thoughtseeds establish transient Markov blankets (Key Characteristics)"},

    # Attractor dynamics
    {"source": "Core Attractor", "target": "Neuronal Packet", "type": "CHARACTERIZES", "confidence": 0.9, "evidence": "Core attractor represents NP's most stable state (Section 4.1)"},
    {"source": "Subordinate Attractor", "target": "Neuronal Packet", "type": "CHARACTERIZES", "confidence": 0.85, "evidence": "Subordinate attractors provide flexibility (Section 4.1)"},
    {"source": "Pullback Attractor", "target": "Thoughtseed", "type": "CHARACTERIZES", "confidence": 0.9, "evidence": "Thoughtseeds function as pullback attractors (Key Characteristics)"},

    # Free energy relationships
    {"source": "Variational Free Energy", "target": "Expected Free Energy", "type": "COMPONENT_OF", "confidence": 0.9, "evidence": "EFE extends VFE with expected consequences (Equation 23)"},
    {"source": "Expected Free Energy", "target": "Generalized Free Energy", "type": "COMPONENT_OF", "confidence": 0.9, "evidence": "GFE = VFE + expected EFE (Equation 23)"},
    {"source": "Epistemic Affordance", "target": "Expected Free Energy", "type": "COMPONENT_OF", "confidence": 0.9, "evidence": "EFE = epistemic + pragmatic (Equation 24)"},
    {"source": "Pragmatic Affordance", "target": "Expected Free Energy", "type": "COMPONENT_OF", "confidence": 0.9, "evidence": "EFE = epistemic + pragmatic (Equation 24)"},

    # Prior hierarchy
    {"source": "Basal Prior", "target": "Lineage-Specific Prior", "type": "CONSTRAINS", "confidence": 0.85, "evidence": "Inner layers constrain outer ones (Figure 2)"},
    {"source": "Lineage-Specific Prior", "target": "Dispositional Prior", "type": "CONSTRAINS", "confidence": 0.85, "evidence": "Quasi-hierarchical influence flow (Table 2)"},
    {"source": "Dispositional Prior", "target": "Learned Prior", "type": "CONSTRAINS", "confidence": 0.8, "evidence": "Learned priors shaped by dispositional priors (Section 9.1)"},
    {"source": "Basal Prior", "target": "Thoughtseed", "type": "SHAPES", "confidence": 0.85, "evidence": "Evolutionary priors shape thoughtseed emergence (Section 4.2)"},
    {"source": "Learned Prior", "target": "Thoughtseed", "type": "SHAPES", "confidence": 0.9, "evidence": "Learned priors continuously update internal model (Section 9.1)"},

    # Competition and selection
    {"source": "Active Thoughtseed Pool", "target": "Dominant Thoughtseed", "type": "SELECTS", "confidence": 0.9, "evidence": "Dominant selected from active pool via EFE minimization (Equation 33)"},
    {"source": "Dominant Thoughtseed", "target": "Inner Screen", "type": "CONTROLS", "confidence": 0.95, "evidence": "Single dominant shapes unitary conscious experience (Equation 34)"},

    # Framework relationships
    {"source": "Free Energy Principle", "target": "Active Inference", "type": "SUBSUMES", "confidence": 0.95, "evidence": "Active inference is core process under FEP (Introduction)"},
    {"source": "Active Inference", "target": "Thoughtseed", "type": "GOVERNS", "confidence": 0.9, "evidence": "Thoughtseeds engage in active inference (Key Characteristics)"},
    {"source": "Embodied Cognition", "target": "Thoughtseed", "type": "FRAMEWORK_FOR", "confidence": 0.85, "evidence": "Framework for biologically-grounded embodied cognition (Section 5)"},

    # Authorship
    {"source": "Prakash Chandra Kavi", "target": "Thoughtseed", "type": "PROPOSED", "confidence": 1.0, "evidence": "Lead author of Thoughtseeds paper"},
    {"source": "Daniel Ari Friedman", "target": "Active Inference Institute", "type": "AFFILIATED_WITH", "confidence": 1.0, "evidence": "Co-author affiliation"},
]

# Paper sections for chunked ingestion
PAPER_SECTIONS = [
    {
        "title": "Abstract",
        "content": """The emergence of cognition requires a framework that bridges evolutionary principles with neurocomputational mechanisms. This paper introduces the "thoughtseed" framework, proposing that cognition arises from the dynamic interaction of self-organizing units of embodied knowledge called "thoughtseeds." We leverage foundational concepts from evolutionary theory, "neuronal packets," and the "Inner Screen" hypothesis within Free Energy Principle, and propose a four-level hierarchical/heterarchical model of the cognitive agent's internal states: Neuronal Packet Domains (NPDs), Knowledge Domains (KDs), thoughtseeds network, and meta-cognition. The dynamic interplay within this hierarchy, mediated by nested Markov blankets and reciprocal message passing, facilitates the emergence of thoughtseeds as coherent patterns of activity that guide perception, action, and learning."""
    },
    {
        "title": "Introduction - Embodied Cognition",
        "content": """The Free Energy Principle (FEP) provides a unifying framework for understanding how organisms maintain stability and adapt by minimizing surprise. Organisms reduce the discrepancy between predictions from their generative models and sensory input, approximated by variational free energy (VFE). To minimize surprise or VFE, they engage in active inference – a process of proactively refining their internal models and taking actions that shape future sensory experiences. The Markov blanket, central to the FEP, separates internal states from the external world, enabling localized computations and conditional independence."""
    },
    {
        "title": "Layer 1: Neuronal Packet Domains",
        "content": """Neuronal Packets (NPs) serve as the fundamental units of neuronal representation. An NP could exist in three states: Unmanifested State (potential configuration with high prior probability), Manifested State (emerged with Markov Blanket stabilized by energy barrier, featuring core attractor and subordinate attractors), and Activated State (transient heightened neural activity). NPs compete for resources by minimizing VFE, leading to neural Darwinism and a diverse repertoire of specialized NPs. Superordinate Ensembles (SEs) emerge from coordinated NP activity, enabling representation of complex concepts across multiple scales."""
    },
    {
        "title": "Layer 2: Knowledge Domains",
        "content": """Knowledge Domains (KDs) function as large-scale organized structures within the brain's internal model, akin to knowledge graphs. They act as knowledge repositories providing conceptual scaffolding for interpreting sensory information projected from NPDs. The dynamic and context-dependent binding process within KDs contributes to the content of consciousness on the Inner Screen. KDs exhibit both hierarchical and heterarchical structures, enabling flexible knowledge retrieval."""
    },
    {
        "title": "Layer 3: Thoughtseeds Network",
        "content": """Thoughtseeds emerge from coordinated activity of distributed neural networks, generating the content of consciousness on the Inner Screen. As sub-agents, thoughtseeds engage in active inference to generate predictions, influence actions, and update internal models. When active, thoughtseeds function as pullback attractors, integrating information from multiple SEs and KDs. Thoughtseed states include: Unmanifested, Manifested (Inactive, Activated, Dominant), and Dissipated. The thoughtseed's generative model evaluates actions based on predicted outcomes, balancing exploration (epistemic affordances) and exploitation (pragmatic affordances)."""
    },
    {
        "title": "Layer 4: Meta-Cognition",
        "content": """Meta-cognition, the ability to monitor and control one's thoughts, orchestrates thoughtseed dynamics on the Inner Screen. Agent-level goals represent desired outcomes, while agent-level policies are strategies to achieve these goals. The emergence of global goals and policies can be understood through ergodic principles. The dominant thoughtseed is selected via competitive process where the thoughtseed with lowest cumulative EFE emerges. Higher-order thoughtseeds adjust attentional precision and meta-awareness parameters influencing lower-level thoughtseeds."""
    },
    {
        "title": "Mathematical Framework",
        "content": """Key equations: NP State (Eq 1), NP Generative Model (Eq 2), NP VFE (Eq 3), SE State Integration (Eq 4), Thoughtseed Characteristic States (Eq 16), Thoughtseed Goals/Policies (Eq 18-19), Affordances (Eq 20), Thoughtseed Generative Model (Eq 21), Thoughtseed VFE (Eq 22), GFE (Eq 23), EFE Decomposition (Eq 24), Activation Level (Eq 25), Active Pool (Eq 26), Dominant Selection via EFE Minimization (Eq 33), Inner Screen Content (Eq 34), Higher-Order Influence (Eq 35)."""
    },
    {
        "title": "Evolutionary Priors",
        "content": """Evolutionary priors shape an organism's cognitive landscape through phylogenetic (Basal + Lineage-specific) and ontogenetic (Dispositional + Learned) components. Basal priors represent fundamental species-wide biases - core needs and behaviors. Lineage-specific priors are adaptations for a specific lineage within its niche. Dispositional priors arise from genetic variation and developmental experiences. Learned priors evolve throughout lifetime shaped by environmental interactions. These priors form a quasi-hierarchical structure where inner layers constrain outer ones."""
    },
]


async def ingest_paper():
    """Main ingestion function."""
    from api.services.graphiti_service import get_graphiti_service

    logger.info("Initializing Graphiti service...")
    service = await get_graphiti_service()

    # 1. Ingest paper sections as episodes
    logger.info("Ingesting paper sections...")
    for section in PAPER_SECTIONS:
        content = f"[{section['title']}] {section['content']}"
        result = await service.ingest_message(
            content=content,
            source_description="Thoughtseeds Paper (Kavi et al. 2024)",
            group_id="thoughtseeds-paper",
            valid_at=datetime(2024, 1, 1),  # Paper publication date
        )
        logger.info(f"Ingested section '{section['title']}': {result.get('episode_uuid', 'N/A')}")

    # 2. Extract and ingest structured relationships
    logger.info("Ingesting structured relationships...")
    result = await service.ingest_extracted_relationships(
        relationships=[
            {**rel, "status": "approved"} for rel in THOUGHTSEEDS_RELATIONSHIPS
        ],
        source_id="thoughtseeds-paper-structured",
        group_id="thoughtseeds-paper",
    )
    logger.info(f"Ingested {result.get('ingested', 0)} relationships")

    # 3. Verify ingestion with search
    logger.info("Verifying ingestion...")
    search_result = await service.search(
        query="thoughtseed neuronal packet inner screen",
        group_ids=["thoughtseeds-paper"],
        limit=5,
    )
    logger.info(f"Found {search_result.get('count', 0)} related edges")

    return {
        "sections_ingested": len(PAPER_SECTIONS),
        "relationships_ingested": result.get("ingested", 0),
        "verification_edges": search_result.get("count", 0),
    }


if __name__ == "__main__":
    result = asyncio.run(ingest_paper())
    print(f"\n=== Ingestion Complete ===")
    print(f"Sections: {result['sections_ingested']}")
    print(f"Relationships: {result['relationships_ingested']}")
    print(f"Verification: {result['verification_edges']} edges found")
