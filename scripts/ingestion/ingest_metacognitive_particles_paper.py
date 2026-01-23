#!/usr/bin/env python3
"""
Ingest Metacognitive Particles paper into Neo4j knowledge graph via Graphiti.

Extracts key concepts, equations, and relationships from Sandved-Smith & Da Costa (2024)
"Metacognitive particles, mental action and the sense of agency"

Feature: 038-thoughtseeds-framework
Memory Types: Episodic (paper sections), Semantic (concepts), Procedural (formulas), Strategic (architecture)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# SEMANTIC MEMORY: Core concepts from the paper
# =============================================================================
METACOGNITIVE_CONCEPTS = [
    # Core framework concepts
    {
        "name": "Metacognitive Particle",
        "type": "concept",
        "description": "A system with beliefs about its own beliefs - capable of monitoring and potentially modulating lower-level cognitive processes",
        "memory_type": "semantic",
    },
    {
        "name": "Cognitive Particle",
        "type": "concept",
        "description": "A system with beliefs about external states but no beliefs about its own beliefs - basic cognitive unit",
        "memory_type": "semantic",
    },
    {
        "name": "Passive Metacognition",
        "type": "concept",
        "description": "Metacognition that only observes lower-level beliefs without modulating them - monitoring without intervention",
        "memory_type": "semantic",
    },
    {
        "name": "Active Metacognition",
        "type": "concept",
        "description": "Metacognition where higher-level active paths (a^2) modulate lower-level beliefs (mu^1) - mental actions",
        "memory_type": "semantic",
    },
    {
        "name": "Mental Action",
        "type": "concept",
        "description": "Actions taken by metacognitive level that modulate lower-level belief parameters like precision or attention",
        "memory_type": "semantic",
    },
    {
        "name": "Strange Particle",
        "type": "concept",
        "description": "System where active paths cannot directly influence internal paths - must infer via sensory observation",
        "memory_type": "semantic",
    },
    {
        "name": "Cognitive Core",
        "type": "concept",
        "description": "Innermost mu^N paths that cannot be targets of further metacognitive beliefs - protected core states",
        "memory_type": "semantic",
    },
    {
        "name": "Sense of Agency",
        "type": "concept",
        "description": "Statistical dependence between internal and active paths measured via KL divergence",
        "memory_type": "semantic",
    },
    # Markov blanket concepts
    {
        "name": "Nested Markov Blanket",
        "type": "concept",
        "description": "Hierarchical boundaries where higher-level blankets encompass lower-level ones - eta/b/mu partition at each level",
        "memory_type": "semantic",
    },
    {
        "name": "External Paths (eta)",
        "type": "concept",
        "description": "Paths outside the Markov blanket - environmental states not directly observable",
        "memory_type": "semantic",
    },
    {
        "name": "Sensory Paths (s)",
        "type": "concept",
        "description": "Input surface of Markov blanket - how internal states receive information from environment",
        "memory_type": "semantic",
    },
    {
        "name": "Active Paths (a)",
        "type": "concept",
        "description": "Output surface of Markov blanket - how internal states influence environment",
        "memory_type": "semantic",
    },
    {
        "name": "Internal Paths (mu)",
        "type": "concept",
        "description": "States within the Markov blanket - internal model states conditionally independent of external given blanket",
        "memory_type": "semantic",
    },
    # Authors
    {
        "name": "Lars Sandved-Smith",
        "type": "person",
        "description": "Lead author, researcher in metacognition and Bayesian mechanics",
        "memory_type": "semantic",
    },
    {
        "name": "Lancelot Da Costa",
        "type": "person",
        "description": "Co-author, expert in free energy principle and active inference mathematics",
        "memory_type": "semantic",
    },
]

# =============================================================================
# SEMANTIC MEMORY: Relationships between concepts
# =============================================================================
METACOGNITIVE_RELATIONSHIPS = [
    # Hierarchy of particles
    {
        "source": "Cognitive Particle",
        "target": "Metacognitive Particle",
        "type": "EXTENDS_TO",
        "confidence": 0.95,
        "evidence": "Metacognitive particles add beliefs-about-beliefs to cognitive particles (Section 2-3)",
    },
    {
        "source": "Passive Metacognition",
        "target": "Metacognitive Particle",
        "type": "VARIANT_OF",
        "confidence": 0.9,
        "evidence": "Passive metacognition is minimal form - observes but doesn't modulate (Section 4)",
    },
    {
        "source": "Active Metacognition",
        "target": "Passive Metacognition",
        "type": "EXTENDS",
        "confidence": 0.95,
        "evidence": "Active metacognition adds modulation capability to passive observation (Section 5)",
    },
    {
        "source": "Mental Action",
        "target": "Active Metacognition",
        "type": "COMPONENT_OF",
        "confidence": 0.9,
        "evidence": "Mental actions are the mechanism by which active metacognition modulates beliefs (Section 5)",
    },
    # Strange particle constraints
    {
        "source": "Strange Particle",
        "target": "Metacognitive Particle",
        "type": "CONSTRAINT_ON",
        "confidence": 0.85,
        "evidence": "Strange particle architecture prevents direct a->mu influence (Section 6)",
    },
    {
        "source": "Strange Particle",
        "target": "Sensory Paths (s)",
        "type": "REQUIRES",
        "confidence": 0.9,
        "evidence": "Strange particles must infer lower states through sensory observation (Section 6)",
    },
    # Markov blanket structure
    {
        "source": "Nested Markov Blanket",
        "target": "External Paths (eta)",
        "type": "CONTAINS",
        "confidence": 0.95,
        "evidence": "eta paths are outside the blanket boundary (Definition 1)",
    },
    {
        "source": "Nested Markov Blanket",
        "target": "Sensory Paths (s)",
        "type": "CONTAINS",
        "confidence": 0.95,
        "evidence": "Sensory paths are part of the blanket boundary (Definition 1)",
    },
    {
        "source": "Nested Markov Blanket",
        "target": "Active Paths (a)",
        "type": "CONTAINS",
        "confidence": 0.95,
        "evidence": "Active paths are part of the blanket boundary (Definition 1)",
    },
    {
        "source": "Nested Markov Blanket",
        "target": "Internal Paths (mu)",
        "type": "CONTAINS",
        "confidence": 0.95,
        "evidence": "Internal paths are inside the blanket boundary (Definition 1)",
    },
    # Sense of agency
    {
        "source": "Sense of Agency",
        "target": "Internal Paths (mu)",
        "type": "MEASURES_DEPENDENCE_OF",
        "confidence": 0.9,
        "evidence": "Agency = KL divergence of joint vs marginal of mu and a (Section 7)",
    },
    {
        "source": "Sense of Agency",
        "target": "Active Paths (a)",
        "type": "MEASURES_DEPENDENCE_OF",
        "confidence": 0.9,
        "evidence": "Agency = KL divergence of joint vs marginal of mu and a (Section 7)",
    },
    # Cognitive core
    {
        "source": "Cognitive Core",
        "target": "Internal Paths (mu)",
        "type": "INNERMOST_OF",
        "confidence": 0.85,
        "evidence": "Cognitive core is mu^N - cannot be target of further metacognition (Section 8)",
    },
    # Authorship
    {
        "source": "Lars Sandved-Smith",
        "target": "Metacognitive Particle",
        "type": "PROPOSED",
        "confidence": 1.0,
        "evidence": "Lead author of Metacognitive Particles paper",
    },
    {
        "source": "Lancelot Da Costa",
        "target": "Metacognitive Particle",
        "type": "CO_PROPOSED",
        "confidence": 1.0,
        "evidence": "Co-author providing mathematical formalism",
    },
]

# =============================================================================
# PROCEDURAL MEMORY: Mathematical formulas and equations
# =============================================================================
PROCEDURAL_KNOWLEDGE = [
    {
        "name": "Langevin Equation for Particle Dynamics",
        "formula": "dx = f(x)dt + sigma(x)dW",
        "description": "Stochastic differential equation governing particle state evolution over time",
        "application": "Used to model how cognitive/metacognitive particle states evolve",
        "memory_type": "procedural",
    },
    {
        "name": "Conditional Independence via Markov Blanket",
        "formula": "mu _|_ eta | b",
        "description": "Internal paths are conditionally independent of external paths given the blanket",
        "application": "Foundation for isolating cognitive processes from environment",
        "memory_type": "procedural",
    },
    {
        "name": "Sense of Agency Formula",
        "formula": "D_KL[p(mu,a) || p(mu)p(a)]",
        "description": "KL divergence between joint distribution and product of marginals",
        "application": "Measures statistical dependence between internal states and actions - high KL = agency",
        "memory_type": "procedural",
    },
    {
        "name": "Precision-Weighted Belief Update",
        "formula": "mu_new = (pi_prior * mu_prior + pi_obs * obs) / (pi_prior + pi_obs)",
        "description": "Bayesian update weighted by precision (inverse variance)",
        "application": "How beliefs are updated with precision weighting - mental actions can modulate precision",
        "memory_type": "procedural",
    },
    {
        "name": "Nested Blanket Constraint",
        "formula": "mu^(n+1) subset mu^n",
        "description": "Higher-level internal paths are subset of lower-level internal paths",
        "application": "Ensures proper nesting of Markov blanket hierarchy",
        "memory_type": "procedural",
    },
]

# =============================================================================
# STRATEGIC MEMORY: Architecture patterns and design decisions
# =============================================================================
STRATEGIC_PATTERNS = [
    {
        "name": "Passive-First Metacognition Pattern",
        "pattern": "Implement passive observation before active modulation",
        "rationale": "Passive metacognition is prerequisite for active - must observe before modulating",
        "implementation": "Start with logging/monitoring, then add parameter modulation",
        "memory_type": "strategic",
    },
    {
        "name": "Strange Particle Constraint Pattern",
        "pattern": "Prevent direct active->internal influence paths",
        "rationale": "Biologically realistic - higher cognition cannot directly read lower states",
        "implementation": "All cross-level observation must go through sensory interface",
        "memory_type": "strategic",
    },
    {
        "name": "Cognitive Core Protection Pattern",
        "pattern": "Protect innermost beliefs from metacognitive modification",
        "rationale": "Core identity/values should not be modifiable by metacognition",
        "implementation": "Define protected belief set, reject modification attempts",
        "memory_type": "strategic",
    },
    {
        "name": "Precision Modulation Pattern",
        "pattern": "Mental actions modulate precision rather than mean beliefs",
        "rationale": "More biologically plausible - attention adjusts confidence not content",
        "implementation": "Add precision parameter to beliefs, mental actions adjust precision",
        "memory_type": "strategic",
    },
    {
        "name": "Agency Detection Pattern",
        "pattern": "Use KL divergence to detect self-caused vs external changes",
        "rationale": "Statistical measure of agency without metaphysical assumptions",
        "implementation": "Calculate KL between joint and marginal distributions of mu and a",
        "memory_type": "strategic",
    },
]

# =============================================================================
# EPISODIC MEMORY: Paper sections for chunked ingestion
# =============================================================================
PAPER_SECTIONS = [
    {
        "title": "Abstract",
        "content": """This paper leverages Bayesian mechanics to explore the formal properties of metacognitive systems in terms of the constraints that they place on the internal structure of particles. We define particles as systems that possess beliefs or inference capabilities pertaining to states beyond their boundaries. We first introduce cognitive particles, systems that have beliefs about external states, but not about their own beliefs. We then examine what further structure is needed for particles that do have beliefs about their own beliefs, which we call metacognitive particles. In particular, we distinguish between passive metacognitive particles and their active counterparts, where the latter engage in mental actions.""",
        "memory_type": "episodic",
    },
    {
        "title": "1. Introduction - Bayesian Mechanics Framework",
        "content": """Bayesian mechanics is a physics of beliefs. It studies the mechanical properties of systems that can be said to have 'beliefs' or 'inference capabilities' - which we call 'particles'. This framework allows formalizing cognitive systems in terms of Markov blankets and free energy principles. We extend this to metacognition - beliefs about beliefs - which requires nested Markov blanket structures.""",
        "memory_type": "episodic",
    },
    {
        "title": "2. Cognitive Particles - Basic Belief Systems",
        "content": """A cognitive particle is a system that has beliefs about external states but not about its own beliefs. Formally, internal paths mu encode beliefs about external paths eta, mediated by the Markov blanket b = (s, a). The key property is conditional independence: mu is independent of eta given b. This defines the boundary between self and world.""",
        "memory_type": "episodic",
    },
    {
        "title": "3. Metacognitive Particles - Beliefs About Beliefs",
        "content": """A metacognitive particle extends cognitive particles by having beliefs about its own beliefs. This requires nested structure: external world eta, first-level blanket b1, first-level internal mu1 (which forms the 'external' for the second level), second-level blanket b2, second-level internal mu2. The mu2 paths encode beliefs about mu1 - metacognition.""",
        "memory_type": "episodic",
    },
    {
        "title": "4. Passive Metacognitive Particle",
        "content": """A passive metacognitive particle observes its own beliefs without modulating them. The higher-level active paths a2 do not influence the lower-level internal paths mu1. This is the minimal form of metacognition - monitoring without intervention. Such a system can have beliefs about its beliefs but cannot engage in mental actions.""",
        "memory_type": "episodic",
    },
    {
        "title": "5. Active Metacognition and Mental Actions",
        "content": """Active metacognition occurs when higher-level active paths a2 can modulate lower-level belief parameters. This constitutes 'mental action' - using metacognitive beliefs to influence cognitive processes. Examples include attention allocation (modulating precision), working memory maintenance, and cognitive control. The key insight is that mental actions target parameters like precision rather than belief content directly.""",
        "memory_type": "episodic",
    },
    {
        "title": "6. Strange Metacognitive Particles",
        "content": """A strange particle is one where active paths cannot directly influence internal paths - they must act through the environment. For metacognitive particles, this means a2 cannot directly access mu1; it must infer mu1 state through sensory observation s2. This constraint makes metacognition more realistic - we cannot directly introspect our neural states but must infer them from their effects.""",
        "memory_type": "episodic",
    },
    {
        "title": "7. Sense of Agency",
        "content": """The sense of agency can be formalized as the statistical dependence between internal and active paths: D_KL[p(mu,a) || p(mu)p(a)]. High KL divergence indicates strong coupling - actions are determined by internal states, not external factors. Zero KL means independence - no agency, mere coincidence. This provides a mathematical foundation for phenomenological agency.""",
        "memory_type": "episodic",
    },
    {
        "title": "8. Higher Forms of Metacognition",
        "content": """The framework extends to N levels of nesting. Each level adds metacognitive capability about the level below. However, there must be a 'cognitive core' - the innermost mu^N paths that cannot be targets of further metacognitive beliefs. This prevents infinite regress and provides stable ground for the metacognitive hierarchy.""",
        "memory_type": "episodic",
    },
]


async def ingest_paper():
    """Main ingestion function with memory type routing."""
    from api.services.graphiti_service import get_graphiti_service
    from api.services.kg_learning_service import get_kg_learning_service

    logger.info("Initializing services...")
    graphiti = await get_graphiti_service()
    kg_learning = get_kg_learning_service()

    results = {
        "episodic": {"ingested": 0, "errors": []},
        "semantic": {"ingested": 0, "errors": []},
        "procedural": {"ingested": 0, "errors": []},
        "strategic": {"ingested": 0, "errors": []},
    }

    # 1. Ingest EPISODIC memory (paper sections)
    logger.info("Ingesting EPISODIC memory (paper sections)...")
    for section in PAPER_SECTIONS:
        try:
            content = f"[{section['title']}] {section['content']}"
            result = await graphiti.ingest_message(
                content=content,
                source_description="Metacognitive Particles Paper (Sandved-Smith & Da Costa, 2024)",
                group_id="metacognitive-particles-paper",
                valid_at=datetime(2024, 1, 1),
            )
            results["episodic"]["ingested"] += 1
            logger.info(f"Ingested section '{section['title']}': {result.get('episode_uuid', 'N/A')}")
        except Exception as e:
            results["episodic"]["errors"].append({"section": section["title"], "error": str(e)})
            logger.error(f"Failed to ingest section '{section['title']}': {e}")

    # 2. Ingest SEMANTIC memory (concepts and relationships)
    logger.info("Ingesting SEMANTIC memory (concepts and relationships)...")

    # Concepts as episodes
    for concept in METACOGNITIVE_CONCEPTS:
        try:
            content = f"CONCEPT: {concept['name']}\nTYPE: {concept['type']}\nDESCRIPTION: {concept['description']}"
            await graphiti.ingest_message(
                content=content,
                source_description="Metacognitive Particles Paper - Semantic Extraction",
                group_id="metacognitive-particles-semantic",
            )
            results["semantic"]["ingested"] += 1
        except Exception as e:
            results["semantic"]["errors"].append({"concept": concept["name"], "error": str(e)})

    # Relationships via kg_learning for basin integration
    for rel in METACOGNITIVE_RELATIONSHIPS:
        try:
            formatted_rel = {
                "source": rel["source"],
                "target": rel["target"],
                "relation_type": rel["type"],
                "confidence": rel["confidence"],
                "evidence": rel["evidence"],
                "status": "approved" if rel["confidence"] >= 0.6 else "pending_review",
            }
            await graphiti.ingest_extracted_relationships(
                relationships=[formatted_rel],
                source_id="metacognitive-particles-semantic",
                group_id="metacognitive-particles-semantic",
            )
            results["semantic"]["ingested"] += 1
        except Exception as e:
            results["semantic"]["errors"].append({"relationship": f"{rel['source']}->{rel['target']}", "error": str(e)})

    # 3. Ingest PROCEDURAL memory (formulas and equations)
    logger.info("Ingesting PROCEDURAL memory (formulas)...")
    for proc in PROCEDURAL_KNOWLEDGE:
        try:
            content = (
                f"FORMULA: {proc['name']}\n"
                f"EXPRESSION: {proc['formula']}\n"
                f"DESCRIPTION: {proc['description']}\n"
                f"APPLICATION: {proc['application']}"
            )
            await graphiti.ingest_message(
                content=content,
                source_description="Metacognitive Particles Paper - Procedural Extraction",
                group_id="metacognitive-particles-procedural",
            )
            results["procedural"]["ingested"] += 1
        except Exception as e:
            results["procedural"]["errors"].append({"formula": proc["name"], "error": str(e)})

    # 4. Ingest STRATEGIC memory (architecture patterns)
    logger.info("Ingesting STRATEGIC memory (patterns)...")
    for pattern in STRATEGIC_PATTERNS:
        try:
            content = (
                f"PATTERN: {pattern['name']}\n"
                f"APPROACH: {pattern['pattern']}\n"
                f"RATIONALE: {pattern['rationale']}\n"
                f"IMPLEMENTATION: {pattern['implementation']}"
            )
            await graphiti.ingest_message(
                content=content,
                source_description="Metacognitive Particles Paper - Strategic Extraction",
                group_id="metacognitive-particles-strategic",
            )
            results["strategic"]["ingested"] += 1
        except Exception as e:
            results["strategic"]["errors"].append({"pattern": pattern["name"], "error": str(e)})

    # 5. Verify ingestion with search
    logger.info("Verifying ingestion...")
    search_result = await graphiti.search(
        query="metacognitive particle markov blanket sense of agency",
        group_ids=[
            "metacognitive-particles-paper",
            "metacognitive-particles-semantic",
            "metacognitive-particles-procedural",
            "metacognitive-particles-strategic",
        ],
        limit=10,
    )

    return {
        "results": results,
        "verification_edges": search_result.get("count", 0),
        "totals": {
            "episodic": results["episodic"]["ingested"],
            "semantic": results["semantic"]["ingested"],
            "procedural": results["procedural"]["ingested"],
            "strategic": results["strategic"]["ingested"],
        },
    }


if __name__ == "__main__":
    result = asyncio.run(ingest_paper())
    print("\n=== Metacognitive Particles Paper Ingestion Complete ===")
    print(f"EPISODIC (paper sections): {result['totals']['episodic']}")
    print(f"SEMANTIC (concepts/relationships): {result['totals']['semantic']}")
    print(f"PROCEDURAL (formulas): {result['totals']['procedural']}")
    print(f"STRATEGIC (patterns): {result['totals']['strategic']}")
    print(f"Verification: {result['verification_edges']} edges found")

    # Report errors
    for mem_type, data in result["results"].items():
        if data["errors"]:
            print(f"\n{mem_type.upper()} ERRORS:")
            for err in data["errors"]:
                print(f"  - {err}")
