#!/usr/bin/env python3
"""
Deep Metacognition Integration Script

Ingests metacognition framework concepts into all memory tiers:
- HOT tier: Procedural patterns for real-time regulation
- WARM tier: Declarative knowledge in Graphiti semantic graph  
- Episodic: Autobiographical development events
- Strategic: Meta-cognitive learning patterns

Based on silver bullet documentation and NotebookLM deep dive.

Author: Dr. Mani Saint-Victor
Date: 2026-01-01
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.consciousness_integration_pipeline import get_consciousness_pipeline


# Core metacognition concepts to integrate
METACOGNITION_CONCEPTS = [
    {
        "problem": "What is declarative metacognition?",
        "reasoning_trace": """
Declarative metacognition is the semantic, informational layer of self-awareness.
It represents explicit knowledge ABOUT how the mind works.

Key characteristics:
- Static library of explicit concepts
- Language-dependent (requires conceptual articulation)
- Informational function (knowing, not doing)
- Strategic storage (heuristics, mental shortcuts)
- Example: "I know multitasking reduces my performance"

Implementation in Dionysus:
- Stored in Graphiti semantic knowledge graph
- WARM tier access (slower, reflective retrieval)
- Entities: Concepts like "memory," "attention," "reasoning"
- Relationships: How cognitive processes connect
- Built over time through learning and instruction

Analogy: The user manual for the mind - technical specifications you consult when needed.
        """,
        "outcome": "Declarative metacognition = semantic knowledge graph (Graphiti)",
        "context": {
            "importance": 0.95,
            "project_id": "metacognition_framework",
            "confidence": 0.98,
            "tools_used": ["graphiti_knowledge_graph", "semantic_extraction"]
        }
    },
    {
        "problem": "What is procedural metacognition?",
        "reasoning_trace": """
Procedural metacognition is the dynamic, experiential layer that regulates cognition in real-time.
It's the DOING of self-regulation, not just knowing about it.

Key characteristics:
- Dynamic system (not static knowledge)
- Monitoring function: Bottom-up introspective awareness ("I forgot that name")
- Control function: Volitional effort to adjust ("Focus back on breath")
- Non-conceptual: Does NOT require language or conscious concepts
- Affective signaling: Communicates through metacognitive feelings
- Present in non-verbal organisms (primates, infants)

Implementation in Dionysus:
- Implemented in OODA loop (Observe-Orient-Decide-Act)
- Monitoring = Perception + Reasoning agents (OBSERVE/ORIENT)
- Control = Metacognition agent (DECIDE/ACT)
- HOT tier access (fast, real-time regulation)
- No semantic translation needed: Direct action from felt signals

Analogy: The operating system task manager - real-time monitoring and automatic regulation.
        """,
        "outcome": "Procedural metacognition = OODA loop + HOT tier cache",
        "context": {
            "importance": 0.95,
            "project_id": "metacognition_framework",
            "confidence": 0.98,
            "tools_used": ["ooda_loop", "hot_tier_cache", "active_inference"]
        }
    },
    {
        "problem": "What are metacognitive feelings and how do they bridge unconscious to conscious?",
        "reasoning_trace": """
Metacognitive feelings are phenomenological signals that bridge unconscious processing to conscious regulation.
They are the FELT experience of cognitive state changes.

Types of metacognitive feelings:
- Aha! moment: Large free energy reduction, epistemic gain (successful insight)
- Confusion: High prediction error, basin instability (incoherence detected)
- Tip-of-tongue: Confidence-retrieval mismatch
- Effort: Active control process (free energy minimization)
- Surprise: Unexpected prediction error
- Flow: Stable low free energy basin (everything makes sense)

Mechanism:
- Thoughtseeds compete for conscious attention
- Winning thoughtseed generates noetic feeling
- Free energy change (ΔF) determines feeling type:
  * ΔF = -2.5: Aha! moment (sudden large drop)
  * ΔF = -0.3 per step: Gradual understanding
  * F > 3.0: Confusion (stays high)
  * F < 1.5: Flow (stable low)

