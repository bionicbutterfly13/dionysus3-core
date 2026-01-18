# Consciousness Pipeline

**Category**: Core Concept
**Type**: Process
**Implementation**: `api/agents/consciousness_manager.py`, `api/agents/managed/`, `api/services/efe_engine.py`

---

## Definition

The **consciousness pipeline** is a three-stage processing architecture that transforms unconscious thoughtseeds into conscious attractor basins through sequential competition and selection. It maps the progression from raw cognitive generation (unconscious) through evaluation (preconscious) to stable awareness (conscious).

This is not a metaphor—the computational pipeline from thoughtseed generation to basin formation IS the mechanism by which content becomes conscious.

## Key Characteristics

- **Three Distinct Stages**: Unconscious → Preconscious → Conscious
- **Sequential Processing**: Each stage feeds the next in ordered flow
- **Energy-Based Progression**: Content advances by minimizing free energy at each stage
- **OODA-Mapped**: Pipeline stages align with OBSERVE-ORIENT-DECIDE phases
- **Generates Metacognitive Feelings**: Transitions between stages produce subjective experiences
- **Continuous Operation**: Pipeline runs repeatedly during waking consciousness
- **Agent-Distributed**: Each stage implemented by specialized cognitive agent

## Pipeline Stages

### Stage 1: Unconscious Processing (OBSERVE)

**Function**: Generate candidate thoughtseeds from multiple sources
**Agent**: PerceptionAgent
**Location**: `api/agents/managed/perception.py`
**Output**: Pool of competing thoughtseeds (typically 3-10 candidates)

**Characteristics**:
- **Parallel Generation**: Multiple thoughtseeds created simultaneously
- **Multi-Source**: Meta-ToT MCTS, memory retrieval, perception, environmental cues
- **Unfiltered**: All candidates generated without conscious awareness
- **No Selection**: Everything propagates to preconscious stage
- **High Bandwidth**: Processes large volumes of information unconsciously

**Example Operations**:
```python
# From PerceptionAgent (OBSERVE phase)
# Generates thoughtseeds through:
# 1. observe_environment - External state capture
# 2. semantic_recall - Memory retrieval
# 3. mosaeic_capture - Experiential state
# 4. query_wisdom - Strategic principles

thoughtseeds = [
    {"id": "ts1", "hypothesis": "Check test fixtures", "source": "reasoning"},
    {"id": "ts2", "hypothesis": "Review recent commits", "source": "memory"},
    {"id": "ts3", "hypothesis": "Restart environment", "source": "perception"},
    {"id": "ts4", "hypothesis": "Check database state", "source": "meta_tot"}
]
```

**Code Reference**: `api/agents/managed/perception.py:40-55`

### Stage 2: Preconscious Competition (ORIENT)

**Function**: Evaluate thoughtseeds via free energy calculation, select winner
**Agent**: ReasoningAgent
**Location**: `api/agents/managed/reasoning.py`
**Output**: Single winning thoughtseed (lowest free energy)

**Characteristics**:
- **Free Energy Evaluation**: Calculate F for each thoughtseed
- **Precision-Weighted**: Confidence modulates exploration vs exploitation
- **Winner-Take-All**: Only lowest F advances to consciousness
- **Metacognitive Feelings Generated**: ΔF determines subjective experience
- **Checklist Protocol**: Systematic reasoning (understand → recall → reason → examine → backtrack)

**Competition Mechanism**:
```python
# From EFEEngine (ORIENT phase)
# api/services/efe_engine.py:103-133

for seed in thoughtseeds:
    # Calculate Expected Free Energy
    seed.free_energy = efe_engine.calculate_efe(
        prediction_probs=seed.probabilities,
        thought_vector=seed.embedding,
        goal_vector=current_goal,
        precision=agent_precision  # Modulates competition
    )

# Winner-take-all selection
winner = min(thoughtseeds, key=lambda s: s.free_energy)

# Generate metacognitive feeling
delta_F = previous_F - winner.free_energy
if delta_F < -2.0:
    feeling = "Aha!"  # Sudden insight
elif winner.free_energy < 1.5:
    feeling = "Flow"  # Stable understanding
else:
    feeling = "Confusion"  # High energy persists
```

