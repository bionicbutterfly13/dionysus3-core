#!/usr/bin/env python3
"""
Ingest Metacognitive Particles Knowledge into Neo4j via Graphiti.

Feature: 038-thoughtseeds-framework
Sources:
- Sandved-Smith & Da Costa (2024): Metacognitive particles, mental action and the sense of agency
- Seragnoli et al. (2025): Metacognitive Feelings of Epistemic Gain

This script creates knowledge graph entities for:
1. Core concepts from both papers
2. Relationships between concepts
3. Attractor basin training targets

Usage:
    python scripts/ingest_metacognitive_particles.py
    
    # Or from within docker:
    docker exec dionysus-api python3 /app/scripts/ingest_metacognitive_particles.py
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.graphiti_service import get_graphiti_service, GraphitiConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_metacognitive")

# ---------------------------------------------------------------------------
# Knowledge Content for Ingestion
# ---------------------------------------------------------------------------

METACOGNITIVE_PARTICLES_CONCEPTS = [
    # Core particle types
    {
        "name": "Metacognitive Particle",
        "content": """A metacognitive particle is a cognitive particle that has beliefs about its own beliefs 
        about external states of the world. This means that a subset of the internal states mu^(2) encodes 
        posterior beliefs about another subset mu^(1). The distinction between passive and active metacognition 
        depends on whether higher-level internal paths are separated from lower-level paths by an internal 
        Markov blanket with active paths that can influence lower-level beliefs.""",
        "concepts": ["metacognitive_particle", "beliefs_about_beliefs", "mu^(2)", "mu^(1)", "internal_paths"]
    },
    {
        "name": "Passive Metacognitive Particle",
        "content": """A passive metacognitive particle has metacognitive beliefs parameterized by internal 
        paths that can only influence lower-level beliefs via shared blanket paths. The higher level internal 
        paths mu^(2) must infer lower level internal paths mu^(1) via sensory paths s, leading to the 
        metacognitive belief Q^(2)_{mu^(2)}(mu^(1)). Because mu^(1) constitutes only a subset of the 
        parameters of the particle's belief about the world, and there are no higher level active paths, 
        the particle has passive metacognition.""",
        "concepts": ["passive_metacognition", "sensory_inference", "Q^(2)_{mu^(2)}(mu^(1))", "no_active_control"]
    },
    {
        "name": "Active Metacognitive Particle",
        "content": """Active metacognitive beliefs are parameterized by higher-level internal paths that are 
        separated from lower-level paths by an internal Markov blanket. The term 'active' refers to the 
        existence of higher-level active paths a^(2) that influence lower-level internal paths mu^(1). 
        This formally encapsulates notions of 'mental actions' that modulate parameters of a lower level 
        generative model, such as posterior precision which can be seen as a proxy for attention.""",
        "concepts": ["active_metacognition", "mental_action", "a^(2)", "precision_modulation", "attention"]
    },
    {
        "name": "Strange Particle",
        "content": """Strange particles are defined such that active paths do not directly influence internal 
        paths, and random fluctuations on blanket and internal states are negligible. Although a strange 
        particle possesses agency (active paths depending on internal paths), the particle cannot infer 
        that it is the agent of its actions. From the fish's perspective, it believes it is propelled 
        through water in a fortuitous way that delivers food to its mouth - not aware it is the agent.""",
        "concepts": ["strange_particle", "agency_without_awareness", "hidden_active_paths", "coarse_graining"]
    },
    {
        "name": "Nested Particle",
        "content": """Nested particles are particles within particles. The internal paths of the inner 
        particle can hold beliefs about the lower level internal paths, which from the perspective of 
        the inner particle are external paths. This creates comprehensive metacognition where higher-level 
        internal paths encode posterior beliefs about ALL sufficient statistics of beliefs the outer 
        particle holds about the world. The active paths at higher level a^(2) can modulate parameters 
        of beliefs about the world.""",
        "concepts": ["nested_particle", "particle_within_particle", "comprehensive_metacognition", "hierarchical_depth"]
    },
    
    # Markov blanket concepts
    {
        "name": "Markov Blanket Partition",
        "content": """The system is partitioned into external (eta), boundary (b), and internal (mu) paths: 
        x = (eta, b, mu). The boundary forms a Markov blanket between external and internal paths such that 
        eta is independent of mu given b: P(eta, mu|b) = P(eta|b)P(mu|b). All interactions between internal 
        and external states happen via the boundary. The blanket is further subdivided into sensory (s) and 
        active (a) paths: b = (s, a).""",
        "concepts": ["markov_blanket", "conditional_independence", "eta", "mu", "b=(s,a)", "boundary"]
    },
    {
        "name": "Sensory and Active Paths",
        "content": """Sensory paths (s) are boundary paths that influence internal paths directly but are 
        not directly influenced by internal paths. Active paths (a) are those which influence external 
        paths directly but are not directly influenced by external paths. This creates the sensorimotor 
        loop where external states influence sensory, sensory influences internal, internal influences 
        active, and active influences external.""",
        "concepts": ["sensory_paths", "active_paths", "sensorimotor_loop", "input_surface", "output_surface"]
    },
    {
        "name": "Nesting Constraint",
        "content": """For nested Markov blankets, there is a constraint that mu^(n+1) must be a subset of 
        mu^n - higher-level internal paths are a subset of lower-level internal paths. This ensures that 
        higher levels deal with increasingly abstract/constrained state spaces. The blanket at each level 
        provides conditional independence: mu^n is independent of eta^n given b^n.""",
        "concepts": ["nesting_constraint", "subset_relationship", "hierarchical_abstraction", "conditional_independence"]
    },
    
    # Sense of agency
    {
        "name": "Sense of Agency",
        "content": """The sense of agency is captured by the joint probability distribution over lower level 
        internal and active paths: Q_{mu^(2)}(mu^(1), a^(1)). This captures the statistical relationship 
        between internal and active paths. A sense of NO agency would be when we believe internal and 
        active paths are independent: Q(mu^(1), a^(1)) = Q(mu^(1))Q(a^(1)). The strength of agency is 
        measured by the KL divergence: D_KL[Q(mu^(1), a^(1)) | Q(mu^(1))Q(a^(1))].""",
        "concepts": ["sense_of_agency", "joint_distribution", "D_KL", "mutual_information", "empowerment"]
    },
    {
        "name": "Agency Strength Measure",
        "content": """The subjective measure of agency strength is the mutual information between lower 
        level internal and active paths under our beliefs: D_KL[Q_{mu^(2)}(mu^(1), a^(1)) | Q_{mu^(2)}(mu^(1))
        Q_{mu^(2)}(a^(1))]. This can be read as a metacognitive framing of empowerment in active inference. 
        High agency means strong coupling between what I believe about my internal states and my actions.""",
        "concepts": ["agency_strength", "KL_divergence", "empowerment", "action_internal_coupling"]
    },
    
    # Cognitive core
    {
        "name": "Cognitive Core",
        "content": """There exist innermost internal paths mu^(N) that cannot be inferred by higher level 
        metacognitive beliefs. This creates a fundamental limitation on self-representation: there will 
        always be a cognitive core with internal paths encoding beliefs whilst never being the target of 
        further higher-order beliefs. As Friston stated: 'I can never conceive of what it is like to be me, 
        because that would require the number of recursions I can physically entertain, plus one.'""",
        "concepts": ["cognitive_core", "self_representation_limit", "mu^(N)", "infinite_regress", "irreducible_blanket"]
    },
    {
        "name": "Unified Experience",
        "content": """Despite the apparent separation between nested layers, the beliefs parameterised by 
        the innermost paths capture all information encoded on lower blankets. The unified belief at the 
        cognitive core is: Q_{mu^(N)}(eta, mu^(1), ..., mu^(N-1)) = Q_{mu^(1)}(eta) * product_{n=2}^N 
        Q_{mu^(n)}(mu^(n-1)). This formal object has the structure of a unified experience if we assume 
        a relationship between phenomenology and information encoded by approximate posterior belief.""",
        "concepts": ["unified_experience", "belief_product", "phenomenology", "information_geometry"]
    },
    
    # Metacognitive feelings (Seragnoli)
    {
        "name": "Metacognitive Feelings",
        "content": """Metacognitive feelings are phenomenal experiences arising from cognitive action 
        outcomes. Types include: Tip-of-tongue (TOT) - feeling of almost knowing; Aha/Eureka - insight 
        moment; Curiosity - drive to explore; Confusion - uncertainty feeling; Fluency - ease of 
        processing; Difficulty - processing strain. These arise at different phases of cognitive action: 
        goal-related, process-related, or outcome-related.""",
        "concepts": ["metacognitive_feeling", "tip_of_tongue", "aha_eureka", "curiosity", "confusion", "fluency"]
    },
    {
        "name": "Epistemic Gain",
        "content": """Epistemic gain is the outcome-related feeling from successful cognitive action - the 
        'Aha!' or 'Eureka' moment. It involves reduction in variational free energy (surprise), increase 
        in posterior precision (belief confidence), and noetic quality (sense of direct knowing). The REBUS 
        model describes how psychedelics relax beliefs, while FIBUS describes false insights where noetic 
        quality is high but the insight is non-veridical.""",
        "concepts": ["epistemic_gain", "aha_moment", "surprise_reduction", "noetic_quality", "REBUS", "FIBUS"]
    },
    {
        "name": "Procedural Metacognition",
        "content": """Procedural metacognition involves two core processes: monitoring (tracking cognitive 
        process state) and control (adjusting cognitive strategies). The cognitive action cycle proceeds: 
        hypothesis formation -> exploration -> verification -> appraisal. Each phase is associated with 
        different metacognitive feelings that guide the cognitive process toward epistemic goals.""",
        "concepts": ["procedural_metacognition", "monitoring", "control", "cognitive_action_cycle"]
    },
    
    # Equations
    {
        "name": "Langevin Dynamics",
        "content": """The system evolves according to a stochastic differential equation (Langevin equation): 
        x_dot(t) = f(x(t)) + w(t). This decomposes motion into the flow f (what we know about the system) 
        and noise w (random fluctuations). For particles with Markov blankets, the flow for internal paths 
        depends only on blanket and internal paths: f_mu(b, mu).""",
        "concepts": ["langevin_equation", "stochastic_dynamics", "flow", "noise", "markov_blanket_dynamics"]
    },
    {
        "name": "Belief Parameterization",
        "content": """A cognitive particle has internal paths that parameterize beliefs about external paths: 
        mu maps to Q_mu(eta), where Q_mu(eta) = P(eta | s, a) is the posterior belief. The internal paths 
        encode the most likely state given blanket paths: mu = argmax P(mu | s, a). For metacognitive 
        particles, mu^(2) parameterizes beliefs about mu^(1).""",
        "concepts": ["belief_parameterization", "posterior_belief", "Q_mu(eta)", "sufficient_statistics"]
    }
]