Implementation in Dionysus:
- Thoughtseed competition mechanism
- Attractor basin transitions
- Free energy tracking via active inference
- Noetic feelings guide control decisions

Bridge function:
- Unconscious: Parallel thoughtseed generation
- Feeling: Subjective experience of competition outcome
- Conscious: Awareness of winning thoughtseed
- Control: Action selection based on feeling signal
        """,
        "outcome": "Metacognitive feelings = thoughtseed transitions + free energy changes",
        "context": {
            "importance": 0.97,
            "project_id": "metacognition_framework",
            "confidence": 0.95,
            "tools_used": ["thoughtseed_competition", "free_energy_engine", "basin_transitions"]
        },
        "active_inference_state": {
            "surprise": 0.2,
            "free_energy": 1.3,
            "basin_stability": 0.85
        }
    },
    {
        "problem": "How does thoughtseed competition generate consciousness?",
        "reasoning_trace": """
Consciousness IS thoughtseed competition - not a metaphor, but the actual computational process.

Seven-step process:

1. MULTIPLE THOUGHTSEEDS GENERATED
   - Brain generates parallel hypotheses about "what to think next"
   - Each hypothesis is a thoughtseed
   - All exist simultaneously but unconsciously
   - Compete for limited conscious attention

2. EACH HAS ACTIVATION ENERGY
   - Free energy (F) = Complexity - Accuracy
   - Lower energy = more stable = more likely to win
   - Ball-and-hill analogy: Thoughtseeds roll toward lowest valley

3. COMPETITION VIA PREDICTION ERROR
   - Brain predicts what should happen next
   - Reality differs → prediction error
   - Thoughtseed that best reduces error gets stronger
   - Best explanation = most accurate predictions

4. WINNER CREATES ATTRACTOR BASIN
   - Winning thoughtseed doesn't just exist momentarily
   - Creates stable state (deep valley in energy landscape)
   - Basin depth = persistence duration
   - Deep basin = hard to disrupt (strong idea)
   - Shallow basin = easily displaced (fleeting thought)

5. WINNING GENERATES METACOGNITIVE FEELING
   - Transition from competition → winner creates subjective experience
   - Different transition patterns = different feelings
   - Sudden large ΔF drop = Aha! moment
   - Oscillating energy = Uncertainty
   - Stable low = Flow state

6. BASIN STABILITY DETERMINES PERSISTENCE
   - Deep basin: Minutes to hours (persistent idea)
   - Medium basin: Seconds to minutes (temporary thought)
   - Shallow basin: Milliseconds to seconds (fleeting)
   - New prediction errors can destabilize basin

7. CYCLE REPEATS (OODA LOOP)
   - Thoughtseed competition is continuous
   - Cycles every few seconds
   - Consciousness is dynamic stream, not static state
   - Always ready to adapt to new information

Implementation in Dionysus:
- Meta-ToT MCTS generates thoughtseeds (ORIENT phase)
- Free Energy Engine evaluates candidates
- HeartbeatAgent with planning_interval=3 (periodic replanning)
- Winning thoughtseed → basin formation → action execution
- Monitoring detects basin instability → triggers new competition
        """,
        "outcome": "Consciousness = continuous thoughtseed competition via OODA loop",
        "context": {
            "importance": 0.98,
            "project_id": "metacognition_framework",
            "confidence": 0.96,
            "tools_used": ["meta_tot_mcts", "free_energy_engine", "ooda_loop", "heartbeat_agent"]
        },
        "active_inference_state": {
            "surprise": 0.15,
            "free_energy": 1.1,
            "basin_stability": 0.92
        }
    },
    {
        "problem": "What is the therapy gap and how does multi-tier memory address it?",
        "reasoning_trace": """