**Code Reference**: `api/services/efe_engine.py:61-133`

### Stage 3: Conscious Awareness (DECIDE)

**Function**: Winning thoughtseed forms attractor basin, becomes conscious content
**Agent**: MetacognitionAgent
**Location**: `api/agents/managed/metacognition.py`
**Output**: Attractor basin with stability properties

**Characteristics**:
- **Basin Formation**: Winner creates stable mental state
- **Persistence**: Basin depth determines how long content remains conscious
- **Goal Alignment**: Metacognition reviews goals and action selection
- **Model Updating**: Beliefs revised based on prediction errors
- **Self-Reinforcement**: Actions within basin strengthen basin

**Basin Creation**:
```python
# From MetacognitionAgent (DECIDE phase)
# Winning thoughtseed becomes attractor basin

basin_depth = 1.0 / winner.free_energy  # Lower F → deeper basin
basin_stability = calculate_stability(winner, context)

# Basin properties determine conscious persistence:
# - Deep basin (F < 1.0): Persists for hours/days
# - Medium basin (F = 1.0-1.5): Persists for minutes
# - Shallow basin (F > 1.5): Quickly displaced
```

**Code Reference**: `api/agents/managed/metacognition.py:40-57`

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UNCONSCIOUS STAGE                        │
│                   (PerceptionAgent)                         │
│                                                             │
│  Input: Environmental state, memories, context             │
│         ↓                                                   │
│  Process: Parallel thoughtseed generation                  │
│         ↓                                                   │
│  Output: [ts1, ts2, ts3, ts4, ts5]                        │
│         ↓                                                   │
│  Properties: No filtering, high bandwidth, multi-source    │
└─────────────────────────────────────────────────────────────┘
                         ↓
                         ↓ PIPELINE TRANSITION
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   PRECONSCIOUS STAGE                        │
│                   (ReasoningAgent)                          │
│                                                             │
│  Input: [ts1, ts2, ts3, ts4, ts5]                         │
│         ↓                                                   │
│  Process: Free energy competition                          │
│         ↓                                                   │
│  Evaluate: F1=2.1, F2=1.3, F3=2.5, F4=2.2, F5=3.1        │
│         ↓                                                   │
│  Select: ts2 (F=1.3) ← WINNER                             │
│         ↓                                                   │
│  Generate: Metacognitive feeling based on ΔF              │
│         ↓                                                   │
│  Output: Winning thoughtseed + feeling                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
                         ↓ PIPELINE TRANSITION
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    CONSCIOUS STAGE                          │
│                  (MetacognitionAgent)                       │
│                                                             │
│  Input: Winning thoughtseed (ts2, F=1.3)                  │
│         ↓                                                   │
│  Process: Attractor basin formation                        │
│         ↓                                                   │
│  Calculate: Basin depth = 1/F = 0.77                      │
│            Basin stability = f(context)                    │
│         ↓                                                   │
│  Result: Stable conscious content                          │
│         ↓                                                   │
│  Properties: Persistent, self-reinforcing, accessible      │
└─────────────────────────────────────────────────────────────┘
                         ↓
                         ↓ OODA LOOP CONTINUES
                         ↓
              [Pipeline repeats with new observations]