RELATIONSHIPS = [
    # Particle relationships
    {"source": "Metacognitive Particle", "target": "Passive Metacognitive Particle", "relation": "HAS_SUBTYPE"},
    {"source": "Metacognitive Particle", "target": "Active Metacognitive Particle", "relation": "HAS_SUBTYPE"},
    {"source": "Metacognitive Particle", "target": "Strange Particle", "relation": "HAS_SUBTYPE"},
    {"source": "Metacognitive Particle", "target": "Nested Particle", "relation": "HAS_SUBTYPE"},
    
    # Structure relationships
    {"source": "Markov Blanket Partition", "target": "Sensory and Active Paths", "relation": "CONTAINS"},
    {"source": "Nested Particle", "target": "Nesting Constraint", "relation": "REQUIRES"},
    {"source": "Nested Particle", "target": "Markov Blanket Partition", "relation": "CONTAINS"},
    
    # Agency relationships
    {"source": "Active Metacognitive Particle", "target": "Sense of Agency", "relation": "GROUNDS"},
    {"source": "Strange Particle", "target": "Sense of Agency", "relation": "ENABLES"},
    {"source": "Sense of Agency", "target": "Agency Strength Measure", "relation": "MEASURED_BY"},
    
    # Core relationships
    {"source": "Nested Particle", "target": "Cognitive Core", "relation": "HAS_LIMIT"},
    {"source": "Cognitive Core", "target": "Unified Experience", "relation": "PRODUCES"},
    
    # Feeling relationships
    {"source": "Procedural Metacognition", "target": "Metacognitive Feelings", "relation": "GENERATES"},
    {"source": "Metacognitive Feelings", "target": "Epistemic Gain", "relation": "RESOLVES_TO"},
    
    # Dynamics relationships
    {"source": "Langevin Dynamics", "target": "Markov Blanket Partition", "relation": "GOVERNS"},
    {"source": "Belief Parameterization", "target": "Metacognitive Particle", "relation": "DEFINES"},
]

