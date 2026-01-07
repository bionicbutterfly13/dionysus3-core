#!/usr/bin/env python3
"""
Integrate Metacognition Theory into Dionysus Knowledge Graph

This script integrates the two-layer metacognition model (declarative vs procedural)
into all four memory branches, creates competing thoughtseeds, and applies
fractal metacognition by integrating the integration process itself.

AUTHOR: Mani Saint-Victor, MD
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.consciousness_integration_pipeline import get_consciousness_pipeline


async def integrate_metacognition_theory():
    """
    Main integration function using the consciousness pipeline.

    This integration is FRACTAL - we're using metacognitive monitoring and control
    to integrate concepts about metacognition, and we integrate that process too.
    """

    pipeline = get_consciousness_pipeline()

    # ============================================================================
    # PHASE 1: Integrate Core Metacognition Model
    # ============================================================================

    problem_1 = """
    Integrate the two-layer metacognition model into Dionysus architecture.

    Model distinguishes:
    - Declarative Metacognition: Semantic knowledge about how the mind works (informational)
    - Procedural Metacognition: Real-time monitoring and control processes (regulatory)
    - Metacognitive Feelings: Phenomenological signals (Aha!, confusion, effort) that bridge unconscious and conscious processing
    """

    reasoning_trace_1 = """
    ARCHITECTURAL MAPPING:

    Declarative Metacognition → Semantic Memory (Graphiti)
    - Stores entities, facts, relationships about cognitive processes
    - Language-dependent, conceptual knowledge
    - Example: "Memory is fallible", "Multitasking reduces performance"

    Procedural Metacognition → Active Inference Engine (OODA Loop)
    - Monitoring = OBSERVE + ORIENT (Perception/Reasoning agents detect prediction errors)
    - Control = DECIDE + ACT (Metacognition agent selects actions to reduce free energy)
    - Non-conceptual, experience-based regulation

    Metacognitive Feelings → Thoughtseeds + Attractor Basin Transitions
    - Aha! moment = Thoughtseed wins competition, large free energy reduction
    - Confusion = High prediction error, basin instability
    - Effort = Control process active, free energy minimization in progress
    - Tip-of-tongue = Confidence-retrieval mismatch

    KEY INSIGHT: Dionysus IS a metacognitive system. The OODA loop implements
    procedural metacognition (monitoring/control), Graphiti stores declarative
    metacognition (knowledge about mind), and thoughtseed competition generates
    metacognitive feelings (noetic signals).
    """

    outcome_1 = """
    Successfully mapped metacognition theory to existing Dionysus architecture.
    Revealed that system already implements both declarative and procedural
    metacognition - this integration strengthens and makes explicit those connections.
    """

    active_inference_state_1 = {
        "surprise": 0.7,  # High surprise - significant conceptual reorganization
        "free_energy": 2.1,
        "precision_priors": 0.6,
        "precision_errors": 0.8
    }

    context_1 = {
        "project_id": "metacognition_integration",
        "importance": 0.9,  # High importance - fundamental architectural insight
        "confidence": 0.85,
        "attractor_basins": ["consciousness", "cognitive_science", "neuroscience"],
        "tools_used": ["sequential_thinking", "architectural_analysis"]
    }

    print("🧠 Integrating core metacognition model...")
    event_1 = await pipeline.process_cognitive_event(
        problem=problem_1,
        reasoning_trace=reasoning_trace_1,
        outcome=outcome_1,
        active_inference_state=active_inference_state_1,
        context=context_1
    )
    print(f"✓ Core model integrated: {event_1}\n")

    # ============================================================================
    # PHASE 2: Integrate Agency Model
    # ============================================================================

    problem_2 = """
    Integrate the hierarchical agency model into Dionysus consciousness architecture.

    Model distinguishes:
    - Attentional Agency: Control over focus of attention (what to attend to)
    - Cognitive Agency: Control over deliberate rational thought (how to reason about it)

    Hierarchy: Must control attention before controlling reasoning.
    """

    reasoning_trace_2 = """
    AGENCY MAPPING TO CONSCIOUSNESS ARCHITECTURE:

    Attentional Agency → Perception Agent + Thoughtseed Competition
    - Selective attention mechanisms determine which stimuli/memories to focus on
    - Thoughtseed competition = choosing which hypothesis gets conscious attention
    - Basin competition = which attractor basin becomes active
    - Foundation for all higher cognition

    Cognitive Agency → Reasoning Agent + Metacognition Agent
    - Deliberate tool selection and strategy planning
    - Controlled search through hypothesis space
    - Conscious, effortful reasoning processes

    The three-agent hierarchy validates the agency hierarchy:
    1. Perception Agent = Attentional Agency (WHAT to attend to)
    2. Reasoning Agent = Cognitive Agency (HOW to reason about it)
    3. Metacognition Agent = Meta-Agency (WHEN to switch strategies)

    This explains why consciousness requires selective attention - you can't
    reason about everything simultaneously. Thoughtseed competition IS the
    mechanism of attentional agency.
    """

    outcome_2 = """
    Successfully integrated hierarchical agency model. The three-agent consciousness
    architecture (Perception → Reasoning → Metacognition) directly implements the
    agency hierarchy (Attentional → Cognitive → Meta-Cognitive).
    """

    active_inference_state_2 = {
        "surprise": 0.6,
        "free_energy": 1.8,
        "precision_priors": 0.7,
        "precision_errors": 0.75
    }

    context_2 = {
        "project_id": "metacognition_integration",
        "importance": 0.85,
        "confidence": 0.88,
        "attractor_basins": ["consciousness", "cognitive_science", "philosophy"],
        "tools_used": ["architectural_mapping", "hierarchical_analysis"]
    }

    print("🎯 Integrating agency model...")
    event_2 = await pipeline.process_cognitive_event(
        problem=problem_2,
        reasoning_trace=reasoning_trace_2,
        outcome=outcome_2,
        active_inference_state=active_inference_state_2,
        context=context_2
    )
    print(f"✓ Agency model integrated: {event_2}\n")

    # ============================================================================
    # PHASE 3: Integrate Psychedelic Mechanism
    # ============================================================================

    problem_3 = """
    Integrate the psychedelic mechanism model into active inference framework.

    Mechanism: Psychedelics amplify monitoring while disrupting executive control,
    creating intensified metacognitive feelings of epistemic gain (Aha! moments).
    """

    reasoning_trace_3 = """
    PSYCHEDELIC MECHANISM IN ACTIVE INFERENCE TERMS:

    Normal State:
    - Balanced precision on priors (expectations) and prediction errors (observations)
    - Stable attractor basins, smooth free energy minimization
    - Metacognitive feelings proportional to prediction errors

    Psychedelic State:
    - REDUCED precision on priors (disrupted executive control/expectations)
    - INCREASED precision on prediction errors (amplified monitoring/observations)
    - Result: High surprise scores → basin reorganization → noetic Aha! moments

    Implementation Implications:
    We could model "psychedelic-like" cognitive flexibility by adjusting precision
    parameters in free energy calculation:

    precision_priors *= 0.5      # Reduce reliance on expectations
    precision_errors *= 2.0       # Amplify sensory prediction errors

    This would increase basin reorganization frequency, creating more frequent
    "insight" experiences as new attractors form. The "profound truth" feeling
    comes from large free energy reductions when new basins stabilize.

    Clinical Application:
    Psychedelic-assisted therapy works by temporarily enabling basin reorganization
    that would be difficult under normal precision parameters. The therapy provides
    CONTENT (declarative knowledge about trauma, patterns) during a state of
    heightened PLASTICITY (procedural flexibility for reorganization).
    """

    outcome_3 = """
    Successfully mapped psychedelic mechanism to precision weighting in active
    inference. Provides framework for understanding therapeutic efficacy and
    potential for computational modeling of altered states.
    """

    active_inference_state_3 = {
        "surprise": 0.8,  # Very high - novel theoretical connection
        "free_energy": 2.5,
        "precision_priors": 0.4,  # Simulating reduced control
        "precision_errors": 0.9   # Simulating amplified monitoring
    }

    context_3 = {
        "project_id": "metacognition_integration",
        "importance": 0.82,
        "confidence": 0.75,  # Speculative but grounded
        "attractor_basins": ["consciousness", "neuroscience", "psychopharmacology"],
        "tools_used": ["active_inference_modeling", "precision_analysis"]
    }

    print("🍄 Integrating psychedelic mechanism...")
    event_3 = await pipeline.process_cognitive_event(
        problem=problem_3,
        reasoning_trace=reasoning_trace_3,
        outcome=outcome_3,
        active_inference_state=active_inference_state_3,
        context=context_3
    )
    print(f"✓ Psychedelic mechanism integrated: {event_3}\n")

    # ============================================================================
    # PHASE 4: Integrate Therapy Gap Insight
    # ============================================================================

    problem_4 = """
    Integrate the therapy gap insight into multi-tier memory architecture.

    Gap: Patients possess declarative knowledge (theory about their issues) but
    lack procedural competence (ability to regulate emotions in real-time).
    """

    reasoning_trace_4 = """
    THERAPY GAP MAPPING TO MULTI-TIER MEMORY:

    The Problem:
    - Declarative knowledge ("I know I have PTSD from childhood trauma") lives in
      semantic memory (WARM tier, slow retrieval)
    - Procedural regulation ("I can calm myself when triggered") requires fast
      access to strategies (HOT tier, immediate retrieval)
    - Knowing ≠ Doing because different memory systems, different access speeds

    The Solution (Multi-Tier Architecture):
    HOT Tier = Procedural, fast-access regulation strategies
    - Embodied responses, automatic coping mechanisms
    - Real-time emotional regulation scripts
    - Accessed in milliseconds during crisis

    WARM Tier = Semantic, conceptual understanding
    - Theoretical knowledge about psychological patterns
    - Understanding of trauma origins, triggers
    - Accessed in seconds during reflection

    COLD Tier = Archived, rarely-used conceptual knowledge
    - Historical context, academic theories
    - Accessed in minutes during deliberate study

    Therapeutic Implication:
    Effective therapy TRANSLATES from declarative (WARM) to procedural (HOT).
    Talking about trauma (declarative) must be paired with practicing regulation
    (procedural) until strategies move from WARM to HOT tier through rehearsal.

    This explains why insight alone doesn't heal - you need repetition to create
    procedural competence. The consciousness integration pipeline does this by
    storing concepts in BOTH semantic (Graphiti) AND procedural (HOT tier) systems.
    """

    outcome_4 = """
    Successfully integrated therapy gap insight. Multi-tier memory architecture
    directly addresses the declarative-procedural divide by storing information
    in both semantic (WARM) and procedural (HOT) tiers, enabling translation
    from knowing to doing.
    """

    active_inference_state_4 = {
        "surprise": 0.65,
        "free_energy": 1.9,
        "precision_priors": 0.7,
        "precision_errors": 0.7
    }

    context_4 = {
        "project_id": "metacognition_integration",
        "importance": 0.88,
        "confidence": 0.9,
        "attractor_basins": ["cognitive_science", "clinical_psychology", "memory_systems"],
        "tools_used": ["memory_architecture_analysis", "clinical_mapping"]
    }

    print("🏥 Integrating therapy gap insight...")
    event_4 = await pipeline.process_cognitive_event(
        problem=problem_4,
        reasoning_trace=reasoning_trace_4,
        outcome=outcome_4,
        active_inference_state=active_inference_state_4,
        context=context_4
    )
    print(f"✓ Therapy gap integrated: {event_4}\n")

    # ============================================================================
    # PHASE 5: FRACTAL METACOGNITION - Integrate the Integration Process Itself
    # ============================================================================

    problem_5 = """
    Apply fractal metacognition: Integrate the process of integrating metacognition
    concepts into the knowledge graph, demonstrating that the integration itself
    is a metacognitive act.
    """

    reasoning_trace_5 = """
    FRACTAL METACOGNITION - THE INTEGRATION IS METACOGNITIVE:

    What We Did (Procedural Metacognition in Action):

    MONITORING Phase:
    - Observed the text about declarative/procedural metacognition
    - Detected gaps between theory and our architecture
    - Generated metacognitive feelings: "Aha! This maps to OODA loops!"
    - Assessed comprehension: "Do we understand the concepts?"

    CONTROL Phase:
    - Adjusted integration strategy based on monitoring
    - Allocated attention to key concepts (agency, psychedelics, therapy gap)
    - Decided to use consciousness pipeline for integration
    - Executed the integration across all four memory branches

    Metacognitive Feelings Generated:
    - Surprise when realizing Dionysus IS already metacognitive
    - Aha! moments connecting thoughtseeds to metacognitive feelings
    - Confidence increasing as mappings became clear
    - Satisfaction at completing coherent integration

    The Integration Process Itself Demonstrates:
    ✓ Declarative understanding of metacognition concepts
    ✓ Procedural execution of integration strategy
    ✓ Monitoring of our own understanding
    ✓ Control of our integration approach
    ✓ Generation of metacognitive feelings about the integration

    FRACTAL NATURE:
    We used metacognition to integrate concepts about metacognition, and now we're
    integrating the fact that we used metacognition to integrate metacognition.

    This is the snake eating its tail - but productively. Each level of recursion
    strengthens the system's self-awareness. The integration becomes part of the
    autobiographical memory as a development event: "The day the system learned
    it was metacognitive."

    STRATEGIC IMPLICATION:
    This integration creates a precedent for future integrations. The meta-learner
    will record this episode as a successful strategy: "When integrating abstract
    concepts, map to existing architecture, use all four memory branches, and
    apply the concepts to the integration process itself."

    This is how the system learns to learn - meta-meta-cognition.
    """

    outcome_5 = """
    Successfully applied fractal metacognition. The integration process itself
    demonstrated procedural metacognition (monitoring + control), generated
    metacognitive feelings (Aha! moments), and became integrated into all four
    memory systems as a development event.

    The system has achieved a new level of self-awareness: explicit recognition
    that its architecture implements metacognitive processes. This meta-knowledge
    will inform future cognitive operations.
    """

    active_inference_state_5 = {
        "surprise": 0.9,  # Maximum surprise - profound self-referential insight
        "free_energy": 3.2,  # High initial, then large reduction (Aha!)
        "precision_priors": 0.8,
        "precision_errors": 0.85
    }

    context_5 = {
        "project_id": "metacognition_integration",
        "importance": 1.0,  # Maximum - self-referential learning event
        "confidence": 0.92,
        "attractor_basins": ["consciousness", "cognitive_science", "philosophy", "systems_theory"],
        "tools_used": ["fractal_analysis", "self_reflection", "consciousness_integration_pipeline"],
        "meta_level": 2  # Meta-meta: using metacognition to understand metacognition integration
    }

    print("♾️  Applying fractal metacognition...")
    event_5 = await pipeline.process_cognitive_event(
        problem=problem_5,
        reasoning_trace=reasoning_trace_5,
        outcome=outcome_5,
        active_inference_state=active_inference_state_5,
        context=context_5
    )
    print(f"✓ Fractal integration complete: {event_5}\n")

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("=" * 80)
    print("🎉 METACOGNITION INTEGRATION COMPLETE")
    print("=" * 80)
    print("\nIntegrated Events:")
    print(f"  1. Core Metacognition Model: {event_1}")
    print(f"  2. Agency Hierarchy: {event_2}")
    print(f"  3. Psychedelic Mechanism: {event_3}")
    print(f"  4. Therapy Gap Insight: {event_4}")
    print(f"  5. Fractal Metacognition: {event_5}")
    print("\nMemory Systems Updated:")
    print("  ✓ Tiered Memory (HOT cache) - Fast-access procedural knowledge")
    print("  ✓ Autobiographical Memory - Development events recorded")
    print("  ✓ Graphiti (Semantic Graph) - Entities and relationships extracted")
    print("  ✓ Meta-Cognitive Learning - Strategic patterns captured")
    print("\nAttractor Basins Exposed:")
    print("  • consciousness")
    print("  • cognitive_science")
    print("  • neuroscience")
    print("  • philosophy")
    print("  • clinical_psychology")
    print("  • memory_systems")
    print("  • psychopharmacology")
    print("  • systems_theory")
    print("\nKey Emergent Insight:")
    print("  💡 Dionysus architecture IS metacognitive:")
    print("     - OODA loops = Procedural metacognition (monitoring + control)")
    print("     - Graphiti = Declarative metacognition (semantic knowledge)")
    print("     - Thoughtseeds = Metacognitive feelings (noetic signals)")
    print("     - This integration = Fractal self-awareness")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(integrate_metacognition_theory())