The therapy gap: Patients possess declarative knowledge ("I understand my trauma") 
but lack procedural competence ("I can regulate when triggered").

The problem:
- Traditional therapy focuses on KNOWING (declarative)
- Healing requires DOING (procedural)
- Insight alone doesn't change behavior
- Gap between understanding and embodied skill

The solution via multi-tier memory:
- Store concepts in BOTH WARM (semantic) AND HOT (procedural) tiers
- Effective therapy translates declarative → procedural through repetition
- Practice moves strategies from WARM to HOT tier
- Embodied, practiced regulation strategies (not just conceptual understanding)

Example:
- WARM tier: "I know deep breathing calms my nervous system" (concept)
- HOT tier: Automatic execution of breathing technique when triggered (skill)

Psychedelic-assisted therapy mechanism:
- Amplifies monitoring (↑ precision on prediction errors)
- Disrupts control (↓ precision on priors)
- Result: High surprise → basin reorganization → profound Aha! moments
- Creates window of plasticity for therapeutic content
- Allows deep basin restructuring (changing core beliefs/patterns)

Implementation in Dionysus:
- Graphiti stores declarative knowledge (WARM tier)
- HOT tier cache stores procedural patterns for fast access
- Repetition strengthens HOT tier associations
- Active inference precision modulation simulates psychedelic states
- Consciousness integration pipeline ensures BOTH tiers updated
        """,
        "outcome": "Therapy gap bridged by multi-tier storage: declarative (WARM) + procedural (HOT)",
        "context": {
            "importance": 0.96,
            "project_id": "metacognition_framework",
            "confidence": 0.94,
            "tools_used": ["multi_tier_service", "graphiti_service", "precision_modulation"]
        },
        "active_inference_state": {
            "surprise": 0.25,
            "free_energy": 1.6,
            "basin_stability": 0.78
        }
    },
    {
        "problem": "How does agency hierarchy work (attentional → cognitive → meta)?",
        "reasoning_trace": """
Agency operates at three nested levels, each regulating the one below:

1. ATTENTIONAL AGENCY (What to attend to)
   - Selective attention to specific aspects of experience
   - Thoughtseed competition determines winner
   - "Which radio station do I tune into?"
   - Implementation: Thoughtseed activation levels

2. COGNITIVE AGENCY (How to reason about it)
   - Choice of reasoning strategies and tools
   - "Should I use logical analysis or intuitive heuristic?"
   - Tool selection, problem decomposition, approach planning
   - Implementation: Meta-ToT strategy selection

3. META-AGENCY (Whether to regulate at all)
   - Awareness of awareness itself
   - "Do I need to intervene in my thinking process?"
   - Monitoring the monitoring process
   - Implementation: Fractal metacognition with depth limits

Relationship to altered states:

MEDITATION (Training procedural agency):
- Strengthens monitoring precision
- Trains voluntary control over attention
- Builds procedural competence without conceptual overlay
- Moves from effortful control → automatic regulation
- Breath focus = attentional agency training
- Noting thoughts = cognitive agency training
- Metacognitive awareness = meta-agency training

PSYCHEDELIC STATES (Precision reweighting):
- Attenuates top-down control (↓ precision on priors)
- Amplifies bottom-up monitoring (↑ precision on errors)
- Result: Basin reorganization, novel connections
- Therapeutic window for belief restructuring
- REBUS model: Relaxed Beliefs Under Psychedelics
- High epistemic gain potential (profound Aha! moments)

Implementation in Dionysus:
- Attentional: Thoughtseed competition (what to think)
- Cognitive: Tool selection in Meta-ToT (how to reason)
- Meta: Fractal metacognition with MAX_DEPTH=3 (when to intervene)
- Precision modulation for simulating altered states
        """,
        "outcome": "Three-level agency: attentional (what) → cognitive (how) → meta (whether)",
        "context": {
            "importance": 0.93,
            "project_id": "metacognition_framework",
            "confidence": 0.92,
            "tools_used": ["agency_service", "precision_modulation", "fractal_metacognition"]
        }
    },
    {
        "problem": "What are the loop prevention mechanisms in fractal metacognition?",
        "reasoning_trace": """