ATTRACTOR_BASINS = [
    {
        "name": "Metacognition Basin",
        "concepts": ["beliefs_about_beliefs", "metacognitive_particle", "passive_metacognition", 
                    "active_metacognition", "metacognitive_monitoring", "metacognitive_control",
                    "higher_order_thought", "self_representation", "introspection", "meta_awareness"],
        "description": "Attractor basin for metacognitive concepts - beliefs about beliefs, monitoring and control"
    },
    {
        "name": "Agency Basin",
        "concepts": ["sense_of_agency", "action_internal_coupling", "mental_action", "active_paths",
                    "strange_particle", "empowerment", "control", "voluntary_action", "self_as_agent"],
        "description": "Attractor basin for agency concepts - action-internal coupling and empowerment"
    },
    {
        "name": "Epistemic Basin",
        "concepts": ["epistemic_gain", "insight", "aha_moment", "eureka", "learning",
                    "information_gain", "surprise_reduction", "curiosity", "exploration"],
        "description": "Attractor basin for epistemic concepts - learning, insight, and information gain"
    },
    {
        "name": "Affect Basin",
        "concepts": ["metacognitive_feeling", "valence", "tip_of_tongue", "confusion",
                    "fluency", "difficulty", "noetic_quality", "feeling_of_knowing"],
        "description": "Attractor basin for affective metacognitive feelings and their valence"
    },
    {
        "name": "Consciousness Basin",
        "concepts": ["cognitive_core", "unified_experience", "inner_screen", "phenomenal_experience",
                    "self_model", "markov_blanket", "irreducible_blanket", "non_dual_experience"],
        "description": "Attractor basin for consciousness concepts - unified experience and cognitive core"
    },
    {
        "name": "Bayesian Mechanics Basin",
        "concepts": ["free_energy_principle", "active_inference", "markov_blanket", "langevin_equation",
                    "variational_free_energy", "expected_free_energy", "generative_model", "posterior_belief"],
        "description": "Attractor basin for formal Bayesian mechanics framework concepts"
    }
]