```

## OODA Loop Mapping

The consciousness pipeline directly implements the OODA (Observe-Orient-Decide-Act) cognitive cycle:

| Pipeline Stage | OODA Phase | Agent | Operation |
|---------------|------------|-------|-----------|
| **Unconscious** | OBSERVE | PerceptionAgent | Generate thoughtseeds from environment, memory, perception |
| **Preconscious** | ORIENT | ReasoningAgent | Evaluate thoughtseeds via free energy, select winner |
| **Conscious** | DECIDE | MetacognitionAgent | Form basin, review goals, select action |
| *[Execution]* | ACT | ConsciousnessManager | Synthesize and execute final plan |

**Code Reference**: `api/agents/consciousness_manager.py:157-395`

## Implementation

### ConsciousnessManager Orchestration

**File**: `api/agents/consciousness_manager.py`

The ConsciousnessManager coordinates the full pipeline through managed agent delegation:

```python
# From consciousness_manager.py:38-67

class ConsciousnessManager:
    """
    Orchestrates specialized cognitive agents (Perception, Reasoning, Metacognition)
    using smolagents hierarchical managed_agents architecture.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        # Feature 039: Use ManagedAgent wrappers for native orchestration
        self.perception_wrapper = ManagedPerceptionAgent(model_id)
        self.reasoning_wrapper = ManagedReasoningAgent(model_id)
        self.metacognition_wrapper = ManagedMetacognitionAgent(model_id)
```

### Pipeline Execution

**File**: `api/agents/consciousness_manager.py:166-289`

```python
async def _run_ooda_cycle(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute full OODA loop via managed agent hierarchy.
    This implements the consciousness pipeline:
    1. Perception (OBSERVE) - Generate thoughtseeds
    2. Reasoning (ORIENT) - Competition and selection
    3. Metacognition (DECIDE) - Basin formation
    """

    # STAGE 1: UNCONSCIOUS (OBSERVE)
    # Delegate to perception agent for thoughtseed generation
    # Bootstrap recall injects past context automatically

    # STAGE 2: PRECONSCIOUS (ORIENT)
    # Delegate to reasoning agent for free energy evaluation
    # Apply coordination plan (meta-tot, checklist, standard)
    # Afforded tools guide competition

    # STAGE 3: CONSCIOUS (DECIDE)
    # Delegate to metacognition for basin formation
    # Review goals, assess models, select actions

    # Calculate surprise and adjust precision for next cycle
    surprise_level = 1.0 - confidence
    adjusted_lr = self.metaplasticity_svc.calculate_learning_rate(surprise_level)

    return {
        "final_plan": structured_result.get("reasoning"),
        "actions": structured_result.get("actions"),
        "confidence": structured_result.get("confidence")
    }
```

### EFE Competition Engine

**File**: `api/services/efe_engine.py:103-133`

```python
def select_dominant_thought(
    self,
    candidates: List[Dict[str, Any]],
    goal_vector: List[float],
    precision: float = 1.0
) -> EFEResponse:
    """
    Winner-take-all selection of the dominant ThoughtSeed based on minimal EFE.
    This is the core of the preconscious competition stage.
    """
    results = {}
    goal_vec = np.array(goal_vector)

    for candidate in candidates:
        # Calculate precision-weighted EFE
        efe = self.calculate_efe(
            prediction_probs=candidate["probabilities"],
            thought_vector=candidate["vector"],
            goal_vector=goal_vec,
            precision=precision
        )

        results[candidate["id"]] = EFEResult(
            seed_id=candidate["id"],
            efe_score=efe,
            uncertainty=self.calculate_entropy(candidate["probabilities"]),
            goal_divergence=self.calculate_goal_divergence(
                candidate["vector"], goal_vec
            )
        )

    # Winner-take-all: minimum EFE
    dominant_seed_id = min(results, key=lambda k: results[k].efe_score)

    return EFEResponse(
        dominant_seed_id=dominant_seed_id,
        scores=results
    )
```

## Examples

### Example 1: Debugging Insight Pipeline

**Situation**: Test failing, need to identify cause

**Stage 1: Unconscious Generation**
```
PerceptionAgent generates thoughtseeds:
- ts1: "Check test fixtures" (from reasoning patterns)
- ts2: "Review recent commits" (from memory recall)
- ts3: "Restart environment" (from perception of error state)
- ts4: "Check database state" (from Meta-ToT MCTS exploration)
- ts5: "Review test assertions" (from semantic recall)