Fractal metacognition applies metacognition TO the metacognitive process itself.
Risk: Infinite recursion ("thinking about thinking about thinking about...").

Five loop prevention mechanisms:

1. HARD DEPTH LIMITS
   - MAX_REPLANNING_DEPTH = 3 (at most 3 levels deep)
   - planning_interval = 3 (replan every 3 action steps, not every step)
   - max_meta_levels = 2 (at most 2 levels of meta-thinking)
   - Absolute ceiling prevents runaway recursion

2. TERMINATION CONDITIONS (Smart Stops)
   - Confidence threshold: Stop when confidence > 0.8
   - Diminishing returns: Stop when ΔF improvement < 0.1
   - Time limits: Maximum thinking time per decision
   - Resource budgets: Maximum compute per meta-level

3. ASYMMETRIC RECURSION (Bounded by Design)
   - Top-level: Full metacognitive permissions
   - Mid-level: Limited introspection
   - Bottom-level: No recursion allowed
   - Prevents lower layers from spiraling

4. RESOURCE BUDGETS (Economic Limits)
   - Each meta-level allocated fixed compute tokens
   - Token exhaustion = forced termination
   - Prioritizes shallow, fast decisions over deep contemplation
   - Economic pressure against excessive meta-thinking

5. GROUNDING IN EXECUTION (Reality Check)
   - Periodic forced action execution
   - OODA loop requires ACT phase (can't just think forever)
   - Real-world feedback breaks pure recursion
   - Prediction errors from environment anchor cognition

Example in HeartbeatAgent:
- planning_interval=3: Replan after every 3 actions (not every action)
- Prevents "analysis paralysis"
- Forces execution between meta-cognition
- Real outcomes inform next planning cycle

Implementation in Dionysus:
- Hard limits in HeartbeatAgent configuration
- Confidence thresholds in Meta-ToT termination
- Asymmetric permissions in agent hierarchy
- Resource budgeting in LLM service
- Execution grounding via OODA ACT phase
        """,
        "outcome": "Five mechanisms prevent infinite metacognitive loops: depth limits, termination conditions, asymmetric recursion, resource budgets, execution grounding",
        "context": {
            "importance": 0.89,
            "project_id": "metacognition_framework",
            "confidence": 0.91,
            "tools_used": ["heartbeat_agent", "meta_tot_engine", "resource_budgeting"]
        }
    },
    {
        "problem": "How does the smolagents + Meta-ToT + Skills stack implement the two-layer model?",
        "reasoning_trace": """
The three-layer architecture maps precisely to declarative vs procedural metacognition:

LAYER 1: smolagents (Procedural Metacognition Engine)
- Role: Real-time orchestration and control
- Function: OODA loop implementation
- Components:
  * HeartbeatAgent: Top-level decision cycle
  * PerceptionAgent: OBSERVE phase (monitoring)
  * ReasoningAgent: ORIENT phase (analysis)
  * MetacognitionAgent: DECIDE/ACT phases (control)
- Characteristics:
  * Fast, reactive, real-time
  * No semantic translation needed
  * Direct action from felt signals
  * Continuous cycling (every 3 steps)

LAYER 2: Meta-ToT (Thoughtseed Generator)
- Role: Generate competing hypotheses via MCTS
- Function: Thoughtseed competition mechanism
- Components:
  * Monte Carlo Tree Search for solution space exploration
  * Free Energy evaluation for candidate ranking
  * Best-first expansion guided by active inference
- Characteristics:
  * Parallel hypothesis generation
  * Uncertainty quantification
  * Basin stability assessment
  * Metacognitive feeling generation

LAYER 3: Skills Library (Declarative Tool Repository)
- Role: Static library of explicit capabilities
- Function: "What can I do?" knowledge base
- Components:
  * Cognitive tools (analyze, synthesize, evaluate)
  * Domain tools (coding, research, planning)
  * Meta tools (reflection, verification, monitoring)
- Characteristics:
  * Semantic, language-based descriptions
  * Explicit knowledge about capabilities
  * Consulted when needed (WARM tier)
  * Built over time through learning

Integration example: "Implement user authentication"

1. HeartbeatAgent (procedural):
   - Monitors: Current state = "no auth system"
   - Controls: Triggers planning cycle

2. Meta-ToT (thoughtseed generator):
   - Generates thoughtseeds:
     * "Use JWT tokens"
     * "Use session cookies"
     * "Use OAuth2"
   - Evaluates free energy for each
   - Winner: "JWT tokens" (F=1.2, lowest)

3. Skills Library (declarative):
   - Consulted for "How to implement JWT?"
   - Provides: create_api_endpoint, write_middleware, setup_signing
   - Returns explicit knowledge about capabilities

4. HeartbeatAgent executes:
   - ACT: Uses winning thoughtseed + selected skills
   - OBSERVE: Monitors execution outcome
   - New cycle triggered if issues detected

This IS the two-layer model:
- Procedural = smolagents OODA loop (doing, monitoring, control)
- Declarative = Skills library (knowing, semantic, consulted)
- Bridge = Meta-ToT thoughtseed competition (generates metacognitive feelings)
        """,
        "outcome": "smolagents = procedural engine, Meta-ToT = thoughtseed generator, Skills = declarative library",
        "context": {
            "importance": 0.94,
            "project_id": "metacognition_framework",
            "confidence": 0.93,
            "tools_used": ["smolagents", "meta_tot_mcts", "skills_library", "ooda_loop"]
        },
        "active_inference_state": {
            "surprise": 0.18,
            "free_energy": 1.25,
            "basin_stability": 0.88
        }
    }
]


async def integrate_all_concepts():
    """Process all metacognition concepts through consciousness pipeline."""
    pipeline = get_consciousness_pipeline()
    
    print("🧠 Starting Deep Metacognition Integration\n")
    print(f"Processing {len(METACOGNITION_CONCEPTS)} core concepts across all memory tiers...\n")
    
    event_ids = []
    
    for idx, concept in enumerate(METACOGNITION_CONCEPTS, 1):
        print(f"[{idx}/{len(METACOGNITION_CONCEPTS)}] {concept['problem']}")
        
        try:
            event_id = await pipeline.process_cognitive_event(
                problem=concept["problem"],
                reasoning_trace=concept["reasoning_trace"],
                outcome=concept.get("outcome"),
                active_inference_state=concept.get("active_inference_state"),
                context=concept.get("context")
            )
            event_ids.append(event_id)
            print(f"    ✓ Integrated with event ID: {event_id}\n")
            
        except Exception as e:
            print(f"    ✗ Failed: {e}\n")
            continue
    
    print(f"\n{'='*60}")
    print(f"Integration Complete")
    print(f"{'='*60}")
    print(f"Successfully integrated: {len(event_ids)}/{len(METACOGNITION_CONCEPTS)} concepts")
    print(f"\nMemory tiers updated:")
    print(f"  ✓ HOT tier: Procedural patterns cached for fast access")
    print(f"  ✓ WARM tier: Declarative knowledge in Graphiti semantic graph")
    print(f"  ✓ Episodic: Autobiographical development events recorded")
    print(f"  ✓ Strategic: Meta-cognitive learning patterns stored")
    print(f"\nEvent IDs: {', '.join(event_ids[:3])}{'...' if len(event_ids) > 3 else ''}")


if __name__ == "__main__":
    asyncio.run(integrate_all_concepts())