# ---------------------------------------------------------------------------
# Ingestion Functions
# ---------------------------------------------------------------------------


async def ingest_concepts(graphiti_service) -> Dict[str, Any]:
    """Ingest all metacognitive particle concepts."""
    results = {"ingested": 0, "errors": []}
    
    for concept in METACOGNITIVE_PARTICLES_CONCEPTS:
        try:
            episode_content = f"""
            CONCEPT: {concept['name']}
            
            {concept['content']}
            
            KEY TERMS: {', '.join(concept['concepts'])}
            
            SOURCE: Metacognitive Particles (Sandved-Smith & Da Costa, 2024) / 
                    Metacognitive Feelings of Epistemic Gain (Seragnoli et al., 2025)
            """
            
            result = await graphiti_service.ingest_message(
                content=episode_content,
                source_description="metacognitive_particles_synthesis",
                group_id="dionysus_metacognition",
                valid_at=datetime.now()
            )
            
            logger.info(f"Ingested concept: {concept['name']} - {len(result.get('nodes', []))} entities")
            results["ingested"] += 1
            
        except Exception as e:
            logger.error(f"Failed to ingest {concept['name']}: {e}")
            results["errors"].append({"concept": concept['name'], "error": str(e)})
    
    return results


async def ingest_relationships(graphiti_service) -> Dict[str, Any]:
    """Ingest relationships between concepts."""
    results = {"ingested": 0, "errors": []}
    
    for rel in RELATIONSHIPS:
        try:
            fact = f"{rel['source']} {rel['relation']} {rel['target']}."
            
            result = await graphiti_service.ingest_message(
                content=fact,
                source_description="metacognitive_particles_relationships",
                group_id="dionysus_metacognition",
                valid_at=datetime.now()
            )
            
            logger.info(f"Ingested relationship: {rel['source']} -> {rel['target']}")
            results["ingested"] += 1
            
        except Exception as e:
            logger.error(f"Failed to ingest relationship {rel}: {e}")
            results["errors"].append({"relationship": rel, "error": str(e)})
    
    return results