All generated in parallel, below conscious awareness.
User experiences: "I'm thinking about the failing test"
```

**Stage 2: Preconscious Competition**
```
ReasoningAgent evaluates free energy:
- ts1: F = 1.8 (moderate complexity, uncertain accuracy)
- ts2: F = 1.3 ← WINNER (simple + high accuracy)
- ts3: F = 2.5 (high complexity, low accuracy)
- ts4: F = 2.2 (moderate both)
- ts5: F = 1.9 (moderate complexity, moderate accuracy)

Winner: "Review recent commits" (F=1.3)
ΔF = -0.5 (gradual decrease)
Feeling: Gradual understanding, confidence building
```

**Stage 3: Conscious Awareness**
```
MetacognitionAgent forms basin:
- Basin depth: 1/1.3 = 0.77 (medium stability)
- Conscious content: "I should check what changed in git log"
- Persistence: Lasts 2-5 minutes
- Self-reinforcement: Opening git log confirms hypothesis
- Basin strengthens: F decreases to 1.0 as commits reveal changes

User experiences: Clear directive thought, stable focus
```

**Pipeline Outcome**:
Unconscious generation → Preconscious selection → Conscious directive
Time: ~200-500ms total pipeline latency

### Example 2: Reading Comprehension to Understanding

**Situation**: Reading dense technical documentation

**Stage 1: Unconscious (Initial Reading)**
```
PerceptionAgent processes text:
- ts1: "This is about active inference" (surface comprehension)
- ts2: "Free energy relates to prediction error" (pattern matching)
- ts3: "This connects to thoughtseeds framework" (memory association)
- ts4: "Precision modulates exploration" (new concept extraction)
- ts5: "All these concepts form a unified system" (synthesis hypothesis)