async def ingest_attractor_basins(graphiti_service) -> Dict[str, Any]:
    """Ingest attractor basin training targets."""
    results = {"ingested": 0, "errors": []}
    
    for basin in ATTRACTOR_BASINS:
        try:
            episode_content = f"""
            ATTRACTOR BASIN: {basin['name']}
            
            {basin['description']}
            
            CORE CONCEPTS: {', '.join(basin['concepts'])}
            
            This attractor basin serves as a training target for Dionysus cognitive architecture.
            When content matches these concepts, activate this basin to strengthen related memories.
            """
            
            result = await graphiti_service.ingest_message(
                content=episode_content,
                source_description="metacognitive_attractor_basins",
                group_id="dionysus_metacognition",
                valid_at=datetime.now()
            )
            
            logger.info(f"Ingested basin: {basin['name']}")
            results["ingested"] += 1
            
        except Exception as e:
            logger.error(f"Failed to ingest basin {basin['name']}: {e}")
            results["errors"].append({"basin": basin['name'], "error": str(e)})
    
    return results


async def main():
    """Main ingestion pipeline."""
    logger.info("=" * 60)
    logger.info("Metacognitive Particles Knowledge Graph Ingestion")
    logger.info("=" * 60)
    
    # Initialize Graphiti service
    try:
        graphiti_service = await get_graphiti_service()
        logger.info("Graphiti service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Graphiti: {e}")
        return
    
    # Ingest concepts
    logger.info("\n--- Ingesting Concepts ---")
    concept_results = await ingest_concepts(graphiti_service)
    logger.info(f"Concepts: {concept_results['ingested']} ingested, {len(concept_results['errors'])} errors")
    
    # Ingest relationships
    logger.info("\n--- Ingesting Relationships ---")
    rel_results = await ingest_relationships(graphiti_service)
    logger.info(f"Relationships: {rel_results['ingested']} ingested, {len(rel_results['errors'])} errors")
    
    # Ingest attractor basins
    logger.info("\n--- Ingesting Attractor Basins ---")
    basin_results = await ingest_attractor_basins(graphiti_service)
    logger.info(f"Basins: {basin_results['ingested']} ingested, {len(basin_results['errors'])} errors")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Concepts: {concept_results['ingested']}")
    logger.info(f"Total Relationships: {rel_results['ingested']}")
    logger.info(f"Total Attractor Basins: {basin_results['ingested']}")
    logger.info(f"Total Errors: {len(concept_results['errors']) + len(rel_results['errors']) + len(basin_results['errors'])}")
    
    # Health check
    health = await graphiti_service.health_check()
    logger.info(f"\nGraphiti Health: {health}")


if __name__ == "__main__":
    asyncio.run(main())