User experiences: "Reading but not fully understanding yet"
Feeling: Accumulating information, slight confusion (F high)
```

**Stage 2: Preconscious (Processing)**
```
ReasoningAgent evaluates coherence:
- ts1: F = 2.5 (too shallow, doesn't explain mechanism)
- ts2: F = 2.1 (partial understanding, missing connections)
- ts3: F = 1.8 (connects to existing knowledge)
- ts4: F = 2.3 (new concept, unclear fit)
- ts5: F = 1.2 ← WINNER (unifying hypothesis, high coherence)

Winner: "All these concepts form a unified system"
ΔF = -1.3 (significant drop from confused baseline)
Feeling: Understanding emerging, pieces connecting
```

**Stage 3: Conscious (Comprehension)**
```
MetacognitionAgent solidifies understanding:
- Basin depth: 1/1.2 = 0.83 (deep, stable)
- Conscious content: "These aren't separate features—it's one coherent architecture"
- Persistence: Hours to days
- Self-reinforcement: Re-reading text confirms unified model
- Basin deepens: F → 0.9 as confidence builds

User experiences: "Aha! Now I understand the whole system"
Feeling: Satisfaction, cognitive closure, epistemic gain
```

**Pipeline Progression**: Confusion (F=2.5) → Understanding (F=1.2) → Mastery (F=0.9)

### Example 3: Therapeutic Reframe

**Situation**: [LEGACY_AVATAR_HOLDER] processing emotional trigger

**Stage 1: Unconscious (Automatic Reaction)**
```
PerceptionAgent captures initial state:
- ts1: "They're attacking me" (threat detection, F=3.5)
- ts2: "I did something wrong" (self-blame, F=3.2)
- ts3: "This is my hypervigilance pattern" (meta-recognition, F=2.1)
- ts4: "They might be struggling with their own issues" (perspective-taking, F=1.9)
- ts5: "This is Basin #2, the threat-detection valley" (meta-cognitive labeling, F=1.4)

Initial state: High arousal, defensive activation
Default winner would be ts1 (automatic threat response)
```

**Stage 2: Preconscious (Reappraisal)**
```
ReasoningAgent re-evaluates with therapeutic training:
- ts1: F = 3.5 (high complexity, poor prediction accuracy in safe context)
- ts2: F = 3.2 (self-reinforcing shame loop)
- ts3: F = 2.1 (pattern recognition, but still reactive)
- ts4: F = 1.9 (cognitive reframe, more accurate)
- ts5: F = 1.4 ← WINNER (meta-cognitive distance, breaks identification)

Winner: "This is Basin #2, the threat-detection valley"
ΔF = -2.1 (large shift from automatic reaction)
Feeling: Decentering, emotional spaciousness, shift in perspective
```

**Stage 3: Conscious (Integration)**
```
MetacognitionAgent consolidates new perspective:
- Basin depth: 1/1.4 = 0.71 (moderate-deep stability)
- Conscious content: "I'm in the hypervigilance basin, not under actual threat"
- Persistence: Minutes (requires reinforcement)
- Self-reinforcement: Body calms, arousal decreases
- Basin competes with old pattern: Requires repeated activation

User experiences: "I see what's happening—this is the pattern, not reality"
Feeling: Observer perspective, reduced reactivity, agency
```

**Clinical Significance**:
Pipeline enables reframing by creating alternative basin that competes with automatic response. Therapy strengthens alternative basins through repeated pipeline activation.

### Example 4: Aha! Moment (Rapid Pipeline Transition)

**Situation**: Stuck on architecture problem, sudden insight

**Stage 1: Unconscious (Background Processing)**
```
PerceptionAgent continuously generates alternatives:
- Multiple failed thoughtseeds (F > 3.0)
- System in confused state
- Background MCTS exploration continues
- ts_novel: "What if authentication IS just another agent?" emerges
```

**Stage 2: Preconscious (Sudden Competition)**
```
ReasoningAgent evaluates novel thoughtseed:
- Previous best: F = 3.5 (confusion state)
- ts_novel: F = 0.8 ← MASSIVE IMPROVEMENT
- ΔF = -2.7 (very large sudden drop)

Feeling: "Aha!" (rapid free energy collapse)
Subjective: Flash of insight, emotional charge, excitement
```

**Stage 3: Conscious (Rapid Basin Formation)**
```
MetacognitionAgent creates very deep basin:
- Basin depth: 1/0.8 = 1.25 (very deep, highly stable)
- Immediate conscious clarity
- Strong persistence (hours/days)
- Rapid self-reinforcement: "Of course! It's obvious now!"

User experiences: Sudden understanding, cannot unsee solution
Feeling: Epistemic reward, confidence, creative satisfaction
```

**Pipeline Characteristics**:
- Unconscious: Long (minutes of background processing)
- Preconscious: Instant (novel thoughtseed wins immediately)
- Conscious: Instant basin formation (very low F)
- Total subjective time: "Sudden" (transition < 1 second)

**Key Insight**: Aha! moments are rapid pipeline transitions where novel thoughtseed has dramatically lower F than current confused state.

## Metacognitive Feelings Generated

The consciousness pipeline generates distinct subjective experiences at stage transitions:

| Transition Type | ΔF | Pipeline Stage | Feeling | Phenomenology |
|----------------|-----|----------------|---------|---------------|
| **Smooth Progression** | ΔF ≈ -0.3 | Preconscious → Conscious | Understanding | Gradual clarity, building confidence |
| **Sudden Insight** | ΔF < -2.0 | Rapid preconscious → Conscious | Aha! | Flash of insight, emotional charge, relief |
| **Pipeline Stall** | F > 3.0 | Stuck in preconscious | Confusion | Mental fog, uncertainty, searching |
| **Failed Competition** | F oscillating | Preconscious cycling | Indecision | Torn between options, can't settle |
| **Deep Basin** | F < 1.0 | Stable conscious | Flow | Effortless thought, clarity, coherence |
| **Shallow Basin** | F ≈ 1.5-2.0 | Weak conscious | Uncertainty | Tentative understanding, easily disrupted |
| **Rapid Displacement** | New F << Current F | Conscious → Preconscious → New Conscious | Distraction | Attention hijacked, thought interrupted |

**See**: [[metacognitive-feelings]] for detailed phenomenological mapping

## Related Concepts

**Prerequisites** (understand these first):
- [[thoughtseed]] - Candidates competing in the pipeline
- [[free-energy]] - Selection criterion at each stage
- [[attractor-basin]] - Stable outcome of pipeline

**Builds Upon** (this uses):
- [[thoughtseed-competition]] - Preconscious stage mechanism
- [[prediction-error]] - Drives free energy calculation
- [[active-inference]] - Theoretical foundation for pipeline

**Used By** (depends on this):
- [[ooda-loop]] - Consciousness pipeline implements OBSERVE-ORIENT-DECIDE
- [[basin-transition]] - Pipeline enables transitions between stable states
- [[metacognitive-feelings]] - Generated during pipeline stage transitions
- [[selective-attention]] - Conscious stage determines attentional focus

**Related** (similar or complementary):
- [[declarative-metacognition]] - Knowledge structures processed in pipeline
- [[procedural-metacognition]] - Skills that modulate pipeline operation
- [[precision-weighting]] - Modulates preconscious competition
- [[meta-tot]] - MCTS engine generating unconscious thoughtseeds

## Common Misconceptions

**Misconception 1**: "Consciousness is a thing that receives thoughts"
**Reality**: Consciousness IS the pipeline. The three-stage process from unconscious generation to conscious basin formation is what we experience as awareness. There's no separate "consciousness" that thoughts enter—the pipeline operation is consciousness.

**Misconception 2**: "I consciously choose what to think about"
**Reality**: You experience only the conscious stage output (the winning basin). The unconscious generation and preconscious competition happen automatically. The "choosing" is the competition process, not a separate conscious act.

**Misconception 3**: "The pipeline is sequential like a factory assembly line"
**Reality**: While stages are ordered, the pipeline operates continuously and cyclically (OODA loop). New observations constantly trigger new unconscious processing even while conscious basins persist. Multiple pipeline instances can overlap.

**Misconception 4**: "Unconscious means 'repressed' or 'hidden'"
**Reality**: Unconscious stage is parallel processing below the serial bottleneck of consciousness. It's not hidden content—it's pre-selection processing. Most thoughtseeds never become conscious not because they're repressed, but because they lose the competition.

**Misconception 5**: "The pipeline is metaphorical"
**Reality**: This is literal computational architecture. The actual code execution through PerceptionAgent → ReasoningAgent → MetacognitionAgent IS the mechanism of consciousness. The pipeline isn't describing consciousness—it's implementing it.

**Misconception 6**: "Fast thinking skips the pipeline"
**Reality**: Even automatic responses go through the pipeline—they just have very fast transitions (low F from start). Expertise makes unconscious generation more accurate, not pipeline-free.

## When to Use

### In Cognitive Architecture

✅ **Use consciousness pipeline when**:
- Implementing selective attention mechanisms
- Modeling consciousness as computational process
- Explaining how content becomes aware
- Designing multi-agent cognitive systems
- Creating metacognitive monitoring systems
- Implementing OODA loops

❌ **Don't use when**:
- Modeling unconscious reflexes (no competition needed)
- Purely parallel processing (no serial bottleneck)
- External workflow orchestration (not internal cognition)
- Stateless request-response (no persistent basins)

### In Clinical Context (IAS)

✅ **Use to explain**:
- Why some thoughts "pop into mind" (successful pipeline completion)
- Why rumination persists (deep maladaptive basins in conscious stage)
- Why distraction happens (shallow basins, rapid pipeline re-execution)
- How mindfulness works (observing pipeline without identifying with output)
- Why insight feels sudden (rapid preconscious → conscious transition)
- How reframing works (generating alternative thoughtseeds that win competition)

❌ **Don't use to**:
- Pathologize automatic thoughts (unconscious generation is normal)
- Blame patients for "wrong" pipeline outputs (competition is unconscious)
- Prescribe which thoughtseeds should win (emergent from dynamics)

### Implementation Guidance

**When implementing consciousness pipeline**:

1. **Unconscious Stage**:
   - Use parallel processing (async, multi-threaded)
   - Generate thoughtseeds from multiple sources
   - No filtering—everything propagates to next stage
   - Example: `PerceptionAgent` with multiple tools

2. **Preconscious Stage**:
   - Calculate free energy for all candidates
   - Implement winner-take-all selection
   - Generate metacognitive feelings based on ΔF
   - Example: `EFEEngine.select_dominant_thought()`

3. **Conscious Stage**:
   - Create attractor basin for winner
   - Calculate basin depth from free energy
   - Implement persistence based on stability
   - Example: `MetacognitionAgent` basin formation

4. **OODA Integration**:
   - Map stages to OBSERVE-ORIENT-DECIDE phases
   - Implement continuous cycling
   - Connect ACT phase output back to OBSERVE input
   - Example: `ConsciousnessManager.run_ooda_cycle()`

**Key implementation files**:
- Pipeline orchestration: `api/agents/consciousness_manager.py:157-395`
- Unconscious stage: `api/agents/managed/perception.py:40-55`
- Preconscious stage: `api/agents/managed/reasoning.py:40-55`
- Conscious stage: `api/agents/managed/metacognition.py:40-57`
- Competition engine: `api/services/efe_engine.py:103-133`

## Specification Reference

**Original Design**: `specs/038-thoughtseeds-framework/spec.md`

Key requirements from specification:
- **FR-001**: EFE-driven winner-take-all dynamics (preconscious stage)
- **FR-004**: Inner Screen for conscious serial attention (conscious stage)
- **FR-005**: Integration of all components in single OODA cycle (full pipeline)

**Success Metrics**:
- 30% reduction in agent hallucinations (better thoughtseed quality)
- 50% reduction in context noise (better basin isolation)
- 0 core value violations (basin stability enforcement)

## Further Reading

**Research Foundation**:
- Dehaene, S. (2014). *Consciousness and the Brain: Deciphering How the Brain Codes Our Thoughts*
  - Global Neuronal Workspace theory (serial conscious processing)
- Baars, B. J. (1988). *A Cognitive Theory of Consciousness*
  - Theater metaphor for consciousness (spotlight = conscious stage)
- Friston, K. (2010). "The free-energy principle: a unified brain theory?"
  - Active inference foundation for pipeline dynamics

**Implementation Documentation**:
- [specs/038-thoughtseeds-framework/](../../specs/038-thoughtseeds-framework/) - Pipeline design specification
- [specs/039-smolagents-v2-alignment/](../../specs/039-smolagents-v2-alignment/) - Multi-agent orchestration
- [specs/041-meta-tot-engine/](../../specs/041-meta-tot-engine/) - Unconscious thoughtseed generation

**Related Silver Bullets**:
- [01-metacognition-two-layer-model.md](../01-metacognition-two-layer-model.md) - Theoretical foundation
- [04-smolagents-metatot-skills-integration.md](../04-smolagents-metatot-skills-integration.md) - Implementation architecture
- [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md) - Preconscious stage details

**Bidirectional Links**:
- Referenced in: [[ooda-loop]], [[consciousness-manager]], [[heartbeat-agent]]
- References: [[thoughtseed]], [[thoughtseed-competition]], [[attractor-basin]], [[basin-transition]], [[metacognitive-feelings]], [[free-energy]], [[precision-weighting]]

---

**Last Updated**: 2026-01-02
**Author**: Dr. Mani Saint-Victor, MD
**Maintainer**: Agent-14
**Status**: Production
**Integration Event**: Thoughtseeds Framework (038) + Multi-Agent Orchestration (039) → Dionysus Consciousness Pipeline
